from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import ArabicSense, DictionaryEntry, SenseMapping
from app.models.enums import RecordStatus
from app.schemas.admin import DictionaryEntryCreate, DictionaryEntryUpdate
from app.services.embedding import embed_text
from app.services.text import normalize_arabic


class DictionaryService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def search(self, query: str, dialect_id: int | None = None) -> list[DictionaryEntry]:
        normalized = normalize_arabic(query)
        statement = (
            self.db.query(DictionaryEntry)
            .outerjoin(SenseMapping)
            .outerjoin(ArabicSense)
            .filter(DictionaryEntry.review_status == RecordStatus.approved)
            .filter(
                or_(
                    DictionaryEntry.coptic_text.contains(query),
                    DictionaryEntry.normalized_coptic_text.contains(query),
                    DictionaryEntry.transliteration.contains(query),
                    ArabicSense.normalized_arabic_lemma == normalized,
                )
            )
        )
        if dialect_id is not None:
            statement = statement.filter(DictionaryEntry.dialect_id == dialect_id)
        return statement.order_by(DictionaryEntry.id).all()

    def browse(
        self,
        q: str | None = None,
        letter: str | None = None,
        dialect_id: int | None = None,
        part_of_speech: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict], int]:
        statement = (
            self.db.query(DictionaryEntry)
            .filter(DictionaryEntry.review_status == RecordStatus.approved)
        )
        if dialect_id:
            statement = statement.filter(DictionaryEntry.dialect_id == dialect_id)
        if part_of_speech:
            from app.models.enums import PartOfSpeech
            try:
                pos_enum = PartOfSpeech(part_of_speech)
                statement = statement.filter(DictionaryEntry.part_of_speech == pos_enum)
            except ValueError:
                pass
        if letter:
            clean_letter = letter.strip()
            statement = statement.filter(
                or_(
                    DictionaryEntry.coptic_text.startswith(clean_letter),
                    DictionaryEntry.normalized_coptic_text.startswith(clean_letter),
                )
            )
        if q:
            norm_q = normalize_arabic(q)
            statement = (
                statement.outerjoin(SenseMapping)
                .outerjoin(ArabicSense)
                .filter(
                    or_(
                        DictionaryEntry.coptic_text.contains(q),
                        DictionaryEntry.normalized_coptic_text.contains(q),
                        DictionaryEntry.transliteration.contains(q),
                        ArabicSense.normalized_arabic_lemma.contains(norm_q),
                        ArabicSense.definition_ar.contains(norm_q),
                    )
                )
            )

        statement = statement.distinct()
        total = statement.count()
        offset = max(0, (page - 1) * page_size)
        entries = (
            statement.order_by(DictionaryEntry.coptic_text)
            .offset(offset)
            .limit(page_size)
            .all()
        )

        results = []
        for entry in entries:
            meanings = [
                m.arabic_sense.definition_ar or m.arabic_sense.arabic_lemma
                for m in entry.mappings
                if m.arabic_sense
            ]
            source_title = entry.source.title if entry.source else None
            results.append({
                "id": entry.id,
                "coptic_text": entry.coptic_text,
                "normalized_coptic_text": entry.normalized_coptic_text,
                "transliteration": entry.transliteration,
                "dialect_id": entry.dialect_id,
                "source_id": entry.source_id,
                "source_title": source_title,
                "part_of_speech": entry.part_of_speech,
                "review_status": entry.review_status,
                "notes": entry.notes,
                "arabic_meanings": meanings,
            })
        return results, total

    def get_public_entry(self, entry_id: int) -> DictionaryEntry:
        entry = (
            self.db.query(DictionaryEntry)
            .filter(DictionaryEntry.id == entry_id, DictionaryEntry.review_status == RecordStatus.approved)
            .first()
        )
        if entry is None:
            raise HTTPException(status_code=404, detail="Dictionary entry not found")
        return entry

    def create_entry(self, payload: DictionaryEntryCreate, user_id: int | None) -> DictionaryEntry:
        normalized_coptic = payload.normalized_coptic_text or payload.coptic_text
        entry = DictionaryEntry(
            coptic_text=payload.coptic_text,
            normalized_coptic_text=normalized_coptic,
            transliteration=payload.transliteration,
            dialect_id=payload.dialect_id,
            source_id=payload.source_id,
            part_of_speech=payload.part_of_speech,
            gender=payload.gender,
            grammatical_number=payload.grammatical_number,
            root=payload.root,
            example_sentence=payload.example_sentence,
            notes=payload.notes,
            review_status=payload.review_status,
            created_by=user_id,
        )
        self.db.add(entry)
        self.db.flush()
        if payload.arabic_lemma and payload.arabic_definition:
            sense = ArabicSense(
                arabic_lemma=payload.arabic_lemma,
                normalized_arabic_lemma=normalize_arabic(payload.arabic_lemma),
                definition_ar=payload.arabic_definition,
                part_of_speech=payload.part_of_speech,
                meaning_embedding=embed_text(payload.arabic_definition),
                review_status=payload.review_status,
                created_by=user_id,
            )
            self.db.add(sense)
            self.db.flush()
            self.db.add(
                SenseMapping(
                    arabic_sense_id=sense.id,
                    dictionary_entry_id=entry.id,
                    confidence=1.0,
                    is_primary=True,
                    review_status=payload.review_status,
                    created_by=user_id,
                )
            )
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def update_entry(self, entry_id: int, payload: DictionaryEntryUpdate) -> DictionaryEntry:
        entry = self.db.get(DictionaryEntry, entry_id)
        if entry is None:
            raise HTTPException(status_code=404, detail="Dictionary entry not found")
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(entry, field, value)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def delete_entry(self, entry_id: int) -> None:
        entry = self.db.get(DictionaryEntry, entry_id)
        if entry is None:
            raise HTTPException(status_code=404, detail="Dictionary entry not found")
        self.db.delete(entry)
        self.db.commit()
