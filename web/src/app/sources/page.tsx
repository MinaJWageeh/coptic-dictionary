"use client";

import { useQuery } from "@tanstack/react-query";
import { BookOpen, Check, Copy, ExternalLink, Loader2 } from "lucide-react";
import { useState } from "react";
import { PublicShell } from "@/components/public-shell";
import { apiFetch } from "@/lib/api";

interface SourceCitation {
  id: number;
  title: string;
  author: string | null;
  type: string;
  year: number | null;
  url: string | null;
  isbn: string | null;
  notes: string | null;
  entries_count: number;
  segments_count: number;
  citation_text: string;
}

export default function SourcesPage() {
  const [copiedId, setCopiedId] = useState<number | null>(null);

  const sources = useQuery({
    queryKey: ["public-sources"],
    queryFn: () => apiFetch<SourceCitation[]>("/sources", { auth: false })
  });

  const handleCopyCitation = (source: SourceCitation) => {
    navigator.clipboard.writeText(source.citation_text);
    setCopiedId(source.id);
    setTimeout(() => setCopiedId(null), 2500);
  };

  return (
    <PublicShell>
      <section className="page-intro">
        <p className="eyebrow">التوثيق العلمي</p>
        <h1>المصادر الأكاديمية والاستشهادات المعتمدة.</h1>
        <p>
          جميع المفردات والشواهد في المنظومة مستندة إلى مراجع تاريخية وأكاديمية محققة وموثقة ببليوغرافياً.
        </p>
      </section>

      {sources.isPending ? (
        <div className="empty-state">
          <Loader2 className="spin" size={24} />
          <span>جارٍ تحميل بيانات المصادر والمراجع...</span>
        </div>
      ) : null}

      {sources.error ? <p className="error">{(sources.error as Error).message}</p> : null}

      {sources.data && (
        <div style={{ display: "grid", gap: 16 }}>
          {sources.data.map((s) => (
            <article key={s.id} className="panel" style={{ padding: "20px 24px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16 }}>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                    <span
                      style={{
                        padding: "2px 8px",
                        borderRadius: 4,
                        fontSize: "0.75rem",
                        fontWeight: 700,
                        textTransform: "uppercase",
                        background: "var(--canvas-cream, #f5e9d4)",
                        color: "var(--lemon, #9b6829)"
                      }}
                    >
                      {s.type}
                    </span>
                    {s.year && (
                      <span style={{ fontSize: "0.85rem", color: "var(--ink-mute)" }}>
                        عام {s.year}
                      </span>
                    )}
                  </div>

                  <h2 style={{ margin: "0 0 6px", fontSize: "1.25rem", fontWeight: 700 }}>
                    {s.title}
                  </h2>

                  {s.author && (
                    <p style={{ margin: "0 0 8px", color: "var(--ink-secondary)", fontSize: "0.95rem" }}>
                      المؤلف / المحقق: <strong>{s.author}</strong>
                    </p>
                  )}

                  {s.notes && (
                    <p style={{ margin: "0 0 12px", color: "var(--ink-mute)", fontSize: "0.9rem", lineHeight: 1.5 }}>
                      {s.notes}
                    </p>
                  )}

                  {/* Scholarly Citation Box */}
                  <div
                    style={{
                      background: "var(--canvas-soft)",
                      border: "1px solid var(--hairline)",
                      borderRadius: 6,
                      padding: "8px 12px",
                      fontSize: "0.85rem",
                      color: "var(--ink-secondary)",
                      fontFamily: "monospace",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      gap: 12
                    }}
                  >
                    <span>{s.citation_text}</span>
                    <button
                      type="button"
                      onClick={() => handleCopyCitation(s)}
                      style={{
                        background: "none",
                        border: "none",
                        cursor: "pointer",
                        color: copiedId === s.id ? "green" : "var(--primary)",
                        display: "flex",
                        alignItems: "center",
                        gap: 4,
                        fontSize: "0.8rem",
                        fontWeight: 600,
                        whiteSpace: "nowrap"
                      }}
                    >
                      {copiedId === s.id ? (
                        <>
                          <Check size={14} /> تم النسخ
                        </>
                      ) : (
                        <>
                          <Copy size={14} /> نسخ الاستشهاد
                        </>
                      )}
                    </button>
                  </div>
                </div>

                {/* Counts Badge */}
                <div style={{ textAlign: "left", minWidth: 120 }}>
                  <div style={{ background: "var(--canvas-soft)", padding: "10px 14px", borderRadius: 8 }}>
                    <p style={{ margin: 0, fontSize: "1.1rem", fontWeight: 700 }}>
                      {s.entries_count}
                    </p>
                    <p style={{ margin: "2px 0 6px", fontSize: "0.75rem", color: "var(--ink-mute)" }}>
                      كلمة مسندة
                    </p>
                    <p style={{ margin: 0, fontSize: "1rem", fontWeight: 700 }}>
                      {s.segments_count}
                    </p>
                    <p style={{ margin: "2px 0 0", fontSize: "0.75rem", color: "var(--ink-mute)" }}>
                      شاهد نصي
                    </p>
                  </div>

                  {s.url && (
                    <a
                      href={s.url}
                      target="_blank"
                      rel="noreferrer"
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 4,
                        marginTop: 8,
                        fontSize: "0.8rem",
                        color: "var(--primary)",
                        textDecoration: "none"
                      }}
                    >
                      <ExternalLink size={12} /> رابط المصدر
                    </a>
                  )}
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </PublicShell>
  );
}
