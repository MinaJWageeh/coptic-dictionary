from __future__ import annotations

from sqlalchemy import Boolean, Enum, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.db_types import PortableVector
from app.models.enums import RecordStatus


class GrammarRule(Base):
    __tablename__ = "grammar_rules"

    dialect_id: Mapped[int | None] = mapped_column(ForeignKey("dialects.id"), nullable=True, index=True)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    rule_code: Mapped[str | None] = mapped_column(String(120), unique=True, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    description_embedding: Mapped[list[float] | None] = mapped_column(PortableVector(), nullable=True)
    pattern: Mapped[str | None] = mapped_column(Text, nullable=True)
    replacement: Mapped[str | None] = mapped_column(Text, nullable=True)
    examples: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    priority: Mapped[int] = mapped_column(default=100, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    review_status: Mapped[RecordStatus] = mapped_column(
        Enum(RecordStatus, name="grammar_rule_review_status"),
        default=RecordStatus.pending,
        nullable=False,
        index=True,
    )
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
