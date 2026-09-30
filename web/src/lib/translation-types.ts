export type Dialect = {
  id: number;
  code: string;
  name: string;
  native_name?: string | null;
  description?: string | null;
};

export type DictionaryEntry = {
  id: number;
  coptic_text: string;
  normalized_coptic_text?: string;
  transliteration?: string | null;
  dialect_id: number;
  source_id: number;
  part_of_speech: string;
  review_status: string;
  notes?: string | null;
};

export type TranslationReference = Record<string, unknown>;

export type TranslationWordResult = {
  coptic_word?: string;
  coptic_text?: string;
  dialect?: string;
  dialect_name?: string;
  part_of_speech?: string;
  meaning?: string;
  source?: string;
  source_title?: string;
  confidence?: number;
  examples?: Array<Record<string, unknown>>;
  [key: string]: unknown;
};

export type LiteralBreakdownItem = {
  arabic?: string;
  token?: string;
  coptic?: string;
  coptic_word?: string;
  meaning?: string;
  status?: string;
  [key: string]: unknown;
};

export type SimilarExample = {
  id?: number;
  arabic_text?: string;
  coptic_text?: string | null;
  similarity?: number;
  similarity_score?: number;
  source_id?: number;
  dialect_id?: number | null;
  review_status?: string;
  [key: string]: unknown;
};

export type GrammarNote = {
  id?: number;
  title?: string;
  rule_code?: string;
  description?: string;
  note?: string;
  similarity?: number;
  [key: string]: unknown;
};

export type TranslateResponse = {
  input_type: "word" | "sentence";
  status: string;
  translation: string | null;
  confidence: number;
  dictionary_entry_ids?: number[];
  translation_request_id?: number | null;
  translation_candidate_id?: number | null;
  candidate_translation?: string | null;
  word_results: TranslationWordResult[];
  literal_breakdown: LiteralBreakdownItem[];
  used_dictionary_entries?: number[];
  similar_examples: SimilarExample[];
  meaning_examples?: SimilarExample[];
  grammar_notes: GrammarNote[];
  unknown_words: string[];
  needs_human_review: boolean;
  human_review_reason?: string | null;
  references: TranslationReference[];
  evidence?: Record<string, unknown>;
};
