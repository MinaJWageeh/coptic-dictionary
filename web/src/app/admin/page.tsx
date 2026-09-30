"use client";

import { useQuery } from "@tanstack/react-query";
import { Download, Users } from "lucide-react";
import { AppShell, PageHeading } from "@/components/app-shell";
import { ProtectedRoute } from "@/components/protected-route";
import { DataTable } from "@/components/data-table";
import { apiFetch, API_BASE_URL, type ResourceItem } from "@/lib/api";
import { getSession } from "@/lib/auth";

interface EvaluationMetrics {
  total_reviews: number;
  approved_count: number;
  corrected_count: number;
  rejected_count: number;
  approval_rate: number;
  correction_rate: number;
  rejection_rate: number;
  average_model_confidence: number;
  average_target_similarity: number;
}

interface ReviewerStat {
  user_id: number | null;
  display_name: string;
  email: string | null;
  approved_count: number;
  rejected_count: number;
  corrected_count: number;
  total_reviewed: number;
  last_review_at: string | null;
}

interface WorkloadDashboard {
  total_pending_drafts: number;
  total_approved_candidates: number;
  total_rejected_candidates: number;
  total_translation_requests: number;
  reviewers: ReviewerStat[];
  average_confidence: number;
}

export default function AdminDashboardPage() {
  const requests = useQuery({
    queryKey: ["translation-requests"],
    queryFn: () => apiFetch<ResourceItem[]>("/review/translation-requests")
  });
  const candidates = useQuery({
    queryKey: ["translation-candidates"],
    queryFn: () => apiFetch<ResourceItem[]>("/review/translation-candidates")
  });
  const evaluation = useQuery({
    queryKey: ["evaluation-metrics"],
    queryFn: () => apiFetch<EvaluationMetrics>("/admin/evaluation/metrics")
  });
  const workload = useQuery({
    queryKey: ["admin-workload"],
    queryFn: () => apiFetch<WorkloadDashboard>("/admin/workload")
  });

  const requestRows = Array.isArray(requests.data) ? requests.data : [];
  const candidateRows = Array.isArray(candidates.data) ? candidates.data : [];
  const draftCount = candidateRows.filter((row) => row.review_status === "draft").length;
  const evalMetrics = evaluation.data;
  const workloadData = workload.data;

  const downloadFile = async (endpoint: string, filename: string) => {
    try {
      const session = getSession();
      const res = await fetch(`${API_BASE_URL}${endpoint}`, {
        headers: session?.token ? { Authorization: `Bearer ${session.token}` } : {}
      });
      if (!res.ok) throw new Error("Failed to download file");
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      alert("حدث خطأ أثناء تحميل الملف: " + String(err));
    }
  };

  return (
    <ProtectedRoute allowedRoles={["admin", "reviewer"]}>
      <AppShell>
        <PageHeading
          title="لوحة التحكم"
          description="نظرة تشغيلية شاملة على تغطية القاموس، وعبء عمل المراجعين، والتصدير المجمع."
        />
        <div className="grid metrics" style={{ marginBottom: 20 }}>
          <div className="panel metric">
            <p className="metric-value">{requestRows.length}</p>
            <p className="metric-label">طلبات الترجمة</p>
          </div>
          <div className="panel metric">
            <p className="metric-value">{candidateRows.length}</p>
            <p className="metric-label">المرشحات الناتجة</p>
          </div>
          <div className="panel metric">
            <p className="metric-value">{draftCount}</p>
            <p className="metric-label">مسودات تنتظر المراجعة</p>
          </div>
          <div className="panel metric">
            <p className="metric-value">
              {candidateRows.length
                ? Math.round(
                    (candidateRows.reduce((sum, row) => sum + Number(row.confidence || 0), 0) /
                      candidateRows.length) *
                      100
                  )
                : 0}
              %
            </p>
            <p className="metric-label">متوسط الثقة</p>
          </div>
        </div>

        {/* Phase 4 Reviewer Workload Dashboard */}
        {workloadData && (
          <div className="panel" style={{ marginBottom: 24, padding: "16px 20px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
              <Users size={18} style={{ color: "var(--primary)" }} />
              <h3 style={{ margin: 0, fontSize: "1.1rem", fontWeight: 700 }}>
                لوحة عبء عمل المراجعين والمدققين (Reviewer Workload)
              </h3>
            </div>
            <p style={{ margin: "0 0 16px", color: "var(--ink-mute)", fontSize: "0.85rem" }}>
              متابعة توزيع المهام، ومعدل الإنجاز لكل مدقق، والمسودات قيد المراجعة.
            </p>

            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.9rem" }}>
                <thead>
                  <tr style={{ borderBottom: "2px solid var(--hairline)", textAlign: "right" }}>
                    <th style={{ padding: "8px" }}>المراجع / المدقق</th>
                    <th style={{ padding: "8px" }}>إجمالي المراجعات</th>
                    <th style={{ padding: "8px" }}>معتمد مباشرة</th>
                    <th style={{ padding: "8px" }}>مصحح لغوياً</th>
                    <th style={{ padding: "8px" }}>مرفوض</th>
                    <th style={{ padding: "8px" }}>آخر نشاط</th>
                  </tr>
                </thead>
                <tbody>
                  {workloadData.reviewers.map((r) => (
                    <tr key={r.user_id ?? r.display_name} style={{ borderBottom: "1px solid var(--hairline)" }}>
                      <td style={{ padding: "10px 8px", fontWeight: 600 }}>
                        {r.display_name}
                        {r.email && <span style={{ color: "var(--ink-mute)", fontSize: "0.8rem", display: "block" }}>{r.email}</span>}
                      </td>
                      <td style={{ padding: "10px 8px" }}><strong>{r.total_reviewed}</strong></td>
                      <td style={{ padding: "10px 8px", color: "green" }}>{r.approved_count}</td>
                      <td style={{ padding: "10px 8px", color: "blue" }}>{r.corrected_count}</td>
                      <td style={{ padding: "10px 8px", color: "red" }}>{r.rejected_count}</td>
                      <td style={{ padding: "10px 8px", color: "var(--ink-mute)", fontSize: "0.8rem" }}>
                        {r.last_review_at ? new Date(r.last_review_at).toLocaleDateString("ar-EG") : "لا يوجد"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Phase 4 Bulk Import/Export & Phase 3 Evaluation Actions */}
        <div className="panel" style={{ marginBottom: 24, padding: "16px 20px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 12 }}>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                <Download size={18} style={{ color: "var(--primary)" }} />
                <h3 style={{ margin: 0, fontSize: "1.1rem", fontWeight: 700 }}>
                  التصدير المجمع وبيانات التقييم (Bulk Export & Datasets)
                </h3>
              </div>
              <p style={{ margin: 0, color: "var(--ink-mute)", fontSize: "0.85rem" }}>
                تصدير محتوى القاموس، والشواهد المتوازية، وبيانات تدريب نماذج الذكاء الاصطناعي.
              </p>
            </div>

            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
              <button
                type="button"
                className="button"
                onClick={() => downloadFile("/admin/export/dictionary?format=csv", "coptic_dictionary.csv")}
              >
                تصدير القاموس (CSV)
              </button>
              <button
                type="button"
                className="button"
                onClick={() => downloadFile("/admin/export/dictionary?format=json", "coptic_dictionary.json")}
              >
                تصدير القاموس (JSON)
              </button>
              <button
                type="button"
                className="button"
                onClick={() => downloadFile("/admin/export/segments?format=csv", "coptic_parallel_segments.csv")}
              >
                تصدير الشواهد (CSV)
              </button>
              <button
                type="button"
                className="button"
                onClick={() => downloadFile("/admin/evaluation/dataset?format=jsonl", "coptic_eval_dataset.jsonl")}
              >
                تصدير التدريب (JSONL)
              </button>
            </div>
          </div>

          {evalMetrics && (
            <div className="grid metrics" style={{ margin: "16px 0 0" }}>
              <div className="panel metric" style={{ background: "var(--canvas-soft)" }}>
                <p className="metric-value">{evalMetrics.total_reviews}</p>
                <p className="metric-label">إجمالي تقييمات المراجعين</p>
              </div>
              <div className="panel metric" style={{ background: "var(--canvas-soft)" }}>
                <p className="metric-value">{evalMetrics.approval_rate}%</p>
                <p className="metric-label">نسبة الاعتماد المباشر</p>
              </div>
              <div className="panel metric" style={{ background: "var(--canvas-soft)" }}>
                <p className="metric-value">{evalMetrics.correction_rate}%</p>
                <p className="metric-label">نسبة التصحيح البشري</p>
              </div>
              <div className="panel metric" style={{ background: "var(--canvas-soft)" }}>
                <p className="metric-value">{Math.round(evalMetrics.average_target_similarity * 100)}%</p>
                <p className="metric-label">دقة مطابقة الهدف</p>
              </div>
            </div>
          )}
        </div>

        <DataTable
          columns={["id", "input_text", "normalized_input_text", "status", "created_at"]}
          rows={requestRows.slice(0, 10)}
        />
      </AppShell>
    </ProtectedRoute>
  );
}
