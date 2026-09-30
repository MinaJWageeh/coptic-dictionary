"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowLeft, Loader2, Save, Send } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";
import { z } from "zod";
import { PublicShell } from "@/components/public-shell";
import { TranslationResultCard } from "@/components/translation-result-card";
import { apiFetch } from "@/lib/api";
import { dialectNameAr } from "@/lib/dialects";
import {
  getTranslationId,
  saveTranslation,
  storeLastTranslation,
  type SavedTranslation
} from "@/lib/saved-translations";
import type { Dialect, TranslateResponse } from "@/lib/translation-types";

const translateSchema = z.object({
  text: z.string().trim().min(1, "اكتب كلمة أو جملة عربية أولًا."),
  target_dialect_id: z.coerce.number().int().positive("اختر لهجة صحيحة.").optional()
});

function friendlyError(message: string) {
  try {
    const parsed = JSON.parse(message);
    if (parsed && typeof parsed.detail === "string") {
      message = parsed.detail;
    }
  } catch {
    // not json
  }
  if (message.includes("401") || message.toLowerCase().includes("not authenticated") || message.toLowerCase().includes("invalid token")) {
    return "انتهت صلاحية الجلسة، تم تحديث الاتصال تلقائياً. يرجى الضغط على «ترجم» مرة أخرى.";
  }
  return message;
}

export default function TranslatePage() {
  const [text, setText] = useState("");
  const [dialectId, setDialectId] = useState<number | "">("");
  const [formError, setFormError] = useState("");
  const [lastItem, setLastItem] = useState<SavedTranslation | null>(null);
  const [saved, setSaved] = useState(false);

  const dialects = useQuery({
    queryKey: ["dialects"],
    queryFn: () => apiFetch<Dialect[]>("/dialects", { auth: false })
  });

  const defaultDialect = useMemo(() => {
    const rows = Array.isArray(dialects.data) ? dialects.data : [];
    return rows.find((row) => row.code.toLowerCase() === "bohairic") || rows[0];
  }, [dialects.data]);

  const selectedDialectId = dialectId || defaultDialect?.id || "";
  const selectedDialect = (dialects.data || []).find((dialect) => dialect.id === Number(selectedDialectId));

  const translate = useMutation({
    mutationFn: (payload: z.infer<typeof translateSchema>) =>
      apiFetch<TranslateResponse>("/translate", {
        method: "POST",
        body: JSON.stringify(payload)
      }),
    onSuccess: (result, payload) => {
      const item = {
        id: getTranslationId(result),
        createdAt: new Date().toISOString(),
        inputText: payload.text,
        dialectName: dialectNameAr(selectedDialect || defaultDialect),
        result
      };
      setLastItem(item);
      setSaved(false);
      storeLastTranslation(item);
    }
  });

  return (
    <PublicShell>
      <section className="page-intro">
        <p className="eyebrow">ترجمة موثقة</p>
        <h1>اكتب كلمة أو جملة عربية.</h1>
        <p>
          الكلمة تُبحث في القاموس مباشرة، والجملة تنتج مرشحًا مسودة مدعومًا بأمثلة وقواعد ومراجع
          من قاعدة البيانات.
        </p>
      </section>

      <section className="translator-surface">
        <form
          className="translator-form"
          onSubmit={(event) => {
            event.preventDefault();
            const parsed = translateSchema.safeParse({
              text,
              target_dialect_id: selectedDialectId ? Number(selectedDialectId) : undefined
            });
            if (!parsed.success) {
              setFormError(parsed.error.issues[0]?.message || "بيانات غير صالحة.");
              return;
            }
            setFormError("");
            translate.mutate(parsed.data);
          }}
        >
          <label className="field full">
            <span>النص العربي</span>
            <textarea
              className="textarea arabic-input"
              dir="rtl"
              value={text}
              onChange={(event) => setText(event.target.value)}
              placeholder="مثال: الله محبة"
            />
          </label>
          <label className="field">
            <span>اللهجة القبطية</span>
            <select
              className="input"
              disabled={dialects.isPending}
              value={selectedDialectId}
              onChange={(event) => setDialectId(Number(event.target.value))}
            >
              {(dialects.data || []).map((dialect) => (
                <option key={dialect.id} value={dialect.id}>
                  {dialectNameAr(dialect)} {dialect.code.toLowerCase() === "bohairic" ? "(الافتراضية)" : ""}
                </option>
              ))}
            </select>
          </label>
          <button className="button primary translate-button" disabled={translate.isPending || !selectedDialectId}>
            {translate.isPending ? <Loader2 className="spin" size={16} /> : <Send size={16} />}
            {translate.isPending ? "جار الترجمة..." : "ترجم"}
          </button>
        </form>
        {formError ? <p className="error">{formError}</p> : null}
        {dialects.error ? <p className="error">تعذر تحميل اللهجات: {(dialects.error as Error).message}</p> : null}
        {translate.error ? <p className="error">{friendlyError(translate.error.message)}</p> : null}
      </section>

      {lastItem ? (
        <div className="result-actions">
          <button
            className="button"
            onClick={() => {
              saveTranslation(lastItem);
              setSaved(true);
            }}
          >
            <Save size={16} />
            {saved ? "تم الحفظ" : "احفظ النتيجة"}
          </button>
          <Link className="button" href={`/results/${lastItem.id}`}>
            افتح صفحة النتيجة
            <ArrowLeft size={16} />
          </Link>
        </div>
      ) : null}

      {lastItem ? <TranslationResultCard inputText={lastItem.inputText} result={lastItem.result} /> : null}
    </PublicShell>
  );
}
