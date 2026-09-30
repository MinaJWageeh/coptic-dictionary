"use client";

import { AlertTriangle, BookOpen, CheckCircle2, FileText, HelpCircle, Scale } from "lucide-react";
import type {
  GrammarNote,
  LiteralBreakdownItem,
  SimilarExample,
  TranslateResponse,
  TranslationWordResult
} from "@/lib/translation-types";
import { dialectTextAr } from "@/lib/dialects";

function percent(value: number | undefined) {
  return Math.round(Math.max(0, Math.min(1, value || 0)) * 100);
}

function textValue(value: unknown, fallback = "غير متاح") {
  if (value === null || value === undefined || value === "") return fallback;
  return String(value);
}

function statusText(value: unknown) {
  const statuses: Record<string, string> = {
    approved: "معتمدة",
    draft: "مسودة",
    pending: "قيد المراجعة",
    rejected: "مرفوضة",
    completed: "مكتملة",
    queued: "في الانتظار",
    known: "معروفة",
    unknown: "غير معروفة",
    noun: "اسم",
    verb: "فعل",
    adjective: "صفة",
    adverb: "حال",
    pronoun: "ضمير",
    preposition: "حرف جر",
    conjunction: "حرف عطف",
    particle: "أداة",
    phrase: "عبارة",
    unknown_part_of_speech: "نوع غير محدد"
  };
  const key = String(value || "").toLowerCase();
  return statuses[key] || textValue(value);
}

function referenceText(value: unknown) {
  const references: Record<string, string> = {
    dictionary_entries: "مدخل قاموسي",
    parallel_segments: "مثال موازي",
    grammar_rules: "قاعدة نحوية",
    arabic_senses: "معنى عربي",
    sources: "مصدر",
    reference: "مرجع"
  };
  const key = String(value || "").toLowerCase();
  return references[key] || textValue(value, "مرجع");
}

export function TranslationResultCard({ result, inputText }: { result: TranslateResponse; inputText: string }) {
  const confidence = percent(result.confidence);
  const lowConfidence = result.needs_human_review || result.confidence < 0.6;
  const shownTranslation = result.translation || result.candidate_translation;

  return (
    <section className="result-card">
      <div className="result-summary">
        <div>
          <p className="eyebrow">{result.input_type === "word" ? "نتيجة قاموسية" : "ترجمة جملة مقترحة"}</p>
          <h2 className="coptic-title">{shownTranslation || "لا توجد ترجمة كاملة موثقة"}</h2>
          <p className="result-source-text" dir="rtl">
            {inputText}
          </p>
        </div>
        <div className="confidence-widget" aria-label={`Confidence ${confidence}%`}>
          <span>{confidence}%</span>
          <div className="confidence-track">
            <i style={{ width: `${confidence}%` }} />
          </div>
          <small>درجة الثقة</small>
        </div>
      </div>

      {lowConfidence ? (
        <div className="notice warning">
          <AlertTriangle size={18} />
          <span>{result.human_review_reason || "درجة الثقة منخفضة، والترجمة تحتاج مراجعة بشرية قبل اعتمادها."}</span>
        </div>
      ) : null}

      <div className="status-row">
        <span className={`status ${result.status}`}>حالة المراجعة: {statusText(result.status)}</span>
        <span className="status draft">الترجمات الجديدة لا تعتمد تلقائيًا</span>
      </div>

      {result.input_type === "word" ? <WordResult result={result} /> : <SentenceResult result={result} />}

      <ReferenceList references={result.references} />
    </section>
  );
}

function WordResult({ result }: { result: TranslateResponse }) {
  if (!result.word_results.length) {
    return (
      <div className="empty-state compact">
        <HelpCircle size={18} />
        <span>لم يتم العثور على ترجمة قاموسية موثقة لهذه الكلمة.</span>
      </div>
    );
  }

  return (
    <div className="result-grid">
      {result.word_results.map((word, index) => (
        <article className="word-card" key={index}>
          <div>
            <h3 className="coptic-word">{textValue(word.coptic_word || word.coptic_text)}</h3>
            <p>{textValue(word.meaning, "لا يوجد معنى عربي مرفق")}</p>
          </div>
          <dl className="meta-list">
            <div>
              <dt>نوع الكلمة</dt>
              <dd>{statusText(word.part_of_speech)}</dd>
            </div>
            <div>
              <dt>اللهجة</dt>
              <dd>{dialectTextAr(textValue(word.dialect || word.dialect_name, ""))}</dd>
            </div>
            <div>
              <dt>المصدر</dt>
              <dd>{textValue(word.source || word.source_title)}</dd>
            </div>
            <div>
              <dt>الثقة</dt>
              <dd>{percent(typeof word.confidence === "number" ? word.confidence : result.confidence)}%</dd>
            </div>
          </dl>
          <Examples rows={(word.examples || []) as SimilarExample[]} />
        </article>
      ))}
    </div>
  );
}

function SentenceResult({ result }: { result: TranslateResponse }) {
  return (
    <div className="sentence-layout">
      <section className="result-section">
        <h3>
          <Scale size={18} />
          المعنى الحرفي
        </h3>
        {result.literal_breakdown.length ? (
          <div className="breakdown-list">
            {result.literal_breakdown.map((item, index) => (
              <BreakdownItem item={item} key={index} />
            ))}
          </div>
        ) : (
          <p className="muted">لا يوجد تحليل حرفي كاف من القاموس.</p>
        )}
      </section>

      <section className="result-section">
        <h3>
          <BookOpen size={18} />
          الكلمات المستخدمة
        </h3>
        {result.word_results.length ? (
          <div className="chip-list">
            {result.word_results.map((word, index) => (
              <span className="reference-chip" key={index}>
                {textValue(word.coptic_word || word.coptic_text)} · {textValue(word.meaning, "معنى")}
              </span>
            ))}
          </div>
        ) : (
          <p className="muted">لا توجد كلمات قاموسية كافية لتكوين ترجمة آمنة.</p>
        )}
      </section>

      {result.unknown_words.length ? (
        <section className="result-section">
          <h3>
            <HelpCircle size={18} />
            كلمات غير معروفة
          </h3>
          <div className="chip-list">
            {result.unknown_words.map((word) => (
              <span className="unknown-chip" key={word}>
                {word}
              </span>
            ))}
          </div>
        </section>
      ) : null}

      <section className="result-section">
        <h3>
          <FileText size={18} />
          أمثلة مشابهة
        </h3>
        <Examples rows={result.similar_examples} />
      </section>

      <section className="result-section">
        <h3>
          <CheckCircle2 size={18} />
          ملاحظات نحوية
        </h3>
        <GrammarNotes rows={result.grammar_notes} />
      </section>
    </div>
  );
}

function BreakdownItem({ item }: { item: LiteralBreakdownItem }) {
  return (
    <div className="breakdown-item">
      <span dir="rtl">{textValue(item.arabic || item.token)}</span>
      <strong className="coptic-text">{textValue(item.coptic || item.coptic_word, "غير معروف")}</strong>
      <small>{item.meaning ? textValue(item.meaning) : statusText(item.status || "من القاموس")}</small>
    </div>
  );
}

function Examples({ rows }: { rows: SimilarExample[] }) {
  if (!rows.length) return <p className="muted">لا توجد أمثلة مشابهة كافية.</p>;
  return (
    <div className="example-list">
      {rows.slice(0, 5).map((example, index) => (
        <article className="example-card" key={example.id || index}>
          <p dir="rtl">{textValue(example.arabic_text, "مثال عربي غير متاح")}</p>
          <strong className="coptic-text">{textValue(example.coptic_text, "لا يوجد نص قبطي")}</strong>
          <small>
            {typeof example.similarity === "number" || typeof example.similarity_score === "number"
              ? `تشابه ${percent((example.similarity || example.similarity_score) as number)}%`
              : `مصدر #${textValue(example.source_id, "-")}`}
          </small>
        </article>
      ))}
    </div>
  );
}

function GrammarNotes({ rows }: { rows: GrammarNote[] }) {
  if (!rows.length) return <p className="muted">لا توجد قاعدة نحوية مطابقة بما يكفي.</p>;
  return (
    <div className="note-list">
      {rows.slice(0, 5).map((note, index) => (
        <article className="note-card" key={note.id || index}>
          <strong>{textValue(note.title || note.rule_code, "قاعدة نحوية")}</strong>
          <p>{textValue(note.description || note.note, "لا يوجد وصف")}</p>
        </article>
      ))}
    </div>
  );
}

function ReferenceList({ references }: { references: TranslateResponse["references"] }) {
  return (
    <section className="result-section">
      <h3>
        <BookOpen size={18} />
        المراجع من قاعدة البيانات
      </h3>
      {references.length ? (
        <div className="chip-list">
          {references.map((reference, index) => (
            <span className="reference-chip" key={index}>
              {referenceText(reference.table || reference.type || "reference")} #{textValue(reference.id || index + 1)}
            </span>
          ))}
        </div>
      ) : (
        <p className="muted">لم يرجع النظام مراجع كافية، لذلك لا يجب اعتماد النتيجة.</p>
      )}
    </section>
  );
}
