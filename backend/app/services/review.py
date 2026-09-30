from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import DictionaryEntry, ParallelSegment, Source, TranslationCandidate, TranslationReview
from app.models.enums import RecordStatus, SourceType
from app.services import admin as admin_service
from app.services.text import normalize_coptic


class ReviewService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def approve(self, candidate_id: int, reviewer_id: int | None) -> TranslationCandidate:
        candidate = self._candidate(candidate_id)
        candidate.review_status = RecordStatus.approved
        self._create_feedback_segment(candidate, reviewer_id)
        self.db.add(
            TranslationReview(
                translation_candidate_id=candidate.id,
                reviewer_id=reviewer_id,
                review_status=RecordStatus.approved,
            )
        )
        self.db.commit()
        self.db.refresh(candidate)
        return candidate

    def reject(
        self, candidate_id: int, reviewer_id: int | None, comment: str | None
    ) -> TranslationCandidate:
        candidate = self._candidate(candidate_id)
        candidate.review_status = RecordStatus.rejected
        self.db.add(
            TranslationReview(
                translation_candidate_id=candidate.id,
                reviewer_id=reviewer_id,
                review_status=RecordStatus.rejected,
                comment=comment,
            )
        )
        self.db.commit()
        self.db.refresh(candidate)
        return candidate

    def correct(
        self, candidate_id: int, reviewer_id: int | None, corrected_text: str, comment: str | None
    ) -> TranslationCandidate:
        candidate = self._candidate(candidate_id)
        candidate.candidate_text = corrected_text
        candidate.normalized_candidate_text = normalize_coptic(corrected_text)
        candidate.review_status = RecordStatus.approved
        self._create_feedback_segment(candidate, reviewer_id)
        self.db.add(
            TranslationReview(
                translation_candidate_id=candidate.id,
                reviewer_id=reviewer_id,
                review_status=RecordStatus.approved,
                corrected_text=corrected_text,
                comment=comment,
            )
        )
        self.db.commit()
        self.db.refresh(candidate)
        return candidate

    def _candidate(self, candidate_id: int) -> TranslationCandidate:
        candidate = self.db.get(TranslationCandidate, candidate_id)
        if candidate is None:
            raise HTTPException(status_code=404, detail="Translation candidate not found")
        return candidate

    def _create_feedback_segment(
        self, candidate: TranslationCandidate, reviewer_id: int | None
    ) -> None:
        if not (candidate.candidate_text or "").strip():
            return
        request = candidate.translation_request
        if request is None:
            return
        source_id = self._source_id_from_evidence(candidate)
        if source_id is None:
            # Never pick an arbitrary scholarly source (like Source.id == 1).
            # Look up a dedicated user/reviewer submission source, or abort if none.
            reviewer_source = (
                self.db.query(Source)
                .filter(Source.type == SourceType.user_submission)
                .first()
            )
            if reviewer_source:
                source_id = reviewer_source.id
            else:
                return
        admin_service.create_reviewed_parallel_segment(
            self.db,
            arabic_text=request.input_text,
            coptic_text=candidate.candidate_text,
            source_id=source_id,
            dialect_id=candidate.dialect_id or request.target_dialect_id,
            reviewer_id=reviewer_id,
        )

    def _source_id_from_evidence(self, candidate: TranslationCandidate) -> int | None:
        evidence = candidate.evidence or {}
        for entry_id in evidence.get("dictionary_entry_ids", []):
            entry = self.db.get(DictionaryEntry, entry_id)
            if entry is not None and entry.source_id is not None:
                return entry.source_id
        for segment_id in evidence.get("parallel_segment_ids", []):
            segment = self.db.get(ParallelSegment, segment_id)
            if segment is not None and segment.source_id is not None:
                return segment.source_id
        return None
