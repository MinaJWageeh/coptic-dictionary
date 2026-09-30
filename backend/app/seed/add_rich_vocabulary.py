"""
Add rich authentic Coptic vocabulary for commonly searched words, professions,
military, daily life, nature, church, and society terms (Bohairic & Sahidic).
"""
import io, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///manual_web.db"
sys.path.insert(0, ".")

from app.database import SessionLocal
from app.models.dictionary import DictionaryEntry, ArabicSense, SenseMapping
from app.models.enums import PartOfSpeech, RecordStatus
from app.services.text import normalize_arabic, normalize_coptic

VOCABULARY = [
    # Guard / Watchman / Protect
    {
        "coptic": "ⲣⲉϥⲁⲣⲉϩ",
        "translit": "ref-areh",
        "dialect_id": 1,
        "pos": PartOfSpeech.noun,
        "arabic_lemma": "حارس",
        "definition_ar": "حارس، حافظ، رقيب، من يتولى الحراسة والحفظ",
        "variants": ["حارس", "حافظ", "رقيب", "حراس", "خفير"]
    },
    {
        "coptic": "ⲣⲉϥⲣⲟⲓⲥ",
        "translit": "ref-rois",
        "dialect_id": 1,
        "pos": PartOfSpeech.noun,
        "arabic_lemma": "ساهر",
        "definition_ar": "ساهر، حارس في الليل، رقيب",
        "variants": ["ساهر", "سهران", "حارس ليلي"]
    },
    {
        "coptic": "ⲁⲣⲉϩ",
        "translit": "areh",
        "dialect_id": 1,
        "pos": PartOfSpeech.verb,
        "arabic_lemma": "يحرس",
        "definition_ar": "يحرس، يحفظ، يصون، يرعى",
        "variants": ["حرس", "يحرس", "احرس", "حفظ", "يحفظ", "احفظ", "صان", "يصون"]
    },
    {
        "coptic": "ⲣⲟⲓⲥ",
        "translit": "rois",
        "dialect_id": 1,
        "pos": PartOfSpeech.verb,
        "arabic_lemma": "يسهر",
        "definition_ar": "يسهر، يرصد، يحرس متيقظاً",
        "variants": ["سهر", "يسهر", "اسهر"]
    },
    
    # Soldier / Army / Military
    {
        "coptic": "ⲙⲁⲧⲟⲓ",
        "translit": "matoi",
        "dialect_id": 1,
        "pos": PartOfSpeech.noun,
        "arabic_lemma": "جندي",
        "definition_ar": "جندي، عسكري، مقاتل، حارس عسكري",
        "variants": ["جندي", "عسكري", "مقاتل", "جنود", "عساكر"]
    },
    {
        "coptic": "ⲥⲧⲣⲁⲧⲓⲱⲧⲏⲥ",
        "translit": "stratiōtēs",
        "dialect_id": 1,
        "pos": PartOfSpeech.noun,
        "arabic_lemma": "جندي",
        "definition_ar": "جندي، محارب، عسكري (لفظ معرب من اليونانية)",
        "variants": ["جندي", "عسكري", "محارب"]
    },
    {
        "coptic": "ⲉⲕⲁⲧⲟⲛⲧⲁⲣⲭⲟⲥ",
        "translit": "hekatontarchos",
        "dialect_id": 1,
        "pos": PartOfSpeech.noun,
        "arabic_lemma": "قائد مئة",
        "definition_ar": "قائد مئة، ضابط روماني، قائد عسكري",
        "variants": ["قائد مئة", "قائد مئه", "قائد"]
    },
    {
        "coptic": "ⲥⲏϥⲓ",
        "translit": "sēfi",
        "dialect_id": 1,
        "pos": PartOfSpeech.noun,
        "arabic_lemma": "سيف",
        "definition_ar": "سيف، حسام، سلاح قاطع",
        "variants": ["سيف", "سيوف", "حسام"]
    },
    {
        "coptic": "ⲗⲉⲃϣ",
        "translit": "lebsh",
        "dialect_id": 1,
        "pos": PartOfSpeech.noun,
        "arabic_lemma": "درع",
        "definition_ar": "درع، مجن، ترس للحماية في الحرب",
        "variants": ["درع", "دروع", "ترس"]
    },
    {
        "coptic": "ⲡⲉⲣⲓⲕⲉⲫⲁⲗⲉⲁ",
        "translit": "perikefalea",
        "dialect_id": 1,
        "pos": PartOfSpeech.noun,
        "arabic_lemma": "خوذة",
        "definition_ar": "خوذة، خوذة الخلاص، غطاء الرأس العسكري",
        "variants": ["خوذة", "خوذه", "خوذ"]
    },
    {
        "coptic": "ϩⲟⲡⲗⲟⲛ",
        "translit": "hoplon",
        "dialect_id": 1,
        "pos": PartOfSpeech.noun,
        "arabic_lemma": "سلاح",
        "definition_ar": "سلاح، عتاد حربي",
        "variants": ["سلاح", "اسلحة", "اسلحه", "عتاد"]
    },
    {
        "coptic": "ⲡⲟⲗⲉⲙⲟⲥ",
        "translit": "polemos",
        "dialect_id": 1,
        "pos": PartOfSpeech.noun,
        "arabic_lemma": "حرب",
        "definition_ar": "حرب، قتال، معركة",
        "variants": ["حرب", "حروب", "معركة", "معركه"]
    },
    {
        "coptic": "ϭⲣⲟ",
        "translit": "ch'ro",
        "dialect_id": 1,
        "pos": PartOfSpeech.noun,
        "arabic_lemma": "نصر",
        "definition_ar": "نصر، غلبة، انتصار، ظفر",
        "variants": ["نصر", "غلبة", "غلبه", "انتصار", "ظفر"]
    },
    
    # Society / Professions / Ranks
    {
        "coptic": "ⲥⲏⲓⲛⲓ",
        "translit": "sēini",
        "dialect_id": 1,
        "pos": PartOfSpeech.noun,
        "arabic_lemma": "طبيب",
        "definition_ar": "طبيب، معالج، حكيم يشفي الأمراض",
        "variants": ["طبيب", "اطباء", "معالج", "دكتور"]
    },
    {
        "coptic": "ⲥⲁϧ",
        "translit": "sakh",
        "dialect_id": 1,
        "pos": PartOfSpeech.noun,
        "arabic_lemma": "معلم",
        "definition_ar": "معلم، كاتب، أستاذ، عالم",
        "variants": ["معلم", "كاتب", "استاذ", "علماء", "اساتذة"]
    },
    {
        "coptic": "ⲣⲉϥϯⲥⲃⲱ",
        "translit": "ref-ti-sbō",
        "dialect_id": 1,
        "pos": PartOfSpeech.noun,
        "arabic_lemma": "معلم",
        "definition_ar": "معلم، ملقن، مرشد تعليمي",
        "variants": ["معلم", "مدرس", "مرشد"]
    },
    {
        "coptic": "ⲣⲉϥϯϩⲁⲡ",
        "translit": "ref-ti-hap",
        "dialect_id": 1,
        "pos": PartOfSpeech.noun,
        "arabic_lemma": "قاضي",
        "definition_ar": "قاضي، حاكم، من يصدر الحكم والعدل",
        "variants": ["قاضي", "قضاة", "حاكم"]
    },
    {
        "coptic": "ⲕⲣⲓⲧⲏⲥ",
        "translit": "kritēs",
        "dialect_id": 1,
        "pos": PartOfSpeech.noun,
        "arabic_lemma": "ديان",
        "definition_ar": "ديان، قاضي، حاكم بالعدل",
        "variants": ["ديان", "قاضي", "حاكم"]
    },
    {
        "coptic": "ⲣⲉϥϫⲱⲣϫ",
        "translit": "ref-jōrj",
        "dialect_id": 1,
        "pos": PartOfSpeech.noun,
        "arabic_lemma": "صياد",
        "definition_ar": "صياد، صياد سمك، قناص",
        "variants": ["صياد", "صيادون", "صيادين", "قناص"]
    },
    {
        "coptic": "ⲟⲩⲟⲓ",
        "translit": "uoi",
        "dialect_id": 1,
        "pos": PartOfSpeech.noun,
        "arabic_lemma": "فلاح",
        "definition_ar": "فلاح، زارع، حارث الأرض",
        "variants": ["فلاح", "زارع", "مزارع", "فلاحين", "فلاحون"]
    },
    {
        "coptic": "ⲃⲱⲕ",
        "translit": "bōk",
        "dialect_id": 1,
        "pos": PartOfSpeech.noun,
        "arabic_lemma": "عبد",
        "definition_ar": "عبد، خادم، غلام",
        "variants": ["عبد", "خادم", "غلام", "عبيد", "خدام"]
    },
    {
        "coptic": "ⲃⲱⲕⲓ",
        "translit": "bōki",
        "dialect_id": 1,
        "pos": PartOfSpeech.noun,
        "arabic_lemma": "امة",
        "definition_ar": "أمة، جارية، خادمة",
        "variants": ["امة", "جارية", "خادمة", "خادمه", "اماء"]
    },
    {
        "coptic": "ⲣⲉϥϣⲉⲙϣⲓ",
        "translit": "ref-shemshi",
        "dialect_id": 1,
        "pos": PartOfSpeech.noun,
        "arabic_lemma": "خادم",
        "definition_ar": "خادم، شماس، عابد، ممارس الخدمة",
        "variants": ["خادم", "خدام", "شماس", "عابد"]
    },
    
    # Geography & Nature
    {
        "coptic": "ⲡⲟⲗⲓⲥ",
        "translit": "polis",
        "dialect_id": 1,
        "pos": PartOfSpeech.noun,
        "arabic_lemma": "مدينة",
        "definition_ar": "مدينة، بلدة كبرى",
        "variants": ["مدينة", "مدينه", "مدن", "بلدة", "بلده"]
    },
    {
        "coptic": "ⲃⲁⲕⲓ",
        "translit": "baki",
        "dialect_id": 1,
        "pos": PartOfSpeech.noun,
        "arabic_lemma": "مدينة",
        "definition_ar": "مدينة، قرية محصنة، بلدة",
        "variants": ["مدينة", "مدينه", "مدن", "بلدة"]
    },
    {
        "coptic": "ϯⲙⲓ",
        "translit": "timi",
        "dialect_id": 1,
        "pos": PartOfSpeech.noun,
        "arabic_lemma": "قرية",
        "definition_ar": "قرية، ضيعة، كفر، بلدة صغيرة",
        "variants": ["قرية", "قريه", "قرى", "ضيعة", "ضيعه"]
    },
    {
        "coptic": "ⲙⲱⲓⲧ",
        "translit": "mōit",
        "dialect_id": 1,
        "pos": PartOfSpeech.noun,
        "arabic_lemma": "طريق",
        "definition_ar": "طريق، سبيل، مسلك، درب",
        "variants": ["طريق", "سبيل", "مسلك", "درب", "طرق", "طرقات", "سبل"]
    },
    {
        "coptic": "ⲫⲓⲁⲣⲟ",
        "translit": "fiaro",
        "dialect_id": 1,
        "pos": PartOfSpeech.noun,
        "arabic_lemma": "نهر",
        "definition_ar": "نهر، مجرى مائي عذب، نهر النيل",
        "variants": ["نهر", "انهار", "النيل"]
    },
    {
        "coptic": "ⲓⲟⲙ",
        "translit": "iom",
        "dialect_id": 1,
        "pos": PartOfSpeech.noun,
        "arabic_lemma": "بحر",
        "definition_ar": "بحر، يم، لجة مائية واسعة",
        "variants": ["بحر", "بحار", "يم"]
    },
    {
        "coptic": "ⲧⲱⲟⲩ",
        "translit": "tōou",
        "dialect_id": 1,
        "pos": PartOfSpeech.noun,
        "arabic_lemma": "جبل",
        "definition_ar": "جبل، طود، مرتفع شاهق، دير في الجبل",
        "variants": ["جبل", "جبال", "طور"]
    },
    {
        "coptic": "ϣⲁϥⲉ",
        "translit": "shafe",
        "dialect_id": 1,
        "pos": PartOfSpeech.noun,
        "arabic_lemma": "برية",
        "definition_ar": "برية، صحراء، قفر، فضاء خالي",
        "variants": ["برية", "بريه", "صحراء", "قفر"]
    },
]


def add_vocabulary():
    db = SessionLocal()
    try:
        added_entries = 0
        added_senses = 0
        added_mappings = 0

        for item in VOCABULARY:
            cop = item["coptic"].strip()
            norm_cop = normalize_coptic(cop)
            dialect_id = item["dialect_id"]
            pos = item["pos"]

            # 1. Find or create DictionaryEntry
            entry = db.query(DictionaryEntry).filter(
                DictionaryEntry.coptic_text == cop,
                DictionaryEntry.dialect_id == dialect_id
            ).first()

            if not entry:
                entry = DictionaryEntry(
                    coptic_text=cop,
                    normalized_coptic_text=norm_cop,
                    transliteration=item.get("translit"),
                    dialect_id=dialect_id,
                    source_id=1,
                    part_of_speech=pos,
                    review_status=RecordStatus.approved,
                    notes=item["definition_ar"]
                )
                db.add(entry)
                db.flush()
                added_entries += 1

            # 2. Add all variant Arabic senses and map them
            all_variants = [item["arabic_lemma"]] + item.get("variants", [])
            seen_norm_lemmas = set()
            mapped_sense_ids = set()

            for var in all_variants:
                norm_ar = normalize_arabic(var)
                if not norm_ar or norm_ar in seen_norm_lemmas:
                    continue
                seen_norm_lemmas.add(norm_ar)

                # Find or create ArabicSense
                sense = db.query(ArabicSense).filter(
                    ArabicSense.normalized_arabic_lemma == norm_ar
                ).first()

                if not sense:
                    sense = ArabicSense(
                        arabic_lemma=var,
                        normalized_arabic_lemma=norm_ar,
                        sense_key=f"{norm_ar}:1",
                        definition_ar=item["definition_ar"],
                        part_of_speech=pos,
                        source_id=1,
                        review_status=RecordStatus.approved
                    )
                    db.add(sense)
                    db.flush()
                    added_senses += 1

                if sense.id in mapped_sense_ids:
                    continue

                # Check if mapping already exists
                mapping = db.query(SenseMapping).filter(
                    SenseMapping.dictionary_entry_id == entry.id,
                    SenseMapping.arabic_sense_id == sense.id
                ).first()

                if not mapping:
                    mapping = SenseMapping(
                        dictionary_entry_id=entry.id,
                        arabic_sense_id=sense.id,
                        confidence=0.99,
                        is_primary=(norm_ar == normalize_arabic(item["arabic_lemma"])),
                        review_status=RecordStatus.approved,
                        usage_note="Lexical mapping added via vocabulary enrichment"
                    )
                    db.add(mapping)
                    added_mappings += 1

                mapped_sense_ids.add(sense.id)

        db.commit()
        print(f"Successfully added {added_entries} entries, {added_senses} senses, and {added_mappings} mappings!")
    except Exception as e:
        db.rollback()
        print(f"Error adding vocabulary: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    add_vocabulary()
