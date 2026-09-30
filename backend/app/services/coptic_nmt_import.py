from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session

from app.models import ArabicSense, CorpusText, Dialect, DictionaryEntry, ParallelSegment, SenseMapping, Source, User
from app.models.enums import PartOfSpeech, RecordStatus, Role, SourceType
from app.services.embedding import embed_text
from app.services.text import normalize_arabic


UPSTREAM_REPO_URL = "https://github.com/Coptic-NMT/coptic-translator-backend"

COPTIC_TO_ROMAN = {
    "ⲁ": "a",
    "ⲃ": "v",
    "ⲅ": "g",
    "ⲇ": "d",
    "ⲉ": "e",
    "ⲋ": "s",
    "ⲍ": "z",
    "ⲏ": "h",
    "ⲑ": "th",
    "ⲓ": "i",
    "ⲕ": "k",
    "ⲗ": "l",
    "ⲙ": "m",
    "ⲛ": "n",
    "ⲝ": "ks",
    "ⲟ": "o",
    "ⲡ": "p",
    "ⲣ": "r",
    "ⲥ": "s",
    "ⲧ": "t",
    "ⲩ": "u",
    "ⲫ": "f",
    "ⲭ": "kh",
    "ⲯ": "ps",
    "ⲱ": "o",
    "ϣ": "sh",
    "ϥ": "f",
    "ϧ": "kh",
    "ϩ": "h",
    "ϫ": "j",
    "ϭ": "ch",
    "ϯ": "ti",
}

POS_ALIASES = {
    "adj": PartOfSpeech.adjective,
    "adjective": PartOfSpeech.adjective,
    "adv": PartOfSpeech.adverb,
    "adverb": PartOfSpeech.adverb,
    "article": PartOfSpeech.article,
    "conj": PartOfSpeech.conjunction,
    "conjunction": PartOfSpeech.conjunction,
    "interj": PartOfSpeech.interjection,
    "interjection": PartOfSpeech.interjection,
    "n": PartOfSpeech.noun,
    "noun": PartOfSpeech.noun,
    "num": PartOfSpeech.numeral,
    "numeral": PartOfSpeech.numeral,
    "particle": PartOfSpeech.particle,
    "prep": PartOfSpeech.preposition,
    "preposition": PartOfSpeech.preposition,
    "pron": PartOfSpeech.pronoun,
    "pronoun": PartOfSpeech.pronoun,
    "v": PartOfSpeech.verb,
    "verb": PartOfSpeech.verb,
}


def romanize_coptic(text: str) -> str:
    return "".join(COPTIC_TO_ROMAN.get(char.lower(), char.lower()) for char in text)


def _clean(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.lower() in {"nan", "none", "null", "...", "…"} else text


def _part_of_speech(value: str) -> PartOfSpeech:
    return POS_ALIASES.get(_clean(value).lower(), PartOfSpeech.other)


def _dialect(db: Session, code: str) -> Dialect:
    dialect = db.query(Dialect).filter(Dialect.code == code).first()
    if dialect:
        return dialect
    dialect = Dialect(code=code, name=code.replace("_", " ").title(), is_active=True)
    db.add(dialect)
    db.flush()
    return dialect


def _admin_id(db: Session) -> int | None:
    admin = db.query(User).filter(User.role == Role.admin).order_by(User.id).first()
    return admin.id if admin else None


def _source(
    db: Session,
    *,
    title: str,
    source_type: SourceType,
    admin_id: int | None,
    notes: str,
    author: str = "Coptic-NMT",
) -> tuple[Source, bool]:
    source = (
        db.query(Source)
        .filter(Source.title == title, Source.url == UPSTREAM_REPO_URL)
        .first()
    )
    if source:
        source.author = author
        source.type = source_type
        source.notes = notes
        return source, False
    source = Source(
        title=title,
        author=author,
        type=source_type,
        url=UPSTREAM_REPO_URL,
        notes=notes,
        created_by=admin_id,
    )
    db.add(source)
    db.flush()
    return source, True


def _dictionary_entry(
    db: Session,
    *,
    coptic_text: str,
    dialect_id: int,
    source_id: int,
    part_of_speech: PartOfSpeech,
    english_gloss: str,
    admin_id: int | None,
) -> tuple[DictionaryEntry, bool]:
    entry = (
        db.query(DictionaryEntry)
        .filter(
            DictionaryEntry.normalized_coptic_text == coptic_text,
            DictionaryEntry.dialect_id == dialect_id,
            DictionaryEntry.part_of_speech == part_of_speech,
            DictionaryEntry.source_id == source_id,
        )
        .first()
    )
    notes = (
        "Imported from Coptic-NMT raw_dictionary.csv. "
        "English gloss preserved for reviewer validation."
    )
    if english_gloss:
        notes = f"{notes} English gloss: {english_gloss}"
    values = {
        "coptic_text": coptic_text,
        "transliteration": romanize_coptic(coptic_text),
        "notes": notes,
        "review_status": RecordStatus.pending,
        "example_embedding": embed_text(english_gloss or coptic_text),
    }
    if entry:
        for field, value in values.items():
            setattr(entry, field, value)
        return entry, False
    entry = DictionaryEntry(
        normalized_coptic_text=coptic_text,
        dialect_id=dialect_id,
        source_id=source_id,
        part_of_speech=part_of_speech,
        created_by=admin_id,
        **values,
    )
    db.add(entry)
    db.flush()
    return entry, True


def _arabic_sense(
    db: Session,
    *,
    arabic: str,
    english_gloss: str,
    source_id: int,
    part_of_speech: PartOfSpeech,
    admin_id: int | None,
) -> tuple[ArabicSense, bool]:
    normalized = normalize_arabic(arabic)
    definition = arabic
    if english_gloss:
        definition = f"{arabic}. English gloss from Coptic-NMT: {english_gloss}"
    sense = (
        db.query(ArabicSense)
        .filter(
            ArabicSense.normalized_arabic_lemma == normalized,
            ArabicSense.definition_ar == definition,
        )
        .first()
    )
    values = {
        "arabic_lemma": arabic,
        "part_of_speech": part_of_speech,
        "source_id": source_id,
        "review_status": RecordStatus.pending,
        "meaning_embedding": embed_text(definition),
    }
    if sense:
        for field, value in values.items():
            setattr(sense, field, value)
        return sense, False
    sense = ArabicSense(
        normalized_arabic_lemma=normalized,
        sense_key=f"coptic-nmt:{normalized}:{part_of_speech.value}",
        definition_ar=definition,
        created_by=admin_id,
        **values,
    )
    db.add(sense)
    db.flush()
    return sense, True


def _sense_mapping(
    db: Session,
    *,
    sense_id: int,
    entry_id: int,
    admin_id: int | None,
) -> tuple[SenseMapping, bool]:
    mapping = (
        db.query(SenseMapping)
        .filter(
            SenseMapping.arabic_sense_id == sense_id,
            SenseMapping.dictionary_entry_id == entry_id,
        )
        .first()
    )
    values = {
        "confidence": 0.45,
        "usage_note": "Imported from Coptic-NMT data; needs human review before approval.",
        "review_status": RecordStatus.pending,
        "is_primary": True,
    }
    if mapping:
        for field, value in values.items():
            setattr(mapping, field, value)
        return mapping, False
    mapping = SenseMapping(
        arabic_sense_id=sense_id,
        dictionary_entry_id=entry_id,
        created_by=admin_id,
        **values,
    )
    db.add(mapping)
    db.flush()
    return mapping, True

@dataclass(frozen=True)
class DictionaryImportStats:
    entries_created: int = 0
    entries_updated: int = 0
    senses_created: int = 0
    senses_updated: int = 0
    mappings_created: int = 0
    mappings_updated: int = 0
    rows_skipped: int = 0


@dataclass(frozen=True)
class CorpusImportStats:
    corpus_texts_created: int = 0
    corpus_texts_updated: int = 0
    parallel_segments_created: int = 0
    parallel_segments_updated: int = 0
    rows_skipped: int = 0


def import_coptic_nmt_dictionary_csv(
    db: Session,
    csv_path: str | Path,
    *,
    dialect_code: str = "sahidic",
) -> DictionaryImportStats:
    dialect = _dialect(db, dialect_code)
    admin_id = _admin_id(db)
    source, _ = _source(
        db,
        title="Coptic-NMT raw dictionary",
        source_type=SourceType.dictionary,
        admin_id=admin_id,
        notes=(
            "Imported from dictionary_translator.py expected file "
            "datasets/raw_dictionary.csv in Coptic-NMT/coptic-translator-backend."
        ),
    )

    entries_created = entries_updated = 0
    senses_created = senses_updated = 0
    mappings_created = mappings_updated = 0
    rows_skipped = 0

    with Path(csv_path).open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            coptic_text = _clean(row.get("coptic") or row.get("norm") or row.get("norm_group"))
            if not coptic_text:
                rows_skipped += 1
                continue
            english_gloss = _clean(row.get("eng") or row.get("translation"))
            part_of_speech = _part_of_speech(_clean(row.get("pos") or row.get("func")))

            entry, created = _dictionary_entry(
                db,
                coptic_text=coptic_text,
                dialect_id=dialect.id,
                source_id=source.id,
                part_of_speech=part_of_speech,
                english_gloss=english_gloss,
                admin_id=admin_id,
            )
            if created:
                entries_created += 1
            else:
                entries_updated += 1

            arabic = _clean(row.get("arabic"))
            if arabic:
                sense, created = _arabic_sense(
                    db,
                    arabic=arabic,
                    english_gloss=english_gloss,
                    source_id=source.id,
                    part_of_speech=part_of_speech,
                    admin_id=admin_id,
                )
                if created:
                    senses_created += 1
                else:
                    senses_updated += 1
                _, created = _sense_mapping(
                    db,
                    sense_id=sense.id,
                    entry_id=entry.id,
                    admin_id=admin_id,
                )
                if created:
                    mappings_created += 1
                else:
                    mappings_updated += 1

    db.commit()
    return DictionaryImportStats(
        entries_created=entries_created,
        entries_updated=entries_updated,
        senses_created=senses_created,
        senses_updated=senses_updated,
        mappings_created=mappings_created,
        mappings_updated=mappings_updated,
        rows_skipped=rows_skipped,
    )


def _corpus_text(
    db: Session,
    *,
    title: str,
    source_id: int,
    dialect_id: int,
    upstream_corpus: str,
    admin_id: int | None,
) -> tuple[CorpusText, bool]:
    corpus = (
        db.query(CorpusText)
        .filter(
            CorpusText.title == title,
            CorpusText.source_id == source_id,
            CorpusText.dialect_id == dialect_id,
        )
        .first()
    )
    metadata = {
        "imported_from": UPSTREAM_REPO_URL,
        "upstream_corpus": upstream_corpus,
    }
    if corpus:
        corpus.language = "parallel"
        corpus.review_status = RecordStatus.pending
        corpus.extra_metadata = metadata
        return corpus, False
    corpus = CorpusText(
        title=title,
        source_id=source_id,
        dialect_id=dialect_id,
        language="parallel",
        review_status=RecordStatus.pending,
        extra_metadata=metadata,
        created_by=admin_id,
    )
    db.add(corpus)
    db.flush()
    return corpus, True


def _parallel_segment(
    db: Session,
    *,
    corpus_id: int,
    source_id: int,
    dialect_id: int,
    arabic_text: str,
    coptic_text: str,
    english_translation: str,
    admin_id: int | None,
) -> tuple[ParallelSegment, bool]:
    segment = (
        db.query(ParallelSegment)
        .filter(
            ParallelSegment.arabic_text == arabic_text,
            ParallelSegment.dialect_id == dialect_id,
            ParallelSegment.source_id == source_id,
        )
        .first()
    )
    values = {
        "corpus_text_id": corpus_id,
        "coptic_text": coptic_text,
        "normalized_arabic_text": normalize_arabic(arabic_text),
        "normalized_coptic_text": coptic_text,
        "alignment_score": 0.5,
        "arabic_embedding": embed_text(arabic_text),
        "coptic_embedding": embed_text(coptic_text),
        "sentence_embedding": embed_text(arabic_text),
        "review_status": RecordStatus.pending,
    }
    if english_translation:
        values["alignment_score"] = 0.45
    if segment:
        for field, value in values.items():
            setattr(segment, field, value)
        return segment, False
    segment = ParallelSegment(
        source_id=source_id,
        dialect_id=dialect_id,
        arabic_text=arabic_text,
        created_by=admin_id,
        **values,
    )
    db.add(segment)
    db.flush()
    return segment, True


def import_coptic_nmt_corpus_csv(
    db: Session,
    csv_path: str | Path,
    *,
    dialect_code: str = "sahidic",
) -> CorpusImportStats:
    dialect = _dialect(db, dialect_code)
    admin_id = _admin_id(db)

    corpus_texts_created = corpus_texts_updated = 0
    parallel_segments_created = parallel_segments_updated = 0
    rows_skipped = 0

    with Path(csv_path).open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            coptic_text = _clean(row.get("norm_group") or row.get("norm"))
            arabic_text = _clean(row.get("arabic"))
            if not coptic_text or not arabic_text:
                rows_skipped += 1
                continue

            source_title = _clean(row.get("meta::source")) or "Coptic-NMT corpus export"
            corpus_title = _clean(row.get("meta::title")) or _clean(row.get("meta::corpus")) or source_title
            upstream_corpus = _clean(row.get("meta::corpus")) or corpus_title
            english_translation = _clean(row.get("translation") or row.get("meta::translation"))

            source, _ = _source(
                db,
                title=source_title,
                source_type=SourceType.corpus,
                admin_id=admin_id,
                notes="Imported from parsed Coptic-NMT corpus CSV metadata.",
            )
            corpus, created = _corpus_text(
                db,
                title=corpus_title,
                source_id=source.id,
                dialect_id=dialect.id,
                upstream_corpus=upstream_corpus,
                admin_id=admin_id,
            )
            if created:
                corpus_texts_created += 1
            else:
                corpus_texts_updated += 1

            _, created = _parallel_segment(
                db,
                corpus_id=corpus.id,
                source_id=source.id,
                dialect_id=dialect.id,
                arabic_text=arabic_text,
                coptic_text=coptic_text,
                english_translation=english_translation,
                admin_id=admin_id,
            )
            if created:
                parallel_segments_created += 1
            else:
                parallel_segments_updated += 1

    db.commit()
    return CorpusImportStats(
        corpus_texts_created=corpus_texts_created,
        corpus_texts_updated=corpus_texts_updated,
        parallel_segments_created=parallel_segments_created,
        parallel_segments_updated=parallel_segments_updated,
        rows_skipped=rows_skipped,
    )
