from __future__ import annotations

from fastapi.testclient import TestClient

from conftest import auth_header


def _seed_dictionary_word(client: TestClient, arabic: str = "سلام", coptic: str = "ⲉⲓⲣⲏⲛⲏ") -> int:
    headers = auth_header(client, "admin@example.com")
    dialect_id = client.get("/dialects").json()[0]["id"]
    response = client.post(
        "/admin/dictionary",
        json={
            "coptic_text": coptic,
            "normalized_coptic_text": coptic,
            "transliteration": "eirene",
            "dialect_id": dialect_id,
            "source_id": 1,
            "part_of_speech": "noun",
            "arabic_lemma": arabic,
            "arabic_definition": "معنى اختباري معتمد",
            "review_status": "approved",
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _draft_candidate(client: TestClient) -> int:
    _seed_dictionary_word(client, "إله", "ⲛⲟⲩϯ")
    user_headers = auth_header(client, "user@example.com")
    response = client.post("/translate", json={"text": "إله مجهول"}, headers=user_headers)
    assert response.status_code == 200, response.text
    return response.json()["translation_candidate_id"]


def test_login_rejects_invalid_credentials(client: TestClient) -> None:
    response = client.post("/auth/login", json={"email": "user@example.com", "password": "bad"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_translate_word_is_available_without_authentication(client: TestClient) -> None:
    entry_id = _seed_dictionary_word(client)

    response = client.post("/translate", json={"text": "سلام"})

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["input_type"] == "word"
    assert body["translation"] == "ⲉⲓⲣⲏⲛⲏ"
    assert body["dictionary_entry_ids"] == [entry_id]


def test_dictionary_search_returns_approved_entries(client: TestClient) -> None:
    entry_id = _seed_dictionary_word(client)

    response = client.get("/dictionary/search", params={"q": "سلام"})

    assert response.status_code == 200, response.text
    rows = response.json()
    assert [row["id"] for row in rows] == [entry_id]
    assert rows[0]["coptic_text"] == "ⲉⲓⲣⲏⲛⲏ"
    assert rows[0]["review_status"] == "approved"


def test_reviewer_can_approve_draft_translation(client: TestClient) -> None:
    candidate_id = _draft_candidate(client)
    reviewer_headers = auth_header(client, "reviewer@example.com")

    response = client.post(f"/review/translation/{candidate_id}/approve", headers=reviewer_headers)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["id"] == candidate_id
    assert body["review_status"] == "approved"


def test_reviewer_can_reject_draft_translation(client: TestClient) -> None:
    candidate_id = _draft_candidate(client)
    reviewer_headers = auth_header(client, "reviewer@example.com")

    response = client.post(
        f"/review/translation/{candidate_id}/reject",
        json={"comment": "Not enough evidence"},
        headers=reviewer_headers,
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["id"] == candidate_id
    assert body["review_status"] == "rejected"
