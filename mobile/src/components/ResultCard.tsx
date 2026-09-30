import { StyleSheet, Text, View } from "react-native";
import type { TranslateResponse } from "../api";
import { dialectTextAr } from "../dialects";
import { colors, sharedStyles } from "../theme";

function asText(value: unknown, fallback = "غير متاح") {
  if (value === null || value === undefined || value === "") return fallback;
  return String(value);
}

function percent(value: number | undefined) {
  return Math.round(Math.max(0, Math.min(1, value || 0)) * 100);
}

function labelText(value: unknown) {
  const labels: Record<string, string> = {
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
    dictionary_entries: "مدخل قاموسي",
    parallel_segments: "مثال موازي",
    grammar_rules: "قاعدة نحوية",
    arabic_senses: "معنى عربي",
    sources: "مصدر",
    reference: "مرجع"
  };
  const key = String(value || "").toLowerCase();
  return labels[key] || asText(value);
}

export function ResultCard({ result, inputText }: { result: TranslateResponse; inputText: string }) {
  const shownTranslation = result.translation || result.candidate_translation || "لا توجد ترجمة كاملة موثقة";
  const confidence = percent(result.confidence);
  const warning = result.needs_human_review || result.status === "draft" || result.confidence < 0.55;

  return (
    <View style={sharedStyles.panel}>
      <View style={styles.summary}>
        <View style={styles.summaryText}>
          <Text style={sharedStyles.eyebrow}>{result.input_type === "word" ? "نتيجة كلمة" : "مرشح جملة"}</Text>
          <Text style={styles.copticTitle}>{shownTranslation}</Text>
          <Text style={styles.sourceText}>{inputText}</Text>
        </View>
        <View style={styles.confidence}>
          <Text style={styles.confidenceNumber}>{confidence}%</Text>
          <View style={styles.track}>
            <View style={[styles.trackFill, { width: `${confidence}%` }]} />
          </View>
          <Text style={styles.confidenceLabel}>الثقة</Text>
        </View>
      </View>

      {warning ? (
        <View style={styles.warning}>
          <Text style={styles.warningText}>
            {result.human_review_reason || "هذه الترجمة مسودة أو منخفضة الثقة وتحتاج مراجعة بشرية قبل الاعتماد."}
          </Text>
        </View>
      ) : null}

      <View style={styles.statusRow}>
        <Text style={styles.status}>الحالة: {labelText(result.status)}</Text>
        <Text style={styles.status}>{result.input_type === "word" ? "قاموس" : "جملة"}</Text>
      </View>

      {result.input_type === "word" ? <WordResult result={result} /> : <SentenceResult result={result} />}

      <Section title="المصادر من قاعدة البيانات">
        {result.references.length ? (
          <View style={styles.chipRow}>
            {result.references.map((reference, index) => (
              <Text style={styles.referenceChip} key={index}>
                {labelText(reference.table || reference.type || "reference")} #{asText(reference.id || index + 1)}
              </Text>
            ))}
          </View>
        ) : (
          <Text style={sharedStyles.muted}>لا توجد مراجع كافية، لذلك لا يجب اعتماد النتيجة.</Text>
        )}
      </Section>
    </View>
  );
}

function WordResult({ result }: { result: TranslateResponse }) {
  if (!result.word_results.length) {
    return <Text style={sharedStyles.muted}>لم يتم العثور على ترجمة قاموسية موثقة لهذه الكلمة.</Text>;
  }
  return (
    <Section title="الترجمات المحتملة">
      {result.word_results.map((word, index) => (
        <View style={styles.itemCard} key={index}>
          <Text style={styles.copticWord}>{asText(word.coptic_word || word.coptic_text)}</Text>
          <Text style={styles.itemText}>المعنى: {asText(word.meaning, "غير مرفق")}</Text>
          <Text style={styles.itemText}>نوع الكلمة: {labelText(word.part_of_speech)}</Text>
          <Text style={styles.itemText}>اللهجة: {dialectTextAr(asText(word.dialect || word.dialect_name, ""))}</Text>
          <Text style={styles.itemText}>المصدر: {asText(word.source || word.source_title)}</Text>
          <Examples rows={(word.examples || []) as Array<Record<string, unknown>>} />
        </View>
      ))}
    </Section>
  );
}

function SentenceResult({ result }: { result: TranslateResponse }) {
  return (
    <>
      <Section title="المعنى الحرفي">
        {result.literal_breakdown.length ? (
          result.literal_breakdown.map((item, index) => (
            <View style={styles.breakdownItem} key={index}>
              <Text style={styles.itemText}>{asText(item.arabic || item.token)}</Text>
              <Text style={styles.copticInline}>{asText(item.coptic || item.coptic_word, "غير معروف")}</Text>
              <Text style={styles.smallText}>{item.meaning ? asText(item.meaning) : labelText(item.status || "من القاموس")}</Text>
            </View>
          ))
        ) : (
          <Text style={sharedStyles.muted}>لا يوجد تحليل حرفي كاف من القاموس.</Text>
        )}
      </Section>

      <Section title="الكلمات المستخدمة">
        {result.word_results.length ? (
          <View style={styles.chipRow}>
            {result.word_results.map((word, index) => (
              <Text style={styles.referenceChip} key={index}>
                {asText(word.coptic_word || word.coptic_text)} · {asText(word.meaning, "معنى")}
              </Text>
            ))}
          </View>
        ) : (
          <Text style={sharedStyles.muted}>لا توجد كلمات قاموسية كافية.</Text>
        )}
      </Section>

      {result.unknown_words.length ? (
        <Section title="كلمات غير معروفة">
          <View style={styles.chipRow}>
            {result.unknown_words.map((word) => (
              <Text style={styles.unknownChip} key={word}>
                {word}
              </Text>
            ))}
          </View>
        </Section>
      ) : null}

      <Section title="أمثلة مشابهة">
        <Examples rows={result.similar_examples} />
      </Section>

      <Section title="ملاحظات نحوية">
        {result.grammar_notes.length ? (
          result.grammar_notes.slice(0, 5).map((note, index) => (
            <View style={styles.itemCard} key={index}>
              <Text style={styles.itemTitle}>{asText(note.title || note.rule_code, "قاعدة نحوية")}</Text>
              <Text style={styles.itemText}>{asText(note.description || note.note, "لا يوجد وصف")}</Text>
            </View>
          ))
        ) : (
          <Text style={sharedStyles.muted}>لا توجد قاعدة نحوية مطابقة بما يكفي.</Text>
        )}
      </Section>
    </>
  );
}

function Examples({ rows }: { rows: Array<Record<string, unknown>> }) {
  if (!rows.length) return <Text style={sharedStyles.muted}>لا توجد أمثلة كافية.</Text>;
  return (
    <View style={styles.exampleList}>
      {rows.slice(0, 5).map((example, index) => (
        <View style={styles.itemCard} key={asText(example.id, String(index))}>
          <Text style={styles.itemText}>{asText(example.arabic_text, "مثال عربي غير متاح")}</Text>
          <Text style={styles.copticInline}>{asText(example.coptic_text, "لا يوجد نص قبطي")}</Text>
          <Text style={styles.smallText}>
            {typeof example.similarity === "number" || typeof example.similarity_score === "number"
              ? `تشابه ${percent((example.similarity || example.similarity_score) as number)}%`
              : `مصدر #${asText(example.source_id, "-")}`}
          </Text>
        </View>
      ))}
    </View>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>{title}</Text>
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  summary: {
    gap: 12
  },
  summaryText: {
    gap: 8
  },
  copticTitle: {
    color: colors.ink,
    fontSize: 30,
    fontWeight: "800",
    textAlign: "left",
    writingDirection: "ltr"
  },
  sourceText: {
    color: colors.body,
    fontSize: 17,
    lineHeight: 25,
    textAlign: "right",
    writingDirection: "rtl"
  },
  confidence: {
    borderWidth: 1,
    borderColor: colors.hairline,
    borderRadius: 10,
    padding: 12,
    gap: 7
  },
  confidenceNumber: {
    color: colors.ink,
    fontSize: 28,
    fontWeight: "800",
    textAlign: "right"
  },
  confidenceLabel: {
    color: colors.muted,
    textAlign: "right"
  },
  track: {
    height: 8,
    borderRadius: 999,
    backgroundColor: "#e0e2e6",
    overflow: "hidden"
  },
  trackFill: {
    height: "100%",
    backgroundColor: colors.forest
  },
  warning: {
    borderRadius: 10,
    backgroundColor: "#fff6e5",
    padding: 12
  },
  warningText: {
    color: colors.warning,
    lineHeight: 22,
    textAlign: "right",
    writingDirection: "rtl",
    fontWeight: "700"
  },
  statusRow: {
    flexDirection: "row-reverse",
    flexWrap: "wrap",
    gap: 8
  },
  status: {
    backgroundColor: colors.surface,
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 6,
    color: colors.body,
    fontWeight: "700"
  },
  section: {
    borderTopWidth: 1,
    borderTopColor: colors.hairline,
    paddingTop: 12,
    gap: 10
  },
  sectionTitle: {
    color: colors.ink,
    fontSize: 17,
    fontWeight: "800",
    textAlign: "right",
    writingDirection: "rtl"
  },
  itemCard: {
    borderWidth: 1,
    borderColor: colors.hairline,
    borderRadius: 10,
    padding: 12,
    backgroundColor: colors.surface,
    gap: 6
  },
  itemTitle: {
    color: colors.ink,
    fontWeight: "800",
    textAlign: "right",
    writingDirection: "rtl"
  },
  itemText: {
    color: colors.body,
    lineHeight: 22,
    textAlign: "right",
    writingDirection: "rtl"
  },
  smallText: {
    color: colors.muted,
    textAlign: "right",
    writingDirection: "rtl"
  },
  copticWord: {
    color: colors.ink,
    fontSize: 26,
    fontWeight: "800",
    textAlign: "left",
    writingDirection: "ltr"
  },
  copticInline: {
    color: colors.ink,
    fontSize: 18,
    fontWeight: "800",
    textAlign: "left",
    writingDirection: "ltr"
  },
  breakdownItem: {
    borderWidth: 1,
    borderColor: colors.hairline,
    borderRadius: 10,
    padding: 10,
    gap: 4
  },
  chipRow: {
    flexDirection: "row-reverse",
    flexWrap: "wrap",
    gap: 8
  },
  referenceChip: {
    borderWidth: 1,
    borderColor: colors.hairline,
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 6,
    color: colors.body,
    backgroundColor: colors.canvas
  },
  unknownChip: {
    borderWidth: 1,
    borderColor: "#f0c36d",
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 6,
    color: colors.warning,
    backgroundColor: "#fff6e5",
    fontWeight: "800"
  },
  exampleList: {
    gap: 8
  }
});
