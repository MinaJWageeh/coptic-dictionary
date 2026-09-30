"""Database engine, session, and declarative base.

Uses PostgreSQL with the `pgvector` extension. A custom base class adds common
columns (id, timestamps, soft-delete) to every table.
"""
from __future__ import annotations

from collections.abc import Generator
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, create_engine, func
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    """Declarative base with shared columns for all models."""

    metadata: Any  # type: ignore[assignment]

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )


engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=not settings.is_production,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, class_=Session)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a scoped DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_extensions(db: Session) -> None:
    """Create required PostgreSQL extensions (pgvector, pg_trgm)."""
    from sqlalchemy import text

    db.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    db.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
    db.execute(text("CREATE EXTENSION IF NOT EXISTS citext"))
    db.commit()
