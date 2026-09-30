"use client";

import { useQuery } from "@tanstack/react-query";
import { ChevronLeft, ChevronRight, Loader2, Search } from "lucide-react";
import { useMemo, useState } from "react";
import { PublicShell } from "@/components/public-shell";
import { apiFetch } from "@/lib/api";
import { dialectNameAr } from "@/lib/dialects";
import { valueLabelAr } from "@/lib/labels";
import type { Dialect } from "@/lib/translation-types";

const COPTIC_LETTERS = [
  "Ⲁ", "Ⲃ", "Ⲅ", "Ⲇ", "Ⲉ", "ⲋ", "Ⲍ", "Ⲏ", "Ⲑ", "Ⲓ", "Ⲕ", "Ⲗ", "Ⲙ", "Ⲛ",
  "Ⲝ", "Ⲟ", "Ⲡ", "Ⲣ", "Ⲥ", "Ⲧ", "Ⲩ", "Ⲫ", "Ⲭ", "Ⲯ", "Ⲱ", "Ϣ", "Ϥ", "Ϧ", "ϩ", "ϫ", "ϭ", "ϯ"
];

interface BrowseItem {
  id: number;
  coptic_text: string;
  normalized_coptic_text: string;
  transliteration?: string | null;
  dialect_id: number;
  source_id: number;
  source_title?: string | null;
  part_of_speech: string;
  review_status: string;
  notes?: string | null;
  arabic_meanings: string[];
}

interface BrowseResponse {
  items: BrowseItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

export default function DictionaryBrowsePage() {
  const [query, setQuery] = useState("");
  const [selectedLetter, setSelectedLetter] = useState<string>("");
  const [dialectId, setDialectId] = useState<number | "">("");
  const [partOfSpeech, setPartOfSpeech] = useState<string>("");
  const [page, setPage] = useState(1);

  const dialects = useQuery({
    queryKey: ["dialects"],
    queryFn: () => apiFetch<Dialect[]>("/dialects", { auth: false })
  });

  const defaultDialect = useMemo(() => {
    const rows = dialects.data || [];
    return rows.find((dialect) => dialect.code.toLowerCase() === "bohairic") || rows[0];
  }, [dialects.data]);

  const selectedDialectId = dialectId || defaultDialect?.id || "";

  // Browse / Search Query
  const browseQuery = useQuery({
    queryKey: ["dictionary-browse", query, selectedLetter, selectedDialectId, partOfSpeech, page],
    queryFn: () => {
      const params = new URLSearchParams({
        page: String(page),
        page_size: "20"
      });
      if (query.trim()) params.set("q", query.trim());
      if (selectedLetter) params.set("letter", selectedLetter);
      if (selectedDialectId) params.set("dialect_id", String(selectedDialectId));
      if (partOfSpeech) params.set("part_of_speech", partOfSpeech);

      return apiFetch<BrowseResponse>(`/dictionary/browse?${params.toString()}`, { auth: false });
    }
  });

  const data = browseQuery.data;

  return (
    <PublicShell>
      <section className="page-intro">
        <p className="eyebrow">المعجم القبطي العام</p>
        <h1>تصفح وابحث في مفردات اللغة القبطية.</h1>
        <p>تصفح حر متاح للجميع بدون تسجيل؛ يشمل معاني الكلمات واللهجات والمصادر الموثقة.</p>
      </section>

      {/* Search & Filters Bar */}
      <section className="search-panel" style={{ flexWrap: "wrap", gap: 12 }}>
        <label className="search-box" style={{ flex: "1 1 280px" }}>
          <Search size={18} />
          <input
            dir="rtl"
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
              setPage(1);
            }}
            placeholder="ابحث بالاسم العربي أو الكلمة القبطية..."
          />
        </label>

        <select
          className="input"
          disabled={dialects.isPending}
          value={selectedDialectId}
          onChange={(event) => {
            setDialectId(Number(event.target.value));
            setPage(1);
          }}
          style={{ width: "auto" }}
        >
          {(dialects.data || []).map((dialect) => (
            <option key={dialect.id} value={dialect.id}>
              {dialectNameAr(dialect)} {dialect.code.toLowerCase() === "bohairic" ? "(الافتراضية)" : ""}
            </option>
          ))}
        </select>

        <select
          className="input"
          value={partOfSpeech}
          onChange={(event) => {
            setPartOfSpeech(event.target.value);
            setPage(1);
          }}
          style={{ width: "auto" }}
        >
          <option value="">جميع أقسام الكلام</option>
          <option value="noun">اسم (Noun)</option>
          <option value="verb">فعل (Verb)</option>
          <option value="adjective">صفة (Adjective)</option>
          <option value="preposition">حرف جر (Preposition)</option>
          <option value="conjunction">حرف عطف (Conjunction)</option>
          <option value="particle">أداة (Particle)</option>
        </select>
      </section>

      {/* Coptic Alphabet Filter Bar */}
      <div
        style={{
          display: "flex",
          gap: 6,
          overflowX: "auto",
          padding: "8px 0 16px",
          marginBottom: 16,
          borderBottom: "1px solid var(--hairline)"
        }}
      >
        <button
          type="button"
          onClick={() => {
            setSelectedLetter("");
            setPage(1);
          }}
          style={{
            padding: "4px 10px",
            borderRadius: 6,
            border: "1px solid var(--hairline)",
            background: selectedLetter === "" ? "var(--primary)" : "var(--canvas-soft)",
            color: selectedLetter === "" ? "#fff" : "inherit",
            cursor: "pointer",
            fontWeight: 600,
            fontSize: "0.85rem",
            whiteSpace: "nowrap"
          }}
        >
          الكل
        </button>
        {COPTIC_LETTERS.map((char) => (
          <button
            key={char}
            type="button"
            onClick={() => {
              setSelectedLetter(char);
              setPage(1);
            }}
            style={{
              padding: "4px 8px",
              borderRadius: 6,
              border: "1px solid var(--hairline)",
              background: selectedLetter === char ? "var(--primary)" : "var(--canvas-soft)",
              color: selectedLetter === char ? "#fff" : "inherit",
              cursor: "pointer",
              fontWeight: 700,
              fontSize: "1rem",
              fontFamily: "var(--font-coptic)"
            }}
          >
            {char}
          </button>
        ))}
      </div>

      {browseQuery.isPending ? (
        <div className="empty-state">
          <Loader2 className="spin" size={24} />
          <span>جارٍ تحميل المفردات...</span>
        </div>
      ) : null}

      {browseQuery.error ? <p className="error">{(browseQuery.error as Error).message}</p> : null}

      {/* Results List */}
      {data?.items && data.items.length > 0 ? (
        <>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
            <p style={{ margin: 0, color: "var(--ink-mute)", fontSize: "0.85rem" }}>
              إجمالي النتائج: <strong>{data.total}</strong> كلمة معتمدة
            </p>
            <p style={{ margin: 0, color: "var(--ink-mute)", fontSize: "0.85rem" }}>
              صفحة {data.page} من {data.total_pages}
            </p>
          </div>

          <div className="dictionary-results">
            {data.items.map((entry) => (
              <article className="dictionary-item" key={entry.id}>
                <div>
                  <h2 className="coptic-word" style={{ fontFamily: "var(--font-coptic)" }}>
                    {entry.coptic_text}
                  </h2>
                  <p style={{ margin: "4px 0", color: "var(--ink-secondary)", fontSize: "0.95rem" }}>
                    {entry.arabic_meanings && entry.arabic_meanings.length > 0 ? (
                      <strong>المعنى العربي: {entry.arabic_meanings.join("، ")}</strong>
                    ) : (
                      <span className="muted">{entry.transliteration || "لا يوجد نقل صوتي"}</span>
                    )}
                  </p>
                  {entry.transliteration ? (
                    <p style={{ margin: 0, color: "var(--ink-mute)", fontSize: "0.85rem" }}>
                      النطق الصوتي: {entry.transliteration}
                    </p>
                  ) : null}
                </div>
                <dl className="meta-list">
                  <div>
                    <dt>نوع الكلمة</dt>
                    <dd>{valueLabelAr(entry.part_of_speech)}</dd>
                  </div>
                  <div>
                    <dt>المصدر الأكاديمي</dt>
                    <dd>{entry.source_title || `مصدر #${entry.source_id}`}</dd>
                  </div>
                  <div>
                    <dt>الحالة</dt>
                    <dd>{valueLabelAr(entry.review_status)}</dd>
                  </div>
                </dl>
                {entry.notes ? <p className="muted" style={{ margin: "8px 0 0" }}>{entry.notes}</p> : null}
              </article>
            ))}
          </div>

          {/* Pagination Controls */}
          {data.total_pages > 1 ? (
            <div style={{ display: "flex", justifyContent: "center", alignItems: "center", gap: 12, marginTop: 24 }}>
              <button
                type="button"
                className="button"
                disabled={!data.has_prev}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                <ChevronRight size={16} /> السابق
              </button>
              <span style={{ fontSize: "0.9rem", fontWeight: 600 }}>
                {data.page} / {data.total_pages}
              </span>
              <button
                type="button"
                className="button"
                disabled={!data.has_next}
                onClick={() => setPage((p) => p + 1)}
              >
                التالي <ChevronLeft size={16} />
              </button>
            </div>
          ) : null}
        </>
      ) : null}

      {!browseQuery.isPending && data?.items && data.items.length === 0 ? (
        <div className="empty-state">لا توجد كلمات مطابقة لمعايير البحث والتصفية المختارة.</div>
      ) : null}
    </PublicShell>
  );
}
