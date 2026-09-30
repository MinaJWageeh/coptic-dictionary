from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections import OrderedDict
from math import sqrt

from app.config import settings
from app.services.text import normalize_arabic

logger = logging.getLogger(__name__)


class BaseEmbeddingProvider(ABC):
    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        """Generate embedding vector for a single text."""
        ...

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of texts."""
        return [self.embed_text(t) for t in texts]


class DeterministicEmbeddingProvider(BaseEmbeddingProvider):
    """High-performance deterministic embedding provider.

    Produces dense 384-dimensional normalized vectors based on character and
    character-trigram buckets. It is zero-dependency, ultra-fast, and compatible
    with pgvector dimensions for dev/testing.
    """

    def embed_text(self, text: str) -> list[float]:
        dim = settings.EMBEDDING_DIM
        vector = [0.0] * dim
        normalized = normalize_arabic(text or "")
        if not normalized:
            return vector

        # 1. Unigram character distribution
        for index, char in enumerate(normalized):
            primary_bucket = (ord(char) + index) % dim
            secondary_bucket = (ord(char) * 31) % dim
            vector[primary_bucket] += 1.0
            vector[secondary_bucket] += 0.5

        # 2. Character trigram distribution for subword/morphological capture
        if len(normalized) >= 3:
            for i in range(len(normalized) - 2):
                tri = normalized[i : i + 3]
                tri_hash = (ord(tri[0]) * 1013 + ord(tri[1]) * 107 + ord(tri[2])) % dim
                vector[tri_hash] += 0.8

        norm = sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [round(value / norm, 6) for value in vector]


class SentenceTransformerEmbeddingProvider(BaseEmbeddingProvider):
    """Multilingual dense transformer embedding provider.

    Uses models such as 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
    to compute cross-lingual semantic representations.
    """

    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self._model = None
        self._load_error = False

    def _ensure_model(self):
        if self._model is None and not self._load_error:
            try:
                from sentence_transformers import SentenceTransformer

                logger.info("Loading multilingual embedding model: %s", self.model_name)
                self._model = SentenceTransformer(self.model_name)
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Could not load SentenceTransformer (%s). Falling back to deterministic provider: %s",
                    self.model_name,
                    exc,
                )
                self._load_error = True
        return self._model

    def embed_text(self, text: str) -> list[float]:
        model = self._ensure_model()
        if model is None:
            return DeterministicEmbeddingProvider().embed_text(text)

        norm_text = normalize_arabic(text or "")
        vec = model.encode(norm_text, normalize_embeddings=True)
        return [round(float(v), 6) for v in vec]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        model = self._ensure_model()
        if model is None:
            return DeterministicEmbeddingProvider().embed_batch(texts)

        norm_texts = [normalize_arabic(t or "") for t in texts]
        vecs = model.encode(norm_texts, normalize_embeddings=True)
        return [[round(float(v), 6) for v in row] for row in vecs]


class LRUEmbeddingCache:
    """Bounded LRU memory cache for text embeddings."""

    def __init__(self, maxsize: int = 4096) -> None:
        self.maxsize = maxsize
        self._cache: OrderedDict[str, list[float]] = OrderedDict()

    def get(self, key: str) -> list[float] | None:
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        return None

    def set(self, key: str, value: list[float]) -> None:
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = value
        if len(self._cache) > self.maxsize:
            self._cache.popitem(last=False)

    def clear(self) -> None:
        self._cache.clear()


class EmbeddingManager:
    """Coordinates embedding providers with automatic fallback and caching."""

    def __init__(self) -> None:
        self._deterministic = DeterministicEmbeddingProvider()
        self._ml_provider = None
        self._cache = LRUEmbeddingCache(maxsize=4096)

    def get_provider(self) -> BaseEmbeddingProvider:
        if not settings.EMBEDDING_ENABLED:
            return self._deterministic

        # In testing or dev environment where sentence_transformers is not explicitly enforced,
        # prefer fast deterministic provider unless ML model is requested
        if settings.is_testing:
            return self._deterministic

        if self._ml_provider is None:
            self._ml_provider = SentenceTransformerEmbeddingProvider(settings.EMBEDDING_MODEL)
        return self._ml_provider

    def embed_text(self, text: str) -> list[float]:
        normalized = normalize_arabic(text or "").strip()
        if not normalized:
            return [0.0] * settings.EMBEDDING_DIM

        cached = self._cache.get(normalized)
        if cached is not None:
            return cached

        provider = self.get_provider()
        vector = provider.embed_text(normalized)
        self._cache.set(normalized, vector)
        return vector

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        provider = self.get_provider()
        return provider.embed_batch(texts)


# Global singleton manager
_EMBEDDING_MANAGER = EmbeddingManager()


def embed_text(text: str) -> list[float]:
    """Generates embedding vector for a given string."""
    return _EMBEDDING_MANAGER.embed_text(text)


def embed_batch(texts: list[str]) -> list[list[float]]:
    """Generates embedding vectors for a list of strings."""
    return _EMBEDDING_MANAGER.embed_batch(texts)


def cosine_similarity(left: list[float] | None, right: list[float] | None) -> float:
    """Computes cosine similarity between two vector lists."""
    if not left or not right or len(left) != len(right):
        return 0.0
    denominator = sqrt(sum(value * value for value in left)) * sqrt(
        sum(value * value for value in right)
    )
    if denominator == 0:
        return 0.0
    return round(sum(a * b for a, b in zip(left, right, strict=True)) / denominator, 4)
