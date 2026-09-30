from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.models.enums import PartOfSpeech, RecordStatus, SourceType
from app.models.enums import Role


class DictionaryEntryCreate(BaseModel):
    coptic_text: str
    normalized_coptic_text: str | None = None
    transliteration: str | None = None
    dialect_id: int
    source_id: int
    part_of_speech: PartOfSpeech
    gender: str | None = None
    grammatical_number: str | None = None
    root: str | None = None
    example_sentence: str | None = None
    notes: str | None = None
    arabic_lemma: str | None = None
    arabic_definition: str | None = None
    review_status: RecordStatus = RecordStatus.pending


class DictionaryEntryUpdate(BaseModel):
    coptic_text: str | None = None
    normalized_coptic_text: str | None = None
    transliteration: str | None = None
    dialect_id: int | None = None
    source_id: int | None = None
    part_of_speech: PartOfSpeech | None = None
    notes: str | None = None
    review_status: RecordStatus | None = None


class ArabicSenseCreate(BaseModel):
    arabic_lemma: str
    normalized_arabic_lemma: str | None = None
    sense_key: str | None = None
    definition_ar: str
    part_of_speech: PartOfSpeech | None = None
    example_ar: str | None = None
    source_id: int | None = None
    review_status: RecordStatus = RecordStatus.pending


class SenseMappingCreate(BaseModel):
    arabic_sense_id: int
    dictionary_entry_id: int
    confidence: float = 0.5
    usage_note: str | None = None
    is_primary: bool = False
    review_status: RecordStatus = RecordStatus.pending


class CorpusTextCreate(BaseModel):
    title: str
    source_id: int
    dialect_id: int | None = None
    language: str
    content: str | None = None
    review_status: RecordStatus = RecordStatus.pending
    metadata: dict = {}


class ParallelSegmentCreate(BaseModel):
    corpus_text_id: int | None = None
    source_id: int
    dialect_id: int | None = None
    segment_order: int | None = None
    arabic_text: str
    coptic_text: str | None = None
    normalized_arabic_text: str | None = None
    normalized_coptic_text: str | None = None
    alignment_score: float | None = None
    review_status: RecordStatus = RecordStatus.pending


class GrammarRuleCreate(BaseModel):
    dialect_id: int | None = None
    source_id: int | None = None
    title: str
    rule_code: str | None = None
    description: str
    pattern: str | None = None
    replacement: str | None = None
    examples: list = []
    priority: int = 100
    is_active: bool = True
    review_status: RecordStatus = RecordStatus.pending


class SourceCreate(BaseModel):
    title: str
    author: str | None = None
    type: SourceType = SourceType.other
    year: int | None = None
    url: str | None = None
    isbn: str | None = None
    notes: str | None = None


class SourceUpdate(BaseModel):
    title: str | None = None
    author: str | None = None
    type: SourceType | None = None
    year: int | None = None
    url: str | None = None
    isbn: str | None = None
    notes: str | None = None


class SourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    author: str | None = None
    type: SourceType
    year: int | None = None
    url: str | None = None
    isbn: str | None = None
    notes: str | None = None


class UserCreate(BaseModel):
    email: str
    display_name: str
    password: str
    role: Role = Role.user
    preferred_dialect_id: int | None = None
    is_active: bool = True


class UserUpdate(BaseModel):
    email: str | None = None
    display_name: str | None = None
    password: str | None = None
    role: Role | None = None
    preferred_dialect_id: int | None = None
    is_active: bool | None = None


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    display_name: str
    role: Role
    preferred_dialect_id: int | None = None
    is_active: bool


class ArabicSenseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    arabic_lemma: str
    normalized_arabic_lemma: str
    sense_key: str | None = None
    definition_ar: str
    part_of_speech: PartOfSpeech | None = None
    example_ar: str | None = None
    source_id: int | None = None
    review_status: RecordStatus


class ArabicSenseUpdate(BaseModel):
    arabic_lemma: str | None = None
    normalized_arabic_lemma: str | None = None
    sense_key: str | None = None
    definition_ar: str | None = None
    part_of_speech: PartOfSpeech | None = None
    example_ar: str | None = None
    source_id: int | None = None
    review_status: RecordStatus | None = None


class SenseMappingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    arabic_sense_id: int
    dictionary_entry_id: int
    confidence: float
    usage_note: str | None = None
    is_primary: bool
    review_status: RecordStatus


class SenseMappingUpdate(BaseModel):
    arabic_sense_id: int | None = None
    dictionary_entry_id: int | None = None
    confidence: float | None = None
    usage_note: str | None = None
    is_primary: bool | None = None
    review_status: RecordStatus | None = None


class CorpusTextRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    source_id: int
    dialect_id: int | None = None
    language: str
    content: str | None = None
    review_status: RecordStatus
    extra_metadata: dict


class CorpusTextUpdate(BaseModel):
    title: str | None = None
    source_id: int | None = None
    dialect_id: int | None = None
    language: str | None = None
    content: str | None = None
    review_status: RecordStatus | None = None
    metadata: dict | None = None


class ParallelSegmentUpdate(BaseModel):
    corpus_text_id: int | None = None
    source_id: int | None = None
    dialect_id: int | None = None
    segment_order: int | None = None
    arabic_text: str | None = None
    coptic_text: str | None = None
    normalized_arabic_text: str | None = None
    normalized_coptic_text: str | None = None
    alignment_score: float | None = None
    review_status: RecordStatus | None = None


class GrammarRuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dialect_id: int | None = None
    source_id: int | None = None
    title: str
    rule_code: str | None = None
    description: str
    pattern: str | None = None
    replacement: str | None = None
    examples: list
    priority: int
    is_active: bool
    review_status: RecordStatus


class GrammarRuleUpdate(BaseModel):
    dialect_id: int | None = None
    source_id: int | None = None
    title: str | None = None
    rule_code: str | None = None
    description: str | None = None
    pattern: str | None = None
    replacement: str | None = None
    examples: list | None = None
    priority: int | None = None
    is_active: bool | None = None
    review_status: RecordStatus | None = None


class TranslationCandidateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    translation_request_id: int
    candidate_text: str | None = None
    dialect_id: int | None = None
    generated_by: str
    model_name: str | None = None
    rank: int
    confidence: float | None = None
    evidence: dict
    review_status: RecordStatus


class TranslationRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None = None
    input_text: str
    normalized_input_text: str | None = None
    status: str


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None = None
    action: str
    table_name: str | None = None
    record_id: int | None = None
    old_data: dict | None = None
    new_data: dict | None = None


class DictionaryImportPayload(BaseModel):
    format: str = "json"  # "csv", "json", "tei_xml"
    content: str
    default_dialect_code: str = "bohairic"
    default_source_id: int | None = None
    default_review_status: RecordStatus = RecordStatus.approved


class DictionaryImportStats(BaseModel):
    total_processed: int
    entries_created: int
    entries_reused: int
    senses_created: int
    senses_reused: int
    mappings_created: int
    mappings_updated: int
    errors: list[str] = []


class DeduplicationAuditResponse(BaseModel):
    duplicate_coptic_entries_count: int
    duplicate_arabic_senses_count: int
    duplicate_coptic_entries_sample: list[dict]
    duplicate_arabic_senses_sample: list[dict]


class DeduplicationMergeResponse(BaseModel):
    removed_redundant_senses: int
    message: str


class EvaluationMetricsResponse(BaseModel):
    total_reviews: int
    approved_count: int
    corrected_count: int
    rejected_count: int
    approval_rate: float
    correction_rate: float
    rejection_rate: float
    average_model_confidence: float
    average_target_similarity: float


class EvaluationDatasetItem(BaseModel):
    review_id: int
    candidate_id: int
    request_id: int
    input_arabic: str
    normalized_arabic: str | None = None
    predicted_coptic: str
    target_coptic: str
    review_status: str
    was_corrected: bool
    reviewer_id: int | None = None
    reviewer_comment: str | None = None
    rating: int | None = None
    model_confidence: float | None = None
    similarity_to_target: float
    dialect_id: int | None = None
    created_at: str | None = None


class ReviewerStats(BaseModel):
    user_id: int | None
    display_name: str
    email: str | None = None
    approved_count: int
    rejected_count: int
    corrected_count: int
    total_reviewed: int
    last_review_at: str | None = None


class WorkloadDashboardResponse(BaseModel):
    total_pending_drafts: int
    total_approved_candidates: int
    total_rejected_candidates: int
    total_translation_requests: int
    reviewers: list[ReviewerStats]
    average_confidence: float

