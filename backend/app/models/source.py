"""Source model: a documented reference (book, manuscript, lexicon...).

Every Coptic value should link to a source; without one it stays a draft.
"""
from __future__ import annotations

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import SourceType


class Source(Base):
    __tablename__ = "sources"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    type: Mapped[SourceType] = mapped_column(
        Enum(SourceType, name="source_type"), nullable=False, default=SourceType.book
    )
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    isbn: Mapped[str | None] = mapped_column(String(32), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    def __repr__(self) -> str:
        return f"<Source {self.title}>"
