"""
Import Coptic dictionary entries from the Coptic Compass API (copticcompass.com).

This script fetches all ~6,300+ entries from the Comprehensive Coptic Lexicon
via the Coptic Compass REST API and imports them into our local SQLite database.

Each entry gets:
  - A DictionaryEntry (coptic_text, transliteration, dialect, part_of_speech)
  - An ArabicSense (arabic translation derived from English gloss)
  - A SenseMapping linking the two

English glosses are translated to Arabic using a comprehensive built-in dictionary
of common English-Arabic word translations for religious/Coptic vocabulary.
"""

import io
import json
import os
import sys
import time
import unicodedata
from pathlib import Path

# Force UTF-8 stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# Set DATABASE_URL to SQLite for local operations
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///manual_web.db"

# Add backend directory to path
sys.path.append(str(Path(__file__).resolve().parents[2]))

import requests
from sqlalchemy import select

from app.database import SessionLocal
from app.models import ArabicSense, DictionaryEntry, SenseMapping
from app.models.dictionary import Dialect
from app.models.enums import PartOfSpeech, RecordStatus
from app.models.source import Source

# ---------------------------------------------------------------------------
# English -> Arabic Translation Dictionary
# Covers common Coptic/religious/general vocabulary
# ---------------------------------------------------------------------------
EN_TO_AR = {
    # Religious / Spiritual
    "god": "الله", "lord": "رب", "jesus": "يسوع", "christ": "المسيح",
    "holy": "مقدس", "spirit": "روح", "soul": "نفس", "angel": "ملاك",
    "heaven": "سماء", "hell": "جحيم", "sin": "خطيئة", "prayer": "صلاة",
    "pray": "صلى", "worship": "عبادة", "faith": "إيمان", "grace": "نعمة",
    "salvation": "خلاص", "church": "كنيسة", "priest": "كاهن", "bishop": "أسقف",
    "monk": "راهب", "saint": "قديس", "cross": "صليب", "baptism": "معمودية",
    "communion": "تناول", "eucharist": "إفخارستيا", "resurrection": "قيامة",
    "repentance": "توبة", "confession": "اعتراف", "praise": "تسبيح",
    "thanksgiving": "شكر", "blessing": "بركة", "miracle": "معجزة",
    "prophet": "نبي", "apostle": "رسول", "disciple": "تلميذ",
    "gospel": "إنجيل", "scripture": "كتاب مقدس", "psalm": "مزمور",
    "hymn": "ترنيمة", "altar": "مذبح", "temple": "هيكل",
    "sacrifice": "ذبيحة", "offering": "قربان", "incense": "بخور",
    "icon": "أيقونة", "virgin": "عذراء", "martyr": "شهيد",
    "paradise": "فردوس", "kingdom": "ملكوت", "eternal": "أبدي",
    "eternity": "أبدية", "righteous": "بار", "righteousness": "بر",
    "mercy": "رحمة", "forgiveness": "مغفرة", "forgive": "غفر",
    "redeem": "فدى", "rescue": "أنقذ", "ransom": "فدية",
    "covenant": "عهد", "commandment": "وصية", "law": "شريعة",
    "judgment": "دينونة", "judge": "قاضي", "justice": "عدل",
    "truth": "حقيقة", "true": "حقيقي", "wisdom": "حكمة",
    "knowledge": "معرفة", "revelation": "إعلان", "mystery": "سر",
    "glory": "مجد", "honour": "كرامة", "honor": "كرامة",
    "power": "قوة", "strength": "قوة", "authority": "سلطة",
    "dominion": "سيادة", "creation": "خليقة", "creator": "خالق",
    "savior": "مخلص", "redeemer": "فادي", "shepherd": "راعي",
    "flock": "قطيع", "lamb": "حمل", "dove": "حمامة",
    "devil": "شيطان", "demon": "شيطان", "evil": "شر",
    "wicked": "شرير", "darkness": "ظلمة", "death": "موت",
    "die": "مات", "dead": "ميت", "burial": "دفن",
    "tomb": "قبر", "grave": "قبر",

    # Body
    "eye": "عين", "ear": "أذن", "mouth": "فم", "hand": "يد",
    "foot": "قدم", "head": "رأس", "face": "وجه", "heart": "قلب",
    "mind": "عقل", "body": "جسد", "flesh": "لحم", "blood": "دم",
    "bone": "عظم", "skin": "جلد", "tongue": "لسان", "tooth": "سن",
    "hair": "شعر", "finger": "إصبع", "arm": "ذراع", "leg": "ساق",
    "neck": "عنق", "shoulder": "كتف", "chest": "صدر", "belly": "بطن",
    "knee": "ركبة", "lip": "شفة", "nose": "أنف", "back": "ظهر",
    "breast": "ثدي", "womb": "رحم",

    # Nature
    "light": "نور", "sun": "شمس", "moon": "قمر", "star": "نجم",
    "sky": "سماء", "earth": "أرض", "land": "أرض", "sea": "بحر",
    "water": "ماء", "river": "نهر", "mountain": "جبل", "tree": "شجرة",
    "fire": "نار", "wind": "ريح", "rain": "مطر", "cloud": "سحابة",
    "stone": "حجر", "rock": "صخرة", "sand": "رمل", "dust": "تراب",
    "flower": "زهرة", "fruit": "ثمرة", "seed": "بذرة", "grass": "عشب",
    "field": "حقل", "garden": "حديقة", "desert": "صحراء",
    "dawn": "فجر", "night": "ليل", "day": "يوم",
    "gold": "ذهب", "silver": "فضة", "iron": "حديد",

    # People / Relations
    "man": "رجل", "woman": "امرأة", "child": "طفل", "son": "ابن",
    "daughter": "ابنة", "father": "أب", "mother": "أم",
    "brother": "أخ", "sister": "أخت", "husband": "زوج", "wife": "زوجة",
    "king": "ملك", "queen": "ملكة", "servant": "خادم", "slave": "عبد",
    "master": "سيد", "friend": "صديق", "enemy": "عدو",
    "human being": "إنسان", "human": "إنساني", "people": "شعب",
    "nation": "أمة", "tribe": "قبيلة", "family": "عائلة",
    "elder": "شيخ", "youth": "شاب", "baby": "رضيع",
    "noble": "نبيل", "royal": "ملكي", "kinsman": "قريب",

    # Actions / Verbs
    "give": "أعطى", "take": "أخذ", "come": "جاء", "go": "ذهب",
    "see": "رأى", "look": "نظر", "hear": "سمع", "speak": "تكلم",
    "say": "قال", "tell": "أخبر", "write": "كتب", "read": "قرأ",
    "know": "عرف", "think": "فكر", "believe": "آمن",
    "love": "أحب", "hate": "كره", "fear": "خاف",
    "eat": "أكل", "drink": "شرب", "sleep": "نام",
    "walk": "مشى", "run": "ركض", "sit": "جلس", "stand": "وقف",
    "open": "فتح", "close": "أغلق", "hide": "أخفى",
    "find": "وجد", "seek": "طلب", "ask": "سأل",
    "live": "عاش", "die": "مات", "kill": "قتل",
    "build": "بنى", "destroy": "دمر", "break": "كسر",
    "make": "صنع", "do": "فعل", "create": "خلق",
    "send": "أرسل", "receive": "استقبل", "carry": "حمل",
    "put": "وضع", "set": "ثبت", "place": "وضع",
    "fight": "قاتل", "fall": "سقط", "rise": "قام",
    "become": "صار", "be": "كان", "exist": "وُجد",
    "pay": "دفع", "buy": "اشترى", "sell": "باع",
    "sing": "غنى", "cry": "بكى", "laugh": "ضحك",
    "teach": "علم", "learn": "تعلم", "rule": "حكم",
    "heal": "شفى", "suffer": "تألم", "bear": "حمل",
    "beget": "ولد", "bring forth": "أنجب",
    "smite": "ضرب", "grasp": "أمسك", "embrace": "احتضن",
    "possess": "امتلك", "detain": "حبس", "restrain": "كبح",
    "prevail": "تغلب", "entreat": "توسل", "console": "عزى",
    "reveal": "كشف", "uncover": "أظهر",
    "dwell": "سكن", "exalt": "عظّم",
    "acquit": "برّأ", "acquire": "اكتسب",
    "register": "سجل", "draw": "رسم", "paint": "رسم",
    "behold": "تأمل", "provide": "وفر",
    "cease": "توقف", "stop": "توقف",

    # Adjectives / Qualities
    "good": "جيد", "bad": "سيء", "great": "عظيم",
    "small": "صغير", "big": "كبير", "old": "قديم", "new": "جديد",
    "young": "شاب", "strong": "قوي", "weak": "ضعيف",
    "rich": "غني", "poor": "فقير", "beautiful": "جميل",
    "high": "عالي", "low": "منخفض", "deep": "عميق",
    "long": "طويل", "short": "قصير", "wide": "واسع",
    "clean": "نظيف", "pure": "طاهر", "bright": "مشرق",
    "luminous": "مضيء", "hidden": "مخفي", "acceptable": "مقبول",
    "divine": "إلهي", "godly": "تقي",

    # Abstract / Concepts
    "life": "حياة", "love": "حب", "peace": "سلام",
    "hope": "رجاء", "joy": "فرح", "happiness": "سعادة",
    "sorrow": "حزن", "pain": "ألم", "fear": "خوف",
    "war": "حرب", "freedom": "حرية", "word": "كلمة",
    "name": "اسم", "voice": "صوت", "time": "وقت",
    "place": "مكان", "way": "طريق", "path": "مسلك",
    "work": "عمل", "rest": "راحة", "food": "طعام",
    "bread": "خبز", "wine": "خمر", "oil": "زيت",
    "garment": "ثوب", "cloth": "قماش", "sword": "سيف",
    "book": "كتاب", "letter": "رسالة", "sign": "علامة",
    "miracle": "معجزة", "wonder": "عجب", "treasure": "كنز",
    "treasury": "خزينة", "store house": "مخزن",
    "age": "عصر", "period of time": "فترة زمنية",
    "house": "بيت", "household": "أسرة", "door": "باب",
    "road": "طريق", "city": "مدينة", "village": "قرية",
    "country": "بلد", "world": "عالم",
    "ship": "سفينة", "boat": "قارب",

    # Thanks
    "thank": "شكر", "thanks": "شكر", "thanked": "شكر",
    "gratitude": "امتنان", "acknowledgment": "اعتراف",
    "thanks-giver": "شاكر",

    # Misc
    "receive": "استلم", "contain": "احتوى",
    "giver": "مانح", "receiver": "مستلم",
    "have pity": "رحم", "pity": "شفقة",
}


def pos_from_api(api_pos: str) -> PartOfSpeech:
    """Map Coptic Compass API POS codes to our PartOfSpeech enum."""
    mapping = {
        "N": PartOfSpeech.noun,
        "V": PartOfSpeech.verb,
        "ADJ": PartOfSpeech.adjective,
        "ADV": PartOfSpeech.adverb,
        "PREP": PartOfSpeech.preposition,
        "CONJ": PartOfSpeech.conjunction,
        "NUM": PartOfSpeech.numeral,
        "ART": PartOfSpeech.article,
        "INTJ": PartOfSpeech.interjection,
        "PRON": PartOfSpeech.pronoun,
        "PART": PartOfSpeech.particle,
    }
    return mapping.get(api_pos, PartOfSpeech.other)


def translate_en_to_ar(english_glosses: list[str]) -> str:
    """Translate a list of English glosses to Arabic using our built-in dictionary."""
    arabic_parts = []
    for gloss in english_glosses:
        gloss_lower = gloss.lower().strip()
        # Try direct match
        if gloss_lower in EN_TO_AR:
            arabic_parts.append(EN_TO_AR[gloss_lower])
            continue
        # Try matching individual words in multi-word glosses
        words = gloss_lower.replace(",", "").split()
        translated_words = []
        for word in words:
            word = word.strip(".,;:()")
            if word in EN_TO_AR:
                translated_words.append(EN_TO_AR[word])
        if translated_words:
            arabic_parts.append("، ".join(dict.fromkeys(translated_words)))  # unique, preserve order
        else:
            # Keep the English as-is if no translation found
            arabic_parts.append(gloss)
    return "، ".join(arabic_parts) if arabic_parts else ""


def normalize_coptic(text: str) -> str:
    """Normalize Coptic text for matching."""
    return unicodedata.normalize("NFC", text.strip().lower())


def get_or_create_dialect(session, code: str, name: str) -> int:
    """Get or create a dialect by code."""
    dialect = session.execute(
        select(Dialect).where(Dialect.code == code)
    ).scalar_one_or_none()
    if not dialect:
        dialect = Dialect(code=code, name=name, is_active=True)
        session.add(dialect)
        session.flush()
    return dialect.id


def get_or_create_source(session, title: str, source_type: str) -> int:
    """Get or create a source."""
    from app.models.enums import SourceType
    source = session.execute(
        select(Source).where(Source.title == title)
    ).scalar_one_or_none()
    if not source:
        st = SourceType.lexicon if source_type == "lexicon" else SourceType.dictionary
        source = Source(
            title=title,
            type=st,
            url="https://coptic-dictionary.org",
            notes="Comprehensive Coptic Lexicon (CCL) v1.2, CC BY-SA 4.0. Data from copticcompass.com API.",
        )
        session.add(source)
        session.flush()
    return source.id


DIALECT_MAP = {
    "S": ("sahidic", "Sahidic"),
    "B": ("bohairic", "Bohairic"),
    "F": ("fayyumic", "Fayyumic"),
    "A": ("akhmimic", "Akhmimic"),
    "L": ("lycopolitan", "Lycopolitan"),
    "M": ("lycopolitan", "Mesokemic"),
    "O": ("sahidic", "Old Coptic / Proto-Sahidic"),
    "Sa": ("sahidic", "Sahidic Variant"),
    "Sf": ("sahidic", "Sub-Fayyumic"),
    "Sl": ("sahidic", "Sub-Lycopolitan"),
}


def fetch_all_entries() -> list[dict]:
    """Fetch all entries from the Coptic Compass API."""
    all_entries = []
    offset = 0
    limit = 100
    total = None

    while True:
        url = f"https://www.copticcompass.com/api/v1/dictionary/search?q=&limit={limit}&offset={offset}"
        print(f"  Fetching offset={offset} ...", end=" ")
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(2)
            continue

        entries = data.get("entries", [])
        if total is None:
            total = data.get("totalEntries", 0)
            print(f"Total entries available: {total}")

        all_entries.extend(entries)
        print(f"got {len(entries)} entries (total so far: {len(all_entries)})")

        if not data.get("hasMore", False) or not entries:
            break

        offset += limit
        time.sleep(0.3)  # Be respectful to the API

    return all_entries


def import_entries(entries: list[dict]):
    """Import fetched entries into the database."""
    session = SessionLocal()
    try:
        # Create source
        source_id = get_or_create_source(session, "Comprehensive Coptic Lexicon (CCL)", "lexicon")

        # Pre-cache dialect IDs
        dialect_cache: dict[str, int] = {}
        for code, (db_code, name) in DIALECT_MAP.items():
            dialect_cache[code] = get_or_create_dialect(session, db_code, name)

        # Default dialect for entries without a specific one
        default_dialect_id = dialect_cache.get("S", 1)

        new_entries = 0
        new_senses = 0
        new_mappings = 0
        skipped = 0

        for i, entry in enumerate(entries):
            headword = entry.get("headword", "").strip()
            if not headword:
                continue

            # Collect all senses' English meanings
            senses = entry.get("senses", [])
            if not senses:
                continue

            # Determine the primary dialect
            dialects_data = entry.get("dialects", {})
            primary_dialect_code = None
            for d_code in ["S", "B", "A", "F", "L"]:  # Prefer Sahidic > Bohairic
                if d_code in dialects_data:
                    primary_dialect_code = d_code
                    break
            if not primary_dialect_code and dialects_data:
                primary_dialect_code = next(iter(dialects_data))

            dialect_id = dialect_cache.get(primary_dialect_code, default_dialect_id) if primary_dialect_code else default_dialect_id

            # Get the absolute form for the primary dialect
            coptic_text = headword
            if primary_dialect_code and primary_dialect_code in dialects_data:
                d_info = dialects_data[primary_dialect_code]
                if isinstance(d_info, dict) and "absolute" in d_info:
                    coptic_text = d_info["absolute"]

            normalized = normalize_coptic(coptic_text)

            # Process each sense
            for sense in senses:
                grammar = sense.get("grammar", {})
                api_pos = grammar.get("pos", "")
                pos = pos_from_api(api_pos)

                # Get English meanings
                meanings = sense.get("meanings", {})
                en_meanings = meanings.get("en", [])
                if not en_meanings:
                    continue

                # Check if this entry already exists
                existing = session.execute(
                    select(DictionaryEntry).where(
                        DictionaryEntry.normalized_coptic_text == normalized,
                        DictionaryEntry.dialect_id == dialect_id,
                        DictionaryEntry.part_of_speech == pos,
                        DictionaryEntry.source_id == source_id,
                    )
                ).scalar_one_or_none()

                if existing:
                    dict_entry = existing
                    skipped += 1
                else:
                    dict_entry = DictionaryEntry(
                        coptic_text=coptic_text,
                        normalized_coptic_text=normalized,
                        transliteration=None,  # Not available in API
                        dialect_id=dialect_id,
                        source_id=source_id,
                        part_of_speech=pos,
                        review_status=RecordStatus.approved,
                    )
                    session.add(dict_entry)
                    session.flush()
                    new_entries += 1

                # Translate English to Arabic
                arabic_text = translate_en_to_ar(en_meanings)
                english_text = "; ".join(en_meanings)

                if not arabic_text:
                    continue

                # Create or get Arabic sense
                existing_sense = session.execute(
                    select(ArabicSense).where(
                        ArabicSense.arabic_lemma == arabic_text.split("،")[0].strip(),
                        ArabicSense.definition_ar == arabic_text,
                    )
                ).scalar_one_or_none()

                if existing_sense:
                    sense_obj = existing_sense
                else:
                    sense_obj = ArabicSense(
                        arabic_lemma=arabic_text.split("،")[0].strip(),
                        normalized_arabic_lemma=arabic_text.split("،")[0].strip(),
                        definition_ar=f"{arabic_text}. English: {english_text}",
                        part_of_speech=pos,
                        source_id=source_id,
                        review_status=RecordStatus.approved,
                    )
                    session.add(sense_obj)
                    session.flush()
                    new_senses += 1

                # Create mapping if it doesn't exist
                existing_mapping = session.execute(
                    select(SenseMapping).where(
                        SenseMapping.arabic_sense_id == sense_obj.id,
                        SenseMapping.dictionary_entry_id == dict_entry.id,
                    )
                ).scalar_one_or_none()

                if not existing_mapping:
                    mapping = SenseMapping(
                        arabic_sense_id=sense_obj.id,
                        dictionary_entry_id=dict_entry.id,
                        confidence=0.85,
                        is_primary=True,
                        review_status=RecordStatus.approved,
                    )
                    session.add(mapping)
                    new_mappings += 1

            # Periodic commit and progress
            if (i + 1) % 500 == 0:
                session.commit()
                print(f"  Progress: {i + 1}/{len(entries)} entries processed "
                      f"(new entries: {new_entries}, senses: {new_senses}, mappings: {new_mappings})")

        session.commit()
        print(f"\n✓ Import completed!")
        print(f"  New dictionary entries: {new_entries}")
        print(f"  New Arabic senses: {new_senses}")
        print(f"  New sense mappings: {new_mappings}")
        print(f"  Skipped (already existed): {skipped}")

    except Exception as e:
        session.rollback()
        print(f"\n✗ Error during import: {e}")
        raise
    finally:
        session.close()


def main():
    print("=" * 60)
    print("Coptic Compass Lexicon Importer")
    print("=" * 60)
    print()

    print("Step 1: Fetching entries from Coptic Compass API...")
    entries = fetch_all_entries()
    print(f"\nFetched {len(entries)} entries total.")

    if not entries:
        print("No entries fetched. Aborting.")
        return

    print(f"\nStep 2: Importing into database...")
    import_entries(entries)

    print("\nDone!")


if __name__ == "__main__":
    main()
