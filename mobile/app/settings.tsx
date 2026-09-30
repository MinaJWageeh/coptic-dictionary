import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { StyleSheet, Text, TextInput, View } from "react-native";
import { z } from "zod";
import { getDialects, login } from "../src/api";
import { PrimaryButton, Screen, SecondaryButton } from "../src/components/Screen";
import {
  clearFavorites,
  clearSession,
  getApiBaseUrl,
  getSession,
  saveApiBaseUrl,
  saveSession,
  type Session
} from "../src/storage";
import { colors, sharedStyles } from "../src/theme";

const loginSchema = z.object({
  email: z.string().email("أدخل بريدًا صحيحًا."),
  password: z.string().min(1, "أدخل كلمة المرور.")
});

const apiSchema = z.string().trim().url("أدخل رابط خادم صحيحًا مثل http://10.0.2.2:8000");

export default function SettingsScreen() {
  const queryClient = useQueryClient();
  const [email, setEmail] = useState("user@example.com");
  const [password, setPassword] = useState("ChangeMe123!");
  const [apiUrl, setApiUrl] = useState("");
  const [session, setSessionState] = useState<Session | null>(null);
  const [message, setMessage] = useState("");

  useEffect(() => {
    getSession().then(setSessionState);
    getApiBaseUrl().then(setApiUrl);
  }, []);

  const apiBase = useQuery({
    queryKey: ["api-base"],
    queryFn: getApiBaseUrl
  });

  const loginMutation = useMutation({
    mutationFn: async () => {
      const parsed = loginSchema.safeParse({ email, password });
      if (!parsed.success) throw new Error(parsed.error.issues[0]?.message || "بيانات دخول غير صالحة.");
      return login(parsed.data.email, parsed.data.password);
    },
    onSuccess: async (token) => {
      const next = { token: token.access_token, email };
      await saveSession(next);
      setSessionState(next);
      setMessage("تم تسجيل الدخول.");
    },
    onError: (error) => setMessage(error instanceof Error ? error.message : "فشل تسجيل الدخول.")
  });

  const connectionMutation = useMutation({
    mutationFn: getDialects,
    onSuccess: (dialects) => setMessage(`تم الاتصال بنجاح. عدد اللهجات: ${dialects.length}.`),
    onError: (error) => setMessage(error instanceof Error ? error.message : "فشل اختبار الاتصال.")
  });

  async function applyApiPreset(url: string) {
    setApiUrl(url);
    await saveApiBaseUrl(url);
    await queryClient.invalidateQueries();
    setMessage(`تم حفظ رابط الخادم: ${url}`);
  }

  return (
    <Screen>
      <View>
        <Text style={sharedStyles.eyebrow}>الإعدادات</Text>
        <Text style={sharedStyles.title}>الاتصال والحساب.</Text>
        <Text style={sharedStyles.subtitle}>
          اضبط رابط الخادم. تسجيل الدخول اختياري لربط طلبات الجمل بحساب مراجعة.
        </Text>
      </View>

      <View style={sharedStyles.panel}>
        <Text style={styles.sectionTitle}>رابط الخادم</Text>
        <TextInput
          autoCapitalize="none"
          onChangeText={setApiUrl}
          placeholder="http://localhost:8000"
          style={[sharedStyles.input, styles.ltr]}
          value={apiUrl || apiBase.data || ""}
        />
        <PrimaryButton
          label="حفظ رابط الخادم"
          onPress={async () => {
            const parsed = apiSchema.safeParse(apiUrl);
            if (!parsed.success) {
              setMessage(parsed.error.issues[0]?.message || "رابط غير صالح.");
              return;
            }
            await saveApiBaseUrl(parsed.data);
            await queryClient.invalidateQueries();
            setMessage("تم حفظ رابط الخادم.");
          }}
        />
        <View style={styles.presetRow}>
          <SecondaryButton label="الجهاز الحالي" onPress={() => applyApiPreset("http://localhost:8000")} />
          <SecondaryButton label="محاكي أندرويد" onPress={() => applyApiPreset("http://10.0.2.2:8000")} />
          <SecondaryButton label="اختبار الاتصال" disabled={connectionMutation.isPending} onPress={() => connectionMutation.mutate()} />
        </View>
        <Text style={sharedStyles.muted}>على محاكي أندرويد غالبًا استخدم http://10.0.2.2:8000 بدل http://localhost:8000.</Text>
      </View>

      <View style={sharedStyles.panel}>
        <Text style={styles.sectionTitle}>تسجيل الدخول</Text>
        {session ? <Text style={styles.signedIn}>مسجل كـ {session.email}</Text> : null}
        <TextInput
          autoCapitalize="none"
          keyboardType="email-address"
          onChangeText={setEmail}
          placeholder="البريد الإلكتروني"
          style={[sharedStyles.input, styles.ltr]}
          value={email}
        />
        <TextInput
          onChangeText={setPassword}
          placeholder="كلمة المرور"
          secureTextEntry
          style={[sharedStyles.input, styles.ltr]}
          value={password}
        />
        <PrimaryButton
          disabled={loginMutation.isPending}
          label={loginMutation.isPending ? "جار الدخول..." : "تسجيل الدخول"}
          onPress={() => loginMutation.mutate()}
        />
        <SecondaryButton
          label="تسجيل الخروج"
          onPress={async () => {
            await clearSession();
            setSessionState(null);
            setMessage("تم تسجيل الخروج.");
          }}
        />
      </View>

      <View style={sharedStyles.panel}>
        <Text style={styles.sectionTitle}>المفضلة</Text>
        <SecondaryButton
          label="مسح الترجمات المحفوظة"
          onPress={async () => {
            await clearFavorites();
            setMessage("تم مسح المفضلة.");
          }}
        />
      </View>

      {message ? <Text style={styles.message}>{message}</Text> : null}
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
  ltr: {
    textAlign: "left",
    writingDirection: "ltr"
  },
  signedIn: {
    color: colors.success,
    fontWeight: "800",
    textAlign: "right"
  },
  message: {
    color: colors.body,
    textAlign: "right",
    writingDirection: "rtl",
    fontWeight: "700"
  },
  presetRow: {
    flexDirection: "row-reverse",
    flexWrap: "wrap",
    gap: 8
  }
});
