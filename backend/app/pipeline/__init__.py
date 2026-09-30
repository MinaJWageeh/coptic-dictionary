"""Translation pipeline package.

The pipeline is a chain of pure(ish) stages orchestrated by `orchestrator.py`.
Each stage produces a typed context object consumed by the next, and all emit
signals used by the confidence scorer.
"""
from app.pipeline.types import PipelineContext, TokenMatch

__all__ = ["PipelineContext", "TokenMatch"]
