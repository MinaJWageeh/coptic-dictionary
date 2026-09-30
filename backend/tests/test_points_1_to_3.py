"""Test fixes for points 1, 2, and 3."""
import pytest
from sqlalchemy.orm import Session
from app.models import Source, TranslationCandidate, TranslationRequest, ParallelSegment
from app.models.enums import RecordStatus, SourceType
from app.services.translation import TranslationService
from app.services.review import ReviewService
from app.services.text import normalize_coptic


def test_point_1_empty_candidate_text_stored_as_null(db_session: Session) -> None:
    """When a sentence cannot be translated, candidate_text must be None (NULL), never empty string."""
    service = TranslationService(db_session)
    # Sentence with completely unknown words
    result = service.translate_sentence("كلمة مجهولة تماما وغير معروفة", user_id=None, target_dialect_id=1)
    
    assert result["candidate_translation"] is None
    candidate_id = result.get("translation_candidate_id")
    assert candidate_id is not None

    candidate = db_session.get(TranslationCandidate, candidate_id)
    assert candidate is not None
    assert candidate.candidate_text is None, f"Expected None but got: {repr(candidate.candidate_text)}"
    assert candidate.normalized_candidate_text is None


def test_point_2_correct_normalizes_coptic_text(db_session: Session) -> None:
    """ReviewService.correct must normalize coptic text rather than assigning raw text."""
    req = TranslationRequest(input_text="تجربة", status="completed")
    db_session.add(req)
    db_session.flush()

    candidate = TranslationCandidate(
        translation_request_id=req.id,
        candidate_text="ⲡⲓⲣⲱⲙⲓ",
        dialect_id=1,
        review_status=RecordStatus.draft
    )
    db_session.add(candidate)
    db_session.commit()

    raw_coptic = "ⲡⲓⲣⲱⲙⲓ"
    review_service = ReviewService(db_session)
    updated = review_service.correct(candidate.id, reviewer_id=None, corrected_text=raw_coptic, comment="Corrected")

    assert updated.candidate_text == raw_coptic
    assert updated.normalized_candidate_text == normalize_coptic(raw_coptic)


def test_point_3_no_arbitrary_source_fallback(db_session: Session) -> None:
    """When no evidence source exists, ReviewService must not arbitrarily pick Source.id == 1."""
    req = TranslationRequest(input_text="سماء", status="completed")
    db_session.add(req)
    db_session.flush()

    # Candidate with NO dictionary or parallel segment evidence
    candidate = TranslationCandidate(
        translation_request_id=req.id,
        candidate_text="ⲧⲫⲉ",
        dialect_id=1,
        evidence={},
        review_status=RecordStatus.draft
    )
    db_session.add(candidate)
    db_session.commit()

    review_service = ReviewService(db_session)
    source_id = review_service._source_id_from_evidence(candidate)

    # It must not arbitrarily return Source 1 or any ID without matching evidence
    assert source_id is None
