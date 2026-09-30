from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import ArabicSense, GrammarRule, ParallelSegment
from app.models.enums import PartOfSpeech, RecordStatus
from app.services.retrieval import RetrievalService
from conftest import auth_header


def _segment(db: Session, arabic: str, coptic: str) -> ParallelSegment:
    service = RetrievalService(db)
    segment = ParallelSegment(
        source_id=1,
        dialect_id=1,
        arabic_text=arabic,
        normalized_arabic_text=service.normalize_arabic(arabic),
        coptic_text=coptic,
        normalized_coptic_text=coptic,
        arabic_embedding=service.embed_text(arabic),
        coptic_embedding=service.embed_text(coptic),
        sentence_embedding=service.embed_text(arabic),
        review_status=RecordStatus.approved,
    )
    db.add(segment)
    db.commit()
    db.refresh(segment)
    return segment


def _sense(db: Session, lemma: str, meaning: str) -> ArabicSense:
    service = RetrievalService(db)
    sense = ArabicSense(
        arabic_lemma=lemma,
        normalized_arabic_lemma=service.normalize_arabic(lemma),
        definition_ar=meaning,
        meaning_embedding=service.embed_text(meaning),
        part_of_speech=PartOfSpeech.noun,
        review_status=RecordStatus.approved,
    )
    db.add(sense)
    db.commit()
    db.refresh(sense)
    return sense


def _rule(db: Session, description: str) -> GrammarRule:
    service = RetrievalService(db)
    rule = GrammarRule(
        dialect_id=1,
        source_id=1,
        title="Noun adjective rule",
        description=description,
        description_embedding=service.embed_text(description),
        pattern="noun adjective",
        replacement="{noun} {adjective}",
        priority=10,
        review_status=RecordStatus.approved,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def test_retrieval_returns_top_five_similar_segments_with_references(db_session: Session) -> None:
    best = _segment(db_session, "إله صالح", "ⲛⲟⲩϯ ⲁⲅⲁⲑⲟⲥ")
    _segment(db_session, "إله صالح جدا", "ⲛⲟⲩϯ ⲁⲅⲁⲑⲟⲥ ⲉⲙⲁⲧⲉ")
    for index in range(6):
        _segment(db_session, f"نص بعيد {index}", f"ⲧⲉⲝⲧ {index}")

    results = RetrievalService(db_session).similar_segments("إله صالح")

    assert len(results) == 5
    assert results[0]["id"] == best.id
    assert results[0]["similarity_score"] == 1.0
    assert results[0]["reference"]["table"] == "parallel_segments"
    assert all("reference" in item for item in results)


def test_retrieval_finds_examples_by_shared_words_and_meanings(db_session: Session) -> None:
    segment = _segment(db_session, "الإله صالح", "ⲡⲛⲟⲩϯ ⲁⲅⲁⲑⲟⲥ")
    sense = _sense(db_session, "إله", "كائن إلهي معبود")

    results = RetrievalService(db_session).examples_for_sentence("إله صالح")

    assert results["segments"][0]["id"] == segment.id
    assert results["senses"][0]["id"] == sense.id
    assert results["segments"][0]["reference"]["id"] == segment.id
    assert results["senses"][0]["reference"]["table"] == "arabic_senses"


def test_retrieval_finds_matching_grammar_rules_by_description(db_session: Session) -> None:
    rule = _rule(db_session, "قاعدة ترتيب الاسم قبل الصفة في الجملة القبطية")

    results = RetrievalService(db_session).grammar_rules_for_sentence("إله صالح")

    assert results[0]["id"] == rule.id
    assert results[0]["similarity_score"] > 0
    assert results[0]["reference"] == {"table": "grammar_rules", "id": rule.id}


def test_retrieval_endpoint_returns_similar_segments(client: TestClient) -> None:
    headers = auth_header(client, "user@example.com")
    admin_headers = auth_header(client, "admin@example.com")
    dialect_id = client.get("/dialects").json()[0]["id"]
    corpus = client.post(
        "/admin/corpus-texts",
        json={
            "title": "RAG examples",
            "source_id": 1,
            "dialect_id": dialect_id,
            "language": "ar-cop",
            "review_status": "approved",
        },
        headers=admin_headers,
    )
    assert corpus.status_code == 201, corpus.text
    segment = client.post(
        "/admin/parallel-segments",
        json={
            "corpus_text_id": corpus.json()["id"],
            "source_id": 1,
            "dialect_id": dialect_id,
            "arabic_text": "إله صالح",
            "coptic_text": "ⲛⲟⲩϯ ⲁⲅⲁⲑⲟⲥ",
            "review_status": "approved",
        },
        headers=admin_headers,
    )
    assert segment.status_code == 201, segment.text

    response = client.post(
        "/retrieval/similar-segments",
        json={"q": "إله صالح", "limit": 5},
        headers=headers,
    )

    assert response.status_code == 200, response.text
    assert response.json()["items"][0]["id"] == segment.json()["id"]
    assert response.json()["items"][0]["reference"]["table"] == "parallel_segments"
