from __future__ import annotations

from sqlalchemy import Enum, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.db_types import PortableVector
from app.models.enums import RecordStatus


class CorpusText(Base):
    __tablename__ = "corpus_texts"

    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), nullable=False, index=True)
    dialect_id: Mapped[int | None] = mapped_column(ForeignKey("dialects.id"), nullable=True, index=True)
    language: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_status: Mapped[RecordStatus] = mapped_column(
        Enum(RecordStatus, name="corpus_review_status"),
        default=RecordStatus.pending,
        nullable=False,
        index=True,
    )
    extra_metadata: Mapped[dict] = mapped_column("metadata", JSON, default=dict, nullable=False)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    segments: Mapped[list["ParallelSegment"]] = relationship(
        back_populates="corpus_text", cascade="all, delete-orphan"
    )


class ParallelSegment(Base):
    __tablename__ = "parallel_segments"

    corpus_text_id: Mapped[int | None] = mapped_column(
        ForeignKey("corpus_texts.id"), nullable=True, index=True
    )
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), nullable=False, index=True)
    dialect_id: Mapped[int | None] = mapped_column(ForeignKey("dialects.id"), nullable=True, index=True)
    segment_order: Mapped[int | None] = mapped_column(nullable=True)
    arabic_text: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    coptic_text: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)
    normalized_arabic_text: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)
    normalized_coptic_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    alignment_score: Mapped[float | None] = mapped_column(nullable=True)
    arabic_embedding: Mapped[list[float] | None] = mapped_column(PortableVector(), nullable=True)
    coptic_embedding: Mapped[list[float] | None] = mapped_column(PortableVector(), nullable=True)
    sentence_embedding: Mapped[list[float] | None] = mapped_column(PortableVector(), nullable=True)
    review_status: Mapped[RecordStatus] = mapped_column(
        Enum(RecordStatus, name="parallel_segment_review_status"),
        default=RecordStatus.pending,
        nullable=False,
        index=True,
    )
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    corpus_text: Mapped[CorpusText | None] = relationship(back_populates="segments")


Example = ParallelSegment
ExampleCitation = CorpusText
