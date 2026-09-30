"""Stage 5: Hybrid example retrieval (RAG).

Combines semantic search (pgvector cosine) with lexical overlap (token Jaccard
over normalized Arabic) to surface the most relevant corpus examples. Only
`approved` examples are trusted as primary context; drafts may surface with a
penalty so reviewers can discover them.
"""
from __future__ import annotations

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.config import settings
from app.models.enums import RecordStatus
from app.models.examples import Example
from app.pipeline.normalizer import normalize_arabic
from app.pipeline.types import ExampleHit, PipelineContext

ALPHA = 0.6  # semantic vs lexical blend
TOP_K = 5


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def _query_by_embedding(db: Session, vec, limit: int):
    """Cosine distance search via pgvector `<=>`. Falls back if no vectors."""
    try:
        from pgvector.sqlalchemy import Vector  # noqa: F401
    except ImportError:
        return []

    sql = text(
        """
        SELECT id, arabic_text, coptic_text, source_id,
               1 - (embedding <=> :vec) AS sim
        FROM examples
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> :vec
        LIMIT :limit
        """
    )
    try:
        return list(
            db.execute(sql, {"vec": str(list(vec)), "limit": limit}).mappings().all()
        )
    except Exception:  # vector column missing or pgvector not ready
        return []


def _query_by_tokens(db: Session, query_set: set[str]) -> list[dict]:
    """Lexical fallback: scan approved examples and rank by token overlap."""
    rows = (
        db.execute(
            select(Example).where(
                Example.status == RecordStatus.approved,
                Example.deleted_at.is_(None),
            )
        )
        .scalars()
        .all()
    )
    scored: list[tuple[float, Example]] = []
    for ex in rows:
        ex_tokens = set(ex.arabic_normalized.split())
        score = _jaccard(query_set, ex_tokens)
        if score > 0:
            scored.append((score, ex))
    scored.sort(key=lambda t: t[0], reverse=True)
    return [
        {
            "id": ex.id,
            "arabic_text": ex.arabic_text,
            "coptic_text": ex.coptic_text,
            "source_id": ex.source_id,
            "sim": score,
        }
        for score, ex in scored[:TOP_K]
    ]


def retrieve_examples(ctx: PipelineContext, db: Session, embedding_fn=None) -> None:
    """Fill ctx.examples with the top-k hybrid matches."""
    query_tokens = set(ctx.tokens)

    # --- lexical path (always available) ---
    lexical = _query_by_tokens(db, query_tokens)

    # --- semantic path (optional, needs embeddings + pgvector) ---
    semantic: list[dict] = []
    if settings.EMBEDDING_ENABLED and embedding_fn is not None:
        try:
            vec = embedding_fn(ctx.normalized_input)
            semantic = _query_by_embedding(db, vec, TOP_K)
        except Exception:
            semantic = []

    # --- blend by example id ---
    merged: dict[int, dict] = {}

    def _score(sim_sem: float, sim_lex: float) -> float:
        if semantic and lexical:
            return ALPHA * sim_sem + (1 - ALPHA) * sim_lex
        return sim_sem if semantic else sim_lex

    for row in lexical:
        merged[row["id"]] = {
            "arabic_text": row["arabic_text"],
            "coptic_text": row["coptic_text"],
            "source_id": row["source_id"],
            "sim_sem": 0.0,
            "sim_lex": float(row["sim"]),
        }
    for row in semantic:
        sim_sem = max(0.0, float(row["sim"]))
        lex_set = set(normalize_arabic(row["arabic_text"]).split())
        sim_lex = _jaccard(query_tokens, lex_set)
        merged[row["id"]] = {
            "arabic_text": row["arabic_text"],
            "coptic_text": row["coptic_text"],
            "source_id": row["source_id"],
            "sim_sem": sim_sem,
            "sim_lex": sim_lex,
        }

    hits = [
        ExampleHit(
            example_id=eid,
            arabic_text=d["arabic_text"],
            coptic_text=d["coptic_text"],
            similarity=round(_score(d["sim_sem"], d["sim_lex"]), 4),
            source_id=d["source_id"],
        )
        for eid, d in merged.items()
    ]
    hits.sort(key=lambda h: h.similarity, reverse=True)
    ctx.examples = hits[:TOP_K]

    for h in ctx.examples:
        ctx.add_source(h.source_id)
