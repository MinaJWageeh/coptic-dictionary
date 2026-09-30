import { getApiBaseUrl, getCachedResponse, setCachedResponse } from "./storage";

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

export type TranslateResponse = {
  input_type: "word" | "sentence";
  status: string;
  translation: string | null;
  confidence: number;
  dictionary_entry_ids?: number[];
  translation_request_id?: number | null;
  translation_candidate_id?: number | null;
  candidate_translation?: string | null;
  word_results: Array<Record<string, unknown>>;
  literal_breakdown: Array<Record<string, unknown>>;
  used_dictionary_entries?: number[];
  similar_examples: Array<Record<string, unknown>>;
  meaning_examples?: Array<Record<string, unknown>>;
  grammar_notes: Array<Record<string, unknown>>;
  unknown_words: string[];
  needs_human_review: boolean;
  human_review_reason?: string | null;
  references: Array<Record<string, unknown>>;
  evidence?: Record<string, unknown>;
};

export type ParallelSegment = {
  id: number;
  source_id: number;
  dialect_id?: number | null;
  arabic_text: string;
  coptic_text?: string | null;
  review_status: string;
};

export type ApiFetchOptions = RequestInit & {
  token?: string | null;
};

export async function apiFetch<T>(
  path: string,
  options: ApiFetchOptions = {},
  tokenArg?: string | null
): Promise<T> {
  const isGet = !options.method || options.method.toUpperCase() === "GET";
  try {
    const token = options.token ?? tokenArg;
    const headers = new Headers(options.headers);
    headers.set("Content-Type", "application/json");
    if (token) headers.set("Authorization", `Bearer ${token}`);

    const baseUrl = await getApiBaseUrl();
    const { token: _, ...fetchOptions } = options;
    const response = await fetch(`${baseUrl}${path}`, { ...fetchOptions, headers });
    if (!response.ok) {
      const body = await response.text();
      throw new Error(body || `Request failed with ${response.status}`);
    }
    if (response.status === 204) return undefined as T;
    const data = (await response.json()) as T;
    if (isGet) {
      await setCachedResponse(path, data);
    }
    return data;
  } catch (error) {
    if (isGet) {
      const cached = await getCachedResponse<T>(path);
      if (cached !== null) {
        return cached;
      }
    }
    throw error;
  }
}

export async function login(email: string, password: string) {
  return apiFetch<{ access_token: string; token_type?: string }>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password })
  });
}

export async function getDialects() {
  return apiFetch<Dialect[]>("/dialects");
}

export async function translate(text: string, targetDialectId: number | null, token?: string | null) {
  return apiFetch<TranslateResponse>(
    "/translate",
    {
      method: "POST",
      body: JSON.stringify({ text, target_dialect_id: targetDialectId })
    },
    token
  );
}

export async function searchDictionary(query: string, dialectId: number | null) {
  const params = new URLSearchParams({ q: query });
  if (dialectId) params.set("dialect_id", String(dialectId));
  return apiFetch<DictionaryEntry[]>(`/dictionary/search?${params.toString()}`);
}

export async function searchExamples(query: string, dialectId: number | null) {
  const params = new URLSearchParams({ q: query });
  if (dialectId) params.set("dialect_id", String(dialectId));
  return apiFetch<ParallelSegment[]>(`/examples/search?${params.toString()}`);
}
