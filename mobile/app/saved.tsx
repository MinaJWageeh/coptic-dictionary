import { router, useFocusEffect } from "expo-router";
import { useCallback, useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { Screen, SecondaryButton } from "../src/components/Screen";
import { listFavorites, removeFavorite, saveLastTranslation, type SavedTranslation } from "../src/storage";
import { colors, sharedStyles } from "../src/theme";

function statusAr(status: string) {
  const labels: Record<string, string> = {
    approved: "معتمدة",
    draft: "مسودة",
    pending: "قيد المراجعة",
    rejected: "مرفوضة"
  };
  return labels[status] || status;
}

export default function SavedTranslationsScreen() {
  const [items, setItems] = useState<SavedTranslation[]>([]);

  const refresh = useCallback(() => {
    listFavorites().then(setItems);
  }, []);

  useFocusEffect(refresh);

  return (
    <Screen>
      <View>
        <Text style={sharedStyles.eyebrow}>المفضلة</Text>
        <Text style={sharedStyles.title}>الترجمات المحفوظة محليًا.</Text>
        <Text style={sharedStyles.subtitle}>تُحفظ على الجهاز حتى تراجعها لاحقًا أو تعرض مصادرها من جديد.</Text>
      </View>

      {items.length ? (
        items.map((item) => (
          <View style={sharedStyles.panel} key={item.id}>
            <Text style={styles.status}>{statusAr(item.result.status)}</Text>
            <Text style={styles.input}>{item.inputText}</Text>
            <Text style={styles.coptic}>{item.result.translation || item.result.candidate_translation || "لا توجد ترجمة كاملة"}</Text>
            <Text style={styles.meta}>
              {item.dialectName || "البحيرية"} · ثقة {Math.round(item.result.confidence * 100)}% ·{" "}
              {new Date(item.createdAt).toLocaleDateString("ar-EG")}
            </Text>
            <View style={styles.actions}>
              <Pressable
                style={sharedStyles.button}
                onPress={async () => {
                  await saveLastTranslation(item);
                  router.push("/result");
                }}
              >
                <Text style={sharedStyles.buttonText}>عرض</Text>
              </Pressable>
              <SecondaryButton
                label="حذف"
                onPress={async () => {
                  await removeFavorite(item.id);
                  refresh();
                }}
              />
            </View>
          </View>
        ))
      ) : (
        <View style={sharedStyles.panel}>
          <Text style={sharedStyles.muted}>لا توجد ترجمات محفوظة بعد.</Text>
        </View>
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  status: {
    alignSelf: "flex-end",
    backgroundColor: colors.surface,
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 6,
    color: colors.body,
    fontWeight: "800"
  },
  input: {
    color: colors.body,
    fontSize: 17,
    textAlign: "right",
    writingDirection: "rtl"
  },
  coptic: {
    color: colors.ink,
    fontSize: 22,
    fontWeight: "800",
    textAlign: "left",
    writingDirection: "ltr"
  },
  meta: {
    color: colors.muted,
    textAlign: "right"
  },
  actions: {
    flexDirection: "row-reverse",
    flexWrap: "wrap",
    gap: 10
  }
});
