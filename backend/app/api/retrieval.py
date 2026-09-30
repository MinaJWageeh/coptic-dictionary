from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.identity import User
from app.schemas.public import SimilarSegmentsRequest, SimilarSegmentsResponse
from app.services.retrieval import RetrievalService

router = APIRouter(prefix="/retrieval", tags=["retrieval"])


@router.post("/similar-segments", response_model=SimilarSegmentsResponse)
def similar_segments(
    payload: SimilarSegmentsRequest,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> SimilarSegmentsResponse:
    return SimilarSegmentsResponse(
        items=RetrievalService(db).similar_segments(
            payload.q,
            dialect_id=payload.dialect_id,
            limit=payload.limit,
        )
    )
