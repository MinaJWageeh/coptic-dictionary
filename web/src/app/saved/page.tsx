"use client";

import { Trash2 } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { PublicShell } from "@/components/public-shell";
import { listSavedTranslations, removeTranslation, type SavedTranslation } from "@/lib/saved-translations";
import { valueLabelAr } from "@/lib/labels";

export default function SavedTranslationsPage() {
  const [items, setItems] = useState<SavedTranslation[]>([]);

  useEffect(() => {
    setItems(listSavedTranslations());
  }, []);

  return (
    <PublicShell>
      <section className="page-intro">
        <p className="eyebrow">المحفوظات</p>
        <h1>الترجمات التي حفظتها.</h1>
        <p>الحفظ محلي داخل المتصفح لتسهيل مراجعة النتائج والعودة إليها أثناء الاختبار.</p>
      </section>

      {items.length ? (
        <div className="saved-list">
          {items.map((item) => (
            <article className="saved-item" key={item.id}>
              <div>
                <span className={`status ${item.result.status}`}>{valueLabelAr(item.result.status)}</span>
                <h2 dir="rtl">{item.inputText}</h2>
                <p className="coptic-text">{item.result.translation || item.result.candidate_translation || "لا توجد ترجمة كاملة"}</p>
                <small>
                  {item.dialectName || "البحيرية"} · ثقة {Math.round(item.result.confidence * 100)}% ·{" "}
                  {new Date(item.createdAt).toLocaleString("ar-EG")}
                </small>
              </div>
              <div className="saved-actions">
                <Link className="button" href={`/results/${item.id}`}>
                  عرض
                </Link>
                <button
                  className="button danger"
                  onClick={() => {
                    removeTranslation(item.id);
                    setItems(listSavedTranslations());
                  }}
                >
                  <Trash2 size={16} />
                  حذف
                </button>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <div className="empty-state">
          لا توجد ترجمات محفوظة بعد.
          <Link className="button primary" href="/translate">
            ابدأ بترجمة
          </Link>
        </div>
      )}
    </PublicShell>
  );
}
