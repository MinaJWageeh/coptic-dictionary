"""Test fixes for review points 8, 9, and 10."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.identity import User
from app.security import create_access_token
from app.services.rate_limit import InMemoryRateLimiter, login_rate_limiter, translate_rate_limiter
from app.services.translation import TranslationService


def test_point_8_rate_limiting_enforcement(client: TestClient) -> None:
    """Rate limiter must enforce requests limit and return 429 with Retry-After header."""
    limiter = InMemoryRateLimiter(requests_limit=3, window_seconds=60)
    
    # First 3 requests must pass
    limiter.check("1.2.3.4")
    limiter.check("1.2.3.4")
    limiter.check("1.2.3.4")

    # 4th request must raise 429
    with pytest.raises(Exception) as excinfo:
        limiter.check("1.2.3.4")
    
    from fastapi import HTTPException
    assert isinstance(excinfo.value, HTTPException)
    assert excinfo.value.status_code == 429
    assert "Retry-After" in excinfo.value.headers
    assert excinfo.value.detail == "Too many requests. Please wait a moment before trying again."


def test_point_9_candidate_generated_by_is_rule_based(db_session: Session) -> None:
    """Sentence translations composed by the syntax engine must be labeled rule_based rather than ai."""
    from tests.test_translation_service import _entry
    _entry(db_session, "إله", "ⲛⲟⲩϯ", "noun", "كائن إلهي")
    _entry(db_session, "صالح", "ⲁⲅⲁⲑⲟⲥ", "adjective", "طيب")
    
    service = TranslationService(db_session)
    res = service.translate_sentence("إله صالح", user_id=None, target_dialect_id=1)
    
    from app.models import TranslationCandidate
    cand = db_session.get(TranslationCandidate, res["translation_candidate_id"])
    assert cand is not None
    assert cand.generated_by == "rule_based"


def test_point_10_auth_token_does_not_leak_user_existence(client: TestClient) -> None:
    """Non-existent user with valid token structure must return 'Invalid token' rather than 'User not found'."""
    # Token signed with secret but for a user that does not exist in the database
    token = create_access_token("nonexistent_user_999@example.com")
    
    res = client.get("/admin/dictionary", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid token"
