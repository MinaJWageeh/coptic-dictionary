"""SQLAlchemy models. Each module registers its tables on the shared Base."""
from app.models.audit import AuditLog
from app.models.dictionary import (
    ArabicIndex,
    ArabicSense,
    Dialect,
    DictionaryEntry,
    DictionarySense,
    SenseMapping,
)
from app.models.examples import CorpusText, Example, ExampleCitation, ParallelSegment
from app.models.grammar import GrammarRule
from app.models.identity import RefreshToken, RoleRecord, User, UserRole
from app.models.review import Review, TranslationReview
from app.models.source import Source
from app.models.translation import (
    TranslationCandidate,
    TranslationExampleMatch,
    TranslationRequest,
    TranslationResult,
    TranslationWordMatch,
)

__all__ = [
    "ArabicIndex",
    "ArabicSense",
    "AuditLog",
    "CorpusText",
    "Dialect",
    "DictionaryEntry",
    "DictionarySense",
    "Example",
    "ExampleCitation",
    "GrammarRule",
    "RefreshToken",
    "Review",
    "RoleRecord",
    "SenseMapping",
    "Source",
    "ParallelSegment",
    "TranslationCandidate",
    "TranslationReview",
    "TranslationExampleMatch",
    "TranslationRequest",
    "TranslationResult",
    "TranslationWordMatch",
    "User",
    "UserRole",
]
