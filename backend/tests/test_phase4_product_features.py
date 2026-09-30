from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import DictionaryEntry, ParallelSegment, Source
from app.models.enums import PartOfSpeech, RecordStatus, SourceType
from conftest import auth_header


def test_public_dictionary_browsing(client: TestClient, db_session: Session) -> None:
    # 1. Browse without auth
    res = client.get("/dictionary/browse?page=1&page_size=10")
    assert res.status_code == 200, res.text
    data = res.json()
    assert "items" in data
    assert "total" in data
    assert "total_pages" in data
    assert isinstance(data["items"], list)

    # 2. Filter by dialect
    res_dialect = client.get("/dictionary/browse?dialect_id=1&page=1&page_size=5")
    assert res_dialect.status_code == 200
    for item in res_dialect.json()["items"]:
        assert item["dialect_id"] == 1

    # 3. Filter by part of speech
    res_pos = client.get("/dictionary/browse?part_of_speech=noun&page=1&page_size=5")
    assert res_pos.status_code == 200


def test_public_sources_citation_pages(client: TestClient, db_session: Session) -> None:
    # 1. List public sources
    res = client.get("/sources")
    assert res.status_code == 200, res.text
    sources = res.json()
    assert isinstance(sources, list)
    assert len(sources) > 0
    assert "citation_text" in sources[0]
    assert "entries_count" in sources[0]
    assert "segments_count" in sources[0]

    # 2. Detail of a single source
    first_id = sources[0]["id"]
    res_detail = client.get(f"/sources/{first_id}")
    assert res_detail.status_code == 200, res_detail.text
    detail = res_detail.json()
    assert detail["id"] == first_id
    assert "sample_entries" in detail
    assert "sample_segments" in detail


def test_reviewer_workload_dashboard(client: TestClient) -> None:
    admin_headers = auth_header(client, "admin@example.com")
    res = client.get("/admin/workload", headers=admin_headers)
    assert res.status_code == 200, res.text
    data = res.json()
    assert "total_pending_drafts" in data
    assert "total_approved_candidates" in data
    assert "reviewers" in data
    assert isinstance(data["reviewers"], list)


def test_bulk_admin_export(client: TestClient) -> None:
    admin_headers = auth_header(client, "admin@example.com")

    # 1. Export dictionary CSV
    res_csv = client.get("/admin/export/dictionary?format=csv", headers=admin_headers)
    assert res_csv.status_code == 200
    assert "text/csv" in res_csv.headers.get("content-type", "")

    # 2. Export dictionary JSON
    res_json = client.get("/admin/export/dictionary?format=json", headers=admin_headers)
    assert res_json.status_code == 200
    assert "application/json" in res_json.headers.get("content-type", "")

    # 3. Export segments CSV
    res_seg = client.get("/admin/export/segments?format=csv", headers=admin_headers)
    assert res_seg.status_code == 200
    assert "text/csv" in res_seg.headers.get("content-type", "")


def test_freemium_quota_in_translate_response(client: TestClient) -> None:
    # Anonymous call
    res = client.post("/translate", json={"text": "الله", "target_dialect_id": 1})
    assert res.status_code == 200, res.text
    data = res.json()
    assert "quota" in data
    assert data["quota"] is not None
    assert "daily_limit" in data["quota"]
    assert "remaining" in data["quota"]
    assert data["quota"]["daily_limit"] == 10
