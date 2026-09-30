from __future__ import annotations

import csv
import io
import json
from difflib import SequenceMatcher
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import TranslationCandidate, TranslationRequest, TranslationReview
from app.models.enums import RecordStatus


class EvaluationDatasetService:
    """Service for compiling, exporting, and analyzing reviewer feedback

    into benchmark evaluation datasets and training data for Coptic NLP models.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_evaluation_items(
        self,
        status: RecordStatus | None = None,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        query = (
            self.db.query(TranslationReview, TranslationCandidate, TranslationRequest)
            .join(
                TranslationCandidate,
                TranslationReview.translation_candidate_id == TranslationCandidate.id,
            )
            .join(
                TranslationRequest,
                TranslationCandidate.translation_request_id == TranslationRequest.id,
            )
        )

        if status is not None:
            query = query.filter(TranslationReview.review_status == status)

        query = query.order_by(TranslationReview.id.desc()).limit(limit)
        results = query.all()

        items: list[dict[str, Any]] = []
        for review, candidate, request in results:
            predicted = (candidate.candidate_text or "").strip()
            target = (review.corrected_text or candidate.candidate_text or "").strip()
            was_corrected = bool(
                review.corrected_text
                and review.corrected_text.strip() != predicted
            )
            similarity = SequenceMatcher(None, predicted, target).ratio() if predicted and target else 0.0

            items.append({
                "review_id": review.id,
                "candidate_id": candidate.id,
                "request_id": request.id,
                "input_arabic": request.input_text,
                "normalized_arabic": request.normalized_input_text,
                "predicted_coptic": predicted,
                "target_coptic": target,
                "review_status": review.review_status.value if hasattr(review.review_status, "value") else str(review.review_status),
                "was_corrected": was_corrected,
                "reviewer_id": review.reviewer_id,
                "reviewer_comment": review.comment,
                "rating": review.rating,
                "model_confidence": round(candidate.confidence, 4) if candidate.confidence is not None else None,
                "similarity_to_target": round(similarity, 4),
                "dialect_id": candidate.dialect_id or request.target_dialect_id,
                "created_at": review.created_at.isoformat() if hasattr(review, "created_at") and review.created_at else None,
            })
        return items

    def export_jsonl(
        self,
        status: RecordStatus | None = None,
        limit: int = 1000,
    ) -> str:
        """Export dataset as JSON-Lines (NDJSON), standard for LLM / NMT training."""
        items = self.get_evaluation_items(status=status, limit=limit)
        lines = []
        for item in items:
            entry = {
                "source": item["input_arabic"],
                "target": item["target_coptic"],
                "prediction": item["predicted_coptic"],
                "status": item["review_status"],
                "was_corrected": item["was_corrected"],
                "similarity": item["similarity_to_target"],
                "metadata": {
                    "review_id": item["review_id"],
                    "candidate_id": item["candidate_id"],
                    "dialect_id": item["dialect_id"],
                    "confidence": item["model_confidence"],
                    "comment": item["reviewer_comment"],
                },
            }
            lines.append(json.dumps(entry, ensure_ascii=False))
        return "\n".join(lines)

    def export_csv(
        self,
        status: RecordStatus | None = None,
        limit: int = 1000,
    ) -> str:
        """Export dataset as CSV."""
        items = self.get_evaluation_items(status=status, limit=limit)
        output = io.StringIO()
        fieldnames = [
            "review_id",
            "input_arabic",
            "predicted_coptic",
            "target_coptic",
            "review_status",
            "was_corrected",
            "model_confidence",
            "similarity_to_target",
            "reviewer_comment",
            "created_at",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for item in items:
            writer.writerow(item)
        return output.getvalue()

    def compute_metrics(self) -> dict[str, Any]:
        """Compute holistic accuracy, approval, correction, and similarity statistics."""
        reviews = self.db.query(TranslationReview).all()
        total = len(reviews)
        if total == 0:
            return {
                "total_reviews": 0,
                "approved_count": 0,
                "corrected_count": 0,
                "rejected_count": 0,
                "approval_rate": 0.0,
                "correction_rate": 0.0,
                "rejection_rate": 0.0,
                "average_model_confidence": 0.0,
                "average_target_similarity": 0.0,
            }

        approved_count = 0
        corrected_count = 0
        rejected_count = 0
        confidences: list[float] = []
        similarities: list[float] = []

        for r in reviews:
            st = r.review_status.value if hasattr(r.review_status, "value") else str(r.review_status)
            cand = r.translation_candidate
            if cand and cand.confidence is not None:
                confidences.append(cand.confidence)

            if st == "approved":
                if r.corrected_text and cand and r.corrected_text.strip() != (cand.candidate_text or "").strip():
                    corrected_count += 1
                else:
                    approved_count += 1
            elif st == "rejected":
                rejected_count += 1

            if cand and (cand.candidate_text or r.corrected_text):
                pred = (cand.candidate_text or "").strip()
                targ = (r.corrected_text or cand.candidate_text or "").strip()
                similarities.append(SequenceMatcher(None, pred, targ).ratio())

        return {
            "total_reviews": total,
            "approved_count": approved_count,
            "corrected_count": corrected_count,
            "rejected_count": rejected_count,
            "approval_rate": round(approved_count / total * 100.0, 2),
            "correction_rate": round(corrected_count / total * 100.0, 2),
            "rejection_rate": round(rejected_count / total * 100.0, 2),
            "average_model_confidence": round(sum(confidences) / len(confidences), 4) if confidences else 0.0,
            "average_target_similarity": round(sum(similarities) / len(similarities), 4) if similarities else 0.0,
        }
