"""Stage 8: Confidence scorer.

Combines weighted signals into a single score in [0, 1] and stores the
breakdown so the UI can explain *why* the score is what it is.

Signals:
  - token_coverage : fraction of input tokens found in the dictionary
  - example_similarity : best similarity to a corpus example
  - grammar_coverage : fraction of expected grammar categories applied
  - penalties : LLM usage (lower trust), few/zero sources

Weights are documented constants, tunable without code changes later.
"""
from __future__ import annotations

from app.pipeline.types import PipelineContext

# Documented weights (sum of positive weights ~= 1.0 before penalties).
W_COVERAGE = 0.4
W_EXAMPLE = 0.4
W_GRAMMAR = 0.2
PENALTY_LLM = 0.15
PENALTY_NO_SOURCE = 0.25
MIN_CONFIDENCE = 0.0
MAX_CONFIDENCE = 1.0


def score(ctx: PipelineContext) -> None:
    coverage = ctx.coverage
    example_sim = ctx.examples[0].similarity if ctx.examples else 0.0
    grammar_cov = _grammar_coverage(ctx)

    base = (
        W_COVERAGE * coverage
        + W_EXAMPLE * example_sim
        + W_GRAMMAR * grammar_cov
    )

    penalty = 0.0
    if ctx.llm_used:
        penalty += PENALTY_LLM
    if not ctx.source_ids:
        penalty += PENALTY_NO_SOURCE

    # Unknown tokens in the output cap the score hard.
    if ctx.has_unknown_tokens:
        penalty += 0.2 * (1 - coverage)

    confidence = max(MIN_CONFIDENCE, min(MAX_CONFIDENCE, base - penalty))

    ctx.confidence = round(confidence, 3)
    ctx.breakdown = {
        "token_coverage": round(coverage, 3),
        "example_similarity": round(example_sim, 3),
        "grammar_coverage": round(grammar_cov, 3),
        "base_score": round(base, 3),
        "penalty": round(penalty, 3),
        "llm_used": float(ctx.llm_used),
        "source_count": float(len(ctx.source_ids)),
    }


def _grammar_coverage(ctx: PipelineContext) -> float:
    """Heuristic: how many of the relevant grammar categories fired.

    We count applied notes over an expected set. If no notes at all, return a
    neutral mid value (the sentence may simply be nominal with no rules to
    apply, which is fine).
    """
    if not ctx.grammar_notes:
        return 0.5
    applied = sum(1 for n in ctx.grammar_notes if n.applied)
    return min(1.0, applied / 3.0)


def confidence_label(score_value: float) -> str:
    """Map a numeric score to an Arabic qualitative label."""
    if score_value >= 0.85:
        return "عالية"
    if score_value >= 0.6:
        return "متوسطة"
    return "منخفضة"
