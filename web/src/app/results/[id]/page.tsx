"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { PublicShell } from "@/components/public-shell";
import { TranslationResultCard } from "@/components/translation-result-card";
import { findSavedTranslation, type SavedTranslation } from "@/lib/saved-translations";

export default function TranslationResultPage() {
  const params = useParams<{ id: string }>();
  const [item, setItem] = useState<SavedTranslation | null>(null);

  useEffect(() => {
    setItem(findSavedTranslation(params.id));
  }, [params.id]);

  return (
    <PublicShell>
      <section className="page-intro">
        <p className="eyebrow">صفحة النتيجة</p>
        <h1>تفاصيل الترجمة والمراجع.</h1>
        <p>هذه الصفحة تعرض آخر نتيجة مترجمة أو نتيجة محفوظة محليًا على جهازك.</p>
      </section>

      {item ? (
        <TranslationResultCard inputText={item.inputText} result={item.result} />
      ) : (
        <div className="empty-state">
          لا توجد نتيجة بهذا المعرف في المحفوظات المحلية.
          <Link className="button primary" href="/translate">
            ارجع للترجمة
          </Link>
        </div>
      )}
    </PublicShell>
  );
}
