import csv
import json
import os
import sys
from pathlib import Path
import requests

# Set DATABASE_URL to SQLite for local operations
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///manual_web.db"

# Add backend directory to path so we can import from app
sys.path.append(str(Path(__file__).resolve().parents[2]))

from app.database import SessionLocal
from app.models import ArabicSense, DictionaryEntry, ParallelSegment, SenseMapping
from app.models.enums import RecordStatus
from app.services.coptic_nmt_import import (
    import_coptic_nmt_corpus_csv,
    import_coptic_nmt_dictionary_csv,
)

HF_CORPUS_URL = "https://huggingface.co/datasets/megalaa/coptic-corpora/resolve/main/sahidic_train.csv"
LEARN_APP_DATA_DIR = Path("E:/programing/projects/learn-coptic-language/assets/data")

def download_filtered_corpus(dest_path: Path):
    print("Filtering local sahidic_train.csv...")
    local_path = Path("sahidic_train.csv")
    if not local_path.exists():
        print("Error: local sahidic_train.csv not found!")
        return False
        
    with open(local_path, "r", encoding="utf-8") as in_file:
        reader = csv.reader(in_file)
        try:
            headers = next(reader)
        except StopIteration:
            print("Empty file.")
            return False
            
        with open(dest_path, "w", encoding="utf-8", newline="") as out_file:
            writer = csv.writer(out_file)
            writer.writerow(headers)
            
            row_count = 0
            arabic_row_count = 0
            
            for row in reader:
                row_count += 1
                row_dict = dict(zip(headers, row))
                ar = row_dict.get("arabic")
                if ar:
                    ar = ar.strip()
                    if ar and ar.lower() != "nan" and ar != "...":
                        writer.writerow(row)
                        arabic_row_count += 1
                        
    print(f"Filtered corpus written to {dest_path}. Total rows checked: {row_count}, Non-empty Arabic rows extracted: {arabic_row_count}")
    return True

def generate_dictionary_csv(dest_path: Path):
    print("Reading word data from learn-coptic-language...")
    words_ar_path = LEARN_APP_DATA_DIR / "words.json"
    words_en_path = LEARN_APP_DATA_DIR / "words_en.json"
    
    if not words_ar_path.exists() or not words_en_path.exists():
        print(f"Error: Learn app word data files not found in {LEARN_APP_DATA_DIR}")
        return False
        
    with open(words_ar_path, "r", encoding="utf-8") as f:
        words_ar = json.load(f)
        
    with open(words_en_path, "r", encoding="utf-8") as f:
        words_en = json.load(f)
        
    entries = {}
    
    def map_pos(raw_pos):
        if not raw_pos:
            return "noun"
        raw_pos = str(raw_pos).strip().lower()
        if raw_pos in ["مذكر", "مؤنث", "masculine", "feminine"]:
            return "noun"
        if raw_pos in ["اسم علم", "proper noun"]:
            return "proper noun"
        if raw_pos in ["عدد", "number", "numeral"]:
            return "numeral"
        return "noun"

    for category, items in words_ar.items():
        for item in items:
            item_id = item.get("id")
            if not item_id:
                continue
            entries[item_id] = {
                "coptic": item.get("coptic"),
                "arabic": item.get("meaning"),
                "pos": map_pos(item.get("gender") or item.get("pos")),
            }
            
    for category, items in words_en.items():
        for item in items:
            item_id = item.get("id")
            if not item_id:
                continue
            if item_id in entries:
                entries[item_id]["eng"] = item.get("meaning")
                
    # Write to dictionary CSV
    with open(dest_path, "w", encoding="utf-8", newline="") as out_file:
        writer = csv.DictWriter(out_file, fieldnames=["coptic", "eng", "arabic", "pos"])
        writer.writeheader()
        for entry in entries.values():
            if entry.get("coptic") and entry.get("arabic"):
                writer.writerow(entry)
                
    print(f"Generated dictionary CSV at {dest_path} with {len(entries)} words.")
    return True

def approve_all_pending(db):
    print("Approving all pending records in database...")
    
    # Approve Dictionary Entries
    updated_entries = db.query(DictionaryEntry).filter(
        DictionaryEntry.review_status == RecordStatus.pending
    ).update({DictionaryEntry.review_status: RecordStatus.approved})
    
    # Approve Arabic Senses
    updated_senses = db.query(ArabicSense).filter(
        ArabicSense.review_status == RecordStatus.pending
    ).update({ArabicSense.review_status: RecordStatus.approved})
    
    # Approve Sense Mappings
    updated_mappings = db.query(SenseMapping).filter(
        SenseMapping.review_status == RecordStatus.pending
    ).update({SenseMapping.review_status: RecordStatus.approved})
    
    # Approve Parallel Segments
    updated_segments = db.query(ParallelSegment).filter(
        ParallelSegment.review_status == RecordStatus.pending
    ).update({ParallelSegment.review_status: RecordStatus.approved})
    
    db.commit()
    print(f"Approved {updated_entries} dictionary entries, {updated_senses} senses, {updated_mappings} mappings, and {updated_segments} parallel segments.")

def main():
    temp_corpus_csv = Path("temp_coptic_nmt_corpus.csv")
    temp_dict_csv = Path("temp_coptic_nmt_dictionary.csv")
    
    # 1. Download and filter HF corpus
    if not download_filtered_corpus(temp_corpus_csv):
        print("Corpus processing failed.")
        return
        
    # 2. Parse and generate local dictionary CSV
    if not generate_dictionary_csv(temp_dict_csv):
        print("Dictionary processing failed.")
        return
        
    # 3. Connect to db and import
    print("Connecting to local SQLite database...")
    db = SessionLocal()
    try:
        # Import Corpus
        print("Importing parallel segments...")
        corpus_stats = import_coptic_nmt_corpus_csv(db, temp_corpus_csv, dialect_code="sahidic")
        print(f"Corpus import complete: {corpus_stats}")
        
        # Import Dictionary
        print("Importing dictionary entries...")
        dict_stats = import_coptic_nmt_dictionary_csv(db, temp_dict_csv, dialect_code="sahidic")
        print(f"Dictionary import complete: {dict_stats}")
        
        # Approve everything
        approve_all_pending(db)
        
        print("All data successfully imported and approved!")
    except Exception as e:
        db.rollback()
        print(f"Error during database import: {e}")
    finally:
        db.close()
        
    # Cleanup temp files
    if temp_corpus_csv.exists():
        os.remove(temp_corpus_csv)
    if temp_dict_csv.exists():
        os.remove(temp_dict_csv)

if __name__ == "__main__":
    main()
