"use client";

export function FilterBar() {
  return (
    <>
      <select className="select" aria-label="فلتر اللهجة">
        <option>كل اللهجات</option>
        <option value="sahidic">الصعيدية</option>
        <option value="bohairic">البحيرية</option>
      </select>
      <select className="select" aria-label="فلتر حالة المراجعة">
        <option>كل حالات المراجعة</option>
        <option value="draft">مسودة</option>
        <option value="pending">قيد المراجعة</option>
        <option value="approved">معتمدة</option>
        <option value="rejected">مرفوضة</option>
      </select>
      <input className="input" placeholder="معرف المصدر" style={{ width: 120 }} />
      <input className="input" placeholder="أقل ثقة" style={{ width: 150 }} />
      <input className="input" type="date" aria-label="فلتر تاريخ الإنشاء" />
    </>
  );
}
