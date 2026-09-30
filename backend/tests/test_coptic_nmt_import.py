from __future__ import annotations

import csv

from app.models import ArabicSense, CorpusText, DictionaryEntry, ParallelSegment, SenseMapping, Source
from app.models.enums import RecordStatus
from app.services.coptic_nmt_import import (
    import_coptic_nmt_corpus_csv,
    import_coptic_nmt_dictionary_csv,
)


def test_import_coptic_nmt_dictionary_csv_creates_sourced_entries_and_arabic_mappings(
    db_session,
    tmp_path,
) -> None:
    csv_path = tmp_path / "raw_dictionary.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["coptic", "eng", "arabic", "pos"])
        writer.writeheader()
        writer.writerow(
            {
                "coptic": "ⲡⲛⲟⲩⲧⲉ",
                "eng": "God, deity",
                "arabic": "الله",
                "pos": "noun",
            }
        )

    stats = import_coptic_nmt_dictionary_csv(db_session, csv_path)

    assert stats.entries_created == 1
    assert stats.senses_created == 1
    assert stats.mappings_created == 1

    source = db_session.query(Source).filter(Source.title == "Coptic-NMT raw dictionary").one()
    entry = db_session.query(DictionaryEntry).filter(DictionaryEntry.coptic_text == "ⲡⲛⲟⲩⲧⲉ").one()
    sense = db_session.query(ArabicSense).filter(ArabicSense.arabic_lemma == "الله").one()
    mapping = db_session.query(SenseMapping).one()

    assert source.url == "https://github.com/Coptic-NMT/coptic-translator-backend"
    assert entry.source_id == source.id
    assert entry.review_status == RecordStatus.pending
    assert entry.notes and "English gloss: God, deity" in entry.notes
    assert entry.transliteration == "pnoute"
    assert sense.definition_ar == "الله. English gloss from Coptic-NMT: God, deity"
    assert mapping.dictionary_entry_id == entry.id
    assert mapping.arabic_sense_id == sense.id


def test_import_coptic_nmt_corpus_csv_creates_parallel_segments_with_provenance(
    db_session,
    tmp_path,
) -> None:
    csv_path = tmp_path / "parsed_corpus.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "norm_group",
                "translation",
                "arabic",
                "meta::source",
                "meta::title",
                "meta::corpus",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "norm_group": "ⲁⲛⲟⲕ ⲡⲉ",
                "translation": "I am",
                "arabic": "أنا هو",
                "meta::source": "Coptic-NMT Test Source",
                "meta::title": "Example Homily",
                "meta::corpus": "example.homily",
            }
        )

    stats = import_coptic_nmt_corpus_csv(db_session, csv_path)

    assert stats.corpus_texts_created == 1
    assert stats.parallel_segments_created == 1

    source = db_session.query(Source).filter(Source.title == "Coptic-NMT Test Source").one()
    corpus = db_session.query(CorpusText).filter(CorpusText.title == "Example Homily").one()
    segment = db_session.query(ParallelSegment).filter(ParallelSegment.arabic_text == "أنا هو").one()

    assert source.url == "https://github.com/Coptic-NMT/coptic-translator-backend"
    assert corpus.source_id == source.id
    assert corpus.extra_metadata["upstream_corpus"] == "example.homily"
    assert segment.coptic_text == "ⲁⲛⲟⲕ ⲡⲉ"
    assert segment.normalized_arabic_text == "انا هو"
    assert segment.review_status == RecordStatus.pending
