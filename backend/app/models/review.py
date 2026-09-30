from __future__ import annotations

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import RecordStatus


class TranslationReview(Base):
    __tablename__ = "translation_reviews"

    translation_candidate_id: Mapped[int] = mapped_column(
        ForeignKey("translation_candidates.id"), nullable=False, index=True
    )
    reviewer_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    review_status: Mapped[RecordStatus] = mapped_column(
        Enum(RecordStatus, name="translation_review_status"), nullable=False, index=True
    )
    rating: Mapped[int | None] = mapped_column(nullable=True)
    corrected_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    translation_candidate: Mapped["TranslationCandidate"] = relationship(back_populates="reviews")


Review = TranslationReview
