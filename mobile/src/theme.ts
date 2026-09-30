import { StyleSheet } from "react-native";

export const colors = {
  canvas: "#ffffff",
  surface: "#f8fafc",
  ink: "#181d26",
  body: "#333840",
  muted: "#68707d",
  hairline: "#dddddd",
  success: "#006400",
  warning: "#a15c00",
  danger: "#b3261e",
  forest: "#0a2e0e",
  coral: "#aa2d00"
};

export const sharedStyles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: colors.canvas
  },
  content: {
    padding: 18,
    gap: 16
  },
  title: {
    color: colors.ink,
    fontSize: 30,
    fontWeight: "700",
    lineHeight: 38,
    textAlign: "right",
    writingDirection: "rtl"
  },
  subtitle: {
    color: colors.body,
    fontSize: 15,
    lineHeight: 24,
    textAlign: "right",
    writingDirection: "rtl"
  },
  eyebrow: {
    color: colors.coral,
    fontSize: 12,
    fontWeight: "800",
    textAlign: "right",
    writingDirection: "rtl"
  },
  panel: {
    borderWidth: 1,
    borderColor: colors.hairline,
    borderRadius: 12,
    backgroundColor: colors.canvas,
    padding: 16,
    gap: 12
  },
  input: {
    minHeight: 46,
    borderWidth: 1,
    borderColor: colors.hairline,
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    color: colors.ink,
    backgroundColor: colors.canvas
  },
  arabicInput: {
    textAlign: "right",
    writingDirection: "rtl"
  },
  button: {
    minHeight: 46,
    borderRadius: 10,
    backgroundColor: colors.ink,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 14
  },
  secondaryButton: {
    minHeight: 44,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: colors.hairline,
    backgroundColor: colors.canvas,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 14
  },
  buttonText: {
    color: colors.canvas,
    fontWeight: "800"
  },
  secondaryButtonText: {
    color: colors.ink,
    fontWeight: "800"
  },
  error: {
    color: colors.danger,
    textAlign: "right",
    writingDirection: "rtl"
  },
  muted: {
    color: colors.muted,
    lineHeight: 22,
    textAlign: "right",
    writingDirection: "rtl"
  }
});
