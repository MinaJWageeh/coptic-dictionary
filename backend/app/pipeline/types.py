"""Typed data structures shared across pipeline stages.

Using dataclasses keeps each stage composable and testable in isolation,
without touching the ORM or the HTTP layer.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from app.models.enums import MatchType


@dataclass
class TokenMatch:
    """Result of looking up a single token in the dictionary."""

    token: str
    normalized: str
    entry_id: int | None = None
    sense_id: int | None = None
    coptic_word: str | None = None
    transliteration: str | None = None
    arabic_gloss: str | None = None
    literal_meaning: str | None = None
    part_of_speech: str | None = None
    source_id: int | None = None
    match_type: MatchType = MatchType.none
    candidates: list[dict] = field(default_factory=list)

    @property
    def found(self) -> bool:
        return self.match_type != MatchType.none and self.entry_id is not None


@dataclass
class ExampleHit:
    """A retrieved corpus example with its similarity score."""

    example_id: int
    arabic_text: str
    coptic_text: str
    similarity: float
    source_id: int | None = None


@dataclass
class GrammarApplication:
    """A grammar rule that was applied, with explanation."""

    rule_name: str
    category: str
    explanation: str
    applied: bool = True


@dataclass
class PipelineContext:
    """Mutable context threaded through all pipeline stages."""

    raw_input: str
    normalized_input: str
    tokens: list[str]
    input_type: Literal["word", "sentence"]
    dialect: str = "bohairic"

    token_matches: list[TokenMatch] = field(default_factory=list)
    examples: list[ExampleHit] = field(default_factory=list)
    grammar_notes: list[GrammarApplication] = field(default_factory=list)

    coptic_text: str = ""
    literal_meaning: str = ""
    grammar_notes_text: str = ""
    source_ids: list[int] = field(default_factory=list)
    llm_used: bool = False

    # confidence breakdown (filled by the scorer)
    confidence: float = 0.0
    breakdown: dict[str, float] = field(default_factory=dict)

    def add_source(self, source_id: int | None) -> None:
        if source_id and source_id not in self.source_ids:
            self.source_ids.append(source_id)

    @property
    def coverage(self) -> float:
        """Fraction of tokens found in the dictionary."""
        if not self.tokens:
            return 0.0
        found = sum(1 for m in self.token_matches if m.found)
        return found / len(self.tokens)

    @property
    def has_unknown_tokens(self) -> bool:
        return any(not m.found for m in self.token_matches)
