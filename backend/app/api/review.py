from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_roles
from app.models import TranslationCandidate, TranslationRequest
from app.models.enums import Role
from app.models.identity import User
from app.schemas.admin import TranslationCandidateRead, TranslationRequestRead
from app.schemas.review import CorrectRequest, RejectRequest, TranslationCandidateReviewRead
from app.services.review import ReviewService

router = APIRouter(prefix="/review", tags=["review"])


reviewer_dependency = require_roles(Role.reviewer, Role.admin)


@router.get("/translation-requests", response_model=list[TranslationRequestRead])
def list_review_translation_requests(
    db: Session = Depends(get_db),
    _: User = Depends(reviewer_dependency),
):
    return db.query(TranslationRequest).order_by(TranslationRequest.created_at.desc()).all()


@router.get("/translation-candidates", response_model=list[TranslationCandidateRead])
def list_review_translation_candidates(
    db: Session = Depends(get_db),
    _: User = Depends(reviewer_dependency),
):
    return db.query(TranslationCandidate).order_by(TranslationCandidate.created_at.desc()).all()


@router.post("/translation/{candidate_id}/approve", response_model=TranslationCandidateReviewRead)
def approve_translation(
    candidate_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(reviewer_dependency),
):
    return ReviewService(db).approve(candidate_id, user.id)


@router.post("/translation/{candidate_id}/reject", response_model=TranslationCandidateReviewRead)
def reject_translation(
    candidate_id: int,
    payload: RejectRequest,
    db: Session = Depends(get_db),
    user: User = Depends(reviewer_dependency),
):
    return ReviewService(db).reject(candidate_id, user.id, payload.comment)


@router.post("/translation/{candidate_id}/correct", response_model=TranslationCandidateReviewRead)
def correct_translation(
    candidate_id: int,
    payload: CorrectRequest,
    db: Session = Depends(get_db),
    user: User = Depends(reviewer_dependency),
):
    return ReviewService(db).correct(candidate_id, user.id, payload.corrected_text, payload.comment)
