from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Dialect, ParallelSegment, SenseMapping, Source
from app.seed.run import seed
from tests.conftest import auth_header
from tests.test_translation_service import _approved_segment, _entry, _grammar_rule, PartOfSpeech


def test_point_16_auth_header_and_default_passwords(client: TestClient) -> None:
    # Test auth_header with default ChangeMe123!
    header_default = auth_header(client, "user@example.com")
    assert "Authorization" in header_default
    assert header_default["Authorization"].startswith("Bearer ")

    # Test auth_header with secret backward-compatibility fallback
    header_fallback = auth_header(client, "reviewer@example.com", password="secret")
    assert "Authorization" in header_fallback
    assert header_fallback["Authorization"].startswith("Bearer ")


def test_point_17_dynamic_dialect_and_source(db_session: Session) -> None:
    # Verify helpers use dynamic queries rather than hardcoded id=1
    first_dialect = db_session.query(Dialect).first()
    first_source = db_session.query(Source).first()
    assert first_dialect is not None
    assert first_source is not None

    entry = _entry(db_session, "تجربة", "ⲧⲉⲥⲧ", PartOfSpeech.noun, "تجربة")
    assert entry.dialect_id == first_dialect.id
    assert entry.source_id == first_source.id

    segment = _approved_segment(db_session, "تجربة جملة", "ⲧⲉⲥⲧ ⲥⲉⲛⲧⲉⲛⲥⲉ")
    assert segment.dialect_id == first_dialect.id
    assert segment.source_id == first_source.id

    rule = _grammar_rule(db_session)
    assert rule.dialect_id == first_dialect.id
    assert rule.source_id == first_source.id


def test_point_18_seed_alignment_and_confidence(db_session: Session) -> None:
    seed(db_session)
    segments = db_session.query(ParallelSegment).all()
    assert len(segments) > 0
    for s in segments:
        assert s.alignment_score >= 0.85

    mappings = db_session.query(SenseMapping).all()
    assert len(mappings) > 0
    for m in mappings:
        assert m.confidence >= 0.85
