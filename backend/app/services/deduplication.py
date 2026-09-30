from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import ArabicSense, DictionaryEntry, SenseMapping
from app.models.enums import PartOfSpeech, RecordStatus
from app.services.embedding import embed_text
from app.services.text import normalize_arabic, normalize_coptic

# Pattern to strip Coptic combining diacritics / jinkim for fuzzy phonetic deduplication
_COPTIC_COMBINING_MARKS = re.compile(
    r"[\u0300-\u036f\u0483-\u0489\u1dc0-\u1dff\u20d0-\u20ff\ufe20-\ufe2f\u0307\u0308]"
)


def strip_coptic_diacritics(text: str) -> str:
    """Strip combining diacritical marks (e.g. jinkim, spiritus) from Coptic text."""
    if not text:
        return ""
    norm = normalize_coptic(text)
    return _COPTIC_COMBINING_MARKS.sub("", norm)


@dataclass
class DeduplicationResult:
    entry: DictionaryEntry
    is_created: bool
    is_merged: bool


@dataclass
class SenseDeduplicationResult:
    sense: ArabicSense
    is_created: bool
    is_merged: bool


@dataclass
class MappingDeduplicationResult:
    mapping: SenseMapping
    is_created: bool
    is_updated: bool


class DeduplicationService:
    def __init__(self, db: Session):
        self.db = db

    def find_or_create_coptic_entry(
        self,
        *,
        coptic_text: str,
        dialect_id: int,
        part_of_speech: PartOfSpeech,
        source_id: int,
        transliteration: str | None = None,
        notes: str | None = None,
        example_sentence: str | None = None,
        review_status: RecordStatus = RecordStatus.approved,
        admin_id: int | None = None,
    ) -> DeduplicationResult:
        """
        Deduplicates Coptic entries by (normalized_coptic_text, dialect_id, part_of_speech).
        If an entry already exists (even under a different source), merges metadata rather
        than creating a redundant duplicate headword.
        """
        norm_coptic = normalize_coptic(coptic_text)

        # 1. Exact match by normalized coptic, dialect, and POS
        existing = (
            self.db.query(DictionaryEntry)
            .filter(
                DictionaryEntry.normalized_coptic_text == norm_coptic,
                DictionaryEntry.dialect_id == dialect_id,
                DictionaryEntry.part_of_speech == part_of_speech,
            )
            .first()
        )

        if existing:
            is_merged = False
            # Enhance existing entry if new fields provide richer data
            if notes and notes not in (existing.notes or ""):
                existing.notes = f"{existing.notes}\n{notes}".strip() if existing.notes else notes
                is_merged = True
            if transliteration and not existing.transliteration:
                existing.transliteration = transliteration
                is_merged = True
            if example_sentence and not existing.example_sentence:
                existing.example_sentence = example_sentence
                existing.example_embedding = embed_text(example_sentence)
                is_merged = True
            if existing.review_status != RecordStatus.approved and review_status == RecordStatus.approved:
                existing.review_status = RecordStatus.approved
                is_merged = True
            self.db.flush()
            return DeduplicationResult(entry=existing, is_created=False, is_merged=is_merged)

        # 2. Create new entry
        new_entry = DictionaryEntry(
            coptic_text=coptic_text,
            normalized_coptic_text=norm_coptic,
            transliteration=transliteration or norm_coptic,
            dialect_id=dialect_id,
            source_id=source_id,
            part_of_speech=part_of_speech,
            notes=notes,
            example_sentence=example_sentence,
            example_embedding=embed_text(example_sentence or coptic_text),
            review_status=review_status,
            created_by=admin_id,
        )
        self.db.add(new_entry)
        self.db.flush()
        return DeduplicationResult(entry=new_entry, is_created=True, is_merged=False)

    def find_or_create_arabic_sense(
        self,
        *,
        arabic_lemma: str,
        definition_ar: str,
        part_of_speech: PartOfSpeech | None = None,
        source_id: int | None = None,
        example_ar: str | None = None,
        review_status: RecordStatus = RecordStatus.approved,
        admin_id: int | None = None,
    ) -> SenseDeduplicationResult:
        """
        Deduplicates Arabic senses by normalized lemma and part of speech.
        Reuses existing lemma sense instead of creating duplicate fragmented records.
        """
        norm_lemma = normalize_arabic(arabic_lemma)

        query = self.db.query(ArabicSense).filter(
            ArabicSense.normalized_arabic_lemma == norm_lemma
        )
        if part_of_speech:
            query = query.filter(ArabicSense.part_of_speech == part_of_speech)

        existing = query.first()
        if existing:
            is_merged = False
            # If the new definition is richer or not present, merge
            if definition_ar and definition_ar not in existing.definition_ar:
                existing.definition_ar = f"{existing.definition_ar}; {definition_ar}"
                existing.meaning_embedding = embed_text(existing.definition_ar)
                is_merged = True
            if example_ar and not existing.example_ar:
                existing.example_ar = example_ar
                existing.example_embedding = embed_text(example_ar)
                is_merged = True
            if existing.review_status != RecordStatus.approved and review_status == RecordStatus.approved:
                existing.review_status = RecordStatus.approved
                is_merged = True
            self.db.flush()
            return SenseDeduplicationResult(sense=existing, is_created=False, is_merged=is_merged)

        # Create new sense
        new_sense = ArabicSense(
            arabic_lemma=arabic_lemma,
            normalized_arabic_lemma=norm_lemma,
            sense_key=f"sense:{norm_lemma}:{part_of_speech.value if part_of_speech else 'gen'}",
            definition_ar=definition_ar or arabic_lemma,
            part_of_speech=part_of_speech,
            example_ar=example_ar,
            meaning_embedding=embed_text(definition_ar or arabic_lemma),
            example_embedding=embed_text(example_ar) if example_ar else None,
            source_id=source_id,
            review_status=review_status,
            created_by=admin_id,
        )
        self.db.add(new_sense)
        self.db.flush()
        return SenseDeduplicationResult(sense=new_sense, is_created=True, is_merged=False)

    def find_or_create_sense_mapping(
        self,
        *,
        arabic_sense_id: int,
        dictionary_entry_id: int,
        confidence: float = 0.9,
        usage_note: str | None = None,
        is_primary: bool = False,
        review_status: RecordStatus = RecordStatus.approved,
        admin_id: int | None = None,
    ) -> MappingDeduplicationResult:
        """
        Deduplicates mappings between an Arabic sense and a Coptic dictionary entry.
        Prevents duplicate foreign key pairs and upgrades confidence score if higher.
        """
        existing = (
            self.db.query(SenseMapping)
            .filter(
                SenseMapping.arabic_sense_id == arabic_sense_id,
                SenseMapping.dictionary_entry_id == dictionary_entry_id,
            )
            .first()
        )

        if existing:
            is_updated = False
            if confidence > existing.confidence:
                existing.confidence = confidence
                is_updated = True
            if is_primary and not existing.is_primary:
                existing.is_primary = True
                is_updated = True
            if usage_note and usage_note not in (existing.usage_note or ""):
                existing.usage_note = (
                    f"{existing.usage_note}\n{usage_note}".strip()
                    if existing.usage_note
                    else usage_note
                )
                is_updated = True
            if existing.review_status != RecordStatus.approved and review_status == RecordStatus.approved:
                existing.review_status = RecordStatus.approved
                is_updated = True
            self.db.flush()
            return MappingDeduplicationResult(mapping=existing, is_created=False, is_updated=is_updated)

        new_mapping = SenseMapping(
            arabic_sense_id=arabic_sense_id,
            dictionary_entry_id=dictionary_entry_id,
            confidence=confidence,
            usage_note=usage_note,
            is_primary=is_primary,
            review_status=review_status,
            created_by=admin_id,
        )
        self.db.add(new_mapping)
        self.db.flush()
        return MappingDeduplicationResult(mapping=new_mapping, is_created=True, is_updated=False)

    def audit_duplicates(self) -> dict[str, Any]:
        """
        Audits database to detect duplicate or near-duplicate entries and senses.
        """
        # Duplicate Coptic entries by normalized text and dialect
        dup_entries_query = (
            self.db.query(
                DictionaryEntry.normalized_coptic_text,
                DictionaryEntry.dialect_id,
                DictionaryEntry.part_of_speech,
                func.count(DictionaryEntry.id).label("count"),
            )
            .group_by(
                DictionaryEntry.normalized_coptic_text,
                DictionaryEntry.dialect_id,
                DictionaryEntry.part_of_speech,
            )
            .having(func.count(DictionaryEntry.id) > 1)
            .all()
        )

        # Duplicate Arabic senses by normalized lemma and part of speech
        dup_senses_query = (
            self.db.query(
                ArabicSense.normalized_arabic_lemma,
                ArabicSense.part_of_speech,
                func.count(ArabicSense.id).label("count"),
            )
            .group_by(ArabicSense.normalized_arabic_lemma, ArabicSense.part_of_speech)
            .having(func.count(ArabicSense.id) > 1)
            .all()
        )

        return {
            "duplicate_coptic_entries_count": len(dup_entries_query),
            "duplicate_arabic_senses_count": len(dup_senses_query),
            "duplicate_coptic_entries_sample": [
                {
                    "coptic": item[0],
                    "dialect_id": item[1],
                    "pos": item[2].value if hasattr(item[2], "value") else str(item[2]),
                    "occurrences": item[3],
                }
                for item in dup_entries_query[:20]
            ],
            "duplicate_arabic_senses_sample": [
                {
                    "arabic_lemma": item[0],
                    "pos": item[1].value if hasattr(item[1], "value") else str(item[1]),
                    "occurrences": item[2],
                }
                for item in dup_senses_query[:20]
            ],
        }

    def merge_duplicate_arabic_senses(self) -> int:
        """
        Merges redundant Arabic senses that share the exact same normalized lemma and POS.
        Points all mappings to the lowest ID (canonical) sense and deletes the duplicates.
        Returns the number of redundant senses removed.
        """
        dup_groups = (
            self.db.query(
                ArabicSense.normalized_arabic_lemma,
                ArabicSense.part_of_speech,
                func.min(ArabicSense.id).label("canonical_id"),
                func.count(ArabicSense.id).label("count"),
            )
            .group_by(ArabicSense.normalized_arabic_lemma, ArabicSense.part_of_speech)
            .having(func.count(ArabicSense.id) > 1)
            .all()
        )

        removed_count = 0
        for group in dup_groups:
            canonical_id = group.canonical_id
            norm_lemma = group.normalized_arabic_lemma
            pos = group.part_of_speech

            redundant_senses = (
                self.db.query(ArabicSense)
                .filter(
                    ArabicSense.normalized_arabic_lemma == norm_lemma,
                    ArabicSense.part_of_speech == pos,
                    ArabicSense.id != canonical_id,
                )
                .all()
            )

            for red in redundant_senses:
                # Re-point or merge mappings
                for mapping in red.mappings:
                    # Check if canonical already has mapping to this entry
                    existing_m = (
                        self.db.query(SenseMapping)
                        .filter(
                            SenseMapping.arabic_sense_id == canonical_id,
                            SenseMapping.dictionary_entry_id == mapping.dictionary_entry_id,
                        )
                        .first()
                    )
                    if existing_m:
                        existing_m.confidence = max(existing_m.confidence, mapping.confidence)
                        self.db.delete(mapping)
                    else:
                        mapping.arabic_sense_id = canonical_id

                self.db.delete(red)
                removed_count += 1

        self.db.commit()
        return removed_count
