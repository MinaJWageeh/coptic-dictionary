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
    response = client.post(
        "/admin/dictionary",
        json={
            "coptic_text": coptic,
            "normalized_coptic_text": coptic,
            "transliteration": coptic,
            "dialect_id": dialect_id,
            "source_id": 1,
            "part_of_speech": part_of_speech,
            "arabic_lemma": arabic,
            "arabic_definition": definition,
            "review_status": "approved",
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_admin_can_update_delete_source_and_view_audit_logs(client: TestClient) -> None:
    headers = auth_header(client, "admin@example.com")
    created = client.post(
        "/admin/sources",
        json={
            "title": "Editable Source",
            "author": "Original Author",
            "type": "book",
            "year": 1900,
        },
        headers=headers,
    )
    assert created.status_code == 201, created.text
    source_id = created.json()["id"]

    updated = client.put(
        f"/admin/sources/{source_id}",
        json={"title": "Updated Source", "author": "Reviewed Author", "type": "lexicon"},
        headers=headers,
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["title"] == "Updated Source"
    assert updated.json()["author"] == "Reviewed Author"

    deleted = client.delete(f"/admin/sources/{source_id}", headers=headers)
    assert deleted.status_code == 204, deleted.text

    listed = client.get("/admin/sources", headers=headers)
    assert listed.status_code == 200
    assert source_id not in [item["id"] for item in listed.json()]

    audit = client.get("/admin/audit-logs", headers=headers)
    assert audit.status_code == 200, audit.text
    source_events = [
        item for item in audit.json() if item["table_name"] == "sources" and item["record_id"] == source_id
    ]
    assert [event["action"] for event in source_events] == ["delete", "update", "create"]
    assert source_events[0]["old_data"]["title"] == "Updated Source"
    assert source_events[1]["new_data"]["title"] == "Updated Source"


def test_reviewer_correction_adds_approved_parallel_segment(client: TestClient) -> None:
    _seed_word(client, "إله", "ⲛⲟⲩϯ", "noun", "كائن إلهي معبود")
    user_headers = auth_header(client, "user@example.com")
    translation = client.post("/translate", json={"text": "إله صالح"}, headers=user_headers)
    assert translation.status_code == 200, translation.text
    candidate_id = translation.json()["translation_candidate_id"]

    reviewer_headers = auth_header(client, "reviewer@example.com")
    corrected = client.post(
        f"/review/translation/{candidate_id}/correct",
        json={"corrected_text": "ⲛⲟⲩϯ ⲁⲅⲁⲑⲟⲥ", "comment": "Approved by reviewer"},
        headers=reviewer_headers,
    )
    assert corrected.status_code == 200, corrected.text

    admin_headers = auth_header(client, "admin@example.com")
    segments = client.get("/admin/parallel-segments", headers=admin_headers)
    assert segments.status_code == 200
    feedback_segments = [
        item for item in segments.json() if item["arabic_text"] == "إله صالح"
    ]
    assert feedback_segments
    assert feedback_segments[0]["coptic_text"] == "ⲛⲟⲩϯ ⲁⲅⲁⲑⲟⲥ"
    assert feedback_segments[0]["review_status"] == "approved"
