import { Link } from "expo-router";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { Screen } from "../src/components/Screen";
import { colors, sharedStyles } from "../src/theme";

export default function HomeScreen() {
  return (
    <Screen>
      <View style={styles.hero}>
        <Text style={sharedStyles.eyebrow}>قاموس + متن + قواعد + مراجعة</Text>
        <Text style={sharedStyles.title}>ترجمة عربية إلى قبطية موثقة على الهاتف.</Text>
        <Text style={sharedStyles.subtitle}>
          اكتب كلمة أو جملة عربية، اختر اللهجة القبطية، وشاهد الترجمة المقترحة مع الثقة
          والمصادر والأمثلة بدل نتيجة غير موثقة.
        </Text>
        <View style={styles.actions}>
          <Link href="/translate" asChild>
            <Pressable style={sharedStyles.button}>
              <Text style={sharedStyles.buttonText}>ابدأ الترجمة</Text>
            </Pressable>
          </Link>
          <Link href="/dictionary" asChild>
            <Pressable style={sharedStyles.secondaryButton}>
              <Text style={sharedStyles.secondaryButtonText}>ابحث في القاموس</Text>
            </Pressable>
          </Link>
        </View>
      </View>

      <View style={styles.specimen}>
        <Text style={styles.specimenLabel}>اللهجة الافتراضية: البحيرية</Text>
        <Text style={styles.coptic}>ⲡⲓⲱⲟⲩ ⲛ̀ⲧⲉ ⲛⲓⲣⲉϥϯ</Text>
        <Text style={sharedStyles.muted}>
          الجمل الجديدة تبقى مسودة حتى يراجعها إنسان، وأي كلمة ناقصة تظهر بوضوح ككلمة غير معروفة.
        </Text>
      </View>

      <View style={styles.featureGrid}>
        <Feature title="كلمة" body="بحث مباشر في القاموس مع نوع الكلمة واللهجة والمصدر." />
        <Feature title="جملة" body="مسار الترجمة يسترجع أمثلة وقواعد قبل إنتاج مرشح ترجمة." />
        <Feature title="مراجعة" body="الثقة المنخفضة أو المسودات تظهر تحذيرًا واضحًا." />
      </View>
    </Screen>
  );
}

function Feature({ title, body }: { title: string; body: string }) {
  return (
    <View style={styles.feature}>
      <Text style={styles.featureTitle}>{title}</Text>
      <Text style={sharedStyles.muted}>{body}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  hero: {
    gap: 12
  },
  actions: {
    flexDirection: "row-reverse",
    flexWrap: "wrap",
    gap: 10
  },
  specimen: {
    borderWidth: 1,
    borderColor: colors.hairline,
    borderRadius: 12,
    padding: 16,
    backgroundColor: colors.surface,
    gap: 10
  },
  specimenLabel: {
    color: colors.muted,
    fontWeight: "800"
  },
  coptic: {
    color: colors.ink,
    fontSize: 34,
    fontWeight: "800",
    textAlign: "left",
    writingDirection: "ltr"
  },
  featureGrid: {
    gap: 10
  },
  feature: {
    borderWidth: 1,
    borderColor: colors.hairline,
    borderRadius: 12,
    padding: 14,
    gap: 6
  },
  featureTitle: {
    color: colors.ink,
    fontSize: 18,
    fontWeight: "800",
    textAlign: "right"
  }
});
