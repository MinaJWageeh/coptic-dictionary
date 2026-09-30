"use client";

import { Plus } from "lucide-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { AppShell, PageHeading } from "@/components/app-shell";
import { DataTable } from "@/components/data-table";
import { ProtectedRoute } from "@/components/protected-route";
import { ResourceForm } from "@/components/resource-form";
import { apiFetch, type ResourceItem } from "@/lib/api";
import type { ResourceConfig } from "@/lib/resource-config";

function pathWithId(path: string, id: string | number) {
  return path.replace(":id", String(id));
}

function normalizeRows(data: unknown): ResourceItem[] {
  if (Array.isArray(data)) return data as ResourceItem[];
  if (data && typeof data === "object" && "items" in data && Array.isArray((data as { items: unknown }).items)) {
    return (data as { items: ResourceItem[] }).items;
  }
  return [];
}

export function ResourcePage({ resource }: { resource: ResourceConfig }) {
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState<ResourceItem | null>(null);
  const [formOpen, setFormOpen] = useState(false);

  const query = useQuery({
    queryKey: ["resource", resource.key],
    queryFn: () => apiFetch<unknown>(resource.endpoint.endsWith("=") ? `${resource.endpoint} ` : resource.endpoint)
  });

  const rows = useMemo(() => normalizeRows(query.data), [query.data]);

  const saveMutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) => {
      if (editing && resource.updateEndpoint) {
        return apiFetch(pathWithId(resource.updateEndpoint, editing.id || ""), {
          method: "PUT",
          body: JSON.stringify(payload)
        });
      }
      return apiFetch(resource.createEndpoint || resource.endpoint, {
        method: "POST",
        body: JSON.stringify(payload)
      });
    },
    onSuccess: () => {
      setEditing(null);
      setFormOpen(false);
      queryClient.invalidateQueries({ queryKey: ["resource", resource.key] });
    }
  });

  const deleteMutation = useMutation({
    mutationFn: (item: ResourceItem) =>
      apiFetch(pathWithId(resource.deleteEndpoint || "", item.id || ""), { method: "DELETE" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["resource", resource.key] })
  });

  return (
    <ProtectedRoute allowedRoles={resource.allowedRoles}>
      <AppShell>
        <PageHeading
          title={resource.title}
          description={resource.description}
          action={
            resource.createEndpoint ? (
              <button
                className="button primary"
                onClick={() => {
                  setEditing(null);
                  setFormOpen((value) => !value);
                }}
              >
                <Plus size={16} />
                جديد
              </button>
            ) : null
          }
        />
        {formOpen || editing ? (
          <section className="panel" style={{ marginBottom: 20 }}>
            <div className="panel-header">
              <strong>{editing ? "تعديل السجل" : "إنشاء سجل"}</strong>
              <button
                className="button"
                onClick={() => {
                  setEditing(null);
                  setFormOpen(false);
                }}
              >
                إغلاق
              </button>
            </div>
            <ResourceForm
              fields={resource.fields}
              schema={editing ? resource.updateSchema || resource.schema : resource.schema}
              initial={editing || undefined}
              submitLabel={editing ? "تحديث" : "إنشاء"}
              onSubmit={(payload) => saveMutation.mutate(payload)}
            />
            {saveMutation.error && <p className="error" style={{ padding: "0 18px 18px" }}>{saveMutation.error.message}</p>}
          </section>
        ) : null}
        {query.error ? (
          <section className="panel" style={{ padding: 18, marginBottom: 20 }}>
            <strong>مصدر البيانات غير متاح</strong>
            <p style={{ color: "var(--muted)" }}>
              {(query.error as Error).message}. الصفحة جاهزة عند إتاحة نقطة الخادم المطلوبة.
            </p>
          </section>
        ) : null}
        <DataTable
          columns={resource.columns}
          rows={rows}
          onEdit={resource.updateEndpoint ? (item) => setEditing(item) : undefined}
          onDelete={resource.deleteEndpoint ? (item) => deleteMutation.mutate(item) : undefined}
        />
      </AppShell>
    </ProtectedRoute>
  );
}
