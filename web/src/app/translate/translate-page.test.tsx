import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import TranslatePage from "./page";
import { apiFetch } from "@/lib/api";

vi.mock("next/link", () => ({
  default: ({ href, children, ...props }: { href: string; children: React.ReactNode }) =>
    React.createElement("a", { href, ...props }, children)
}));

vi.mock("next/navigation", () => ({
  usePathname: () => "/translate",
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() })
}));

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return { ...actual, apiFetch: vi.fn() };
});

const dialects = [
  { id: 1, code: "bohairic", name: "Bohairic" },
  { id: 2, code: "sahidic", name: "Sahidic" }
];

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return render(React.createElement(QueryClientProvider, { client }, React.createElement(TranslatePage)));
}

describe("TranslatePage", () => {
  beforeEach(() => {
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      if (path === "/dialects") return dialects;
      throw new Error(`Unhandled path ${path}`);
    });
  });

  it("renders translate form with Arabic input and dialect selector", async () => {
    renderPage();

    expect(await screen.findByText("ترجمة موثقة")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("مثال: الله محبة")).toBeInTheDocument();
    expect(await screen.findByRole("option", { name: /البحيرية/ })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: /الصعيدية/ })).toBeInTheDocument();
  });

  it("submits word translation and displays confidence", async () => {
    vi.mocked(apiFetch).mockImplementation(async (path: string, options?: RequestInit) => {
      if (path === "/dialects") return dialects;
      if (path === "/translate") {
        expect(JSON.parse(String(options?.body))).toMatchObject({ text: "سلام", target_dialect_id: 1 });
        return {
          input_type: "word",
          status: "approved",
          translation: "ⲉⲓⲣⲏⲛⲏ",
          confidence: 0.82,
          word_results: [
            {
              coptic_word: "ⲉⲓⲣⲏⲛⲏ",
              part_of_speech: "noun",
              meaning: "سلام",
              dialect: "Bohairic",
              source: "Sample Dictionary Source",
              confidence: 0.82,
              examples: []
            }
          ],
          literal_breakdown: [],
          similar_examples: [],
          grammar_notes: [],
          unknown_words: [],
          needs_human_review: false,
          references: [{ table: "dictionary_entries", id: 1 }]
        };
      }
      throw new Error(`Unhandled path ${path}`);
    });
    renderPage();

    await userEvent.type(await screen.findByPlaceholderText("مثال: الله محبة"), "سلام");
    await userEvent.click(screen.getByRole("button", { name: "ترجم" }));

    expect((await screen.findAllByText("ⲉⲓⲣⲏⲛⲏ")).length).toBeGreaterThan(0);
    expect(screen.getAllByText("82%").length).toBeGreaterThan(0);
    expect(screen.getByText("Sample Dictionary Source")).toBeInTheDocument();
  });

  it("submits sentence translation and displays unknown words plus draft warning", async () => {
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      if (path === "/dialects") return dialects;
      if (path === "/translate") {
        return {
          input_type: "sentence",
          status: "draft",
          translation: null,
          candidate_translation: null,
          confidence: 0.32,
          word_results: [{ coptic_word: "Ⲫⲛⲟⲩϯ", meaning: "الله" }],
          literal_breakdown: [
            { arabic: "الله", coptic: "Ⲫⲛⲟⲩϯ", status: "known" },
            { arabic: "غامض", coptic: null, status: "unknown" }
          ],
          similar_examples: [{ id: 3, arabic_text: "الله محبة", coptic_text: "Ⲫⲛⲟⲩϯ ⲁⲅⲁⲡⲏ", similarity_score: 0.51 }],
          grammar_notes: [{ id: 2, title: "جملة اسمية", description: "sample rule" }],
          unknown_words: ["غامض"],
          needs_human_review: true,
          human_review_reason: "كلمات غير معروفة، الترجمة تحتاج مراجعة بشرية قبل اعتمادها.",
          references: [{ table: "parallel_segments", id: 3 }]
        };
      }
      throw new Error(`Unhandled path ${path}`);
    });
    renderPage();

    await userEvent.type(await screen.findByPlaceholderText("مثال: الله محبة"), "الله غامض");
    await userEvent.click(screen.getByRole("button", { name: "ترجم" }));

    expect(await screen.findByText("لا توجد ترجمة كاملة موثقة")).toBeInTheDocument();
    expect(screen.getAllByText("32%").length).toBeGreaterThan(0);
    expect(screen.getAllByText("غامض").length).toBeGreaterThan(0);
    expect(screen.getByText(/تحتاج مراجعة بشرية/)).toBeInTheDocument();
    expect(screen.getByText("جملة اسمية")).toBeInTheDocument();
  });

  it("shows backend errors as an error state", async () => {
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      if (path === "/dialects") return dialects;
      throw new Error("Request failed with 500");
    });
    renderPage();

    await userEvent.type(await screen.findByPlaceholderText("مثال: الله محبة"), "سلام");
    await userEvent.click(screen.getByRole("button", { name: "ترجم" }));

    await waitFor(() => expect(screen.getByText("Request failed with 500")).toBeInTheDocument());
  });
});
