"use client";

import { useQuery } from "@tanstack/react-query";
import { AppShell, PageHeading } from "@/components/app-shell";
import { DataTable } from "@/components/data-table";
import { ProtectedRoute } from "@/components/protected-route";
import { apiFetch, type ResourceItem } from "@/lib/api";

export default function TranslationRequestsPage() {
  const query = useQuery({
    queryKey: ["translation-requests"],
    queryFn: () => apiFetch<ResourceItem[]>("/review/translation-requests")
  });

  return (
    <ProtectedRoute allowedRoles={["admin", "reviewer"]}>
      <AppShell>
        <PageHeading
          title="طلبات الترجمة"
          description="مراجعة النص العربي المرسل واللهجة المطلوبة وحالة المعالجة ووقت الإنشاء."
        />
        <DataTable
          columns={["id", "user_id", "input_text", "normalized_input_text", "target_dialect_id", "status", "created_at"]}
          rows={Array.isArray(query.data) ? query.data : []}
        />
      </AppShell>
    </ProtectedRoute>
  );
}
