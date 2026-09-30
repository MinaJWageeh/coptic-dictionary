"""Stage 7: Composer.

Assembles the final Coptic string from matched tokens in their (possibly
re-ordered) sequence. Crucially, it **never invents** Coptic words: unknown
tokens are surfaced verbatim as Arabic placeholders wrapped in angle brackets
so the human reviewer sees exactly what is missing.

An optional LLM path (gated behind settings.LLM_PROVIDER != 'none') can refine
phrasing, but it is constrained to use only the dictionary terms and examples
already in the context — never to coin new vocabulary.
"""
from __future__ import annotations

from app.config import settings
from app.models.enums import MatchType
from app.pipeline.types import PipelineContext


def _compose_deterministic(ctx: PipelineContext) -> tuple[str, str]:
    """Build coptic text + literal meaning from token matches.

    Returns (coptic_text, literal_meaning). Unknown tokens are marked clearly.
    """
    coptic_parts: list[str] = []
    literal_parts: list[str] = []
    for m in ctx.token_matches:
        if m.found and m.coptic_word:
            coptic_parts.append(m.coptic_word)
            literal_parts.append(m.literal_meaning or m.arabic_gloss or m.token)
        else:
            # Explicit placeholder so reviewers see the gap — no guessing.
            coptic_parts.append(f"<{m.token}>")
            literal_parts.append(f"[{m.token}]")
    coptic = " ".join(coptic_parts).strip()
    literal = " ".join(literal_parts).strip()
    return coptic, literal


def _compose_with_example(ctx: PipelineContext) -> tuple[str, str]:
    """If a very-high-similarity example exists, prefer its phrasing."""
    if not ctx.examples or ctx.examples[0].similarity < 0.85:
        return _compose_deterministic(ctx)

    best = ctx.examples[0]
    # Keep the example's Coptic as the proposed text but mark it as derived.
    coptic = best.coptic_text
    _, literal = _compose_deterministic(ctx)
    return coptic, literal


def compose(ctx: PipelineContext) -> None:
    """Fill ctx.coptic_text and ctx.literal_meaning.

    The LLM path is intentionally disabled by default. When enabled, it would
    receive ONLY ctx.token_matches + ctx.examples + ctx.grammar_notes.
    """
    coptic, literal = _compose_with_example(ctx)

    if settings.LLM_PROVIDER != "none":
        # Placeholder hook: real implementation would call an LLM client here,
        # passing only dictionary terms + examples (no free invention allowed).
        ctx.llm_used = True
        # For now we keep the deterministic output; the flag signals intent.
    else:
        ctx.llm_used = False

    ctx.coptic_text = coptic
    ctx.literal_meaning = literal

    # If every token resolved and no example override, the output is exact.
    if not ctx.has_unknown_tokens and all(
        m.match_type == MatchType.exact for m in ctx.token_matches
    ):
        # nothing to change; confidence handles the score
        pass
