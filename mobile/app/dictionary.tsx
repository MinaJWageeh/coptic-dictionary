import { useQuery } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { ActivityIndicator, StyleSheet, Text, TextInput, View } from "react-native";
import { z } from "zod";
import { getDialects, searchDictionary, searchExamples } from "../src/api";
import { DialectSelector } from "../src/components/DialectSelector";
import { Screen } from "../src/components/Screen";
import { dialectNameAr } from "../src/dialects";
import { colors, sharedStyles } from "../src/theme";

const querySchema = z.string().trim().min(1);

function valueLabelAr(value?: string | null) {
  const labels: Record<string, string> = {
    draft: "مسودة",
    pending: "قيد المراجعة",
    approved: "معتمدة",
    rejected: "مرفوضة",
    needs_revision: "تحتاج مراجعة",
    noun: "اسم",
    verb: "فعل",
    adjective: "صفة",
    adverb: "حال",
    pronoun: "ضمير",
    preposition: "حرف جر",
    conjunction: "حرف عطف",
    particle: "أداة",
    other: "أخرى"
  };
  return value ? labels[value] || value : "غير محدد";
}

export default function DictionarySearchScreen() {
  const [query, setQuery] = useState("");
  const [dialectId, setDialectId] = useState<number | null>(null);
  const parsed = querySchema.safeParse(query);

  const dialects = useQuery({
    queryKey: ["dialects"],
    queryFn: getDialects
  });

  const defaultDialect = useMemo(() => {
    const rows = dialects.data || [];
    return rows.find((dialect) => dialect.code.toLowerCase() === "bohairic") || rows[0];
  }, [dialects.data]);

  const dialectNameById = useMemo(() => {
    return new Map((dialects.data || []).map((dialect) => [dialect.id, dialectNameAr(dialect)]));
  }, [dialects.data]);

  useEffect(() => {
    if (!dialectId && defaultDialect) setDialectId(defaultDialect.id);
  }, [defaultDialect, dialectId]);

  const dictionary = useQuery({
    queryKey: ["dictionary", parsed.success ? parsed.data : "", dialectId],
    enabled: parsed.success && Boolean(dialectId),
    queryFn: () => searchDictionary(parsed.success ? parsed.data : "", dialectId)
  });

  const examples = useQuery({
    queryKey: ["examples", parsed.success ? parsed.data : "", dialectId],
    enabled: parsed.success && Boolean(dialectId),
    queryFn: () => searchExamples(parsed.success ? parsed.data : "", dialectId)
  });

  return (
    <Screen>
      <View>
        <Text style={sharedStyles.eyebrow}>القاموس والأمثلة</Text>
        <Text style={sharedStyles.title}>ابحث في الكلمات والأمثلة المعتمدة.</Text>
        <Text style={sharedStyles.subtitle}>النتائج تأتي من نفس الخادم وتعرض المصدر واللهجة والحالة.</Text>
      </View>

      <View style={sharedStyles.panel}>
        <TextInput
          onChangeText={setQuery}
          placeholder="اكتب كلمة للبحث"
          style={[sharedStyles.input, sharedStyles.arabicInput]}
          value={query}
        />
        <DialectSelector dialects={dialects.data || []} selectedId={dialectId} onSelect={setDialectId} />
      </View>

      {dictionary.isPending && parsed.success ? <ActivityIndicator color={colors.ink} /> : null}
      {dictionary.error ? <Text style={sharedStyles.error}>{(dictionary.error as Error).message}</Text> : null}

      <View style={sharedStyles.panel}>
        <Text style={styles.sectionTitle}>نتائج القاموس</Text>
        {!parsed.success ? <Text style={sharedStyles.muted}>اكتب كلمة لبدء البحث.</Text> : null}
        {dictionary.data?.length ? (
          dictionary.data.map((entry) => (
            <View style={styles.item} key={entry.id}>
              <Text style={styles.coptic}>{entry.coptic_text}</Text>
              <Text style={styles.meta}>نوع الكلمة: {valueLabelAr(entry.part_of_speech)}</Text>
              <Text style={styles.meta}>اللهجة: {dialectNameById.get(entry.dialect_id) || `#${entry.dialect_id}`} · المصدر #{entry.source_id}</Text>
              <Text style={styles.meta}>الحالة: {valueLabelAr(entry.review_status)}</Text>
              {entry.notes ? <Text style={sharedStyles.muted}>{entry.notes}</Text> : null}
            </View>
          ))
        ) : parsed.success && dictionary.data ? (
          <Text style={sharedStyles.muted}>لا توجد نتيجة قاموسية معتمدة.</Text>
        ) : null}
      </View>

      <View style={sharedStyles.panel}>
        <Text style={styles.sectionTitle}>أمثلة مشابهة</Text>
        {examples.data?.length ? (
          examples.data.slice(0, 5).map((example) => (
            <View style={styles.item} key={example.id}>
              <Text style={styles.exampleArabic}>{example.arabic_text}</Text>
              <Text style={styles.copticInline}>{example.coptic_text || "لا يوجد نص قبطي"}</Text>
              <Text style={styles.meta}>مصدر #{example.source_id} · {valueLabelAr(example.review_status)}</Text>
            </View>
          ))
        ) : parsed.success && examples.data ? (
          <Text style={sharedStyles.muted}>لا توجد أمثلة كافية.</Text>
        ) : null}
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  sectionTitle: {
    color: colors.ink,
    fontSize: 18,
    fontWeight: "800",
    textAlign: "right"
  },
  item: {
    borderTopWidth: 1,
    borderTopColor: colors.hairline,
    paddingTop: 12,
    gap: 5
  },
  coptic: {
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
  exampleArabic: {
    color: colors.body,
    textAlign: "right",
    writingDirection: "rtl",
    lineHeight: 22
  },
  meta: {
    color: colors.muted,
    textAlign: "right",
    writingDirection: "rtl"
  }
});
