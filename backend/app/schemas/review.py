from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.models.enums import RecordStatus


class RejectRequest(BaseModel):
    comment: str | None = None


class CorrectRequest(BaseModel):
    corrected_text: str
    comment: str | None = None


class TranslationCandidateReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    candidate_text: str | None = None
    review_status: RecordStatus
