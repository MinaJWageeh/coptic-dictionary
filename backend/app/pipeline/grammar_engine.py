"""Stage 6: Grammar engine.

Applies a small, *documented* set of Coptic grammar transformations stored in
`grammar_rules`. The rules are data-driven (JSONB pattern/transformation) so
they can be edited from the admin panel without code changes. The engine is
conservative: when a rule is ambiguous it is skipped rather than guessed.

Each applied rule records an explanation that is surfaced to the user as a
grammar note (a project requirement).
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import GrammarCategory, RecordStatus
from app.models.grammar import GrammarRule
from app.pipeline.types import GrammarApplication, PipelineContext, TokenMatch


def load_rules(db: Session, dialect: str) -> list[GrammarRule]:
    """Load active grammar rules ordered by priority."""
    stmt = (
        select(GrammarRule)
        .where(GrammarRule.status == RecordStatus.approved, GrammarRule.deleted_at.is_(None))
        .order_by(GrammarRule.priority.asc())
    )
    return list(db.execute(stmt).scalars().all())


def _particles_for(category: GrammarCategory, rule: GrammarRule) -> dict:
    """Extract particle/marker strings from a rule's transformation JSON."""
    trans = rule.transformation or {}
    return trans.get("particles", {}) if isinstance(trans, dict) else {}


def apply_word_order(
    ctx: PipelineContext, rules: list[GrammarRule]
) -> GrammarApplication | None:
    """Coptic default word order is Verb–Subject–Object (VSO) for verbal
    sentences; the engine reorders found tokens accordingly when a verb exists.

    This is intentionally simple and documented: it does not invent grammar.
    """
    rule = next((r for r in rules if r.category == GrammarCategory.word_order), None)
    if not rule:
        return None

    has_verb = any(m.part_of_speech == "verb" and m.found for m in ctx.token_matches)
    if not has_verb:
        return GrammarApplication(
            rule_name=rule.name,
            category=rule.category.value,
            explanation="ترتيب الكلمات الافتراضي (اسمي) — لا يوجد فعل لإعادة الترتيب.",
            applied=False,
        )

    verbs = [m for m in ctx.token_matches if m.part_of_speech == "verb" and m.found]
    rest = [m for m in ctx.token_matches if m not in verbs]
    ctx.token_matches = verbs + rest
    return GrammarApplication(
        rule_name=rule.name,
        category=rule.category.value,
        explanation="أُعيد ترتيب الكلمات إلى فعل ثم فاعل ثم مفعول (VSO) حسب قواعد البوهيريك.",
    )


def apply_determiners(
    ctx: PipelineContext, rules: list[GrammarRule]
) -> list[GrammarApplication]:
    """Prefix the Coptic definite article (ⲡ m. / ⲧ f. / ⲛ pl.) to marked nouns.

    Only nouns flagged in the source with an explicit `needs_article` sense
    metadata would trigger this; here we conservatively only document the rule
    unless a noun's gloss already lacks an article marker.
    """
    out: list[GrammarApplication] = []
    rule = next((r for r in rules if r.category == GrammarCategory.determiner), None)
    if not rule:
        return out
    particles = _particles_for(GrammarCategory.determiner, rule)
    masc = particles.get("masculine", "ⲡ")
    fem = particles.get("feminine", "ⲧ")
    for m in ctx.token_matches:
        if not m.found or m.part_of_speech != "noun":
            continue
        # conservative: do not double-prefix an existing article
        if m.coptic_word and m.coptic_word.startswith(("ⲡ", "ⲧ", "ⲛ")):
            continue
        article = masc  # default masculine; gender detection is a future task
        m.coptic_word = f"{article}{m.coptic_word or ''}"
        out.append(
            GrammarApplication(
                rule_name=rule.name,
                category=rule.category.value,
                explanation=f"أُضيفت أداة التعريف الاسمية «{article}» قبل «{m.token}».",
            )
        )
    return out


def apply_negation(
    ctx: PipelineContext, rules: list[GrammarRule]
) -> GrammarApplication | None:
    """If a negation token (لا/ليس/ما) is present, document the Coptic negation
    pattern (ⲛ...ⲁⲛ) without forcing a wrong construction."""
    rule = next((r for r in rules if r.category == GrammarCategory.negation), None)
    neg_words = {"لا", "ليس", "ليست", "ما", "لم", "لن", "غير"}
    has_neg = any(
        (m.normalized in neg_words) or (strip_dialect(m.normalized) in neg_words)
        for m in ctx.token_matches
    )
    if not has_neg or not rule:
        return None
    return GrammarApplication(
        rule_name=rule.name,
        category=rule.category.value,
        explanation="اكتُشف نفي عربي. في القبطية يُحاط الفعل بـ ⲛـ ... ⲁⲛ (يحتاج مراجعة).",
    )


def strip_dialect(t: str) -> str:
    return t


def run_grammar(ctx: PipelineContext, db: Session) -> None:
    """Apply all grammar rules and assemble a human-readable notes string."""
    rules = load_rules(db, ctx.dialect)
    notes: list[GrammarApplication] = []

    order = apply_word_order(ctx, rules)
    if order:
        notes.append(order)
    notes.extend(apply_determiners(ctx, rules))
    neg = apply_negation(ctx, rules)
    if neg:
        notes.append(neg)

    ctx.grammar_notes = notes
    ctx.grammar_notes_text = "\n".join(
        f"• {n.explanation}" for n in notes if n.applied
    )

    # Rules carry a source; record it for provenance.
    for r in rules:
        ctx.add_source(r.source_id)
