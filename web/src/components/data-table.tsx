"use client";

import { ChevronLeft, ChevronRight, Search } from "lucide-react";
import { useMemo, useState } from "react";
import type { ResourceItem } from "@/lib/api";
import { labelAr, valueLabelAr } from "@/lib/labels";

function stringify(value: unknown) {
  if (value === null || value === undefined) return "";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

export function DataTable({
  columns,
  rows,
  onEdit,
  onDelete,
  filters
}: {
  columns: string[];
  rows: ResourceItem[];
  onEdit?: (item: ResourceItem) => void;
  onDelete?: (item: ResourceItem) => void;
  filters?: React.ReactNode;
}) {
  const [search, setSearch] = useState("");
  const [dialect, setDialect] = useState("");
  const [status, setStatus] = useState("");
  const [sourceId, setSourceId] = useState("");
  const [minConfidence, setMinConfidence] = useState("");
  const [createdAt, setCreatedAt] = useState("");
  const [page, setPage] = useState(1);
  const pageSize = 8;

  const filtered = useMemo(() => {
    const needle = search.trim().toLowerCase();
    return rows.filter((row) => {
      const matchesSearch =
        !needle || columns.some((column) => stringify(row[column]).toLowerCase().includes(needle));
      const matchesDialect =
        !dialect ||
        stringify(row.dialect_id).toLowerCase() === dialect ||
        stringify(row.dialect).toLowerCase().includes(dialect);
      const matchesStatus = !status || stringify(row.review_status || row.status).toLowerCase() === status;
      const matchesSource = !sourceId || stringify(row.source_id) === sourceId;
      const matchesConfidence =
        !minConfidence || Number(row.confidence || 0) >= Number(minConfidence || 0);
      const matchesCreated =
        !createdAt || stringify(row.created_at).slice(0, 10) === createdAt;
      return (
        matchesSearch &&
        matchesDialect &&
        matchesStatus &&
        matchesSource &&
        matchesConfidence &&
        matchesCreated
      );
    });
  }, [columns, rows, search, dialect, status, sourceId, minConfidence, createdAt]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const currentPage = Math.min(page, totalPages);
  const pageRows = filtered.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  return (
    <section className="panel">
      <div className="panel-header">
        <div className="toolbar">
          <div style={{ position: "relative" }}>
            <Search size={15} style={{ position: "absolute", left: 12, top: 13, color: "var(--muted)" }} />
            <input
              className="input"
              placeholder="ابحث في الجدول"
              style={{ paddingLeft: 34 }}
              value={search}
              onChange={(event) => {
                setSearch(event.target.value);
                setPage(1);
              }}
            />
          </div>
          <select className="select" aria-label="فلتر اللهجة" value={dialect} onChange={(event) => setDialect(event.target.value)}>
            <option value="">كل اللهجات</option>
            <option value="1">اللهجة #1</option>
            <option value="bohairic">البحيرية</option>
            <option value="sahidic">الصعيدية</option>
          </select>
          <select className="select" aria-label="فلتر حالة المراجعة" value={status} onChange={(event) => setStatus(event.target.value)}>
            <option value="">كل حالات المراجعة</option>
            <option value="draft">مسودة</option>
            <option value="pending">قيد المراجعة</option>
            <option value="approved">معتمدة</option>
            <option value="rejected">مرفوضة</option>
            <option value="needs_revision">تحتاج تعديل</option>
          </select>
          <input className="input" placeholder="معرف المصدر" style={{ width: 120 }} value={sourceId} onChange={(event) => setSourceId(event.target.value)} />
          <input className="input" placeholder="أقل ثقة" style={{ width: 150 }} value={minConfidence} onChange={(event) => setMinConfidence(event.target.value)} />
          <input className="input" type="date" aria-label="فلتر تاريخ الإنشاء" value={createdAt} onChange={(event) => setCreatedAt(event.target.value)} />
          {filters}
        </div>
        <span style={{ color: "var(--muted)", fontSize: 13 }}>{filtered.length} سجل</span>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              {columns.map((column) => (
                <th key={column}>{labelAr(column)}</th>
              ))}
              {(onEdit || onDelete) && <th>الإجراءات</th>}
            </tr>
          </thead>
          <tbody>
            {pageRows.length ? (
              pageRows.map((row, index) => (
                <tr key={String(row.id ?? index)}>
                  {columns.map((column) => {
                    const value = stringify(row[column]);
                    const statusClass = column.includes("status") ? `status ${value}` : "";
                    return (
                      <td key={column}>
                        {column.includes("status") ? <span className={statusClass}>{valueLabelAr(value || "none")}</span> : value}
                      </td>
                    );
                  })}
                  {(onEdit || onDelete) && (
                    <td>
                      <div className="toolbar">
                        {onEdit && (
                          <button className="button" onClick={() => onEdit(row)}>
                            تعديل
                          </button>
                        )}
                        {onDelete && (
                          <button className="button danger" onClick={() => onDelete(row)}>
                            حذف
                          </button>
                        )}
                      </div>
                    </td>
                  )}
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={columns.length + 1} style={{ color: "var(--muted)" }}>
                  لا توجد سجلات مطابقة.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      <div className="pagination">
        <span style={{ color: "var(--muted)", fontSize: 13 }}>
          صفحة {currentPage} من {totalPages}
        </span>
        <div className="toolbar">
          <button className="button" disabled={currentPage === 1} onClick={() => setPage((value) => value - 1)}>
            <ChevronLeft size={16} />
          </button>
          <button
            className="button"
            disabled={currentPage === totalPages}
            onClick={() => setPage((value) => value + 1)}
          >
            <ChevronRight size={16} />
          </button>
        </div>
      </div>
    </section>
  );
}
