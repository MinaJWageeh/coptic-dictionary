import { z } from "zod";

export type FieldConfig = {
  name: string;
  label: string;
  type?: "text" | "textarea" | "number" | "select";
  options?: string[];
  required?: boolean;
  full?: boolean;
};

export type ResourceConfig = {
  key: string;
  title: string;
  description: string;
  endpoint: string;
  createEndpoint?: string;
  updateEndpoint?: string;
  deleteEndpoint?: string;
  allowedRoles: Array<"admin" | "reviewer" | "user">;
  columns: string[];
  fields: FieldConfig[];
  schema: z.ZodTypeAny;
  updateSchema?: z.ZodTypeAny;
};

const statusOptions = ["draft", "pending", "approved", "rejected", "needs_revision"];
const posOptions = [
  "noun",
  "verb",
  "adjective",
  "adverb",
  "pronoun",
  "preposition",
  "conjunction",
  "particle",
  "other"
];

export const resources: ResourceConfig[] = [
  {
    key: "dictionary",
    title: "إدارة القاموس",
    description: "إنشاء وتعديل وإيقاف المداخل القبطية المرتبطة باللهجات والمصادر.",
    endpoint: "/admin/dictionary",
    createEndpoint: "/admin/dictionary",
    updateEndpoint: "/admin/dictionary/:id",
    deleteEndpoint: "/admin/dictionary/:id",
    allowedRoles: ["admin"],
    columns: ["id", "coptic_text", "transliteration", "dialect_id", "source_id", "part_of_speech", "review_status"],
    fields: [
      { name: "coptic_text", label: "الكلمة القبطية", required: true },
      { name: "normalized_coptic_text", label: "النص القبطي المعياري" },
      { name: "transliteration", label: "النقل الصوتي" },
      { name: "dialect_id", label: "معرف اللهجة", type: "number", required: true },
      { name: "source_id", label: "معرف المصدر", type: "number", required: true },
      { name: "part_of_speech", label: "نوع الكلمة", type: "select", options: posOptions, required: true },
      { name: "arabic_lemma", label: "الكلمة العربية" },
      { name: "arabic_definition", label: "المعنى العربي", type: "textarea", full: true },
      { name: "review_status", label: "حالة المراجعة", type: "select", options: statusOptions }
    ],
    schema: z.object({
      coptic_text: z.string().min(1),
      normalized_coptic_text: z.string().optional(),
      transliteration: z.string().optional(),
      dialect_id: z.coerce.number().int().positive(),
      source_id: z.coerce.number().int().positive(),
      part_of_speech: z.string().min(1),
      arabic_lemma: z.string().optional(),
      arabic_definition: z.string().optional(),
      review_status: z.string().default("pending")
    }),
    updateSchema: z.object({
      coptic_text: z.string().optional(),
      normalized_coptic_text: z.string().optional(),
      transliteration: z.string().optional(),
      dialect_id: z.coerce.number().int().positive().optional(),
      source_id: z.coerce.number().int().positive().optional(),
      part_of_speech: z.string().optional(),
      notes: z.string().optional(),
      review_status: z.string().optional()
    })
  },
  {
    key: "senses",
    title: "إدارة المعاني العربية",
    description: "إدارة الكلمات العربية ومعانيها قبل ربطها بالمداخل القبطية.",
    endpoint: "/admin/senses",
    createEndpoint: "/admin/senses",
    updateEndpoint: "/admin/senses/:id",
    deleteEndpoint: "/admin/senses/:id",
    allowedRoles: ["admin"],
    columns: ["id", "arabic_lemma", "normalized_arabic_lemma", "definition_ar", "part_of_speech", "review_status"],
    fields: [
      { name: "arabic_lemma", label: "الكلمة العربية", required: true },
      { name: "normalized_arabic_lemma", label: "الكلمة المعيارية" },
      { name: "definition_ar", label: "المعنى", type: "textarea", required: true, full: true },
      { name: "part_of_speech", label: "نوع الكلمة", type: "select", options: posOptions },
      { name: "source_id", label: "معرف المصدر", type: "number" },
      { name: "review_status", label: "حالة المراجعة", type: "select", options: statusOptions }
    ],
    schema: z.object({
      arabic_lemma: z.string().min(1),
      normalized_arabic_lemma: z.string().optional(),
      definition_ar: z.string().min(1),
      part_of_speech: z.string().optional(),
      source_id: z.coerce.number().optional(),
      review_status: z.string().default("pending")
    }),
    updateSchema: z.object({
      arabic_lemma: z.string().optional(),
      normalized_arabic_lemma: z.string().optional(),
      definition_ar: z.string().optional(),
      part_of_speech: z.string().optional(),
      source_id: z.coerce.number().optional(),
      review_status: z.string().optional()
    })
  },
  {
    key: "mappings",
    title: "إدارة ربط المعاني",
    description: "ربط كل معنى عربي بمدخل قبطي واحد أو أكثر مع درجة ثقة.",
    endpoint: "/admin/mappings",
    createEndpoint: "/admin/mappings",
    updateEndpoint: "/admin/mappings/:id",
    deleteEndpoint: "/admin/mappings/:id",
    allowedRoles: ["admin"],
    columns: ["id", "arabic_sense_id", "dictionary_entry_id", "confidence", "is_primary", "review_status"],
    fields: [
      { name: "arabic_sense_id", label: "معرف المعنى العربي", type: "number", required: true },
      { name: "dictionary_entry_id", label: "معرف المدخل القاموسي", type: "number", required: true },
      { name: "confidence", label: "درجة الثقة", type: "number" },
      { name: "usage_note", label: "ملاحظة الاستخدام", type: "textarea", full: true },
      { name: "review_status", label: "حالة المراجعة", type: "select", options: statusOptions }
    ],
    schema: z.object({
      arabic_sense_id: z.coerce.number().int().positive(),
      dictionary_entry_id: z.coerce.number().int().positive(),
      confidence: z.coerce.number().min(0).max(1).default(0.5),
      usage_note: z.string().optional(),
      review_status: z.string().default("pending")
    }),
    updateSchema: z.object({
      arabic_sense_id: z.coerce.number().int().positive().optional(),
      dictionary_entry_id: z.coerce.number().int().positive().optional(),
      confidence: z.coerce.number().min(0).max(1).optional(),
      usage_note: z.string().optional(),
      review_status: z.string().optional()
    })
  },
  {
    key: "corpus-texts",
    title: "إدارة نصوص المتون",
    description: "تسجيل وثائق المتون المدعومة بالمصادر والتي تحتوي على أمثلة متوازية.",
    endpoint: "/admin/corpus-texts",
    createEndpoint: "/admin/corpus-texts",
    updateEndpoint: "/admin/corpus-texts/:id",
    deleteEndpoint: "/admin/corpus-texts/:id",
    allowedRoles: ["admin"],
    columns: ["id", "title", "source_id", "dialect_id", "language", "review_status"],
    fields: [
      { name: "title", label: "العنوان", required: true },
      { name: "source_id", label: "معرف المصدر", type: "number", required: true },
      { name: "dialect_id", label: "معرف اللهجة", type: "number" },
      { name: "language", label: "اللغة", required: true },
      { name: "content", label: "المحتوى", type: "textarea", full: true },
      { name: "review_status", label: "حالة المراجعة", type: "select", options: statusOptions }
    ],
    schema: z.object({
      title: z.string().min(1),
      source_id: z.coerce.number().int().positive(),
      dialect_id: z.coerce.number().optional(),
      language: z.string().min(1),
      content: z.string().optional(),
      review_status: z.string().default("pending")
    }),
    updateSchema: z.object({
      title: z.string().optional(),
      source_id: z.coerce.number().int().positive().optional(),
      dialect_id: z.coerce.number().optional(),
      language: z.string().optional(),
      content: z.string().optional(),
      review_status: z.string().optional()
    })
  },
  {
    key: "parallel-segments",
    title: "إدارة الأمثلة المتوازية",
    description: "إضافة جمل عربية/قبطية متوازية للاسترجاع وإعادة استخدام الترجمات المعتمدة.",
    endpoint: "/admin/parallel-segments",
    createEndpoint: "/admin/parallel-segments",
    updateEndpoint: "/admin/parallel-segments/:id",
    deleteEndpoint: "/admin/parallel-segments/:id",
    allowedRoles: ["admin"],
    columns: ["id", "arabic_text", "coptic_text", "source_id", "dialect_id", "review_status"],
    fields: [
      { name: "corpus_text_id", label: "معرف نص المتن", type: "number" },
      { name: "source_id", label: "معرف المصدر", type: "number", required: true },
      { name: "dialect_id", label: "معرف اللهجة", type: "number" },
      { name: "arabic_text", label: "النص العربي", type: "textarea", required: true, full: true },
      { name: "coptic_text", label: "النص القبطي", type: "textarea", full: true },
      { name: "review_status", label: "حالة المراجعة", type: "select", options: statusOptions }
    ],
    schema: z.object({
      corpus_text_id: z.coerce.number().optional(),
      source_id: z.coerce.number().int().positive(),
      dialect_id: z.coerce.number().optional(),
      arabic_text: z.string().min(1),
      coptic_text: z.string().optional(),
      review_status: z.string().default("pending")
    }),
    updateSchema: z.object({
      corpus_text_id: z.coerce.number().optional(),
      source_id: z.coerce.number().int().positive().optional(),
      dialect_id: z.coerce.number().optional(),
      arabic_text: z.string().optional(),
      coptic_text: z.string().optional(),
      review_status: z.string().optional()
    })
  },
  {
    key: "grammar-rules",
    title: "إدارة القواعد النحوية",
    description: "تنظيم أوصاف القواعد والأنماط المستخدمة في مسار الترجمة.",
    endpoint: "/admin/grammar-rules",
    createEndpoint: "/admin/grammar-rules",
    updateEndpoint: "/admin/grammar-rules/:id",
    deleteEndpoint: "/admin/grammar-rules/:id",
    allowedRoles: ["admin"],
    columns: ["id", "title", "rule_code", "dialect_id", "priority", "review_status"],
    fields: [
      { name: "title", label: "العنوان", required: true },
      { name: "rule_code", label: "رمز القاعدة" },
      { name: "dialect_id", label: "معرف اللهجة", type: "number" },
      { name: "source_id", label: "معرف المصدر", type: "number" },
      { name: "description", label: "الوصف", type: "textarea", required: true, full: true },
      { name: "pattern", label: "النمط" },
      { name: "replacement", label: "الاستبدال" },
      { name: "priority", label: "الأولوية", type: "number" },
      { name: "review_status", label: "حالة المراجعة", type: "select", options: statusOptions }
    ],
    schema: z.object({
      title: z.string().min(1),
      rule_code: z.string().optional(),
      dialect_id: z.coerce.number().optional(),
      source_id: z.coerce.number().optional(),
      description: z.string().min(1),
      pattern: z.string().optional(),
      replacement: z.string().optional(),
      priority: z.coerce.number().default(100),
      review_status: z.string().default("pending")
    }),
    updateSchema: z.object({
      title: z.string().optional(),
      rule_code: z.string().optional(),
      dialect_id: z.coerce.number().optional(),
      source_id: z.coerce.number().optional(),
      description: z.string().optional(),
      pattern: z.string().optional(),
      replacement: z.string().optional(),
      priority: z.coerce.number().optional(),
      review_status: z.string().optional()
    })
  },
  {
    key: "sources",
    title: "إدارة المصادر",
    description: "تتبع المعاجم والمخطوطات والمتون والمواقع والمراجع الأكاديمية.",
    endpoint: "/admin/sources",
    createEndpoint: "/admin/sources",
    updateEndpoint: "/admin/sources/:id",
    deleteEndpoint: "/admin/sources/:id",
    allowedRoles: ["admin"],
    columns: ["id", "title", "author", "type", "year", "url"],
    fields: [
      { name: "title", label: "العنوان", required: true },
      { name: "author", label: "المؤلف" },
      { name: "type", label: "النوع" },
      { name: "year", label: "السنة", type: "number" },
      { name: "url", label: "الرابط" },
      { name: "notes", label: "ملاحظات", type: "textarea", full: true }
    ],
    schema: z.object({
      title: z.string().min(1),
      author: z.string().optional(),
      type: z.string().optional(),
      year: z.coerce.number().optional(),
      url: z.string().optional(),
      notes: z.string().optional()
    }),
    updateSchema: z.object({
      title: z.string().optional(),
      author: z.string().optional(),
      type: z.string().optional(),
      year: z.coerce.number().optional(),
      url: z.string().optional(),
      notes: z.string().optional()
    })
  },
  {
    key: "users-roles",
    title: "المستخدمون والأدوار",
    description: "عرض المستخدمين وتحديد مستوى الوصول لمسارات الإدارة والمراجعة.",
    endpoint: "/admin/users",
    createEndpoint: "/admin/users",
    updateEndpoint: "/admin/users/:id",
    deleteEndpoint: "/admin/users/:id",
    allowedRoles: ["admin"],
    columns: ["id", "email", "display_name", "role", "is_active"],
    fields: [
      { name: "email", label: "البريد الإلكتروني", required: true },
      { name: "display_name", label: "الاسم المعروض", required: true },
      { name: "role", label: "الدور", type: "select", options: ["user", "reviewer", "admin"] },
      { name: "password", label: "كلمة مرور مؤقتة", required: true }
    ],
    schema: z.object({
      email: z.string().email(),
      display_name: z.string().min(1),
      role: z.string().default("user"),
      password: z.string().min(8)
    }),
    updateSchema: z.object({
      email: z.string().email().optional(),
      display_name: z.string().optional(),
      role: z.string().optional(),
      password: z.string().min(8).optional()
    })
  },
  {
    key: "audit-logs",
    title: "سجل التدقيق",
    description: "مراجعة تغييرات البيانات الإدارية في القاموس والمتون والقواعد والمصادر والمستخدمين.",
    endpoint: "/admin/audit-logs",
    allowedRoles: ["admin"],
    columns: ["id", "action", "table_name", "record_id", "user_id", "created_at"],
    fields: [],
    schema: z.object({})
  }
];

export function getResource(key: string) {
  return resources.find((resource) => resource.key === key);
}
