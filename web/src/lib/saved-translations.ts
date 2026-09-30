import type { TranslateResponse } from "@/lib/translation-types";

const SAVED_KEY = "coptic-web-saved-translations";
const LAST_KEY = "coptic-web-last-translation";

export type SavedTranslation = {
  id: string;
  createdAt: string;
  inputText: string;
  dialectName?: string;
  result: TranslateResponse;
};

function readList(key: string): SavedTranslation[] {
  if (typeof window === "undefined") return [];
  const raw = localStorage.getItem(key);
  if (!raw) return [];
  try {
    const value = JSON.parse(raw);
    return Array.isArray(value) ? (value as SavedTranslation[]) : [];
  } catch {
    return [];
  }
}

function writeList(key: string, items: SavedTranslation[]) {
  localStorage.setItem(key, JSON.stringify(items));
}

export function getTranslationId(result: TranslateResponse) {
  return String(
    result.translation_candidate_id ||
      result.translation_request_id ||
      `${result.input_type}-${Date.now()}-${Math.random().toString(16).slice(2)}`
  );
}

export function storeLastTranslation(item: SavedTranslation) {
  if (typeof window === "undefined") return;
  localStorage.setItem(LAST_KEY, JSON.stringify(item));
}

export function getLastTranslation() {
  return readList(LAST_KEY)[0] || readSingle(LAST_KEY);
}

function readSingle(key: string): SavedTranslation | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(key);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as SavedTranslation;
  } catch {
    return null;
  }
}

export function listSavedTranslations() {
  return readList(SAVED_KEY);
}

export function saveTranslation(item: SavedTranslation) {
  const items = listSavedTranslations();
  const next = [item, ...items.filter((saved) => saved.id !== item.id)].slice(0, 50);
  writeList(SAVED_KEY, next);
}

export function removeTranslation(id: string) {
  writeList(
    SAVED_KEY,
    listSavedTranslations().filter((item) => item.id !== id)
  );
}

export function findSavedTranslation(id: string) {
  const saved = listSavedTranslations().find((item) => item.id === id);
  if (saved) return saved;
  const last = readSingle(LAST_KEY);
  return last?.id === id ? last : null;
}
