"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { z } from "zod";
import { inferRole, saveSession } from "@/lib/auth";
import { login } from "@/lib/api";

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(1)
});

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("admin@example.com");
  const [password, setPassword] = useState("secret");
  const [error, setError] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const parsed = loginSchema.safeParse({ email, password });
    if (!parsed.success) {
      setError("أدخل بريدًا إلكترونيًا وكلمة مرور صحيحين.");
      return;
    }
    try {
      const token = await login(parsed.data.email, parsed.data.password);
      saveSession({
        token: token.access_token,
        email: parsed.data.email,
        role: inferRole(parsed.data.email, token.access_token)
      });
      const params = new URLSearchParams(window.location.search);
      router.replace(params.get("next") || "/admin");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "فشل تسجيل الدخول.");
    }
  }

  return (
    <main className="login-page" dir="rtl">
      <section className="login-art">
        <div>
          <div className="brand-mark">Ϭ</div>
          <h1 style={{ fontSize: 44, fontWeight: 500, lineHeight: 1.1, maxWidth: 560 }}>
            راجع كل ترجمة من العربية إلى القبطية قبل وصولها إلى القارئ.
          </h1>
        </div>
        <p style={{ maxWidth: 520, color: "rgba(255,255,255,0.72)", lineHeight: 1.6 }}>
          أدر المصادر والمعاني والربط وطوابير المراجعة والمراجع التي تجعل المرشحات مستندة إلى قاعدة البيانات.
        </p>
      </section>
      <section className="login-card">
        <form className="panel" onSubmit={handleSubmit} style={{ padding: 24 }}>
          <h2 style={{ margin: "0 0 8px", fontWeight: 500 }}>تسجيل الدخول</h2>
          <p style={{ margin: "0 0 22px", color: "var(--muted)", fontSize: 14 }}>
            استخدم حساب مدير أو مراجع للمتابعة.
          </p>
          <div className="field">
            <label>البريد الإلكتروني</label>
            <input className="input" type="email" value={email} onChange={(event) => setEmail(event.target.value)} />
          </div>
          <div className="field" style={{ marginTop: 14 }}>
            <label>كلمة المرور</label>
            <input
              className="input"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </div>
          {error && <p className="error">{error}</p>}
          <button className="button primary" type="submit" style={{ width: "100%", justifyContent: "center", marginTop: 18 }}>
            دخول
          </button>
        </form>
      </section>
    </main>
  );
}
