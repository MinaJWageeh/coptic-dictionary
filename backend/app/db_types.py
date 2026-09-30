from __future__ import annotations

import json
from typing import Any

from sqlalchemy import JSON
from sqlalchemy.types import TypeDecorator


class PortableVector(TypeDecorator[list[float] | None]):
    """Use pgvector on PostgreSQL and JSON storage in lightweight test DBs."""

    impl = JSON
    cache_ok = True

    def __init__(self, dimensions: int = 384) -> None:
        super().__init__()
        self.dimensions = dimensions

    def load_dialect_impl(self, dialect):  # noqa: ANN001
        if dialect.name == "postgresql":
            from pgvector.sqlalchemy import Vector

            return dialect.type_descriptor(Vector(self.dimensions))
        return dialect.type_descriptor(JSON())

    def process_bind_param(self, value: Any, dialect):  # noqa: ANN001
        if value is None or dialect.name == "postgresql":
            return value
        if isinstance(value, str):
            return json.loads(value)
        return list(value)
