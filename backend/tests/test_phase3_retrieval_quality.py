from __future__ import annotations

import json
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import (
    ParallelSegment,
    Source,
    TranslationCandidate,
    TranslationRequest,
    TranslationReview,
)
from app.models.enums import RecordStatus, SourceType
from app.services.embedding import (
    DeterministicEmbeddingProvider,
    EmbeddingManager,
    SentenceTransformerEmbeddingProvider,
    cosine_similarity,
    embed_batch,
    embed_text,
)
from app.services.evaluation import EvaluationDatasetService
from app.services.retrieval import (
    RetrievalService,
    compute_hybrid_ranking,
    compute_trigram_overlap,
    get_review_status_score,
    get_source_quality_score,
)
from conftest import auth_header


def test_embedding_providers_and_caching() -> None:
    # 1. Deterministic embedding provider
    det_provider = DeterministicEmbeddingProvider()
    vec1 = det_provider.embed_text("الملك الصالح")
    assert len(vec1) == 384
    assert sum(abs(v) for v in vec1) > 0

    # 2. Sentence transformer provider (fallbacks gracefully if model not downloaded/installed)
    ml_provider = SentenceTransformerEmbeddingProvider("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    vec_ml = ml_provider.embed_text("الملك الصالح")
    assert len(vec_ml) == 384

    # 3. Manager and caching
    mgr = EmbeddingManager()
    first = mgr.embed_text("كنيسة")
    second = mgr.embed_text("كنيسة")
    assert first == second

    # 4. Batch embeddings
    batch = mgr.embed_batch(["ملك", "كنيسة"])
    assert len(batch) == 2
    assert len(batch[0]) == 384


def test_trigram_overlap_and_source_weights() -> None:
    # 1. Trigram overlap
    tri = compute_trigram_overlap("الملوك", "الملك")
    assert tri > 0.4  # shared trigrams: 'الم', 'لمل'

    # 2. Source quality scores
    source_crum = Source(title="A Coptic Dictionary (Crum)", type=SourceType.lexicon)
    assert get_source_quality_score(source_crum) == 1.0

    source_web = Source(title="Random Blog Post", type=SourceType.website)
    assert get_source_quality_score(source_web) == 0.70

    # 3. Review status scores
    assert get_review_status_score(RecordStatus.approved) == 1.0
    assert get_review_status_score(RecordStatus.draft) == 0.60
    assert get_review_status_score(RecordStatus.rejected) == 0.0


def test_hybrid_ranking_computation() -> None:
    # Exact match must be 1.0
    exact_score, breakdown_exact = compute_hybrid_ranking(
        text_ratio=1.0,
        token_overlap=1.0,
        trigram_overlap=1.0,
        vector_score=1.0,
        source_quality=1.0,
        review_status=1.0,
    )
    assert exact_score == 1.0
    assert breakdown_exact["text_overlap"] == 1.0
    assert breakdown_exact["vector_similarity"] == 1.0

    # Partial match with high authority vs low authority
    score_scholarly, bd_scholarly = compute_hybrid_ranking(
        text_ratio=0.7,
        token_overlap=0.7,
        trigram_overlap=0.6,
        vector_score=0.8,
        source_quality=1.0,
        review_status=1.0,
    )
    score_low, bd_low = compute_hybrid_ranking(
        text_ratio=0.7,
        token_overlap=0.7,
        trigram_overlap=0.6,
        vector_score=0.8,
        source_quality=0.5,
        review_status=0.6,
    )
    assert score_scholarly > score_low
    assert "source_quality" in bd_scholarly
    assert "review_status" in bd_scholarly


def test_retrieval_service_hybrid_segments(db_session: Session) -> None:
    # Create two segments: one from Crum (lexicon) approved, one unverified draft
    src_crum = Source(title="A Coptic Dictionary (Crum)", type=SourceType.lexicon)
    src_comm = Source(title="Web Community Forum", type=SourceType.website)
    db_session.add_all([src_crum, src_comm])
    db_session.commit()

    seg1 = ParallelSegment(
        source_id=src_crum.id,
        dialect_id=1,
        arabic_text="صلاة مقدسة للرب",
        normalized_arabic_text="صلاة مقدسة للرب",
        coptic_text="ⲟⲩⲡⲣⲟⲥⲉⲩⲭⲏ ⲉⲑⲟⲩⲁⲁⲃ",
        normalized_coptic_text="ⲟⲩⲡⲣⲟⲥⲉⲩⲭⲏ ⲉⲑⲟⲩⲁⲁⲃ",
        arabic_embedding=embed_text("صلاة مقدسة للرب"),
        coptic_embedding=embed_text("ⲟⲩⲡⲣⲟⲥⲉⲩⲭⲏ ⲉⲑⲟⲩⲁⲁⲃ"),
        review_status=RecordStatus.approved,
    )
    db_session.add(seg1)
    db_session.commit()

    retriever = RetrievalService(db_session)
    results = retriever.similar_segments("صلاة مقدسة للرب", limit=1)

    assert len(results) == 1
    assert results[0]["id"] == seg1.id
    assert results[0]["similarity_score"] == 1.0
    assert "score_breakdown" in results[0]
    assert results[0]["score_breakdown"]["source_quality"] == 1.0


def test_evaluation_dataset_service(db_session: Session) -> None:
    # Create sample requests, candidates, and reviews
    req = TranslationRequest(
        input_text="الملك الصالح",
        normalized_input_text="الملك الصالح",
        target_dialect_id=1,
    )
    db_session.add(req)
    db_session.commit()

    cand1 = TranslationCandidate(
        translation_request_id=req.id,
        dialect_id=1,
        candidate_text="ⲡⲓⲟⲩⲣⲟ ⲉⲑⲛⲁⲛⲉϥ",
        normalized_candidate_text="ⲡⲓⲟⲩⲣⲟ ⲉⲑⲛⲁⲛⲉϥ",
        confidence=0.92,
        review_status=RecordStatus.approved,
    )
    db_session.add(cand1)
    db_session.commit()

    rev1 = TranslationReview(
        translation_candidate_id=cand1.id,
        review_status=RecordStatus.approved,
        comment="ترجمة دقيقة مطابقة للشواهد",
    )
    db_session.add(rev1)
    db_session.commit()

    # Second candidate with correction
    cand2 = TranslationCandidate(
        translation_request_id=req.id,
        dialect_id=1,
        candidate_text="ⲡⲓⲟⲩⲣⲟ ⲁⲅⲁⲑⲟⲥ",
        normalized_candidate_text="ⲡⲓⲟⲩⲣⲟ ⲁⲅⲁⲑⲟⲥ",
        confidence=0.75,
        review_status=RecordStatus.approved,
    )
    db_session.add(cand2)
    db_session.commit()

    rev2 = TranslationReview(
        translation_candidate_id=cand2.id,
        review_status=RecordStatus.approved,
        corrected_text="ⲡⲓⲟⲩⲣⲟ ⲉⲑⲛⲁⲛⲉϥ",
        comment="تصحيح الصفة إلى الصياغة القبطية الأصلية",
    )
    db_session.add(rev2)
    db_session.commit()

    eval_service = EvaluationDatasetService(db_session)
    items = eval_service.get_evaluation_items()
    assert len(items) >= 2

    # Test JSONL export
    jsonl_str = eval_service.export_jsonl()
    lines = [json.loads(line) for line in jsonl_str.strip().split("\n")]
    assert len(lines) >= 2
    assert "source" in lines[0]
    assert "target" in lines[0]
    assert "prediction" in lines[0]

    # Test CSV export
    csv_str = eval_service.export_csv()
    assert "input_arabic" in csv_str
    assert "predicted_coptic" in csv_str

    # Test metrics
    metrics = eval_service.compute_metrics()
    assert metrics["total_reviews"] >= 2
    assert metrics["approved_count"] >= 1
    assert metrics["corrected_count"] >= 1
    assert metrics["approval_rate"] > 0


def test_admin_evaluation_endpoints(client: TestClient) -> None:
    admin_headers = auth_header(client, "admin@example.com")

    # 1. Metrics endpoint
    res_metrics = client.get("/admin/evaluation/metrics", headers=admin_headers)
    assert res_metrics.status_code == 200, res_metrics.text
    data = res_metrics.json()
    assert "total_reviews" in data
    assert "approval_rate" in data

    # 2. Dataset JSON endpoint
    res_json = client.get("/admin/evaluation/dataset?format=json", headers=admin_headers)
    assert res_json.status_code == 200, res_json.text
    assert isinstance(res_json.json(), list)

    # 3. Dataset JSONL export
    res_jsonl = client.get("/admin/evaluation/dataset?format=jsonl", headers=admin_headers)
    assert res_jsonl.status_code == 200, res_jsonl.text
    assert "application/x-ndjson" in res_jsonl.headers.get("content-type", "")

    # 4. Dataset CSV export
    res_csv = client.get("/admin/evaluation/dataset?format=csv", headers=admin_headers)
    assert res_csv.status_code == 200, res_csv.text
    assert "text/csv" in res_csv.headers.get("content-type", "")
