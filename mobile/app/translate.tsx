import { useMutation, useQuery } from "@tanstack/react-query";
import { router } from "expo-router";
import { useEffect, useMemo, useState } from "react";
import { ActivityIndicator, StyleSheet, Text, TextInput, View } from "react-native";
import { z } from "zod";
import { getDialects, translate } from "../src/api";
import { DialectSelector } from "../src/components/DialectSelector";
import { PrimaryButton, Screen } from "../src/components/Screen";
import { dialectNameAr } from "../src/dialects";
import {
  getSession,
  getLastTranslation,
  getTranslationDraft,
  getTranslationId,
  saveLastTranslation,
  saveTranslationDraft,
  type SavedTranslation,
  type Session
} from "../src/storage";
import { colors, sharedStyles } from "../src/theme";

const schema = z.object({
  text: z.string().trim().min(1, "اكتب كلمة أو جملة عربية أولًا."),
  targetDialectId: z.number().int().positive("اختر لهجة صحيحة.")
});

export default function TranslateScreen() {
  const [text, setText] = useState("");
  const [dialectId, setDialectId] = useState<number | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [error, setError] = useState("");
  const [draftLoaded, setDraftLoaded] = useState(false);

  useEffect(() => {
    getSession().then(setSession);
    getTranslationDraft().then((draft) => {
      if (draft) {
        setText(draft.text);
        setDialectId(draft.dialectId);
      }
      setDraftLoaded(true);
    });
  }, []);

  const dialects = useQuery({
    queryKey: ["dialects"],
    queryFn: getDialects
  });

  const defaultDialect = useMemo(() => {
    const rows = dialects.data || [];
    return rows.find((dialect) => dialect.code.toLowerCase() === "bohairic") || rows[0];
  }, [dialects.data]);

  useEffect(() => {
    if (!dialectId && defaultDialect) setDialectId(defaultDialect.id);
  }, [defaultDialect, dialectId]);

  const selectedDialect = (dialects.data || []).find((dialect) => dialect.id === dialectId) || defaultDialect;

  useEffect(() => {
    if (!draftLoaded) return;
    saveTranslationDraft({ text, dialectId }).catch(() => undefined);
  }, [draftLoaded, text, dialectId]);

  const mutation = useMutation({
    mutationFn: async () => {
      const parsed = schema.safeParse({ text, targetDialectId: dialectId });
      if (!parsed.success) throw new Error(parsed.error.issues[0]?.message || "بيانات غير صالحة.");
      return translate(parsed.data.text, parsed.data.targetDialectId, session?.token ?? null);
    },
    onSuccess: async (result) => {
      const item: SavedTranslation = {
        id: getTranslationId(result),
        createdAt: new Date().toISOString(),
        inputText: text.trim(),
        dialectName: dialectNameAr(selectedDialect),
        result
      };
      await saveLastTranslation(item);
      router.push("/result");
    },
    onError: (currentError) => {
      setError(currentError instanceof Error ? currentError.message : "تعذر تنفيذ الترجمة.");
    }
  });

  return (
    <Screen>
      <View>
        <Text style={sharedStyles.eyebrow}>ترجمة</Text>
        <Text style={sharedStyles.title}>اكتب كلمة أو جملة عربية.</Text>
        <Text style={sharedStyles.subtitle}>
          الكلمة تترجم من القاموس، والجملة تحفظ كطلب وتنتج مرشحًا مسودة حتى المراجعة.
        </Text>
      </View>

      <View style={sharedStyles.panel}>
        <TextInput
          multiline
          onChangeText={(value) => {
            setText(value);
            setError("");
          }}
          placeholder="مثال: الله محبة"
          style={[sharedStyles.input, sharedStyles.arabicInput, styles.textarea]}
          value={text}
        />

        <Text style={styles.label}>اللهجة القبطية</Text>
        {dialects.isPending ? (
          <ActivityIndicator color={colors.ink} />
        ) : (
          <DialectSelector dialects={dialects.data || []} selectedId={dialectId} onSelect={setDialectId} />
        )}

        {!session ? (
          <Text style={styles.warning}>يمكنك الترجمة الآن. تسجيل الدخول اختياري إذا أردت ربط طلبات الجمل بحساب مراجعة.</Text>
        ) : null}

        <PrimaryButton
          disabled={mutation.isPending || !text.trim()}
          label={mutation.isPending ? "جار الترجمة..." : "ترجم"}
          onPress={() => mutation.mutate()}
        />
        <PrimaryButton
          label="افتح آخر نتيجة"
          onPress={async () => {
            const last = await getLastTranslation();
            if (last) router.push("/result");
            else setError("لا توجد نتيجة محفوظة بعد.");
          }}
        />
        {error ? <Text style={sharedStyles.error}>{error}</Text> : null}
        {dialects.error ? <Text style={sharedStyles.error}>{(dialects.error as Error).message}</Text> : null}
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  textarea: {
    minHeight: 132,
    fontSize: 18,
    lineHeight: 28
  },
  label: {
    color: colors.body,
    fontWeight: "800",
    textAlign: "right"
  },
  warning: {
    color: colors.warning,
    lineHeight: 22,
    textAlign: "right",
    writingDirection: "rtl",
    fontWeight: "700"
  }
});
