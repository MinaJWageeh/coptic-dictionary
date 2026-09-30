import { Link, usePathname } from "expo-router";
import { ReactNode } from "react";
import { Pressable, SafeAreaView, ScrollView, StyleSheet, Text, View } from "react-native";
import { colors, sharedStyles } from "../theme";

const navItems = [
  { href: "/", label: "الرئيسية" },
  { href: "/translate", label: "ترجمة" },
  { href: "/result", label: "آخر نتيجة" },
  { href: "/dictionary", label: "القاموس" },
  { href: "/saved", label: "المحفوظات" },
  { href: "/settings", label: "الإعدادات" }
] as const;

export function Screen({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  return (
    <SafeAreaView style={sharedStyles.screen}>
      <ScrollView contentContainerStyle={sharedStyles.content} keyboardShouldPersistTaps="handled">
        <View style={styles.header}>
          <View style={styles.brandText}>
            <Text style={styles.brandTitle}>المترجم القبطي</Text>
            <Text style={styles.brandSub}>من العربية إلى القبطية الموثقة</Text>
          </View>
          <Text style={styles.logo}>Ϭ</Text>
        </View>
        <View style={styles.nav}>
          {navItems.map((item) => (
            <Link href={item.href} asChild key={item.href}>
              <Pressable style={[styles.navPill, pathname === item.href && styles.navPillActive]}>
                <Text style={[styles.navText, pathname === item.href && styles.navTextActive]}>{item.label}</Text>
              </Pressable>
            </Link>
          ))}
        </View>
        {children}
      </ScrollView>
    </SafeAreaView>
  );
}

export function PrimaryButton({
  label,
  onPress,
  disabled
}: {
  label: string;
  onPress: () => void;
  disabled?: boolean;
}) {
  return (
    <Pressable disabled={disabled} onPress={onPress} style={[sharedStyles.button, disabled && styles.disabled]}>
      <Text style={sharedStyles.buttonText}>{label}</Text>
    </Pressable>
  );
}

export function SecondaryButton({
  label,
  onPress,
  disabled
}: {
  label: string;
  onPress: () => void;
  disabled?: boolean;
}) {
  return (
    <Pressable disabled={disabled} onPress={onPress} style={[sharedStyles.secondaryButton, disabled && styles.disabled]}>
      <Text style={sharedStyles.secondaryButtonText}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 12
  },
  brandText: {
    alignItems: "flex-end",
    flex: 1
  },
  brandTitle: {
    color: colors.ink,
    fontSize: 22,
    fontWeight: "800",
    textAlign: "right"
  },
  brandSub: {
    color: colors.muted,
    marginTop: 2
  },
  logo: {
    width: 44,
    height: 44,
    borderRadius: 12,
    backgroundColor: colors.ink,
    color: colors.canvas,
    textAlign: "center",
    textAlignVertical: "center",
    fontSize: 24,
    fontWeight: "800"
  },
  nav: {
    flexDirection: "row-reverse",
    flexWrap: "wrap",
    gap: 8
  },
  navPill: {
    borderWidth: 1,
    borderColor: colors.hairline,
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 8,
    backgroundColor: colors.canvas
  },
  navPillActive: {
    backgroundColor: colors.ink,
    borderColor: colors.ink
  },
  navText: {
    color: colors.body,
    fontWeight: "700"
  },
  navTextActive: {
    color: colors.canvas
  },
  disabled: {
    opacity: 0.55
  }
});
