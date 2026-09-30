"""
Import full Coptic vocabulary from learn-coptic-language assets/data/words.json
into manual_web.db.
"""
import io
import json
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

JSON_PATH = Path("E:/programing/projects/learn-coptic-language/assets/data/words.json")

def clean_arabic_meaning(meaning: str) -> list[str]:
    meaning = meaning.replace("،", ",").replace("/", ",")
    parts = []
    for part in meaning.split(","):
        cleaned = part.strip()
        cleaned_no_paren = unicodedata.normalize("NFC", cleaned)
        if "(" in cleaned_no_paren:
            base = cleaned_no_paren.split("(")[0].strip()
            if base:
                parts.append(base)
        if cleaned_no_paren:
            parts.append(cleaned_no_paren)
    return list(dict.fromkeys(parts))


def run_import():
    if not JSON_PATH.exists():
        print(f"Error: {JSON_PATH} not found!")
        return

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    db = SessionLocal()
    try:
        source = db.execute(select(Source).where(Source.title == "معجم مناهج اللغة القبطية والطقوس الكنسية")).scalars().first()
        if not source:
            source = Source(
                title="معجم مناهج اللغة القبطية والطقوس الكنسية",
                type=SourceType.lexicon,
                notes="قواميس ومفردات مناهج اللغة القبطية لكافة المراحل والطقوس الكنسية مع النطق والمعاني العربية.",
            )
            db.add(source)
            db.flush()
        source_id = source.id

        d_boh = db.execute(select(Dialect).where(Dialect.code == "bohairic")).scalars().first().id

        # Preload existing mappings to avoid duplicates
        existing_mappings_set = set(
            db.execute(text("SELECT arabic_sense_id, dictionary_entry_id FROM sense_mappings")).fetchall()
        )

        added_entries = 0
        added_senses = 0
        added_mappings = 0
        existing_entries = 0

        for stage_name, words in data.items():
            if not isinstance(words, list):
                continue
            for item in words:
                coptic_text = item.get("coptic", "").strip()
                pronunciation = item.get("pronunciation", "").strip()
                raw_meaning = item.get("meaning", "").strip()
                gender = item.get("gender")

                if not coptic_text or not raw_meaning:
                    continue

                norm_coptic = unicodedata.normalize("NFC", coptic_text.lower())
                
                entry = db.execute(select(DictionaryEntry).where(
                    DictionaryEntry.normalized_coptic_text == norm_coptic,
                    DictionaryEntry.dialect_id == d_boh
                )).scalars().first()

                if not entry:
                    entry = DictionaryEntry(
                        coptic_text=coptic_text,
                        normalized_coptic_text=norm_coptic,
                        transliteration=pronunciation or None,
                        dialect_id=d_boh,
                        source_id=source_id,
                        part_of_speech=PartOfSpeech.noun,
                        gender=gender if gender in ("m", "f") else None,
                        notes=f"النطق: {pronunciation} | المرحلة: {stage_name}" if pronunciation else f"المرحلة: {stage_name}",
                        review_status=RecordStatus.approved,
                    )
                    db.add(entry)
                    db.flush()
                    added_entries += 1
                else:
                    existing_entries += 1
                    if pronunciation and not entry.transliteration:
                        entry.transliteration = pronunciation

                meanings = clean_arabic_meaning(raw_meaning)
                for m in meanings:
                    norm_ar = normalize_arabic(m)
                    if not norm_ar:
                        continue

                    sense = db.execute(select(ArabicSense).where(
                        ArabicSense.normalized_arabic_lemma == norm_ar,
                        ArabicSense.source_id == source_id
                    )).scalars().first()

                    if not sense:
                        sense = ArabicSense(
                            arabic_lemma=m,
                            normalized_arabic_lemma=norm_ar,
                            definition_ar=f"{raw_meaning} (نطق: {pronunciation})" if pronunciation else raw_meaning,
                            part_of_speech=PartOfSpeech.noun,
                            source_id=source_id,
                            review_status=RecordStatus.approved,
                        )
                        db.add(sense)
                        db.flush()
                        added_senses += 1

                    pair = (sense.id, entry.id)
                    if pair not in existing_mappings_set:
                        mapping = SenseMapping(
                            arabic_sense_id=sense.id,
                            dictionary_entry_id=entry.id,
                            confidence=1.0,
                            is_primary=True,
                            usage_note=f"منهج {stage_name}",
                            review_status=RecordStatus.approved,
                        )
                        db.add(mapping)
                        existing_mappings_set.add(pair)
                        added_mappings += 1

        db.commit()
        print("✓ Import of learn-coptic words completed successfully!")
        print(f"  New Dictionary Entries: {added_entries}")
        print(f"  Existing Entries updated: {existing_entries}")
        print(f"  New Arabic Senses: {added_senses}")
        print(f"  New Sense Mappings: {added_mappings}")
    finally:
        db.close()


if __name__ == "__main__":
    run_import()
