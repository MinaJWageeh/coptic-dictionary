from __future__ import annotations

from fastapi.testclient import TestClient

from conftest import auth_header


def _seed_word(
    client: TestClient,
    arabic: str,
    coptic: str,
    part_of_speech: str,
    definition: str,
) -> int:
    headers = auth_header(client, "admin@example.com")
    dialect_id = client.get("/dialects").json()[0]["id"]
    payload = {
        "coptic_text": coptic,
        "normalized_coptic_text": coptic,
        "transliteration": coptic,
        "dialect_id": dialect_id,
        "source_id": 1,
        "part_of_speech": part_of_speech,
        "arabic_lemma": arabic,
        "arabic_definition": definition,
        "example_sentence": f"{coptic} example",
        "review_status": "approved",
    }
    response = client.post("/admin/dictionary", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _seed_dictionary_entry(client: TestClient) -> int:
    return _seed_word(client, "إله", "ⲛⲟⲩϯ", "noun", "كائن إلهي معبود")


def test_login_returns_jwt_access_token(client: TestClient) -> None:
    response = client.post(
        "/auth/login", json={"email": "user@example.com", "password": "ChangeMe123!"}
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_localhost_3001_can_fetch_public_dialects(client: TestClient) -> None:
    response = client.options(
        "/dialects",
        headers={
            "Origin": "http://localhost:3001",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3001"


def test_admin_dictionary_requires_admin_role(client: TestClient) -> None:
    user_headers = auth_header(client, "user@example.com")

    response = client.post(
        "/admin/dictionary",
        json={
            "coptic_text": "ⲁⲅⲁⲑⲟⲥ",
            "normalized_coptic_text": "ⲁⲅⲁⲑⲟⲥ",
            "dialect_id": 1,
            "source_id": 1,
            "part_of_speech": "adjective",
            "review_status": "approved",
        },
        headers=user_headers,
    )

    assert response.status_code == 403


def test_word_translation_uses_approved_dictionary_lookup(client: TestClient) -> None:
    entry_id = _seed_dictionary_entry(client)
    headers = auth_header(client, "user@example.com")

    response = client.post("/translate", json={"text": "إله"}, headers=headers)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["input_type"] == "word"
    assert body["status"] == "approved"
    assert body["translation"] == "ⲛⲟⲩϯ"
    assert body["dictionary_entry_ids"] == [entry_id]


def test_word_translation_exposes_rich_word_results(client: TestClient) -> None:
    entry_id = _seed_dictionary_entry(client)
    headers = auth_header(client, "user@example.com")

    response = client.post("/translate", json={"text": "إله"}, headers=headers)

    assert response.status_code == 200, response.text
    word = response.json()["word_results"][0]
    assert word["dictionary_entry_id"] == entry_id
    assert word["coptic_word"] == "ⲛⲟⲩϯ"
    assert word["dialect"] == "Sahidic"
    assert word["part_of_speech"] == "noun"
    assert word["meaning"] == "كائن إلهي معبود"
    assert word["source"] == "Seed Lexicon"
    assert word["examples"]


def test_sentence_translation_saves_new_candidate_as_draft(client: TestClient) -> None:
    _seed_dictionary_entry(client)
    headers = auth_header(client, "user@example.com")

    response = client.post("/translate", json={"text": "إله صالح"}, headers=headers)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["input_type"] == "sentence"
    assert body["status"] == "draft"
    assert body["translation_request_id"]
    assert body["translation_candidate_id"]

    admin_headers = auth_header(client, "admin@example.com")
    candidates = client.get("/admin/translation-candidates", headers=admin_headers)
    assert candidates.status_code == 200
    assert candidates.json()[0]["review_status"] == "draft"


def test_sentence_translation_exposes_pipeline_details(client: TestClient) -> None:
    entry_id = _seed_dictionary_entry(client)
    headers = auth_header(client, "user@example.com")

    response = client.post("/translate", json={"text": "إله غامض"}, headers=headers)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "draft"
    assert body["candidate_translation"] is None
    assert body["literal_breakdown"] == [
        {"arabic": "اله", "coptic": "ⲛⲟⲩϯ", "status": "known", "dictionary_entry_id": entry_id},
        {"arabic": "غامض", "coptic": None, "status": "unknown", "dictionary_entry_id": None},
    ]
    assert body["used_dictionary_entries"] == [entry_id]
    assert body["unknown_words"] == ["غامض"]
    assert body["needs_human_review"] is True
    assert body["human_review_reason"] == "unknown_words"


def test_existing_approved_sentence_can_return_approved_translation(client: TestClient) -> None:
    headers = auth_header(client, "admin@example.com")
    dialect_id = client.get("/dialects").json()[0]["id"]
    corpus = client.post(
        "/admin/corpus-texts",
        json={
            "title": "Approved examples",
            "source_id": 1,
            "dialect_id": dialect_id,
            "language": "ar-cop",
            "review_status": "approved",
        },
        headers=headers,
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
        headers=headers,
    )
    assert segment.status_code == 201, segment.text

    response = client.post("/translate", json={"text": "إله صالح"}, headers=headers)

    assert response.status_code == 200
    assert response.json()["status"] == "approved"
    assert response.json()["translation"] == "ⲛⲟⲩϯ ⲁⲅⲁⲑⲟⲥ"


def test_reviewer_can_correct_translation_candidate(client: TestClient) -> None:
    _seed_dictionary_entry(client)
    user_headers = auth_header(client, "user@example.com")
    translation = client.post("/translate", json={"text": "إله صالح"}, headers=user_headers)
    candidate_id = translation.json()["translation_candidate_id"]

    reviewer_headers = auth_header(client, "reviewer@example.com")
    response = client.post(
        f"/review/translation/{candidate_id}/correct",
        json={"corrected_text": "ⲛⲟⲩϯ ⲁⲅⲁⲑⲟⲥ", "comment": "Reviewed"},
        headers=reviewer_headers,
    )

    assert response.status_code == 200, response.text
    assert response.json()["review_status"] == "approved"
    assert response.json()["candidate_text"] == "ⲛⲟⲩϯ ⲁⲅⲁⲑⲟⲥ"
