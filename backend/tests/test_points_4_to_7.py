"""Test fixes for review points 4, 5, 6, and 7."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models import Dialect, DictionaryEntry, ParallelSegment, Source
from app.models.enums import PartOfSpeech, RecordStatus
from app.services.retrieval import RetrievalService
from app.services.translation import TranslationService
from conftest import auth_header


def test_point_4_admin_list_endpoints_filter_approved(client: TestClient) -> None:
    """Admin list endpoints should filter by review_status=approved by default and support filtering."""
    from tests.test_admin_workflows import _seed_word
    
    app_id = _seed_word(client, "رجل", "ⲡⲓⲣⲱⲙⲓ", "noun", "انسان")
    
    headers = auth_header(client, "admin@example.com")
    dialect_id = client.get("/dialects").json()[0]["id"]
    draft_res = client.post(
        "/admin/dictionary",
        json={
            "coptic_text": "ⲡⲓⲁⲗⲟⲩ",
            "normalized_coptic_text": "ⲡⲓⲁⲗⲟⲩ",
            "transliteration": "pialou",
            "dialect_id": dialect_id,
            "source_id": 1,
            "part_of_speech": "noun",
            "arabic_lemma": "صبي",
            "arabic_definition": "طفل",
            "review_status": "draft",
        },
        headers=headers,
    )
    assert draft_res.status_code == 201
    draft_id = draft_res.json()["id"]

    # Default should return approved
    res_approved = client.get("/admin/dictionary", headers=headers)
    assert res_approved.status_code == 200
    ids_approved = [e["id"] for e in res_approved.json()]
    assert app_id in ids_approved
    assert draft_id not in ids_approved

    # Explicit query for draft should return draft
    res_draft = client.get("/admin/dictionary?review_status=draft", headers=headers)
    assert res_draft.status_code == 200
    ids_draft = [e["id"] for e in res_draft.json()]
    assert draft_id in ids_draft
    assert app_id not in ids_draft


def test_point_5_no_hallucination_with_unknown_words(db_session: Session) -> None:
    """Unknown words in sentence must strictly prevent candidate_text from being generated, even if similar segments exist."""
    service = TranslationService(db_session)
    res = service.translate_sentence("الله كلمةغيرمعروفة123", user_id=None, target_dialect_id=1)
    
    assert len(res["unknown_words"]) > 0
    assert res["candidate_translation"] is None
    assert res["needs_human_review"] is True


def test_point_6_is_postgres_uses_get_bind(db_session: Session) -> None:
    """RetrievalService._is_postgres must execute cleanly via get_bind() without deprecation warnings/errors."""
    service = RetrievalService(db_session)
    is_pg = service._is_postgres()
    assert is_pg is False


def test_point_7_translate_word_returns_translations_list(client: TestClient, db_session: Session) -> None:
    """translate() on a single word returns primary translation and complete list in translations."""
    from tests.test_translation_service import _entry
    _entry(db_session, "حارس", "ⲣⲉϥⲁⲣⲉϩ", PartOfSpeech.noun, "حافظ")
    service = TranslationService(db_session)
    res = service.translate("حارس", user_id=None, target_dialect_id=1)
    
    assert res.input_type.value == "word"
    assert res.translation == "ⲣⲉϥⲁⲣⲉϩ"
    assert isinstance(res.translations, list)
    assert len(res.translations) >= 1
    assert "ⲣⲉϥⲁⲣⲉϩ" in res.translations
