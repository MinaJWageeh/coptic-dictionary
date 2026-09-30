"""
Import Coptic-Arabic Biblical and Patristic Parallel Corpora (7,900+ verses).
Source: UBC-NLP CoPARA / Coptic Scriptorium
Populates `parallel_segments` and `corpus_texts` in manual_web.db.
"""
from __future__ import annotations

import io
import os
import sys
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///manual_web.db"
sys.path.insert(0, ".")

from app.database import SessionLocal
from app.models.enums import RecordStatus
from app.models.examples import CorpusText, ParallelSegment
from app.models.source import Source
from app.services.embedding import embed_text
from app.services.text import normalize_arabic, normalize_coptic

COPTIC_URL = "https://raw.githubusercontent.com/UBC-NLP/copticmt/main/CoPARA/processed_coptic.txt"
ARABIC_URL = "https://raw.githubusercontent.com/UBC-NLP/copticmt/main/CoPARA/processed_arabic.txt"


def import_biblical_parallel_corpora():
    print("Downloading CoPARA parallel biblical corpus...")
    req_c = urllib.request.Request(COPTIC_URL, headers={"User-Agent": "Mozilla/5.0"})
    req_a = urllib.request.Request(ARABIC_URL, headers={"User-Agent": "Mozilla/5.0"})

    with urllib.request.urlopen(req_c) as rc, urllib.request.urlopen(req_a) as ra:
        c_lines = rc.read().decode("utf-8").splitlines()
        a_lines = ra.read().decode("utf-8").splitlines()

    total = min(len(c_lines), len(a_lines))
    print(f"Downloaded {total} parallel sentence pairs.")

    db = SessionLocal()
    try:
        from app.models.enums import SourceType
        # Get or create Source
        source = db.query(Source).filter(Source.title.like("%CoPARA%")).first()
        if not source:
            source = Source(
                title="الكتاب المقدس القبطي العربي (CoPARA / Coptic Scriptorium)",
                author="مشروع CoPARA و Coptic Scriptorium",
                type=SourceType.corpus,
                url="https://github.com/UBC-NLP/copticmt",
                notes="مجموعة نصوص متوازية من العهد الجديد والمزامير باللغتين القبطية البحيرية والعربية من مشروع CoPARA وCoptic Scriptorium",
            )
            db.add(source)
            db.flush()

        # Get or create CorpusText
        corpus = db.query(CorpusText).filter(CorpusText.title == "العهد الجديد والمزامير قبطي-عربي").first()
        if not corpus:
            corpus = CorpusText(
                title="العهد الجديد والمزامير قبطي-عربي",
                source_id=source.id,
                dialect_id=1,  # Bohairic
                language="cop-ar",
                content="نصوص العهد الجديد والمزامير متوازية قبطي بحيري وعربي",
                review_status=RecordStatus.approved,
            )
            db.add(corpus)
            db.flush()

        # Load existing normalized texts to avoid duplicates
        existing_texts = set(
            db.query(ParallelSegment.normalized_arabic_text)
            .filter(ParallelSegment.normalized_arabic_text.isnot(None))
            .all()
        )
        existing_set = {t[0] for t in existing_texts if t[0]}
        print(f"Found {len(existing_set)} existing parallel segments in DB.")

        new_segments = []
        batch_size = 500
        inserted_count = 0

        for i in range(total):
            c_raw = c_lines[i].strip()
            a_raw = a_lines[i].strip()

            if not c_raw or not a_raw or len(a_raw) < 3 or len(c_raw) < 3:
                continue

            # Skip chapter headers like "5." or "﻿مَتَّى."
            if a_raw.isdigit() or c_raw.isdigit():
                continue

            norm_ar = normalize_arabic(a_raw)
            if not norm_ar or norm_ar in existing_set:
                continue

            norm_cop = normalize_coptic(c_raw)
            emb = embed_text(norm_ar)

            seg = ParallelSegment(
                corpus_text_id=corpus.id,
                source_id=source.id,
                dialect_id=1,
                segment_order=inserted_count + 1,
                arabic_text=a_raw,
                coptic_text=c_raw,
                normalized_arabic_text=norm_ar,
                normalized_coptic_text=norm_cop,
                alignment_score=1.0,
                arabic_embedding=emb,
                coptic_embedding=None,
                sentence_embedding=emb,
                review_status=RecordStatus.approved,
            )
            new_segments.append(seg)
            existing_set.add(norm_ar)
            inserted_count += 1

            if len(new_segments) >= batch_size:
                db.add_all(new_segments)
                db.commit()
                print(f"Committed {inserted_count} / {total} segments...")
                new_segments = []

        if new_segments:
            db.add_all(new_segments)
            db.commit()
            print(f"Committed remaining {len(new_segments)} segments.")

        total_in_db = db.query(ParallelSegment).count()
        print(f"Successfully imported {inserted_count} new biblical parallel segments!")
        print(f"Total Parallel Segments in DB now: {total_in_db}")

    except Exception as e:
        db.rollback()
        print(f"Error importing parallel corpus: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import_biblical_parallel_corpora()
