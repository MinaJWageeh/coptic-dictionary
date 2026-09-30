import { BookOpen, Database, ShieldCheck } from "lucide-react";
import { PublicShell } from "@/components/public-shell";

export default function AboutPage() {
  return (
    <PublicShell>
      <section className="page-intro">
        <p className="eyebrow">عن التطبيق</p>
        <h1>نظام ترجمة محافظ مبني على الأدلة.</h1>
        <p>
          الهدف ليس إنتاج نص قبطي غير موثق، بل مساعدة المستخدم والمراجع على الوصول إلى ترجمة
          قابلة للفحص عبر القاموس، الأمثلة، القواعد، والمصادر.
        </p>
      </section>

      <section className="about-grid">
        <article>
          <BookOpen size={22} />
          <h2>القاموس أولًا</h2>
          <p>الكلمة الواحدة تُترجم فقط من معاني عربية مرتبطة بمدخلات قبطية معتمدة ومصدر واضح.</p>
        </article>
        <article>
          <Database size={22} />
          <h2>استرجاع أدلة للجمل</h2>
          <p>الجملة تستخدم أمثلة متوازية وقواعد نحوية ونتائج استرجاع، وتعرض الأدلة التي رفعت أو خفضت الثقة.</p>
        </article>
        <article>
          <ShieldCheck size={22} />
          <h2>مراجعة بشرية</h2>
          <p>أي ترجمة جملة جديدة تبقى مسودة حتى يعتمدها مراجع، ولا تُعرض كمعتمدة إلا لو كانت مراجعة مسبقًا.</p>
        </article>
      </section>

      <section className="method-section">
        <div>
          <p className="eyebrow">حدود مقصودة</p>
          <h2>النظام لا يخترع كلمات قبطية.</h2>
        </div>
        <p>
          عند غياب كلمة من القاموس تظهر ككلمة غير معروفة، وعند ضعف الأمثلة أو القواعد تنخفض درجة الثقة
          ويظهر تحذير بالمراجعة البشرية. هذا مهم خصوصًا لأن موارد القبطية تحتاج توثيقًا ومراجعة
          قبل الاستخدام العام.
        </p>
      </section>
    </PublicShell>
  );
}
