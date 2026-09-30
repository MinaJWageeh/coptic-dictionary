"use client";

import { BookOpen, Home, Languages, Library, LockKeyhole, Search } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { getSession, type Session } from "@/lib/auth";

const links = [
  { href: "/", label: "الرئيسية", icon: Home },
  { href: "/translate", label: "ترجمة", icon: Languages },
  { href: "/dictionary", label: "القاموس", icon: Search },
  { href: "/sources", label: "المصادر", icon: BookOpen },
  { href: "/saved", label: "المحفوظات", icon: Library },
  { href: "/about", label: "عن التطبيق", icon: Home }
];

export function PublicShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [session, setSession] = useState<Session | null>(null);

  useEffect(() => {
    setSession(getSession());
  }, []);

  return (
    <div className="public-shell" dir="rtl">
      <header className="public-topbar">
        <Link className="public-brand" href="/">
          <span className="brand-mark">Ϭ</span>
          <span>
            <strong>المترجم القبطي</strong>
            <small>من العربية إلى القبطية الموثقة</small>
          </span>
        </Link>
        <nav className="public-nav" aria-label="التنقل الرئيسي">
          {links.map((link) => {
            const Icon = link.icon;
            const active = pathname === link.href;
            return (
              <Link className={active ? "active" : ""} href={link.href} key={link.href}>
                <Icon size={16} />
                <span>{link.label}</span>
              </Link>
            );
          })}
        </nav>
        <Link className="button" href={session ? "/admin" : "/login?next=/translate"}>
          <LockKeyhole size={16} />
          {session ? "لوحة الإدارة" : "تسجيل الدخول"}
        </Link>
      </header>
      <main className="public-main">{children}</main>
    </div>
  );
}
