from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_optional_current_user
from app.models import Dialect, DictionaryEntry, ParallelSegment, Source
from app.models.enums import RecordStatus
from app.models.identity import User
from app.schemas.public import (
    DialectRead,
    DictionaryBrowseResponse,
    DictionaryEntryRead,
    ParallelSegmentRead,
    SourceCitationRead,
    SourceDetailRead,
    TranslateRequest,
    TranslateResponse,
)
from app.services.dictionary import DictionaryService
from app.services.quota import QuotaService
from app.services.rate_limit import translate_rate_limiter
from app.services.retrieval import RetrievalService
from app.services.text import normalize_arabic
from app.services.translation import TranslationService

router = APIRouter(tags=["public"])


@router.post("/translate", response_model=TranslateResponse, dependencies=[Depends(translate_rate_limiter)])
def translate(
    payload: TranslateRequest,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_current_user),
) -> TranslateResponse:
    res = TranslationService(db).translate(
        payload.text,
        user_id=user.id if user else None,
        target_dialect_id=payload.target_dialect_id or (user.preferred_dialect_id if user else None),
        context=payload.context,
    )
    # Attach quota info to response
    quota = QuotaService(db).check_quota(user)
    res.quota = quota
    return res


@router.get("/dictionary/browse", response_model=DictionaryBrowseResponse)
def browse_dictionary(
    q: str | None = None,
    letter: str | None = None,
    dialect_id: int | None = None,
    part_of_speech: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
):
    items, total = DictionaryService(db).browse(
        q=q,
        letter=letter,
        dialect_id=dialect_id,
        part_of_speech=part_of_speech,
        page=page,
        page_size=page_size,
    )
    total_pages = max(1, (total + page_size - 1) // page_size) if page_size else 1
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
    }


@router.get("/dictionary/search", response_model=list[DictionaryEntryRead])
def search_dictionary(
    q: str,
    dialect_id: int | None = None,
    db: Session = Depends(get_db),
) -> list:
    return DictionaryService(db).search(q, dialect_id)


@router.get("/dictionary/{entry_id}", response_model=DictionaryEntryRead)
def get_dictionary_entry(entry_id: int, db: Session = Depends(get_db)):
    return DictionaryService(db).get_public_entry(entry_id)


@router.get("/sources", response_model=list[SourceCitationRead])
def list_public_sources(db: Session = Depends(get_db)) -> list[dict]:
    """List scholarly sources with bibliographic information, citation text, and entry counts."""
    sources = db.query(Source).order_by(Source.id).all()
    results = []
    for s in sources:
        e_count = db.query(func.count(DictionaryEntry.id)).filter(DictionaryEntry.source_id == s.id).scalar() or 0
        p_count = db.query(func.count(ParallelSegment.id)).filter(ParallelSegment.source_id == s.id).scalar() or 0

        citation_parts = [s.title]
        if s.author:
            citation_parts.insert(0, s.author)
        if s.year:
            citation_parts.append(f"({s.year})")
        if s.isbn:
            citation_parts.append(f"ISBN: {s.isbn}")

        results.append({
            "id": s.id,
            "title": s.title,
            "author": s.author,
            "type": s.type.value if hasattr(s.type, "value") else str(s.type),
            "year": s.year,
            "url": s.url,
            "isbn": s.isbn,
            "notes": s.notes,
            "entries_count": e_count,
            "segments_count": p_count,
            "citation_text": " ".join(citation_parts),
        })
    return results


@router.get("/sources/{source_id}", response_model=SourceDetailRead)
def get_public_source_detail(source_id: int, db: Session = Depends(get_db)):
    """Get full bibliographic details and sample citations for a specific scholarly source."""
    s = db.get(Source, source_id)
    if not s:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")

    e_count = db.query(func.count(DictionaryEntry.id)).filter(DictionaryEntry.source_id == s.id).scalar() or 0
    p_count = db.query(func.count(ParallelSegment.id)).filter(ParallelSegment.source_id == s.id).scalar() or 0

    sample_entries = (
        db.query(DictionaryEntry)
        .filter(DictionaryEntry.source_id == s.id, DictionaryEntry.review_status == RecordStatus.approved)
        .limit(10)
        .all()
    )
    sample_segments = (
        db.query(ParallelSegment)
        .filter(ParallelSegment.source_id == s.id, ParallelSegment.review_status == RecordStatus.approved)
        .limit(10)
        .all()
    )

    citation_parts = [s.title]
    if s.author:
        citation_parts.insert(0, s.author)
    if s.year:
        citation_parts.append(f"({s.year})")

    return {
        "id": s.id,
        "title": s.title,
        "author": s.author,
        "type": s.type.value if hasattr(s.type, "value") else str(s.type),
        "year": s.year,
        "url": s.url,
        "isbn": s.isbn,
        "notes": s.notes,
        "entries_count": e_count,
        "segments_count": p_count,
        "citation_text": " ".join(citation_parts),
        "sample_entries": sample_entries,
        "sample_segments": sample_segments,
    }


@router.get("/examples/search", response_model=list[ParallelSegmentRead])
def search_examples(q: str, dialect_id: int | None = None, db: Session = Depends(get_db)) -> list:
    items = RetrievalService(db).similar_segments(q, dialect_id=dialect_id, limit=20)
    ids = [item["id"] for item in items]
    if not ids:
        return []
    segments_by_id = {
        segment.id: segment
        for segment in db.query(ParallelSegment).filter(ParallelSegment.id.in_(ids)).all()
    }
    return [segments_by_id[item_id] for item_id in ids if item_id in segments_by_id]


@router.get("/dialects", response_model=list[DialectRead])
def list_dialects(db: Session = Depends(get_db)) -> list[Dialect]:
    return db.query(Dialect).filter(Dialect.is_active.is_(True)).order_by(Dialect.id).all()
