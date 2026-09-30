"""
Seed curated, high-accuracy Coptic-Arabic core dictionary (Bohairic & Sahidic)
and clean up noisy automated mappings.
"""
import io
import os
import sys
import unicodedata
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///manual_web.db"
sys.path.append(str(Path(__file__).resolve().parents[2]))

from sqlalchemy import select, text
from app.database import SessionLocal
from app.models import ArabicSense, DictionaryEntry, SenseMapping, Source
from app.models.dictionary import Dialect
from app.models.enums import PartOfSpeech, RecordStatus, SourceType
from app.services.text import normalize_arabic

# ----------------------------------------------------------------------
# Clean up obvious erroneous CCL mappings caused by substring splitting
# ----------------------------------------------------------------------
BAD_LEMMA_CLEANUPS = [
    ("الله", ["ⲁⲑⲉⲟⲥ", "ⲁⲥⲉⲃⲏⲥ"]),
    ("ابن", ["ⲡⲟⲗⲓⲧⲏⲥ"]),
    ("المسيح", ["ⲉⲡⲓⲥⲧⲁⲧⲏⲥ"]),
    ("ماء", ["ⲥⲱⲕ", "ϥⲟ", "ⲥⲗϩⲟ", "ϯϩⲙⲉ", "ϣⲁⲣⲕⲉ", "ⳳⲉⲗⲗⲟⲧ", "ϫⲁⲡⲗⲉ", "ⲃⲁⲗⲕⲟⲩ", "ⲉⲓⲁⲗ", "ⲕⲟⲗⲧⲁⳳ", "ⲁⲃⲣⲟⲭⲓⲁ", "ⲕⲁⲇⲟⲥ", "ϩⲩⲇⲣⲁⲅⲱⲅⲟⲥ"]),
    ("عين", ["ⲕⲱⲗⲙ", "ⲗⲟⲩϫ", "ϩⲁⲧⲁⲓⲗⲉ", "ⲁⲩⲧⲟⲥ"]),
]

# ----------------------------------------------------------------------
# Core Curated Vocabulary (Arabic -> (Bohairic, Sahidic, POS, Definition))
# ----------------------------------------------------------------------
CORE_VOCABULARY = [
    # Theological & Biblical
    ("الله", "Ⲫⲛⲟⲩϯ", "ⲡⲛⲟⲩⲧⲉ", PartOfSpeech.noun, "الله، الإله الخالق الضابط الكل"),
    ("اله", "ⲛⲟⲩϯ", "ⲛⲟⲩⲧⲉ", PartOfSpeech.noun, "إله، معبود"),
    ("يسوع", "Ⲓⲏⲥⲟⲩⲥ", "Ⲓⲏⲥⲟⲩⲥ", PartOfSpeech.noun, "يسوع، المخلص، ربنا يسوع المسيح"),
    ("المسيح", "Ⲡⲭⲣⲓⲥⲧⲟⲥ", "Ⲡⲉⲭⲣⲓⲥⲧⲟⲥ", PartOfSpeech.noun, "المسيح، الممسوح، ربنا يسوع المسيح"),
    ("مسيح", "ⲭⲣⲓⲥⲧⲟⲥ", "ⲭⲣⲓⲥⲧⲟⲥ", PartOfSpeech.noun, "مسيح، ممسوح"),
    ("رب", "ϭⲟⲓⲥ", "ϫⲟⲉⲓⲥ", PartOfSpeech.noun, "رب، سيد"),
    ("الرب", "Ⲡϭⲟⲓⲥ", "Ⲡϫⲟⲉⲓⲥ", PartOfSpeech.noun, "الرب، السيد"),
    ("ابن", "ϣⲏⲣⲓ", "ϣⲏⲣⲉ", PartOfSpeech.noun, "ابن، ولد، طفل"),
    ("الابن", "Ⲡϣⲏⲣⲓ", "Ⲡϣⲏⲣⲉ", PartOfSpeech.noun, "الابن"),
    ("اب", "ⲓⲱⲧ", "ⲉⲓⲱⲧ", PartOfSpeech.noun, "أب، والد"),
    ("الاب", "Ⲫⲓⲱⲧ", "Ⲡⲉⲓⲱⲧ", PartOfSpeech.noun, "الآب"),
    ("ام", "ⲙⲁⲩ", "ⲙⲁⲁⲩ", PartOfSpeech.noun, "أم، والدة"),
    ("الام", "Ϯⲙⲁⲩ", "Ⲧⲙⲁⲁⲩ", PartOfSpeech.noun, "الأم"),
    ("روح", "ⲡⲛⲉⲩⲙⲁ", "ⲡⲛⲉⲩⲙⲁ", PartOfSpeech.noun, "روح، الروح"),
    ("الروح", "Ⲡⲓⲡⲛⲉⲩⲙⲁ", "Ⲡⲉⲡⲛⲉⲩⲙⲁ", PartOfSpeech.noun, "الروح"),
    ("قدوس", "ⲟⲩⲁⲃ", "ⲟⲩⲁⲁⲃ", PartOfSpeech.adjective, "قدوس، طاهر، مقدس"),
    ("القدوس", "Ⲫⲏⲉⲑⲟⲩⲁⲃ", "Ⲡⲉⲧⲟⲩⲁⲁⲃ", PartOfSpeech.noun, "القدوس، المقدس"),
    ("قديس", "ⲁⲅⲓⲟⲥ", "ⲁⲅⲓⲟⲥ", PartOfSpeech.noun, "قديس، طاهر"),
    ("صليب", "ⲥⲧⲁⲩⲣⲟⲥ", "ⲥⲧⲁⲩⲣⲟⲥ", PartOfSpeech.noun, "صليب، خشبة الصليب"),
    ("الصليب", "Ⲡⲓⲥⲧⲁⲩⲣⲟⲥ", "Ⲡⲉⲥⲧⲁⲩⲣⲟⲥ", PartOfSpeech.noun, "الصليب"),
    ("انجيل", "ⲉⲩⲁⲅⲅⲉⲗⲓⲟⲛ", "ⲉⲩⲁⲅⲅⲉⲗⲓⲟⲛ", PartOfSpeech.noun, "إنجيل، بشارة مفرحة"),
    ("الانجيل", "Ⲡⲓⲉⲩⲁⲅⲅⲉⲗⲓⲟⲛ", "Ⲡⲉⲩⲁⲅⲅⲉⲗⲓⲟⲛ", PartOfSpeech.noun, "الإنجيل، البشارة"),
    ("كنيسة", "ⲉⲕⲕⲗⲏⲥⲓⲁ", "ⲉⲕⲕⲗⲏⲥⲓⲁ", PartOfSpeech.noun, "كنيسة، جماعة المؤمنين"),
    ("الكنيسة", "Ϯⲉⲕⲕⲗⲏⲥⲓⲁ", "Ⲧⲉⲕⲕⲗⲏⲥⲓⲁ", PartOfSpeech.noun, "الكنيسة"),
    ("صلاة", "ⲉⲩⲭⲏ", "ϣⲗⲏⲗ", PartOfSpeech.noun, "صلاة، تضرع، دعاء"),
    ("الصلاة", "Ϯⲉⲩⲭⲏ", "Ⲡϣⲗⲏⲗ", PartOfSpeech.noun, "الصلاة"),
    ("شكر", "ϣⲉⲡϩ̀ⲙⲟⲧ", "ϣⲡϩⲙⲟⲧ", PartOfSpeech.noun, "شكر، عرفان بالجميل، إفخارستيا"),
    ("الشكر", "Ⲡⲓϣⲉⲡϩ̀ⲙⲟⲧ", "Ⲡϣⲡϩⲙⲟⲧ", PartOfSpeech.noun, "الشكر"),
    ("سلام", "ϩⲓⲣⲏⲛⲏ", "ⲉⲓⲣⲏⲛⲏ", PartOfSpeech.noun, "سلام، طمأنينة، سكينة"),
    ("السلام", "Ϯϩⲓⲣⲏⲛⲏ", "Ⲧⲉⲓⲣⲏⲛⲏ", PartOfSpeech.noun, "السلام"),
    ("محبة", "ⲁⲅⲁⲡⲏ", "ⲙⲉ", PartOfSpeech.noun, "محبة، حب، وداد"),
    ("المحبة", "Ϯⲁⲅⲁⲡⲏ", "Ⲧⲁⲅⲁⲡⲏ", PartOfSpeech.noun, "المحبة، الحب"),
    ("حب", "ⲙⲉⲓ", "ⲙⲉⲣⲉ", PartOfSpeech.noun, "حب، محبة"),
    ("نور", "ⲟⲩⲱⲓⲛⲓ", "ⲟⲩⲟⲉⲓⲛ", PartOfSpeech.noun, "نور، ضياء، إشراق"),
    ("النور", "Ⲡⲓⲟⲩⲱⲓⲛⲓ", "Ⲡⲟⲩⲟⲉⲓⲛ", PartOfSpeech.noun, "النور، الضوء"),
    ("ظلمة", "ⲭⲁⲕⲓ", "ⲕⲁⲕⲉ", PartOfSpeech.noun, "ظلمة، عتمة"),
    ("الظلمة", "Ⲡⲓⲭⲁⲕⲓ", "Ⲡⲕⲁⲕⲉ", PartOfSpeech.noun, "الظلمة"),
    ("حياة", "ⲱⲛϧ", "ⲱⲛϩ", PartOfSpeech.noun, "حياة، عيش، بقاء"),
    ("الحياة", "Ⲡⲓⲱⲛϧ", "Ⲡⲱⲛϩ", PartOfSpeech.noun, "الحياة"),
    ("موت", "ⲙⲟⲩ", "ⲙⲟⲩ", PartOfSpeech.noun, "موت، وفاة، هلاك"),
    ("الموت", "Ⲫⲙⲟⲩ", "Ⲡⲙⲟⲩ", PartOfSpeech.noun, "الموت"),
    ("مجد", "ⲱⲟⲩ", "ⲉⲟⲟⲩ", PartOfSpeech.noun, "مجد، بهاء، عظمة"),
    ("المجد", "Ⲡⲓⲱⲟⲩ", "Ⲡⲉⲟⲟⲩ", PartOfSpeech.noun, "المجد"),
    ("كرامة", "ⲧⲁⲓⲟ", "ⲧⲁⲉⲓⲟ", PartOfSpeech.noun, "كرامة، وقار، إكرام"),
    ("الكرامة", "Ⲡⲓⲧⲁⲓⲟ", "Ⲡⲧⲁⲉⲓⲟ", PartOfSpeech.noun, "الكرامة"),
    ("نعمة", "ϩⲙⲟⲧ", "ϩⲙⲟⲧ", PartOfSpeech.noun, "نعمة، فضل، بركة"),
    ("النعمة", "Ⲡⲓϩⲙⲟⲧ", "Ⲡϩⲙⲟⲧ", PartOfSpeech.noun, "النعمة"),
    ("بركة", "ⲥⲙⲟⲩ", "ⲥⲙⲟⲩ", PartOfSpeech.noun, "بركة، نماء، خير"),
    ("البركة", "Ⲡⲓⲥⲙⲟⲩ", "Ⲡⲥⲙⲟⲩ", PartOfSpeech.noun, "البركة"),
    ("ايمان", "ⲛⲁϩϯ", "ⲡⲓⲥⲧⲓⲥ", PartOfSpeech.noun, "إيمان، تصديق، ثقة بالرب"),
    ("الايمان", "Ⲡⲓⲛⲁϩϯ", "Ⲧⲡⲓⲥⲧⲓⲥ", PartOfSpeech.noun, "الإيمان"),
    ("رجاء", "ϩⲉⲗⲡⲓⲥ", "ϩⲉⲗⲡⲓⲥ", PartOfSpeech.noun, "رجاء، أمل"),
    ("الرجاء", "Ϯϩⲉⲗⲡⲓⲥ", "Ⲧϩⲉⲗⲡⲓⲥ", PartOfSpeech.noun, "الرجاء"),
    ("خلاص", "ⲟⲩϫⲁⲓ", "ⲛⲟϩⲉⲙ", PartOfSpeech.noun, "خلاص، نجاة، فداء"),
    ("الخلاص", "Ⲡⲓⲟⲩϫⲁⲓ", "Ⲡⲛⲟϩⲉⲙ", PartOfSpeech.noun, "الخلاص"),
    ("مخلص", "ⲥⲱⲧⲏⲣ", "ⲥⲱⲧⲏⲣ", PartOfSpeech.noun, "مخلص، منقذ، فادي"),
    ("المخلص", "Ⲡⲓⲥⲱⲧⲏⲣ", "Ⲡⲥⲱⲧⲏⲣ", PartOfSpeech.noun, "المخلص"),
    ("فادي", "ⲣⲉϥⲥⲱϯ", "ⲣⲉϥⲥⲱⲧⲉ", PartOfSpeech.noun, "فادي، مخلص"),
    ("ملكوت", "ⲙⲉⲧⲟⲩⲣⲟ", "ⲙⲛ̄ⲧⲣ̄ⲣⲟ", PartOfSpeech.noun, "ملكوت، مملكة، سلطان"),
    ("الملكوت", "Ϯⲙⲉⲧⲟⲩⲣⲟ", "Ⲧⲙⲛ̄ⲧⲣ̄ⲣⲟ", PartOfSpeech.noun, "الملكوت"),
    ("سماء", "ⲫⲏ", "ⲧⲡⲉ", PartOfSpeech.noun, "سماء، فلك"),
    ("السماء", "Ϯⲫⲏ", "Ⲧⲡⲉ", PartOfSpeech.noun, "السماء"),
    ("سماوات", "ⲫⲏⲟⲩⲓ", "ⲡⲏⲩⲉ", PartOfSpeech.noun, "سماوات، أفلاك"),
    ("السماوات", "Ⲛⲓⲫⲏⲟⲩⲓ", "Ⲛⲡⲏⲩⲉ", PartOfSpeech.noun, "السماوات"),
    ("ارض", "ⲕⲁϩⲓ", "ⲕⲁϩ", PartOfSpeech.noun, "أرض، تراب، يابسة"),
    ("الارض", "Ⲡⲓⲕⲁϩⲓ", "Ⲡⲕⲁϩ", PartOfSpeech.noun, "الأرض"),
    ("ملك", "ⲟⲩⲣⲟ", "ⲣⲣⲟ", PartOfSpeech.noun, "ملك، سلطان، حاكم"),
    ("الملك", "Ⲡⲟⲩⲣⲟ", "Ⲡⲣ̄ⲣⲟ", PartOfSpeech.noun, "الملك"),
    ("ملوك", "ⲟⲩⲣⲱⲟⲩ", "ⲣ̄ⲣⲱⲟⲩ", PartOfSpeech.noun, "ملوك، سلاطين"),
    ("الملوك", "Ⲛⲓⲟⲩⲣⲱⲟⲩ", "Ⲛ̄ⲣ̄ⲣⲱⲟⲩ", PartOfSpeech.noun, "الملوك"),
    ("ارباب", "ϭⲓⲥⲉⲩ", "ϫⲓⲥⲟⲟⲩⲉ", PartOfSpeech.noun, "أرباب، سادة"),
    ("الارباب", "Ⲛⲓϭⲓⲥⲉⲩ", "Ⲛ̄ϫⲓⲥⲟⲟⲩⲉ", PartOfSpeech.noun, "الأرباب، السادة"),
    ("ملاك", "ⲁⲅⲅⲉⲗⲟⲥ", "ⲁⲅⲅⲉⲗⲟⲥ", PartOfSpeech.noun, "ملاك، رسول سماوي"),
    ("الملاك", "Ⲡⲓⲁⲅⲅⲉⲗⲟⲥ", "Ⲡⲁⲅⲅⲉⲗⲟⲥ", PartOfSpeech.noun, "الملاك"),
    ("ملائكة", "ⲁⲅⲅⲉⲗⲟⲥ", "ⲁⲅⲅⲉⲗⲟⲥ", PartOfSpeech.noun, "ملائكة"),
    ("الملائكة", "Ⲛⲓⲁⲅⲅⲉⲗⲟⲥ", "Ⲛⲁⲅⲅⲉⲗⲟⲥ", PartOfSpeech.noun, "الملائكة"),
    ("نبي", "ⲡⲣⲟⲫⲏⲧⲏⲥ", "ⲡⲣⲟⲫⲏⲧⲏⲥ", PartOfSpeech.noun, "نبي، مرسل بالوحي"),
    ("الانبياء", "Ⲛⲓⲡⲣⲟⲫⲏⲧⲏⲥ", "Ⲛⲡⲣⲟⲫⲏⲧⲏⲥ", PartOfSpeech.noun, "الأنبياء"),
    ("رسول", "ⲁⲡⲟⲥⲧⲟⲗⲟⲥ", "ⲁⲡⲟⲥⲧⲟⲗⲟⲥ", PartOfSpeech.noun, "رسول، مبعوث"),
    ("الرسل", "Ⲛⲓⲁⲡⲟⲥⲧⲟⲗⲟⲥ", "Ⲛⲁⲡⲟⲥⲧⲟⲗⲟⲥ", PartOfSpeech.noun, "الرسل"),
    ("تلميذ", "ⲙⲁⲑⲏⲧⲏⲥ", "ⲙⲁⲑⲏⲧⲏⲥ", PartOfSpeech.noun, "تلميذ، تابع"),
    ("التلاميذ", "Ⲛⲓⲙⲁⲑⲏⲧⲏⲥ", "Ⲛⲙⲁⲑⲏⲧⲏⲥ", PartOfSpeech.noun, "التلاميذ"),
    ("عذراء", "ⲡⲁⲣⲑⲉⲛⲟⲥ", "ⲡⲁⲣⲑⲉⲛⲟⲥ", PartOfSpeech.noun, "عذراء، بتول"),
    ("العذراء", "Ϯⲡⲁⲣⲑⲉⲛⲟⲥ", "Ⲧⲡⲁⲣⲑⲉⲛⲟⲥ", PartOfSpeech.noun, "العذراء، البتول"),
    ("شهيد", "ⲙⲁⲣⲧⲩⲣⲟⲥ", "ⲙⲁⲣⲧⲩⲣⲟⲥ", PartOfSpeech.noun, "شهيد، شاهد للإيمان"),
    ("الشهداء", "Ⲛⲓⲙⲁⲣⲧⲩⲣⲟⲥ", "Ⲛⲙⲁⲣⲧⲩⲣⲟⲥ", PartOfSpeech.noun, "الشهداء"),
    ("خطيئة", "ⲛⲟⲃⲓ", "ⲛⲟⲃⲉ", PartOfSpeech.noun, "خطيئة، إثم، معصية"),
    ("الخطايا", "Ⲛⲓⲛⲟⲃⲓ", "Ⲛⲛⲟⲃⲉ", PartOfSpeech.noun, "الخطايا، الآثام"),
    ("توبة", "ⲙⲉⲧⲁⲛⲟⲓⲁ", "ⲙⲉⲧⲁⲛⲟⲓⲁ", PartOfSpeech.noun, "توبة، رجوع للرب"),
    ("مغفرة", "ⲭⲱ ⲉⲃⲟⲗ", "ⲕⲱ ⲉⲃⲟⲗ", PartOfSpeech.noun, "مغفرة، مسامحة، غفران"),
    ("تناول", "ⲙⲉⲧⲁⲗⲏⲙⲯⲓⲥ", "ⲙⲉⲧⲁⲗⲏⲙⲯⲓⲥ", PartOfSpeech.noun, "تناول، سر الإفخارستيا"),
    ("مذبح", "ⲙⲁⲛⲉⲣϣⲱⲟⲩϣⲓ", "ⲙⲁⲛ̄ⲣ̄ϣⲱⲟⲩϣⲉ", PartOfSpeech.noun, "مذبح، موضع الذبيحة"),
    ("هيكل", "ⲉⲣⲫⲉⲓ", "ⲣ̄ⲡⲉ", PartOfSpeech.noun, "هيكل، معبد مقدس"),
    ("بخور", "ⲥⲑⲟⲓⲛⲟⲩϥⲓ", "ⲥⲧⲟⲓⲛⲟⲩϥⲉ", PartOfSpeech.noun, "بخور، عطر مقدس"),
    ("قربان", "ⲡⲣⲟⲥⲫⲟⲣⲁ", "ⲡⲣⲟⲥⲫⲟⲣⲁ", PartOfSpeech.noun, "قربان، تقدمة مقدسة"),
    ("ذبيحة", "ϣⲱⲟⲩϣⲓ", "ϣⲱⲟⲩϣⲉ", PartOfSpeech.noun, "ذبيحة، أضحية مقدسة"),
    ("ترنيمة", "ϩⲱⲇⲏ", "ϩⲱⲇⲏ", PartOfSpeech.noun, "ترنيمة، تسبيحة، نشيد"),
    ("مزمور", "ⲯⲁⲗⲙⲟⲥ", "ⲯⲁⲗⲙⲟⲥ", PartOfSpeech.noun, "مزمور، ترنيمة داود"),
    ("تسبيح", "ϩⲱⲥ", "ϩⲱⲥ", PartOfSpeech.noun, "تسبيح، ترتيل، مدح"),
    ("قيامة", "ⲁⲛⲁⲥⲧⲁⲥⲓⲥ", "ⲧⲱⲟⲩⲛ", PartOfSpeech.noun, "قيامة، نهوض من الموت"),
    ("القيامة", "Ϯⲁⲛⲁⲥⲧⲁⲥⲓⲥ", "Ⲧⲁⲛⲁⲥⲧⲁⲥⲓⲥ", PartOfSpeech.noun, "القيامة"),
    ("صوم", "ⲛⲏⲥⲧⲓⲁ", "ⲛⲏⲥⲧⲓⲁ", PartOfSpeech.noun, "صوم، انقطاع عن الطعام"),
    ("ابدي", "ⲉⲛⲉϩ", "ⲉⲛⲉϩ", PartOfSpeech.adjective, "أبدي، سرمدي، دائم"),
    ("ابدية", "ⲙⲉⲧⲉⲛⲉϩ", "ⲙⲛ̄ⲧⲉⲛⲉϩ", PartOfSpeech.noun, "أبدية، خلود"),
    ("الابد", "Ⲡⲓⲉⲛⲉϩ", "Ⲡⲉⲛⲉϩ", PartOfSpeech.noun, "الأبد، الدهر"),
    ("دهر", "ⲉⲱⲛ", "ⲁⲓⲱⲛ", PartOfSpeech.noun, "دهر، زمان، عصر"),
    ("فردوس", "ⲡⲁⲣⲁⲇⲓⲥⲟⲥ", "ⲡⲁⲣⲁⲇⲉⲓⲥⲟⲥ", PartOfSpeech.noun, "فردوس، جنة النعيم"),
    ("جهنم", "ⲅⲉⲉⲛⲛⲁ", "ⲅⲉϩⲉⲛⲛⲁ", PartOfSpeech.noun, "جهنم، العذاب الأبدي"),
    ("شيطان", "ⲥⲁⲧⲁⲛⲁⲥ", "ⲥⲁⲧⲁⲛⲁⲥ", PartOfSpeech.noun, "شيطان، إبليس، المشتكي"),
    ("ابليس", "ⲇⲓⲁⲃⲟⲗⲟⲥ", "ⲇⲓⲁⲃⲟⲗⲟⲥ", PartOfSpeech.noun, "إبليس، الشرير"),
    ("شر", "ⲡⲉⲧϩⲱⲟⲩ", "ⲡⲉⲑⲟⲟⲩ", PartOfSpeech.noun, "شر، سوء، أذى"),
    ("شرير", "ⲡⲟⲛⲏⲣⲟⲥ", "ⲡⲟⲛⲏⲣⲟⲥ", PartOfSpeech.adjective, "شرير، خبيث، فاسد"),
    ("خير", "ⲡⲉⲑⲛⲁⲛⲉϥ", "ⲡⲉⲧⲛⲁⲛⲟⲩϥ", PartOfSpeech.noun, "خير، صلاح، نفع"),
    ("صالح", "ⲁⲅⲁⲑⲟⲥ", "ⲁⲅⲁⲑⲟⲥ", PartOfSpeech.adjective, "صالح، طيب، فاضل"),
    ("بار", "ⲑⲙⲏⲓ", "ⲇⲓⲕⲁⲓⲟⲥ", PartOfSpeech.adjective, "بار، عادل، مستقيم"),
    ("بر", "ⲙⲉⲑⲙⲏⲓ", "ⲇⲓⲕⲁⲓⲟⲥⲩⲛⲏ", PartOfSpeech.noun, "بر، عدالة، استقامة"),
    ("عدل", "ϩⲁⲡ", "ϩⲁⲡ", PartOfSpeech.noun, "عدل، قضاء، حكم"),
    ("حق", "ⲙⲏⲓ", "ⲙⲉ", PartOfSpeech.noun, "حق، صدق، حقيقة"),
    ("حقيقة", "ⲙⲉⲑⲙⲏⲓ", "ⲙⲛ̄ⲧⲙⲉ", PartOfSpeech.noun, "حقيقة، صدق"),
    ("حكمة", "ⲥⲟⲫⲓⲁ", "ⲥⲟⲫⲓⲁ", PartOfSpeech.noun, "حكمة، تعقل، بصيرة"),
    ("معرفة", "ⲥⲃⲱ", "ⲥⲃⲱ", PartOfSpeech.noun, "معرفة، تعليم، دراية"),
    ("سر", "ⲙⲩⲥⲧⲏⲣⲓⲟⲛ", "ⲙⲩⲥⲧⲏⲣⲓⲟⲛ", PartOfSpeech.noun, "سر كنسي، لغز إلهي"),
    ("قوة", "ϫⲟⲙ", "ϭⲟⲙ", PartOfSpeech.noun, "قوة، قدرة، بأس"),
    ("القوة", "Ϯϫⲟⲙ", "Ⲧϭⲟⲙ", PartOfSpeech.noun, "القوة، القدرة"),
    ("سلطان", "ⲉⲝⲟⲩⲥⲓⲁ", "ⲉⲝⲟⲩⲥⲓⲁ", PartOfSpeech.noun, "سلطان، حجة، ولاية"),
    ("خالق", "ⲣⲉϥⲥⲱⲛⲧ", "ⲣⲉϥⲥⲱⲛⲧ̄", PartOfSpeech.noun, "خالق، مبدع الكون"),
    ("خليقة", "ⲥⲱⲛⲧ", "ⲥⲱⲛⲧ̄", PartOfSpeech.noun, "خليقة، كائنات مخلوقة"),
    ("راعي", "ⲙⲁⲛⲉⲥⲱⲟⲩ", "ⲙⲟⲟⲛⲉ", PartOfSpeech.noun, "راعي، حارس القطيع"),
    ("الراعي", "Ⲡⲓⲙⲁⲛⲉⲥⲱⲟⲩ", "Ⲡⲙⲟⲟⲛⲉ", PartOfSpeech.noun, "الراعي الصالح"),
    ("خروف", "ⲉⲥⲱⲟⲩ", "ⲉⲥⲟⲟⲩ", PartOfSpeech.noun, "خروف، شاة"),
    ("حمل", "ϩⲓⲏⲃ", "ϩⲓⲉⲓⲃ", PartOfSpeech.noun, "حمل، خروف صغير"),
    ("الحمل", "Ⲡⲓϩⲓⲏⲃ", "Ⲡϩⲓⲉⲓⲃ", PartOfSpeech.noun, "حمل الله"),
    ("حمامة", "ϭⲣⲟⲙⲡⲓ", "ϭⲣⲟⲟⲙⲡⲉ", PartOfSpeech.noun, "حمامة"),
    ("عهد", "ⲇⲓⲁⲑⲏⲕⲏ", "ⲇⲓⲁⲑⲏⲕⲏ", PartOfSpeech.noun, "عهد، ميثاق"),
    ("وصية", "ⲉⲛⲧⲟⲗⲏ", "ⲉⲛⲧⲟⲗⲏ", PartOfSpeech.noun, "وصية، أمر إلهي"),
    ("وصايا", "ⲉⲛⲧⲟⲗⲏ", "ⲉⲛⲧⲟⲗⲏ", PartOfSpeech.noun, "وصايا الرب"),
    ("شريعة", "ⲛⲟⲙⲟⲥ", "ⲛⲟⲙⲟⲥ", PartOfSpeech.noun, "شريعة، ناموس"),
    ("ناموس", "ⲛⲟⲙⲟⲥ", "ⲛⲟⲙⲟⲥ", PartOfSpeech.noun, "ناموس، شريعة موسى"),
    ("رحمة", "ⲛⲁⲓ", "ⲛⲁ", PartOfSpeech.noun, "رحمة، شفقة، حنان"),
    ("الرحمة", "Ⲡⲓⲛⲁⲓ", "Ⲡⲛⲁ", PartOfSpeech.noun, "الرحمة"),
    ("فرح", "ⲣⲁϣⲓ", "ⲣⲁϣⲉ", PartOfSpeech.noun, "فرح، بهجة، سرور"),
    ("الفرح", "Ⲡⲓⲣⲁϣⲓ", "Ⲡⲣⲁϣⲉ", PartOfSpeech.noun, "الفرح، البهجة"),
    ("مسرة", "ϯⲙⲁϯ", "ⲧⲙⲁϯ", PartOfSpeech.noun, "مسرة، رضا، سرور"),
    ("المسرة", "Ϯϯⲙⲁϯ", "Ⲧⲧⲙⲁϯ", PartOfSpeech.noun, "المسرة، حسن الرضا"),
    ("علا", "ϭⲓⲥⲓ", "ϫⲓⲥⲉ", PartOfSpeech.noun, "العلى، الأعالي"),
    ("العلى", "Ⲛⲏⲉⲧϭⲟⲥⲓ", "Ⲛⲉⲧϫⲟⲥⲉ", PartOfSpeech.noun, "الأعالي، العلى"),
    ("البدء", "Ϯⲁⲣⲭⲏ", "Ⲧⲁⲣⲭⲏ", PartOfSpeech.noun, "البدء، البداية، الأزل"),
    ("بدء", "ⲁⲣⲭⲏ", "ⲁⲣⲭⲏ", PartOfSpeech.noun, "بدء، بداية"),
    ("بداية", "ϩⲏ", "ϩⲏ", PartOfSpeech.noun, "بداية، أول"),
    ("نهاية", "ϫⲱⲕ", "ϫⲱⲕ", PartOfSpeech.noun, "نهاية، كمال، تمام"),

    # Common Entities & Everyday Nouns
    ("انسان", "ⲣⲱⲙⲓ", "ⲣⲱⲙⲉ", PartOfSpeech.noun, "إنسان، بشر، شخص"),
    ("الانسان", "Ⲡⲓⲣⲱⲙⲓ", "Ⲡⲣⲱⲙⲉ", PartOfSpeech.noun, "الإنسان"),
    ("رجل", "ⲣⲱⲙⲓ", "ⲣⲱⲙⲉ", PartOfSpeech.noun, "رجل، ذكر"),
    ("الرجل", "Ⲡⲓⲣⲱⲙⲓ", "Ⲡⲣⲱⲙⲉ", PartOfSpeech.noun, "الرجل"),
    ("امراة", "ⲥϩⲓⲙⲓ", "ⲥϩⲓⲙⲉ", PartOfSpeech.noun, "امرأة، زوجة، أنثى"),
    ("المراة", "Ϯⲥϩⲓⲙⲓ", "Ⲧⲥϩⲓⲙⲉ", PartOfSpeech.noun, "المرأة، الزوجة"),
    ("ناس", "ⲣⲱⲙⲓ", "ⲣⲱⲙⲉ", PartOfSpeech.noun, "ناس، بشر، جمع إنسان"),
    ("الناس", "Ⲛⲓⲣⲱⲙⲓ", "Ⲛ̄ⲣⲱⲙⲉ", PartOfSpeech.noun, "الناس، البشر"),
    ("شعب", "ⲗⲁⲟⲥ", "ⲗⲁⲟⲥ", PartOfSpeech.noun, "شعب، أمة، جماعة"),
    ("الشعب", "Ⲡⲓⲗⲁⲟⲥ", "Ⲡⲗⲁⲟⲥ", PartOfSpeech.noun, "الشعب"),
    ("عالم", "ⲕⲟⲥⲙⲟⲥ", "ⲕⲟⲥⲙⲟⲥ", PartOfSpeech.noun, "عالم، كون، دنيا"),
    ("العالم", "Ⲡⲓⲕⲟⲥⲙⲟⲥ", "Ⲡⲕⲟⲥⲙⲟⲥ", PartOfSpeech.noun, "العالم"),
    ("كلمة", "ⲥⲁϫⲓ", "ϣⲁϫⲉ", PartOfSpeech.noun, "كلمة، قول، حديث"),
    ("الكلمة", "Ⲡⲓⲥⲁϫⲓ", "Ⲡϣⲁϫⲉ", PartOfSpeech.noun, "الكلمة، اللوغوس، النطق"),
    ("صوت", "ⲥⲙⲏ", "ⲥⲙⲏ", PartOfSpeech.noun, "صوت، نداء"),
    ("الصوت", "Ϯⲥⲙⲏ", "Ⲧⲥⲙⲏ", PartOfSpeech.noun, "الصوت"),
    ("اسم", "ⲣⲁⲛ", "ⲣⲁⲛ", PartOfSpeech.noun, "اسم، لقب، ذكر"),
    ("الاسم", "Ⲡⲓⲣⲁⲛ", "Ⲡⲣⲁⲛ", PartOfSpeech.noun, "الاسم"),
    ("كتاب", "ϫⲱⲙ", "ϫⲱⲱⲙⲉ", PartOfSpeech.noun, "كتاب، سفر، مخطوط"),
    ("الكتاب", "Ⲡⲓϫⲱⲙ", "Ⲡϫⲱⲱⲙⲉ", PartOfSpeech.noun, "الكتاب"),
    ("رسالة", "ⲉⲡⲓⲥⲧⲟⲗⲏ", "ⲉⲡⲓⲥⲧⲟⲗⲏ", PartOfSpeech.noun, "رسالة، خطاب"),
    ("ماء", "ⲙⲱⲟⲩ", "ⲙⲟⲟⲩ", PartOfSpeech.noun, "ماء، سائل الحياة"),
    ("الماء", "Ⲡⲓⲙⲱⲟⲩ", "Ⲡⲙⲟⲟⲩ", PartOfSpeech.noun, "الماء"),
    ("مياه", "ⲙⲱⲟⲩ", "ⲙⲟⲟⲩ", PartOfSpeech.noun, "مياه، بحار، أنهار"),
    ("المياه", "Ⲛⲓⲙⲱⲟⲩ", "Ⲛⲙⲟⲟⲩ", PartOfSpeech.noun, "المياه"),
    ("نار", "ⲭⲣⲱⲙ", "ⲕⲱϩⲧ̄", PartOfSpeech.noun, "نار، لهيب"),
    ("النار", "Ⲡⲓⲭⲣⲱⲙ", "Ⲡⲕⲱϩⲧ̄", PartOfSpeech.noun, "النار"),
    ("خبز", "ⲱⲓⲕ", "ⲟⲉⲓⲕ", PartOfSpeech.noun, "خبز، عيش، طعام"),
    ("الخبز", "Ⲡⲓⲱⲓⲕ", "Ⲡⲟⲉⲓⲕ", PartOfSpeech.noun, "الخبز، خبز الحياة"),
    ("طعام", "ϧⲣⲉ", "ϩⲣⲉ", PartOfSpeech.noun, "طعام، غذاء"),
    ("شجرة", "ϣϣⲏⲛ", "ϣⲏⲛ", PartOfSpeech.noun, "شجرة، نبات ذو ساق"),
    ("الشجرة", "Ⲡⲓϣϣⲏⲛ", "Ⲡϣⲏⲛ", PartOfSpeech.noun, "الشجرة"),
    ("اشجار", "ϣϣⲏⲛ", "ϣⲏⲛ", PartOfSpeech.noun, "أشجار، غرس"),
    ("ثمرة", "ⲟⲩⲧⲁϩ", "ⲟⲩⲧⲁϩ", PartOfSpeech.noun, "ثمرة، فاكهة، نتاج"),
    ("شمس", "ⲣⲏ", "ⲣⲏ", PartOfSpeech.noun, "شمس، كوكب النهار"),
    ("الشمس", "Ⲡⲓⲣⲏ", "Ⲡⲣⲏ", PartOfSpeech.noun, "الشمس"),
    ("قمر", "ⲓⲟϩ", "ⲟⲟϩ", PartOfSpeech.noun, "قمر، هلال، كوكب الليل"),
    ("القمر", "Ⲡⲓⲓⲟϩ", "Ⲡⲟⲟϩ", PartOfSpeech.noun, "القمر"),
    ("نجم", "ⲥⲓⲟⲩ", "ⲥⲓⲟⲩ", PartOfSpeech.noun, "نجم، كوكب دري"),
    ("نجوم", "ⲥⲓⲟⲩ", "ⲥⲓⲟⲩ", PartOfSpeech.noun, "نجوم السماء"),
    ("بحر", "ⲓⲟⲙ", "ⲉⲓⲟⲙ", PartOfSpeech.noun, "بحر، يم، لجة"),
    ("البحر", "Ⲫⲓⲟⲙ", "Ⲡⲉⲓⲟⲙ", PartOfSpeech.noun, "البحر"),
    ("نهر", "ⲓⲁⲣⲟ", "ⲉⲓⲉⲣⲟ", PartOfSpeech.noun, "نهر، مجرى مائي"),
    ("النهر", "Ⲫⲓⲁⲣⲟ", "Ⲡⲉⲓⲉⲣⲟ", PartOfSpeech.noun, "النهر"),
    ("جبل", "ⲧⲱⲟⲩ", "ⲧⲟⲟⲩ", PartOfSpeech.noun, "جبل، هضبة عالية"),
    ("الجبل", "Ⲡⲓⲧⲱⲟⲩ", "Ⲡⲧⲟⲟⲩ", PartOfSpeech.noun, "الجبل"),
    ("بيت", "ⲏⲓ", "ⲏⲓ", PartOfSpeech.noun, "بيت، منزل، مسكن"),
    ("البيت", "Ⲡⲓⲏⲓ", "Ⲡⲏⲓ", PartOfSpeech.noun, "البيت"),
    ("بيوت", "ⲏⲟⲩ", "ⲏⲟⲩ", PartOfSpeech.noun, "بيوت، منازل"),
    ("طريق", "ⲙⲱⲓⲧ", "ϩⲓⲏ", PartOfSpeech.noun, "طريق، سبيل، مسلك"),
    ("الطريق", "Ⲡⲓⲙⲱⲓⲧ", "Ⲧϩⲓⲏ", PartOfSpeech.noun, "الطريق"),
    ("مدينة", "ⲡⲟⲗⲓⲥ", "ⲡⲟⲗⲓⲥ", PartOfSpeech.noun, "مدينة، بلد كبير"),
    ("المدينة", "Ϯⲡⲟⲗⲓⲥ", "Ⲧⲡⲟⲗⲓⲥ", PartOfSpeech.noun, "المدينة"),
    ("قرية", "ϯⲙⲓ", "ϯⲙⲉ", PartOfSpeech.noun, "قرية، بلدة صغيرة"),
    ("باب", "ⲣⲟ", "ⲣⲟ", PartOfSpeech.noun, "باب، مدخل"),
    ("الباب", "Ⲡⲓⲣⲟ", "Ⲡⲣⲟ", PartOfSpeech.noun, "الباب"),
    ("عين", "ⲃⲁⲗ", "ⲃⲁⲗ", PartOfSpeech.noun, "عين، بصر"),
    ("العين", "Ⲡⲓⲃⲁⲗ", "Ⲡⲃⲁⲗ", PartOfSpeech.noun, "العين"),
    ("عيون", "ⲃⲁⲗ", "ⲃⲁⲗ", PartOfSpeech.noun, "عيون، أعين"),
    ("يد", "ϫⲓϫ", "ϭⲓϫ", PartOfSpeech.noun, "يد، كف"),
    ("اليد", "Ϯϫⲓϫ", "Ⲧϭⲓϫ", PartOfSpeech.noun, "اليد"),
    ("رجل", "ⲫⲁⲧ", "ⲟⲩⲉⲣⲏⲧⲉ", PartOfSpeech.noun, "رِجل، قدم"),
    ("قدم", "ⲫⲁⲧ", "ⲟⲩⲉⲣⲏⲧⲉ", PartOfSpeech.noun, "قدم، رجل"),
    ("راس", "ⲁⲫⲉ", "ϫⲱ", PartOfSpeech.noun, "رأس، هامة"),
    ("الراس", "Ϯⲁⲫⲉ", "Ⲡϫⲱ", PartOfSpeech.noun, "الرأس"),
    ("فم", "ⲣⲱ", "ⲧⲁⲡⲣⲟ", PartOfSpeech.noun, "فم، ثغر"),
    ("الفم", "Ⲡⲓⲣⲱ", "Ⲧⲁⲡⲣⲟ", PartOfSpeech.noun, "الفم"),
    ("لسان", "ⲗⲁⲥ", "ⲗⲁⲥ", PartOfSpeech.noun, "لسان، منطق"),
    ("قلب", "ϩⲏⲧ", "ϩⲏⲧ", PartOfSpeech.noun, "قلب، فؤاد، وجدان"),
    ("القلب", "Ⲡⲓϩⲏⲧ", "Ⲡϩⲏⲧ", PartOfSpeech.noun, "القلب"),
    ("قلوب", "ϩⲏⲧ", "ϩⲏⲧ", PartOfSpeech.noun, "قلوب المؤمنين"),
    ("جسد", "ⲥⲱⲙⲁ", "ⲥⲱⲙⲁ", PartOfSpeech.noun, "جسد، بدن، جسم"),
    ("الجسد", "Ⲡⲓⲥⲱⲙⲁ", "Ⲡⲥⲱⲙⲁ", PartOfSpeech.noun, "الجسد"),
    ("دم", "ⲥⲛⲟϥ", "ⲥⲛⲟϥ", PartOfSpeech.noun, "دم، سائل الحياة"),
    ("الدم", "Ⲡⲓⲥⲛⲟϥ", "Ⲡⲥⲛⲟϥ", PartOfSpeech.noun, "الدم المقدس"),
    ("عظم", "ⲕⲁⲥ", "ⲕⲁⲥ", PartOfSpeech.noun, "عظم"),
    ("يوم", "ⲉϩⲟⲟⲩ", "ϩⲟⲟⲩ", PartOfSpeech.noun, "يوم، نهار"),
    ("اليوم", "Ⲡⲓⲉϩⲟⲟⲩ", "Ⲡϩⲟⲟⲩ", PartOfSpeech.noun, "اليوم، النهار، هذا اليوم"),
    ("ايام", "ⲉϩⲟⲟⲩ", "ϩⲟⲟⲩ", PartOfSpeech.noun, "أيام، دهر"),
    ("ليل", "ⲉϫⲱⲣϩ", "ⲟⲩϣⲏ", PartOfSpeech.noun, "ليل، عتمة الليل"),
    ("الليل", "Ⲡⲓⲉϫⲱⲣϩ", "Ⲧⲟⲩϣⲏ", PartOfSpeech.noun, "الليل"),
    ("وقت", "ⲥⲏⲟⲩ", "ⲟⲩⲟⲉⲓϣ", PartOfSpeech.noun, "وقت، زمن، حين"),
    ("ساعة", "ⲁϫⲡ", "ⲟⲩⲛⲟⲩ", PartOfSpeech.noun, "ساعة، حين"),
    ("الساعة", "Ϯⲁϫⲡ", "Ⲧⲟⲩⲛⲟⲩ", PartOfSpeech.noun, "الساعة"),
    ("سنة", "ⲣⲟⲙⲡⲓ", "ⲣⲟⲙⲡⲉ", PartOfSpeech.noun, "سنة، عام"),
    ("السنة", "Ϯⲣⲟⲙⲡⲓ", "Ⲧⲣⲟⲙⲡⲉ", PartOfSpeech.noun, "السنة، العام"),
    ("عمل", "ϩⲱⲃ", "ϩⲱⲃ", PartOfSpeech.noun, "عمل، فعل، صنيع"),
    ("العمل", "Ⲡⲓϩⲱⲃ", "Ⲡϩⲱⲃ", PartOfSpeech.noun, "العمل"),
    ("اعمال", "ϩⲏⲃⲓ", "ϩⲃⲏⲩⲉ", PartOfSpeech.noun, "أعمال، أفعال"),
    ("الاعمال", "Ⲛⲓϩⲏⲃⲓ", "Ⲛϩⲃⲏⲩⲉ", PartOfSpeech.noun, "الأعمال"),

    # Common Verbs (Arabic -> (Bohairic, Sahidic, POS, Definition))
    ("قال", "ϫⲱ", "ϫⲱ", PartOfSpeech.verb, "قال، تكلم، نطق"),
    ("يقول", "ϫⲱ", "ϫⲱ", PartOfSpeech.verb, "يقول، يحدث"),
    ("تكلم", "ⲥⲁϫⲓ", "ϣⲁϫⲉ", PartOfSpeech.verb, "تكلم، تحدث"),
    ("سمع", "ⲥⲱⲧⲉⲙ", "ⲥⲱⲧⲙ̄", PartOfSpeech.verb, "سمع، أصغى، استجاب"),
    ("يسمع", "ⲥⲱⲧⲉⲙ", "ⲥⲱⲧⲙ̄", PartOfSpeech.verb, "يسمع، يصغي"),
    ("راى", "ⲛⲁⲩ", "ⲛⲁⲩ", PartOfSpeech.verb, "رأى، أبصر، عاين"),
    ("يرى", "ⲛⲁⲩ", "ⲛⲁⲩ", PartOfSpeech.verb, "يرى، يبصر"),
    ("نظر", "ⲥⲟⲙⲥ", "ϭⲱϣⲧ̄", PartOfSpeech.verb, "نظر، تأمل، حدق"),
    ("جاء", "ⲓ̀", "ⲉⲓ", PartOfSpeech.verb, "جاء، أتى، قدم"),
    ("ياتي", "ⲛⲏⲟⲩ", "ⲛⲏⲩ", PartOfSpeech.verb, "يأتي، يقدم"),
    ("ذهب", "ϣⲉ", "ⲃⲱⲕ", PartOfSpeech.verb, "ذهب، مضى، سار"),
    ("اعطى", "ϯ", "ϯ", PartOfSpeech.verb, "أعطى، منح، وهب"),
    ("يعطي", "ϯ", "ϯ", PartOfSpeech.verb, "يعطي، يمنح"),
    ("اخذ", "ϭⲓ", "ϫⲓ", PartOfSpeech.verb, "أخذ، تناول، قبل"),
    ("ياخذ", "ϭⲓ", "ϫⲓ", PartOfSpeech.verb, "يأخذ، يتناول"),
    ("صنع", "ⲑⲁⲙⲓⲟ", "ⲧⲁⲙⲓⲟ", PartOfSpeech.verb, "صنع، خلق، جبل"),
    ("فعل", "ⲓⲣⲓ", "ⲉⲓⲣⲉ", PartOfSpeech.verb, "فعل، عمل، أجرى"),
    ("يعمل", "ⲉⲣϩⲱⲃ", "ⲣ̄ϩⲱⲃ", PartOfSpeech.verb, "يعمل، يشتغل"),
    ("عرف", "ⲥⲱⲟⲩⲛ", "ⲥⲟⲟⲩⲛ̄", PartOfSpeech.verb, "عرف، علم، درى"),
    ("يعرف", "ⲥⲱⲟⲩⲛ", "ⲥⲟⲟⲩⲛ̄", PartOfSpeech.verb, "يعرف، يعلم"),
    ("علم", "ϯⲥⲃⲱ", "ϯⲥⲃⲱ", PartOfSpeech.verb, "علّم، درّس"),
    ("احب", "ⲙⲉⲓ", "ⲙⲉⲣⲉ", PartOfSpeech.verb, "أحب، ود، عشق"),
    ("يحب", "ⲙⲉⲓ", "ⲙⲉⲣⲉ", PartOfSpeech.verb, "يحب، يعز"),
    ("عاش", "ⲱⲛϧ", "ⲱⲛϩ", PartOfSpeech.verb, "عاش، حي، بقي"),
    ("يعيش", "ⲱⲛϧ", "ⲱⲛϩ", PartOfSpeech.verb, "يعيش، يحيى"),
    ("مات", "ⲙⲟⲩ", "ⲙⲟⲩ", PartOfSpeech.verb, "مات، توفي، رقد"),
    ("يموت", "ⲙⲟⲩ", "ⲙⲟⲩ", PartOfSpeech.verb, "يموت، يرقد"),
    ("قام", "ⲧⲱⲟⲩⲛ", "ⲧⲱⲟⲩⲛ", PartOfSpeech.verb, "قام، نهض، قام من الموت"),
    ("يقوم", "ⲧⲱⲟⲩⲛ", "ⲧⲱⲟⲩⲛ", PartOfSpeech.verb, "يقوم، ينهض"),
    ("سجد", "ⲟⲩⲱϣⲧ", "ⲟⲩⲱϣⲧ̄", PartOfSpeech.verb, "سجد، خشع، عبد"),
    ("يسجد", "ⲟⲩⲱϣⲧ", "ⲟⲩⲱϣⲧ̄", PartOfSpeech.verb, "يسجد، يعبد"),
    ("صلى", "ⲉⲣⲡⲣⲟⲥⲉⲩⲭⲉⲥⲑⲉ", "ϣⲗⲏⲗ", PartOfSpeech.verb, "صلى، دعا، تضرع"),
    ("يصلي", "ⲧⲱⲃϩ", "ϣⲗⲏⲗ", PartOfSpeech.verb, "يصلي، يتضرع"),
    ("بارك", "ⲥⲙⲟⲩ", "ⲥⲙⲟⲩ", PartOfSpeech.verb, "بارك، قدس، مدح"),
    ("يبارك", "ⲥⲙⲟⲩ", "ⲥⲙⲟⲩ", PartOfSpeech.verb, "يبارك، يقدس"),
    ("سبح", "ϩⲱⲥ", "ϩⲱⲥ", PartOfSpeech.verb, "سبح، رتل، مجد"),
    ("يسبح", "ϩⲱⲥ", "ϩⲱⲥ", PartOfSpeech.verb, "يسبح، يرنم"),
    ("شكر", "ϣⲉⲡϩ̀ⲙⲟⲧ", "ϣⲡϩⲙⲟⲧ", PartOfSpeech.verb, "شكر، قدم الشكر"),
    ("يشكر", "ϣⲉⲡϩ̀ⲙⲟⲧ", "ϣⲡϩⲙⲟⲧ", PartOfSpeech.verb, "يشكر، يعترف بالفضل"),
    ("خلص", "ⲛⲁϩⲙⲉ", "ⲛⲟϩⲉⲙ", PartOfSpeech.verb, "خلّص، أنقذ، نجى"),
    ("يخلص", "ⲛⲟϩⲉⲙ", "ⲛⲟϩⲉⲙ", PartOfSpeech.verb, "يخلص، ينقذ"),
    ("غفر", "ⲭⲱ ⲉⲃⲟⲗ", "ⲕⲱ ⲉⲃⲟⲗ", PartOfSpeech.verb, "غفر، صفح، سامح"),
    ("يغفر", "ⲭⲱ ⲉⲃⲟⲗ", "ⲕⲱ ⲉⲃⲟⲗ", PartOfSpeech.verb, "يغفر، يصفح"),
    ("خلق", "ⲥⲱⲛⲧ", "ⲥⲱⲛⲧ̄", PartOfSpeech.verb, "خلق، أوجد، أبدع"),
    ("يخلق", "ⲥⲱⲛⲧ", "ⲥⲱⲛⲧ̄", PartOfSpeech.verb, "يخلق، يبدع"),
    ("ارحم", "ⲛⲁⲓ", "ⲛⲁ", PartOfSpeech.verb, "ارحم، ترأف"),
    ("يرحم", "ⲛⲁⲓ", "ⲛⲁ", PartOfSpeech.verb, "يرحم، يتعطف"),
    ("اضاء", "ⲉⲣⲟⲩⲱⲓⲛⲓ", "ⲣ̄ⲟⲩⲟⲉⲓⲛ", PartOfSpeech.verb, "أضاء، أنار، أشرق"),
    ("يضيء", "ⲉⲣⲟⲩⲱⲓⲛⲓ", "ⲣ̄ⲟⲩⲟⲉⲓⲛ", PartOfSpeech.verb, "يضيء، ينير"),
    ("كان", "ⲛⲁϥ", "ⲛⲉ", PartOfSpeech.verb, "كان، وجد، ثبت"),
    ("يكون", "ϣⲱⲡⲓ", "ϣⲱⲡⲉ", PartOfSpeech.verb, "يكون، يصير"),
    ("صار", "ϣⲱⲡⲓ", "ϣⲱⲡⲉ", PartOfSpeech.verb, "صار، تحول"),

    # Prepositions, Conjunctions, Particles & Pronouns
    ("في", "ϧⲉⲛ", "ϩⲛ̄", PartOfSpeech.preposition, "في، بداخل، عند"),
    ("على", "ϩⲓϫⲉⲛ", "ⲉϫⲛ̄", PartOfSpeech.preposition, "على، فوق"),
    ("الى", "ⲉ", "ⲉ", PartOfSpeech.preposition, "إلى، نحو، لـ"),
    ("من", "ⲉⲃⲟⲗ ϧⲉⲛ", "ⲉⲃⲟⲗ ϩⲛ̄", PartOfSpeech.preposition, "من، عن"),
    ("مع", "ⲛⲉⲙ", "ⲙⲛ̄", PartOfSpeech.preposition, "مع، بصحبة"),
    ("و", "ⲟⲩⲟϩ", "ⲁⲩⲱ", PartOfSpeech.conjunction, "و، حرف عطف"),
    ("او", "ⲓⲉ", "ⲏ", PartOfSpeech.conjunction, "أو، أم"),
    ("لكن", "ⲁⲗⲗⲁ", "ⲁⲗⲗⲁ", PartOfSpeech.conjunction, "لكن، بل"),
    ("لان", "ϫⲉ", "ϫⲉ", PartOfSpeech.conjunction, "لأن، بما أن، لكي"),
    ("يا", "ⲱ", "ⲱ", PartOfSpeech.particle, "يا أداة نداء"),
    ("كل", "ⲛⲓⲃⲉⲛ", "ⲛⲓⲙ", PartOfSpeech.adjective, "كل، جميع، كافة"),
    ("جميع", "ⲧⲏⲣⲟⲩ", "ⲧⲏⲣⲟⲩ", PartOfSpeech.adjective, "جميعهم، كلهم"),
    ("لا", "ⲙ̀ⲡⲉⲣ", "ⲙ̄ⲡⲣ̄", PartOfSpeech.particle, "لا الناهية أو النافية"),
    ("ليس", "ⲙ̀ⲙⲟⲛ", "ⲙⲛ̄", PartOfSpeech.particle, "ليس، غير موجود"),
    ("لكم", "ⲛⲱⲧⲉⲛ", "ⲛⲏⲧⲛ̄", PartOfSpeech.pronoun, "لكم، إليكم"),
    ("لنا", "ⲛⲁⲛ", "ⲛⲁⲛ", PartOfSpeech.pronoun, "لنا، إلينا"),
    ("لك", "ⲛⲁⲕ", "ⲛⲁⲕ", PartOfSpeech.pronoun, "لكَ"),
    ("لي", "ⲛⲏⲓ", "ⲛⲁⲓ", PartOfSpeech.pronoun, "لي، عندي"),
    ("له", "ⲛⲁϥ", "ⲛⲁϥ", PartOfSpeech.pronoun, "له"),
    ("لها", "ⲛⲁⲥ", "ⲛⲁⲥ", PartOfSpeech.pronoun, "لها"),
    ("لهم", "ⲛⲱⲟⲩ", "ⲛⲁⲩ", PartOfSpeech.pronoun, "لهم"),
    ("انا", "ⲁⲛⲟⲕ", "ⲁⲛⲟⲕ", PartOfSpeech.pronoun, "أنا، ضمير متكلم"),
    ("انت", "ⲛ̀ⲑⲟⲕ", "ⲛ̄ⲧⲟⲕ", PartOfSpeech.pronoun, "أنتَ، ضمير مخاطب"),
    ("انتي", "ⲛ̀ⲑⲟ", "ⲛ̄ⲧⲟ", PartOfSpeech.pronoun, "أنتِ"),
    ("هو", "ⲛ̀ⲑⲟϥ", "ⲛ̄ⲧⲟϥ", PartOfSpeech.pronoun, "هو، ضمير غائب"),
    ("هي", "ⲛ̀ⲑⲟⲥ", "ⲛ̄ⲧⲟⲥ", PartOfSpeech.pronoun, "هي، ضمير غائب مؤنث"),
    ("نحن", "ⲁⲛⲟⲛ", "ⲁⲛⲟⲛ", PartOfSpeech.pronoun, "نحن، ضمير متكلمين"),
    ("انتم", "ⲛ̀ⲑⲱⲧⲉⲛ", "ⲛ̄ⲧⲱⲧⲛ̄", PartOfSpeech.pronoun, "أنتم"),
    ("هم", "ⲛ̀ⲑⲱⲟⲩ", "ⲛ̄ⲧⲟⲟⲩ", PartOfSpeech.pronoun, "هم"),
    ("هذا", "ⲫⲁⲓ", "ⲡⲁⲓ", PartOfSpeech.pronoun, "هذا، اسم إشارة للمذكر"),
    ("هذه", "ⲑⲁⲓ", "ⲧⲁⲓ", PartOfSpeech.pronoun, "هذه، اسم إشارة للمؤنث"),
    ("هؤلاء", "ⲛⲁⲓ", "ⲛⲁⲓ", PartOfSpeech.pronoun, "هؤلاء، اسم إشارة للجمع"),
    ("هنا", "ⲙ̀ⲡⲁⲓⲙⲁ", "ⲙ̄ⲡⲉⲓⲙⲁ", PartOfSpeech.adverb, "هنا، في هذا الموضع"),
    ("هناك", "ⲙ̀ⲙⲁⲩ", "ⲙ̄ⲙⲁⲩ", PartOfSpeech.adverb, "هناك، في ذلك الموضع"),
    ("دائما", "ⲛ̀ⲥⲏⲟⲩ ⲛⲓⲃⲉⲛ", "ⲛ̄ⲟⲩⲟⲉⲓϣ ⲛⲓⲙ", PartOfSpeech.adverb, "دائماً، في كل حين"),
    ("الان", "ϯⲛⲟⲩ", "ⲧⲉⲛⲟⲩ", PartOfSpeech.adverb, "الآن، في هذا الوقت"),
    ("امين", "ⲁⲙⲏⲛ", "ⲁⲙⲏⲛ", PartOfSpeech.interjection, "آمين، حقاً، استجب يا رب"),
    ("هللويا", "ⲁⲗⲗⲏⲗⲟⲩⲓⲁ", "ⲁⲗⲗⲏⲗⲟⲩⲓⲁ", PartOfSpeech.interjection, "هللويا، سبحوا الرب"),

    # Prepositions (حروف الجر والقواعد النحوية)
    ("في", "ϧⲉⲛ", "ϩⲛ̄", PartOfSpeech.preposition, "في، بداخل، عند"),
    ("ب", "ϧⲉⲛ", "ϩⲛ̄", PartOfSpeech.preposition, "بـ، بواسطة، في"),
    ("على", "ϩⲓϫⲉⲛ", "ⲉϫⲛ̄", PartOfSpeech.preposition, "على، فوق، على السطح"),
    ("من", "ⲉ̀ⲃⲟⲗ ϧⲉⲛ", "ⲉⲃⲟⲗ ϩⲛ̄", PartOfSpeech.preposition, "من، عن، من داخل"),
    ("الي", "ⲉ̀", "ⲉ-", PartOfSpeech.preposition, "إلى، نحو، لـ"),
    ("مع", "ⲛⲉⲙ", "ⲙⲛ̄", PartOfSpeech.preposition, "مع، بصحبة، برفقة"),
    ("عند", "ϧⲁⲧⲉⲛ", "ϩⲁⲧⲛ̄", PartOfSpeech.preposition, "عند، لدى، بجانب"),
    ("تحت", "ϧⲁ", "ϩⲁ", PartOfSpeech.preposition, "تحت، أسفل"),
    ("فوق", "ⲉ̀ϩⲣⲏⲓ ⲉ̀ϫⲉⲛ", "ⲉϩⲣⲁⲓ ⲉϫⲛ̄", PartOfSpeech.preposition, "فوق، أعلى"),
    ("قبل", "ϧⲁϫⲱ", "ϩⲁⲧⲏⲩ", PartOfSpeech.preposition, "قبل، قبل أوان"),
    ("بعد", "ⲙⲉⲛⲉⲛⲥⲁ", "ⲙⲛ̄ⲛ̄ⲥⲁ", PartOfSpeech.preposition, "بعد، في إثر"),
    ("بين", "ⲟⲩⲧⲉ", "ⲟⲩⲧⲉ", PartOfSpeech.preposition, "بين، في وسط"),
    ("امام", "ⲙ̀ⲡⲉⲙ̀ⲑⲟ ⲛ̀", "ⲙ̄ⲡⲉⲙ̄ⲧⲟ ⲛ̄", PartOfSpeech.preposition, "أمام، قدام، في حضرة"),
    ("قدام", "ⲙ̀ⲡⲉⲙ̀ⲑⲟ ⲛ̀", "ⲙ̄ⲡⲉⲙ̄ⲧⲟ ⲛ̄", PartOfSpeech.preposition, "قدام، أمام"),
    ("وراء", "ⲥⲁⲙⲉⲛϩⲏⲧ", "ϩⲓⲡⲁϩⲟⲩ", PartOfSpeech.preposition, "وراء، خلف"),
    ("خلف", "ⲥⲁⲙⲉⲛϩⲏⲧ", "ϩⲓⲡⲁϩⲟⲩ", PartOfSpeech.preposition, "خلف، وراء"),
    ("لاجل", "ⲉⲑⲃⲉ", "ⲉⲧⲃⲉ", PartOfSpeech.preposition, "لأجل، بسبب، في سبيل"),
    ("بسبب", "ⲉⲑⲃⲉ", "ⲉⲧⲃⲉ", PartOfSpeech.preposition, "بسبب، لأجل"),
    ("عن", "ⲉⲑⲃⲉ", "ⲉⲧⲃⲉ", PartOfSpeech.preposition, "عن، بخصوص"),
    ("حتى", "ϣⲁ", "ϣⲁ", PartOfSpeech.preposition, "حتى، إلى غاية"),
    ("بدون", "ⲁϭⲛⲉ", "ⲁϫⲛ̄", PartOfSpeech.preposition, "بدون، بغير، دون"),
    ("بغير", "ⲁϭⲛⲉ", "ⲁϫⲛ̄", PartOfSpeech.preposition, "بغير، دون"),
    ("مثل", "ⲙ̀ⲫⲣⲏϯ ⲛ̀", "ⲛ̄ⲑⲉ ⲛ̄", PartOfSpeech.preposition, "مثل، كـ، كشبه"),
    ("حسب", "ⲕⲁⲧⲁ", "ⲕⲁⲧⲁ", PartOfSpeech.preposition, "حسب، وفقاً لـ"),
    ("وفق", "ⲕⲁⲧⲁ", "ⲕⲁⲧⲁ", PartOfSpeech.preposition, "وفقاً لـ، بحسب"),
    ("بواسطة", "ⲉ̀ⲃⲟⲗ ϩⲓⲧⲉⲛ", "ⲉⲃⲟⲗ ϩⲓⲧⲛ̄", PartOfSpeech.preposition, "بواسطة، بيد، من خلال"),
    ("حول", "ⲕⲱϯ ⲉ̀", "ⲕⲱⲧⲉ ⲉ-", PartOfSpeech.preposition, "حول، محيطاً بـ"),
]


def run_curation():
    db = SessionLocal()
    try:
        # 1. Clean bad mappings
        print("Cleaning noisy / incorrect CCL mappings...")
        for lemma, bad_coptics in BAD_LEMMA_CLEANUPS:
            for bad_coptic in bad_coptics:
                db.execute(text("""
                    DELETE FROM sense_mappings 
                    WHERE dictionary_entry_id IN (
                        SELECT id FROM dictionary_entries WHERE coptic_text = :coptic OR normalized_coptic_text = :coptic
                    ) AND arabic_sense_id IN (
                        SELECT id FROM arabic_senses WHERE arabic_lemma = :lemma OR normalized_arabic_lemma = :lemma
                    )
                """), {"coptic": bad_coptic, "lemma": lemma})
        db.commit()
        print("  Bad mappings cleanup complete.")

        # 2. Get or create sources
        source = db.execute(select(Source).where(Source.title == "معجم القبطية والطقوس الكنسية المعتمد")).scalar_one_or_none()
        if not source:
            source = Source(
                title="معجم القبطية والطقوس الكنسية المعتمد",
                type=SourceType.dictionary,
                notes="قواميس اللغة القبطية ومراجع الطقوس والصلوات الكنسية المعتمدة (البحيرية والصعيدية).",
            )
            db.add(source)
            db.flush()
        source_id = source.id

        # Dialect IDs
        d_boh = db.execute(select(Dialect).where(Dialect.code == "bohairic")).scalar_one().id
        d_sah = db.execute(select(Dialect).where(Dialect.code == "sahidic")).scalar_one().id

        added_entries = 0
        added_senses = 0
        added_mappings = 0

        print(f"Seeding {len(CORE_VOCABULARY)} core vocabulary items...")
        for ar_raw, boh_text, sah_text, pos, definition in CORE_VOCABULARY:
            ar_norm = normalize_arabic(ar_raw)

            # Create or get Sense
            sense = db.execute(select(ArabicSense).where(
                ArabicSense.normalized_arabic_lemma == ar_norm,
                ArabicSense.source_id == source_id
            )).scalars().first()

            if not sense:
                sense = ArabicSense(
                    arabic_lemma=ar_raw,
                    normalized_arabic_lemma=ar_norm,
                    definition_ar=definition,
                    part_of_speech=pos,
                    source_id=source_id,
                    review_status=RecordStatus.approved,
                )
                db.add(sense)
                db.flush()
                added_senses += 1

            # Bohairic entry
            if boh_text:
                norm_boh = unicodedata.normalize("NFC", boh_text.strip().lower())
                e_boh = db.execute(select(DictionaryEntry).where(
                    DictionaryEntry.normalized_coptic_text == norm_boh,
                    DictionaryEntry.dialect_id == d_boh,
                )).scalars().first()

                if not e_boh:
                    e_boh = DictionaryEntry(
                        coptic_text=boh_text,
                        normalized_coptic_text=norm_boh,
                        dialect_id=d_boh,
                        source_id=source_id,
                        part_of_speech=pos,
                        review_status=RecordStatus.approved,
                    )
                    db.add(e_boh)
                    db.flush()
                    added_entries += 1

                # Link Bohairic
                map_boh = db.execute(select(SenseMapping).where(
                    SenseMapping.arabic_sense_id == sense.id,
                    SenseMapping.dictionary_entry_id == e_boh.id,
                )).scalars().first()

                if not map_boh:
                    map_boh = SenseMapping(
                        arabic_sense_id=sense.id,
                        dictionary_entry_id=e_boh.id,
                        confidence=1.0,
                        is_primary=True,
                        review_status=RecordStatus.approved,
                    )
                    db.add(map_boh)
                    added_mappings += 1
                else:
                    map_boh.confidence = 1.0
                    map_boh.is_primary = True

            # Sahidic entry
            if sah_text:
                norm_sah = unicodedata.normalize("NFC", sah_text.strip().lower())
                e_sah = db.execute(select(DictionaryEntry).where(
                    DictionaryEntry.normalized_coptic_text == norm_sah,
                    DictionaryEntry.dialect_id == d_sah,
                )).scalars().first()

                if not e_sah:
                    e_sah = DictionaryEntry(
                        coptic_text=sah_text,
                        normalized_coptic_text=norm_sah,
                        dialect_id=d_sah,
                        source_id=source_id,
                        part_of_speech=pos,
                        review_status=RecordStatus.approved,
                    )
                    db.add(e_sah)
                    db.flush()
                    added_entries += 1

                # Link Sahidic
                map_sah = db.execute(select(SenseMapping).where(
                    SenseMapping.arabic_sense_id == sense.id,
                    SenseMapping.dictionary_entry_id == e_sah.id,
                )).scalars().first()

                if not map_sah:
                    map_sah = SenseMapping(
                        arabic_sense_id=sense.id,
                        dictionary_entry_id=e_sah.id,
                        confidence=1.0,
                        is_primary=True,
                        review_status=RecordStatus.approved,
                    )
                    db.add(map_sah)
                    added_mappings += 1
                else:
                    map_sah.confidence = 1.0
                    map_sah.is_primary = True

        db.commit()
        print(f"✓ Curation complete! Added {added_entries} entries, {added_senses} senses, {added_mappings} mappings.")
    finally:
        db.close()


if __name__ == "__main__":
    run_curation()
