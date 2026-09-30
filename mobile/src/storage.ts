import AsyncStorage from "@react-native-async-storage/async-storage";
import type { TranslateResponse } from "./api";

export const DEFAULT_API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL || "http://localhost:8000";

const API_BASE_KEY = "coptic-mobile-api-base-url";
const SESSION_KEY = "coptic-mobile-session";
const LAST_TRANSLATION_KEY = "coptic-mobile-last-translation";
const FAVORITES_KEY = "coptic-mobile-favorites";
const TRANSLATION_DRAFT_KEY = "coptic-mobile-translation-draft";

export type Session = {
  token: string;
  email: string;
};

export type SavedTranslation = {
  id: string;
  createdAt: string;
  inputText: string;
  dialectName?: string;
  result: TranslateResponse;
};

export type TranslationDraft = {
  text: string;
  dialectId: number | null;
};

export async function getApiBaseUrl() {
  return (await AsyncStorage.getItem(API_BASE_KEY)) || DEFAULT_API_BASE_URL;
}

export async function saveApiBaseUrl(url: string) {
  await AsyncStorage.setItem(API_BASE_KEY, url.replace(/\/$/, ""));
}

export async function getSession() {
  const raw = await AsyncStorage.getItem(SESSION_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as Session;
  } catch {
    return null;
  }
}

export async function saveSession(session: Session) {
  await AsyncStorage.setItem(SESSION_KEY, JSON.stringify(session));
}

export async function clearSession() {
  await AsyncStorage.removeItem(SESSION_KEY);
}

export function getTranslationId(result: TranslateResponse) {
  return String(
    result.translation_candidate_id ||
      result.translation_request_id ||
      `${result.input_type}-${Date.now()}-${Math.random().toString(16).slice(2)}`
  );
}

export async function saveLastTranslation(item: SavedTranslation) {
  await AsyncStorage.setItem(LAST_TRANSLATION_KEY, JSON.stringify(item));
}

export async function getLastTranslation() {
  const raw = await AsyncStorage.getItem(LAST_TRANSLATION_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as SavedTranslation;
  } catch {
    return null;
  }
}

export async function listFavorites() {
  const raw = await AsyncStorage.getItem(FAVORITES_KEY);
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? (parsed as SavedTranslation[]) : [];
  } catch {
    return [];
  }
}

export async function saveFavorite(item: SavedTranslation) {
  const current = await listFavorites();
  const next = [item, ...current.filter((favorite) => favorite.id !== item.id)].slice(0, 50);
  await AsyncStorage.setItem(FAVORITES_KEY, JSON.stringify(next));
}

export async function removeFavorite(id: string) {
  const current = await listFavorites();
  await AsyncStorage.setItem(FAVORITES_KEY, JSON.stringify(current.filter((item) => item.id !== id)));
}

export async function clearFavorites() {
  await AsyncStorage.removeItem(FAVORITES_KEY);
}

export async function saveTranslationDraft(draft: TranslationDraft) {
  await AsyncStorage.setItem(TRANSLATION_DRAFT_KEY, JSON.stringify(draft));
}

export async function getTranslationDraft() {
  const raw = await AsyncStorage.getItem(TRANSLATION_DRAFT_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as TranslationDraft;
  } catch {
    return null;
  }
}

const OFFLINE_CACHE_PREFIX = "coptic-offline-cache:";

export async function getCachedResponse<T>(key: string): Promise<T | null> {
  const raw = await AsyncStorage.getItem(`${OFFLINE_CACHE_PREFIX}${key}`);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

export async function setCachedResponse<T>(key: string, data: T): Promise<void> {
  try {
    await AsyncStorage.setItem(`${OFFLINE_CACHE_PREFIX}${key}`, JSON.stringify(data));
  } catch {
    // Ignore cache write quota issues
  }
}
