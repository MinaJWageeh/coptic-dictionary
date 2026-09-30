"""Embedding service: wraps a sentence-transformers model lazily.

The model is loaded once and cached. Loading is guarded so the rest of the
application works without it (e.g. in tests or lightweight dev).
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.config import settings


@lru_cache(maxsize=1)
def get_model() -> Any | None:
    """Load and cache the embedding model, or None if disabled/unavailable."""
    if not settings.EMBEDDING_ENABLED:
        return None
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        return None
    try:
        return SentenceTransformer(settings.EMBEDDING_MODEL)
    except Exception:
        return None


def embed(text: str) -> list[float] | None:
    """Return an embedding vector for `text`, or None if unavailable."""
    model = get_model()
    if model is None:
        return None
    try:
        import numpy as np

        vec = model.encode([text], normalize_embeddings=True)[0]
        return np.asarray(vec).tolist()
    except Exception:
        return None
