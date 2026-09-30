const LABELS_AR: Record<string, string> = {
  id: "المعرف",
  coptic_text: "النص القبطي",
  normalized_coptic_text: "النص القبطي المعياري",
  transliteration: "النقل الصوتي",
  dialect_id: "معرف اللهجة",
  source_id: "معرف المصدر",
  part_of_speech: "نوع الكلمة",
  review_status: "حالة المراجعة",
  arabic_lemma: "الكلمة العربية",
  arabic_definition: "المعنى العربي",
  normalized_arabic_lemma: "الكلمة العربية المعيارية",
  definition_ar: "التعريف العربي",
  arabic_sense_id: "معرف المعنى العربي",
  dictionary_entry_id: "معرف المدخل القاموسي",
  confidence: "الثقة",
  usage_note: "ملاحظة الاستخدام",
  title: "العنوان",
  language: "اللغة",
  content: "المحتوى",
  arabic_text: "النص العربي",
  rule_code: "رمز القاعدة",
  description: "الوصف",
  pattern: "النمط",
  replacement: "الاستبدال",
  priority: "الأولوية",
  author: "المؤلف",
  type: "النوع",
  year: "السنة",
  url: "الرابط",
  notes: "ملاحظات",
  email: "البريد الإلكتروني",
  display_name: "الاسم المعروض",
  role: "الدور",
  is_active: "نشط",
  input_text: "النص المدخل",
  normalized_input_text: "النص المدخل المعياري",
  status: "الحالة",
  created_at: "تاريخ الإنشاء",
  candidate_text: "نص المرشح",
  translation_request_id: "معرف طلب الترجمة"
};

export function labelAr(value: string) {
  return LABELS_AR[value] || value.replaceAll("_", " ");
}

export function valueLabelAr(value: unknown) {
  const labels: Record<string, string> = {
    draft: "مسودة",
    pending: "قيد المراجعة",
    approved: "معتمدة",
    rejected: "مرفوضة",
    needs_revision: "تحتاج تعديل",
    noun: "اسم",
    verb: "فعل",
    adjective: "صفة",
    adverb: "حال",
    pronoun: "ضمير",
    preposition: "حرف جر",
    conjunction: "حرف عطف",
    particle: "أداة",
    other: "أخرى",
    admin: "مدير",
    reviewer: "مراجع",
    user: "مستخدم",
    dictionary_entries: "مدخل قاموسي",
    parallel_segments: "مثال موازي",
    grammar_rules: "قاعدة نحوية",
    arabic_senses: "معنى عربي",
    sources: "مصدر",
    true: "نعم",
    false: "لا",
    none: "لا يوجد"
  };
  const key = String(value ?? "").toLowerCase();
  return labels[key] || String(value ?? "");
}
