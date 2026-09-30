import AsyncStorage from "@react-native-async-storage/async-storage";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react-native";
import React from "react";
import SettingsScreen from "../app/settings";
import TranslateScreen from "../app/translate";
import { getDialects, translate } from "../src/api";
import { ResultCard } from "../src/components/ResultCard";
import { getApiBaseUrl, listFavorites, saveFavorite } from "../src/storage";

jest.mock("../src/api", () => {
  const actual = jest.requireActual("../src/api");
  return {
    ...actual,
    getDialects: jest.fn(),
    login: jest.fn(async () => ({ access_token: "token" })),
    translate: jest.fn()
  };
});

let queryClient: QueryClient;

function withProviders(children: React.ReactNode) {
  queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } }
  });
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}

beforeEach(async () => {
  await AsyncStorage.clear();
  jest.clearAllMocks();
  jest.mocked(getDialects).mockResolvedValue([
    { id: 1, code: "bohairic", name: "Bohairic" },
    { id: 2, code: "sahidic", name: "Sahidic" }
  ]);
});

afterEach(() => {
  queryClient?.clear();
  cleanup();
});

test("translate screen renders", async () => {
  render(withProviders(<TranslateScreen />));

  expect(await screen.findByPlaceholderText("مثال: الله محبة")).toBeTruthy();
  expect(await screen.findByText(/البحيرية/)).toBeTruthy();
  expect(await screen.findByText(/الصعيدية/)).toBeTruthy();
});

test("translate screen submits without requiring login and uses selected dialect", async () => {
  jest.mocked(translate).mockResolvedValue({
    input_type: "word",
    status: "approved",
    translation: "ⲉⲓⲣⲏⲛⲏ",
    confidence: 0.8,
    word_results: [],
    literal_breakdown: [],
    similar_examples: [],
    grammar_notes: [],
    unknown_words: [],
    needs_human_review: false,
    references: []
  });

  render(withProviders(<TranslateScreen />));

  fireEvent.changeText(await screen.findByPlaceholderText("مثال: الله محبة"), "سلام");
  fireEvent.press(await screen.findByText(/الصعيدية/));
  fireEvent.press(screen.getByText("ترجم"));

  await waitFor(() => {
    expect(translate).toHaveBeenCalledWith("سلام", 2, null);
  });
});

test("result screen displays word result", () => {
  render(
    <ResultCard
      inputText="سلام"
      result={{
        input_type: "word",
        status: "approved",
        translation: "ⲉⲓⲣⲏⲛⲏ",
        confidence: 0.8,
        word_results: [
          {
            coptic_word: "ⲉⲓⲣⲏⲛⲏ",
            meaning: "سلام",
            part_of_speech: "noun",
            dialect: "Bohairic",
            source: "Sample Dictionary Source",
            examples: []
          }
        ],
        literal_breakdown: [],
        similar_examples: [],
        grammar_notes: [],
        unknown_words: [],
        needs_human_review: false,
        references: [{ table: "dictionary_entries", id: 1 }]
      }}
    />
  );

  expect(screen.getAllByText("ⲉⲓⲣⲏⲛⲏ").length).toBeGreaterThan(0);
  expect(screen.getByText("80%")).toBeTruthy();
  expect(screen.getByText(/Sample Dictionary Source/)).toBeTruthy();
});

test("result screen displays sentence result", () => {
  render(
    <ResultCard
      inputText="الله غامض"
      result={{
        input_type: "sentence",
        status: "draft",
        translation: null,
        candidate_translation: null,
        confidence: 0.31,
        word_results: [{ coptic_word: "Ⲫⲛⲟⲩϯ", meaning: "الله" }],
        literal_breakdown: [
          { arabic: "الله", coptic: "Ⲫⲛⲟⲩϯ", status: "known" },
          { arabic: "غامض", coptic: null, status: "unknown" }
        ],
        similar_examples: [
          { id: 1, arabic_text: "الله محبة", coptic_text: "Ⲫⲛⲟⲩϯ ⲁⲅⲁⲡⲏ", similarity_score: 0.5 }
        ],
        grammar_notes: [{ id: 1, title: "جملة اسمية", description: "sample" }],
        unknown_words: ["غامض"],
        needs_human_review: true,
        human_review_reason: "كلمات غير معروفة، الترجمة تحتاج مراجعة بشرية قبل اعتمادها.",
        references: [{ table: "parallel_segments", id: 1 }]
      }}
    />
  );

  expect(screen.getByText("لا توجد ترجمة كاملة موثقة")).toBeTruthy();
  expect(screen.getByText("31%")).toBeTruthy();
  expect(screen.getAllByText("غامض").length).toBeGreaterThan(0);
  expect(screen.getByText(/تحتاج مراجعة بشرية/)).toBeTruthy();
});

test("save translation locally", async () => {
  await saveFavorite({
    id: "one",
    createdAt: new Date().toISOString(),
    inputText: "سلام",
    dialectName: "البحيرية",
    result: {
      input_type: "word",
      status: "approved",
      translation: "ⲉⲓⲣⲏⲛⲏ",
      confidence: 0.8,
      word_results: [],
      literal_breakdown: [],
      similar_examples: [],
      grammar_notes: [],
      unknown_words: [],
      needs_human_review: false,
      references: []
    }
  });

  const items = await listFavorites();
  expect(items).toHaveLength(1);
  expect(items[0].inputText).toBe("سلام");
});

test("settings dialect change updates backend API preset", async () => {
  render(withProviders(<SettingsScreen />));

  fireEvent.press(await screen.findByText("محاكي أندرويد"));

  await waitFor(async () => {
    await expect(getApiBaseUrl()).resolves.toBe("http://10.0.2.2:8000");
  });
});
