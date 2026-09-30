import { ArrowLeft, BookOpen, CheckCircle2, Database, Languages, ShieldCheck } from "lucide-react";
import Link from "next/link";
import { PublicShell } from "@/components/public-shell";

export default function HomePage() {
  return (
    <PublicShell>
      <section className="home-hero">
        <div className="home-copy">
          <p className="eyebrow">قاموس + أمثلة + قواعد + مراجعة بشرية</p>
          <h1>ترجمة عربية إلى قبطية موثقة، وليست تخمينًا لغويًا.</h1>
          <p>
            اكتب كلمة أو جملة عربية، واختر اللهجة القبطية. الكلمات تترجم من القاموس، والجمل
            تعرض مرشحًا مدعومًا بمصادر وثقة وحالة مراجعة.
          </p>
          <div className="hero-actions">
            <Link className="button primary" href="/translate">
              ابدأ الترجمة
              <ArrowLeft size={16} />
            </Link>
            <Link className="button" href="/dictionary">
              ابحث في القاموس
            </Link>
          </div>
        </div>
        <div className="translation-specimen" aria-label="عينة قبطية">
          <span className="specimen-label">اللهجة الافتراضية: البحيرية</span>
          <strong className="coptic-display">ⲡⲓⲱⲟⲩ ⲛ̀ⲧⲉ ⲛⲓⲣⲉϥϯ</strong>
          <p>كل نتيجة تعرض الكلمات المستخدمة، الأمثلة المشابهة، القواعد، والمراجع قبل الاعتماد.</p>
        </div>
      </section>

      <section className="feature-band">
        <article>
          <Languages size={20} />
          <h2>كلمة واحدة</h2>
          <p>بحث مباشر في المعاني العربية والربط بالقاموس القبطي مع اللهجة ونوع الكلمة والمصدر.</p>
        </article>
        <article>
          <Database size={20} />
          <h2>جملة كاملة</h2>
          <p>مسار الترجمة يجمع القاموس والمتن وقواعد النحو واسترجاع الأمثلة المشابهة قبل توليد مرشح.</p>
        </article>
        <article>
          <ShieldCheck size={20} />
          <h2>مراجعة آمنة</h2>
          <p>أي جملة جديدة تبقى مسودة حتى يعتمدها مراجع بشري، مع تحذير عند ضعف الأدلة.</p>
        </article>
      </section>

      <section className="method-section">
        <div>
          <p className="eyebrow">منهجية العمل</p>
          <h2>النظام يعرض الدليل قبل النتيجة النهائية.</h2>
        </div>
        <ul className="method-list">
          <li>
            <CheckCircle2 size={18} />
            <span>البحيرية هي اللهجة الافتراضية، مع دعم الصعيدية ولهجات أخرى.</span>
          </li>
          <li>
            <BookOpen size={18} />
            <span>كل ترجمة تعرض المراجع من قاعدة البيانات بدل اعتماد ناتج غير موثق.</span>
          </li>
          <li>
            <ShieldCheck size={18} />
            <span>الثقة المنخفضة تظهر تحذيرًا واضحًا بأن الترجمة تحتاج مراجعة بشرية.</span>
          </li>
        </ul>
      </section>
    </PublicShell>
  );
}
