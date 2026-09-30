"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, X } from "lucide-react";
import { useState } from "react";
import { z } from "zod";
import { AppShell, PageHeading } from "@/components/app-shell";
import { FilterBar } from "@/components/filters";
import { ProtectedRoute } from "@/components/protected-route";
import { apiFetch, type ResourceItem } from "@/lib/api";
import { valueLabelAr } from "@/lib/labels";

const correctionSchema = z.object({
  corrected_text: z.string().min(1),
  comment: z.string().optional()
});

export default function ReviewQueuePage() {
  const queryClient = useQueryClient();
  const [corrections, setCorrections] = useState<Record<string, string>>({});
  const [comments, setComments] = useState<Record<string, string>>({});
  const [error, setError] = useState("");

  const query = useQuery({
    queryKey: ["translation-candidates"],
    queryFn: () => apiFetch<ResourceItem[]>("/review/translation-candidates")
  });

  const candidates = Array.isArray(query.data)
    ? query.data.filter((item) => item.review_status === "draft" || item.review_status === "pending")
    : [];

  const approve = useMutation({
    mutationFn: (id: string | number) => apiFetch(`/review/translation/${id}/approve`, { method: "POST" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["translation-candidates"] })
  });

  const reject = useMutation({
    mutationFn: (id: string | number) =>
      apiFetch(`/review/translation/${id}/reject`, {
        method: "POST",
        body: JSON.stringify({ comment: comments[String(id)] || "مرفوض من لوحة الإدارة" })
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["translation-candidates"] })
  });

  const correct = useMutation({
    mutationFn: ({ id, payload }: { id: string | number; payload: { corrected_text: string; comment?: string } }) =>
      apiFetch(`/review/translation/${id}/correct`, {
        method: "POST",
        body: JSON.stringify(payload)
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["translation-candidates"] })
  });

  return (
    <ProtectedRoute allowedRoles={["admin", "reviewer"]}>
      <AppShell>
        <PageHeading
          title="طابور مراجعة الترجمات"
          description="اعتماد أو رفض أو تصحيح مرشحات الترجمة المسودة مع عرض الثقة والمراجع أثناء المراجعة."
        />
        <section className="panel" style={{ marginBottom: 20 }}>
          <div className="panel-header">
            <div className="toolbar">
              <FilterBar />
            </div>
            <span style={{ color: "var(--muted)", fontSize: 13 }}>{candidates.length} مرشح ينتظر المراجعة</span>
          </div>
          {candidates.length ? (
            candidates.map((candidate) => {
              const id = String(candidate.id);
              const evidence = candidate.evidence as
                | {
                    references?: Array<{ table: string; id: number }>;
                    literal_breakdown?: Array<Record<string, unknown>>;
                    parallel_segment_ids?: number[];
                    grammar_rule_ids?: number[];
                  }
                | undefined;
              return (
                <article className="review-card" key={id}>
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 16 }}>
                    <div>
                      <strong>مرشح #{id}</strong>
                      <p style={{ margin: "6px 0 0", fontSize: 18 }}>{String(candidate.candidate_text || "لا يوجد مرشح آمن")}</p>
                    </div>
                    <span className="status draft">الثقة {Number(candidate.confidence || 0).toFixed(2)}</span>
                  </div>
                  <div className="reference-list">
                    {(evidence?.references || []).map((reference, index) => (
                      <span className="reference-chip" key={`${reference.table}-${reference.id}-${index}`}>
                        {valueLabelAr(reference.table)} #{reference.id}
                      </span>
                    ))}
                    {(evidence?.parallel_segment_ids || []).map((reference) => (
                      <span className="reference-chip" key={`segment-${reference}`}>
                        مثال موازي #{reference}
                      </span>
                    ))}
                    {(evidence?.grammar_rule_ids || []).map((reference) => (
                      <span className="reference-chip" key={`grammar-${reference}`}>
                        قاعدة نحوية #{reference}
                      </span>
                    ))}
                  </div>
                  {evidence?.literal_breakdown ? (
                    <pre style={{ whiteSpace: "pre-wrap", background: "var(--surface)", padding: 12, borderRadius: 8 }}>
                      {JSON.stringify(evidence.literal_breakdown, null, 2)}
                    </pre>
                  ) : null}
                  <div className="form-grid" style={{ padding: 0 }}>
                    <div className="field full">
                      <label>التصحيح</label>
                      <textarea
                        className="textarea"
                        value={corrections[id] ?? String(candidate.candidate_text || "")}
                        onChange={(event) => setCorrections((current) => ({ ...current, [id]: event.target.value }))}
                      />
                    </div>
                    <div className="field full">
                      <label>تعليق المراجع</label>
                      <input
                        className="input"
                        value={comments[id] ?? ""}
                        onChange={(event) => setComments((current) => ({ ...current, [id]: event.target.value }))}
                      />
                    </div>
                  </div>
                  <div className="toolbar">
                    <button className="button primary" onClick={() => approve.mutate(candidate.id || id)}>
                      <Check size={16} />
                      اعتماد
                    </button>
                    <button className="button" onClick={() => reject.mutate(candidate.id || id)}>
                      <X size={16} />
                      رفض
                    </button>
                    <button
                      className="button"
                      onClick={() => {
                        const parsed = correctionSchema.safeParse({
                          corrected_text: corrections[id] ?? String(candidate.candidate_text || ""),
                          comment: comments[id]
                        });
                        if (!parsed.success) {
                          setError("نص التصحيح مطلوب.");
                          return;
                        }
                        setError("");
                        correct.mutate({ id: candidate.id || id, payload: parsed.data });
                      }}
                    >
                      تصحيح واعتماد
                    </button>
                  </div>
                </article>
              );
            })
          ) : (
            <div style={{ padding: 18, color: "var(--muted)" }}>لا توجد مرشحات مسودة تنتظر المراجعة.</div>
          )}
        </section>
        {error && <p className="error">{error}</p>}
      </AppShell>
    </ProtectedRoute>
  );
}
