from __future__ import annotations

from sqlalchemy import Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.db_types import PortableVector
from app.models.enums import PartOfSpeech, RecordStatus


class Dialect(Base):
    __tablename__ = "dialects"

    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    native_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)


class DictionaryEntry(Base):
    __tablename__ = "dictionary_entries"
    __table_args__ = (
        UniqueConstraint(
            "normalized_coptic_text",
            "dialect_id",
            "part_of_speech",
            "source_id",
            name="uq_dictionary_entry_identity",
        ),
    )

    coptic_text: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_coptic_text: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    transliteration: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    dialect_id: Mapped[int] = mapped_column(ForeignKey("dialects.id"), nullable=False, index=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), nullable=False, index=True)
    part_of_speech: Mapped[PartOfSpeech] = mapped_column(
        Enum(PartOfSpeech, name="part_of_speech"), nullable=False, index=True
    )
    gender: Mapped[str | None] = mapped_column(String(40), nullable=True)
    grammatical_number: Mapped[str | None] = mapped_column(String(40), nullable=True)
    root: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    example_sentence: Mapped[str | None] = mapped_column(Text, nullable=True)
    example_embedding: Mapped[list[float] | None] = mapped_column(PortableVector(), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_status: Mapped[RecordStatus] = mapped_column(
        Enum(RecordStatus, name="review_status"),
        default=RecordStatus.pending,
        nullable=False,
        index=True,
    )
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    dialect: Mapped[Dialect] = relationship()
    source: Mapped["Source"] = relationship()  # type: ignore[name-defined]
    mappings: Mapped[list["SenseMapping"]] = relationship(back_populates="dictionary_entry")


class ArabicSense(Base):
    __tablename__ = "arabic_senses"

    arabic_lemma: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    normalized_arabic_lemma: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    sense_key: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    definition_ar: Mapped[str] = mapped_column(Text, nullable=False)
    part_of_speech: Mapped[PartOfSpeech | None] = mapped_column(
        Enum(PartOfSpeech, name="arabic_sense_part_of_speech"), nullable=True, index=True
    )
    example_ar: Mapped[str | None] = mapped_column(Text, nullable=True)
    example_embedding: Mapped[list[float] | None] = mapped_column(PortableVector(), nullable=True)
    meaning_embedding: Mapped[list[float] | None] = mapped_column(PortableVector(), nullable=True)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"), nullable=True)
    review_status: Mapped[RecordStatus] = mapped_column(
        Enum(RecordStatus, name="arabic_sense_review_status"),
        default=RecordStatus.pending,
        nullable=False,
        index=True,
    )
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    mappings: Mapped[list["SenseMapping"]] = relationship(back_populates="arabic_sense")


class SenseMapping(Base):
    __tablename__ = "sense_mappings"
    __table_args__ = (
        UniqueConstraint("arabic_sense_id", "dictionary_entry_id", name="uq_sense_mapping"),
    )

    arabic_sense_id: Mapped[int] = mapped_column(
        ForeignKey("arabic_senses.id"), nullable=False, index=True
    )
    dictionary_entry_id: Mapped[int] = mapped_column(
        ForeignKey("dictionary_entries.id"), nullable=False, index=True
    )
    confidence: Mapped[float] = mapped_column(default=0.5, nullable=False, index=True)
    usage_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_primary: Mapped[bool] = mapped_column(default=False, nullable=False)
    review_status: Mapped[RecordStatus] = mapped_column(
        Enum(RecordStatus, name="sense_mapping_review_status"),
        default=RecordStatus.pending,
        nullable=False,
        index=True,
    )
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    arabic_sense: Mapped[ArabicSense] = relationship(back_populates="mappings")
    dictionary_entry: Mapped[DictionaryEntry] = relationship(back_populates="mappings")


ArabicIndex = ArabicSense
DictionarySense = ArabicSense
