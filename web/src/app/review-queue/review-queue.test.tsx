import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";
import { describe, expect, it, vi } from "vitest";
import ReviewQueuePage from "./page";
import { apiFetch } from "@/lib/api";

vi.mock("next/navigation", () => ({
  usePathname: () => "/review-queue",
  useRouter: () => ({ replace: vi.fn(), push: vi.fn() })
}));

vi.mock("@/components/protected-route", () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => React.createElement(React.Fragment, null, children)
}));

vi.mock("@/components/app-shell", () => ({
  AppShell: ({ children }: { children: React.ReactNode }) => React.createElement("div", null, children),
  PageHeading: ({ title, description }: { title: string; description?: string }) => (
    React.createElement("header", null, React.createElement("h1", null, title), React.createElement("p", null, description))
  )
}));

vi.mock("@/components/filters", () => ({
  FilterBar: () => React.createElement("div", null, "filters")
}));

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return { ...actual, apiFetch: vi.fn() };
});

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return render(React.createElement(QueryClientProvider, { client }, React.createElement(ReviewQueuePage)));
}

describe("ReviewQueuePage", () => {
  it("runs approve and reject review flows", async () => {
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      if (path === "/review/translation-candidates") {
        return [
          { id: 11, candidate_text: "ⲁ", confidence: 0.71, review_status: "draft", evidence: { references: [] } },
          { id: 12, candidate_text: "ⲃ", confidence: 0.42, review_status: "draft", evidence: { references: [] } }
        ];
      }
      if (path === "/review/translation/11/approve") return { id: 11, review_status: "approved" };
      if (path === "/review/translation/12/reject") return { id: 12, review_status: "rejected" };
      throw new Error(`Unhandled path ${path}`);
    });

    renderPage();

    expect((await screen.findAllByText(/مرشح #/)).length).toBeGreaterThan(0);
    await userEvent.click(screen.getAllByRole("button", { name: /اعتماد/ })[0]);
    await userEvent.click(screen.getAllByRole("button", { name: /رفض/ })[1]);

    await waitFor(() => {
      expect(apiFetch).toHaveBeenCalledWith("/review/translation/11/approve", { method: "POST" });
      expect(apiFetch).toHaveBeenCalledWith(
        "/review/translation/12/reject",
        expect.objectContaining({ method: "POST" })
      );
    });
  });
});
