from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import InputType, PartOfSpeech, RecordStatus


class DialectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    native_name: str | None = None
    description: str | None = None


class TranslateRequest(BaseModel):
    text: str
    target_dialect_id: int | None = None
    context: str | None = None


class TranslateResponse(BaseModel):
    input_type: InputType
    status: RecordStatus
    translation: str | None
    translations: list[str] = Field(default_factory=list)
    confidence: float
    dictionary_entry_ids: list[int] = Field(default_factory=list)
    translation_request_id: int | None = None
    translation_candidate_id: int | None = None
    candidate_translation: str | None = None
    word_results: list[dict] = Field(default_factory=list)
    literal_breakdown: list[dict] = Field(default_factory=list)
    used_dictionary_entries: list[int] = Field(default_factory=list)
    similar_examples: list[dict] = Field(default_factory=list)
    meaning_examples: list[dict] = Field(default_factory=list)
    grammar_notes: list[dict] = Field(default_factory=list)
    unknown_words: list[str] = Field(default_factory=list)
    needs_human_review: bool = False
    human_review_reason: str | None = None
    references: list[dict] = Field(default_factory=list)
    evidence: dict = Field(default_factory=dict)
    quota: QuotaInfo | None = None


class QuotaInfo(BaseModel):
    tier: str = "free"
    daily_limit: int = 10
    used_today: int = 0
    remaining: int = 10
    is_unlimited: bool = False


class SimilarSegmentsRequest(BaseModel):
    q: str
    dialect_id: int | None = None
    limit: int = 5


class SimilarSegmentsResponse(BaseModel):
    items: list[dict] = Field(default_factory=list)


class DictionaryEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    coptic_text: str
    normalized_coptic_text: str
    transliteration: str | None = None
    dialect_id: int
    source_id: int
    part_of_speech: PartOfSpeech
    review_status: RecordStatus
    notes: str | None = None


class DictionaryBrowseItem(DictionaryEntryRead):
    arabic_meanings: list[str] = Field(default_factory=list)
    source_title: str | None = None


class DictionaryBrowseResponse(BaseModel):
    items: list[DictionaryBrowseItem]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


class SourceCitationRead(BaseModel):
    id: int
    title: str
    author: str | None = None
    type: str
    year: int | None = None
    url: str | None = None
    isbn: str | None = None
    notes: str | None = None
    entries_count: int = 0
    segments_count: int = 0
    citation_text: str = ""


class SourceDetailRead(SourceCitationRead):
    sample_entries: list[DictionaryEntryRead] = Field(default_factory=list)
    sample_segments: list[ParallelSegmentRead] = Field(default_factory=list)


class ParallelSegmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_id: int
    dialect_id: int | None = None
    arabic_text: str
    coptic_text: str | None = None
    review_status: RecordStatus
