import { Pressable, StyleSheet, Text, View } from "react-native";
import type { Dialect } from "../api";
import { dialectNameAr } from "../dialects";
import { colors } from "../theme";

export function DialectSelector({
  dialects,
  selectedId,
  onSelect
}: {
  dialects: Dialect[];
  selectedId: number | null;
  onSelect: (id: number) => void;
}) {
  return (
    <View style={styles.row}>
      {dialects.map((dialect) => {
        const active = dialect.id === selectedId;
        return (
          <Pressable key={dialect.id} onPress={() => onSelect(dialect.id)} style={[styles.chip, active && styles.active]}>
            <Text style={[styles.text, active && styles.activeText]}>
              {dialectNameAr(dialect)}
              {dialect.code.toLowerCase() === "bohairic" ? " · الافتراضية" : ""}
            </Text>
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: "row-reverse",
    flexWrap: "wrap",
    gap: 8
  },
  chip: {
    borderWidth: 1,
    borderColor: colors.hairline,
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 8
  },
  active: {
    backgroundColor: colors.ink,
    borderColor: colors.ink
  },
  text: {
    color: colors.body,
    fontWeight: "700"
  },
  activeText: {
    color: colors.canvas
  }
});
