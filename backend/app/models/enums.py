"""Shared Python enums mirrored by PostgreSQL ENUM types in migrations.

Keeping them as Python enums gives type-safety in the pipeline while Alembic
creates the matching DB type. See `alembic/versions/...` for the SQL side.
"""
from __future__ import annotations

import enum


class Role(str, enum.Enum):
    user = "user"
    reviewer = "reviewer"
    admin = "admin"


class DialectCode(str, enum.Enum):
    bohairic = "bohairic"
    sahidic = "sahidic"
    fayyumic = "fayyumic"
    akhmimic = "akhmimic"
    lycopolitan = "lycopolitan"


class PartOfSpeech(str, enum.Enum):
    noun = "noun"
    verb = "verb"
    adjective = "adjective"
    pronoun = "pronoun"
    preposition = "preposition"
    conjunction = "conjunction"
    adverb = "adverb"
    numeral = "numeral"
    article = "article"
    interjection = "interjection"
    particle = "particle"
    other = "other"


class LanguageOfOrigin(str, enum.Enum):
    egyptian = "egyptian"
    greek = "greek"
    loanword = "loanword"


class SourceType(str, enum.Enum):
    dictionary = "dictionary"
    corpus = "corpus"
    academic_paper = "academic_paper"
    user_submission = "user_submission"
    other = "other"
    book = "book"
    manuscript = "manuscript"
    paper = "paper"
    website = "website"
    lexicon = "lexicon"
    bible = "bible"


class RecordStatus(str, enum.Enum):
    """Status for dictionary entries, senses, examples, grammar rules."""

    draft = "draft"
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    needs_revision = "needs_revision"


class InputType(str, enum.Enum):
    word = "word"
    sentence = "sentence"


class TranslationStatus(str, enum.Enum):
    queued = "queued"
    processing = "processing"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"
    draft = "draft"
    in_review = "in_review"
    approved = "approved"
    rejected = "rejected"


class MatchType(str, enum.Enum):
    exact = "exact"
    fuzzy = "fuzzy"
    none = "none"


class ReviewDecision(str, enum.Enum):
    approve = "approve"
    reject = "reject"
    request_changes = "request_changes"


class GrammarCategory(str, enum.Enum):
    word_order = "word_order"
    pronoun = "pronoun"
    tense = "tense"
    negation = "negation"
    determiner = "determiner"
    noun_phrase = "noun_phrase"
    preposition = "preposition"
    conjugation = "conjugation"
    other = "other"
