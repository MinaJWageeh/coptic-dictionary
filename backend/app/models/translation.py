from __future__ import annotations

from sqlalchemy import Enum, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import RecordStatus, TranslationStatus


class TranslationRequest(Base):
    __tablename__ = "translation_requests"

    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    source_language: Mapped[str] = mapped_column(String(20), default="ar", nullable=False)
    target_dialect_id: Mapped[int | None] = mapped_column(
        ForeignKey("dialects.id"), nullable=True, index=True
    )
    input_text: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    normalized_input_text: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)
    context: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[TranslationStatus] = mapped_column(
        Enum(TranslationStatus, name="translation_request_status"),
        default=TranslationStatus.queued,
        nullable=False,
        index=True,
    )
    requested_model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    extra_metadata: Mapped[dict] = mapped_column("metadata", JSON, default=dict, nullable=False)

    candidates: Mapped[list["TranslationCandidate"]] = relationship(
        back_populates="translation_request", cascade="all, delete-orphan"
    )


class TranslationCandidate(Base):
    __tablename__ = "translation_candidates"

    translation_request_id: Mapped[int] = mapped_column(
        ForeignKey("translation_requests.id"), nullable=False, index=True
    )
    candidate_text: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)
    normalized_candidate_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    dialect_id: Mapped[int | None] = mapped_column(ForeignKey("dialects.id"), nullable=True, index=True)
    generated_by: Mapped[str] = mapped_column(String(40), default="ai", nullable=False)
    model_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    rank: Mapped[int] = mapped_column(default=1, nullable=False)
    confidence: Mapped[float | None] = mapped_column(nullable=True)
    evidence: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    review_status: Mapped[RecordStatus] = mapped_column(
        Enum(RecordStatus, name="translation_candidate_review_status"),
        default=RecordStatus.draft,
        nullable=False,
        index=True,
    )

    translation_request: Mapped[TranslationRequest] = relationship(back_populates="candidates")
    reviews: Mapped[list["TranslationReview"]] = relationship(
        back_populates="translation_candidate", cascade="all, delete-orphan"
    )


TranslationResult = TranslationCandidate
TranslationExampleMatch = TranslationCandidate
TranslationWordMatch = TranslationCandidate
