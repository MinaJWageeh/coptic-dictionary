"""Stage 9: Pipeline orchestrator.

Coordinates the chain:
    normalizer → classify → (word|sentence) lookup → retrieve → grammar
              → compose → score → persist

The orchestrator returns a persisted TranslationResult plus the structured
context, so the API layer can build a fully-provenance response object.

All new results are saved with status='draft' (constraint C3).
"""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.enums import InputType
from app.models.translation import (
    TranslationExampleMatch,
    TranslationRequest,
    TranslationResult,
    TranslationWordMatch,
)
from app.pipeline.composer import compose
from app.pipeline.confidence import score
from app.pipeline.dictionary_lookup import lookup_tokens, lookup_word
from app.pipeline.example_retriever import retrieve_examples
from app.pipeline.grammar_engine import run_grammar
from app.pipeline.normalizer import normalize_arabic, tokenize
from app.pipeline.types import PipelineContext
from app.services.embedding_service import embed as embed_fn


def run(raw_input: str, db: Session, *, dialect: str = "bohairic",
        user_id: int | None = None) -> dict[str, Any]:
    """Run the full pipeline and persist the result. Returns structured data."""
    # --- Stage 1: normalize + classify ---
    normalized = normalize_arabic(raw_input)
    tokens = tokenize(normalized)
    input_type = InputType.word if len(tokens) <= 1 else InputType.sentence

    ctx = PipelineContext(
        raw_input=raw_input,
        normalized_input=normalized,
        tokens=tokens or [normalized],
        input_type=input_type.value,  # type: ignore[arg-type]
        dialect=dialect,
    )

    stages_log: list[str] = ["normalize", "classify"]

    # --- Stage 2/3a: single word -> dictionary only (constraint C1) ---
    if input_type == InputType.word:
        match = lookup_word(db, ctx.tokens[0], dialect)
        match.token = ctx.tokens[0]
        ctx.token_matches = [match]
        if match.found and match.source_id:
            ctx.add_source(match.source_id)
        stages_log.append("word_lookup")
    else:
        # --- Stage 4: token-level dictionary lookup ---
        lookup_tokens(ctx, db)
        stages_log.append("token_lookup")

        # --- Stage 5: example retrieval (RAG) ---
        retrieve_examples(ctx, db, embedding_fn=embed_fn)
        stages_log.append("example_retrieval")

        # --- Stage 6: grammar engine ---
        run_grammar(ctx, db)
        stages_log.append("grammar")

    # --- Stage 7: compose ---
    compose(ctx)
    stages_log.append("compose")

    # --- Stage 8: confidence ---
    score(ctx)
    stages_log.append("confidence")

    # --- Stage 9: persist as draft (constraint C3) ---
    result = _persist(ctx, db, user_id=user_id, stages=stages_log)

    return _to_response(result, db, ctx)


# --------------------------------------------------------------------------- #
# Persistence
# --------------------------------------------------------------------------- #
def _persist(ctx: PipelineContext, db: Session, *, user_id: int | None,
             stages: list[str]) -> TranslationResult:
    request = TranslationRequest(
        user_id=user_id,
        raw_input=ctx.raw_input,
        normalized_input=ctx.normalized_input,
        input_type=InputType(ctx.input_type),
        dialect_requested=ctx.dialect,
    )
    db.add(request)
    db.flush()  # get request.id

    result = TranslationResult(
        request_id=request.id,
        coptic_text=ctx.coptic_text,
        literal_meaning=ctx.literal_meaning,
        confidence=ctx.confidence,
        confidence_breakdown=ctx.breakdown,
        grammar_notes=ctx.grammar_notes_text or None,
        source_ids=list(ctx.source_ids),
        llm_used=ctx.llm_used,
        pipeline_stages=stages,
    )
    db.add(result)
    db.flush()

    for m in ctx.token_matches:
        db.add(
            TranslationWordMatch(
                result_id=result.id,
                token=m.token,
                entry_id=m.entry_id,
                sense_id=m.sense_id,
                coptic_output=m.coptic_word,
            )
        )
    for h in ctx.examples:
        db.add(
            TranslationExampleMatch(
                result_id=result.id,
                example_id=h.example_id,
                similarity=h.similarity,
            )
        )
    db.commit()
    db.refresh(result)
    return result


# --------------------------------------------------------------------------- #
# Response shaping
# --------------------------------------------------------------------------- #
def _to_response(result: TranslationResult, db: Session,
                 ctx: PipelineContext) -> dict[str, Any]:
    from app.models.source import Source

    words = []
    for m in ctx.token_matches:
        words.append(
            {
                "token": m.token,
                "coptic_word": m.coptic_word,
                "transliteration": m.transliteration,
                "arabic_gloss": m.arabic_gloss,
                "literal_meaning": m.literal_meaning,
                "part_of_speech": m.part_of_speech,
                "found": m.found,
                "match_type": m.match_type.value,
                "candidates": m.candidates,
            }
        )

    examples = [
        {
            "example_id": h.example_id,
            "arabic_text": h.arabic_text,
            "coptic_text": h.coptic_text,
            "similarity": h.similarity,
        }
        for h in ctx.examples
    ]

    sources = []
    if ctx.source_ids:
        src_rows = db.query(Source).filter(Source.id.in_(ctx.source_ids)).all()
        sources = [
            {"id": s.id, "title": s.title, "author": s.author, "year": s.year}
            for s in src_rows
        ]

    return {
        "result_id": result.id,
        "request_id": result.request_id,
        "input_type": ctx.input_type,
        "dialect": ctx.dialect,
        "coptic_text": result.coptic_text,
        "literal_meaning": result.literal_meaning,
        "confidence": float(result.confidence),
        "confidence_breakdown": result.confidence_breakdown,
        "grammar_notes": result.grammar_notes,
        "llm_used": result.llm_used,
        "status": result.status.value,
        "source_ids": result.source_ids,
        "pipeline_stages": result.pipeline_stages,
        "words": words,
        "similar_examples": examples,
        "sources": sources,
    }


def db_fetch_sources(cls) -> list:  # pragma: no cover - kept for backward import safety
    return []
