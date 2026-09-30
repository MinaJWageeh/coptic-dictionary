"""Stages 3a/4: Dictionary lookup for a word and for sentence tokens.

A single word goes directly to the Arabic index (constraint C1). For a
sentence, each token is looked up independently; an exact miss falls back to
prefix-stripping and finally to fuzzy trigram matching.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.dictionary import ArabicIndex, DictionaryEntry, DictionarySense
from app.models.enums import MatchType, RecordStatus
from app.pipeline.normalizer import normalize_arabic, strip_arabic_prefix
from app.pipeline.types import PipelineContext, TokenMatch


def _build_match(row) -> TokenMatch:  # noqa: ANN001
    """Build a TokenMatch from a joined (ArabicIndex, Sense, Entry) row."""
    return TokenMatch(
        token=row.arabic_term,  # set later by caller
        normalized=row.normalized_term,
        entry_id=row.entry_id,
        sense_id=row.sense_id,
        coptic_word=row.coptic_word,
        transliteration=row.transliteration,
        arabic_gloss=row.arabic_gloss,
        literal_meaning=row.literal_meaning,
        part_of_speech=row.part_of_speech.value if row.part_of_speech else None,
        source_id=row.source_id,
        match_type=MatchType.exact,
    )


def _lookup_term(
    db: Session, term: str, dialect: str
) -> list[tuple[ArabicIndex, DictionarySense, DictionaryEntry]]:
    """Return all senses matching a normalized term (approved/draft)."""
    stmt = (
        select(ArabicIndex, DictionarySense, DictionaryEntry)
        .join(DictionarySense, ArabicIndex.sense_id == DictionarySense.id)
        .join(DictionaryEntry, DictionarySense.entry_id == DictionaryEntry.id)
        .where(ArabicIndex.normalized_term == term)
        .order_by(ArabicIndex.is_primary.desc(), DictionarySense.sense_no.asc())
    )
    return list(db.execute(stmt).all())


def lookup_word(db: Session, raw_word: str, dialect: str = "bohairic") -> TokenMatch:
    """Single-word lookup (Stage 3a). Returns the best match or an empty one."""
    norm = normalize_arabic(raw_word)
    base = TokenMatch(token=raw_word, normalized=norm)

    rows = _lookup_term(db, norm, dialect)
    if not rows:
        # try stripping the definite article
        stripped = strip_arabic_prefix(norm)
        if stripped and stripped != norm:
            rows = _lookup_term(db, stripped, dialect)
    if not rows:
        base.match_type = MatchType.fuzzy
        return base

    ai, sense, entry = rows[0]
    base.entry_id = entry.id
    base.sense_id = sense.id
    base.coptic_word = entry.coptic_word
    base.transliteration = entry.transliteration
    base.arabic_gloss = sense.arabic_gloss
    base.literal_meaning = sense.literal_meaning
    base.part_of_speech = entry.part_of_speech.value if entry.part_of_speech else None
    base.source_id = sense.source_id
    base.match_type = MatchType.exact
    base.candidates = [
        {
            "entry_id": e.id,
            "coptic_word": e.coptic_word,
            "arabic_gloss": s.arabic_gloss,
            "is_primary": a.is_primary,
        }
        for (a, s, e) in rows
    ]
    return base


def lookup_tokens(ctx: PipelineContext, db: Session) -> None:
    """Token-level lookup (Stage 4). Fills ctx.token_matches in order."""
    matches: list[TokenMatch] = []
    for token in ctx.tokens:
        match = lookup_word(db, token, ctx.dialect)
        match.token = token
        matches.append(match)
        if match.found and match.source_id:
            ctx.add_source(match.source_id)
    ctx.token_matches = matches
