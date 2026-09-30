"use client";

import {
  BookOpen,
  Boxes,
  FileText,
  Gauge,
  GitBranch,
  Languages,
  Library,
  LogOut,
  MessageSquare,
  Network,
  ScrollText,
  Users
} from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { clearSession, getSession } from "@/lib/auth";

const navGroups = [
  {
    label: "نظرة عامة",
    items: [
      { href: "/admin", label: "لوحة التحكم", icon: Gauge },
      { href: "/translate", label: "المترجم", icon: Languages }
    ]
  },
  {
    label: "البيانات اللغوية",
    items: [
      { href: "/admin/dictionary", label: "القاموس", icon: BookOpen },
      { href: "/admin/senses", label: "المعاني العربية", icon: Languages },
      { href: "/admin/mappings", label: "ربط المعاني", icon: GitBranch },
      { href: "/admin/corpus-texts", label: "نصوص المتون", icon: Library },
      { href: "/admin/parallel-segments", label: "الأمثلة المتوازية", icon: ScrollText },
      { href: "/admin/grammar-rules", label: "القواعد النحوية", icon: Network },
      { href: "/admin/sources", label: "المصادر", icon: FileText }
    ]
  },
  {
    label: "المراجعة",
    items: [
      { href: "/translation-requests", label: "طلبات الترجمة", icon: Boxes },
      { href: "/review-queue", label: "طابور المراجعة", icon: MessageSquare }
    ]
  },
  {
    label: "الصلاحيات",
    items: [
      { href: "/admin/users-roles", label: "المستخدمون والأدوار", icon: Users },
      { href: "/admin/audit-logs", label: "سجل التدقيق", icon: ScrollText }
    ]
  }
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const session = typeof window !== "undefined" ? getSession() : null;

  return (
    <div className="app-shell" dir="rtl">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">Ϭ</div>
          <div>
            <p className="brand-title">المترجم القبطي</p>
            <p className="brand-subtitle">مساحة الإدارة</p>
          </div>
        </div>
        {navGroups.map((group) => (
          <nav className="nav-group" key={group.label}>
            <p className="nav-label">{group.label}</p>
            {group.items.map((item) => {
              const Icon = item.icon;
              const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
              return (
                <Link className={`nav-link ${active ? "active" : ""}`} href={item.href} key={item.href}>
                  <Icon size={17} />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>
        ))}
      </aside>
      <section className="content">
        <header className="topbar">
          <div>
            <strong>{session?.email || "غير مسجل الدخول"}</strong>
            <span style={{ color: "var(--muted)", marginRight: 8 }}>{session?.role}</span>
          </div>
          <button
            className="button"
            onClick={() => {
              clearSession();
              router.replace("/login");
            }}
          >
            <LogOut size={16} />
            تسجيل الخروج
          </button>
        </header>
        <main className="main">{children}</main>
      </section>
    </div>
  );
}

export function PageHeading({
  title,
  description,
  action
}: {
  title: string;
  description?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="page-heading">
      <div>
        <h1 className="page-title">{title}</h1>
        {description ? <p className="page-description">{description}</p> : null}
      </div>
      {action}
    </div>
  );
}
