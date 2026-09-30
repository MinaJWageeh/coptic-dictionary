import type { Dialect } from "@/lib/translation-types";

const DIALECT_NAMES_AR: Record<string, string> = {
  bohairic: "البحيرية",
  sahidic: "الصعيدية",
  fayyumic: "الفيومية",
  akhmimic: "الأخميمية",
  lycopolitan: "الليكوبوليتانية",
  oxyrhynchite: "الأوكسيرنخية"
};

export function dialectNameAr(dialect?: Pick<Dialect, "code" | "name"> | null) {
  if (!dialect) return "";
  return DIALECT_NAMES_AR[dialect.code.toLowerCase()] || dialect.name;
}

export function dialectTextAr(nameOrCode?: string | null) {
  if (!nameOrCode) return "";
  return DIALECT_NAMES_AR[nameOrCode.toLowerCase()] || nameOrCode;
}
