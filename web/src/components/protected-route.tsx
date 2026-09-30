"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { canAccess, getSession, type Role, type Session } from "@/lib/auth";

export function ProtectedRoute({
  allowedRoles,
  children
}: {
  allowedRoles: Role[];
  children: React.ReactNode;
}) {
  const router = useRouter();
  const [session, setSession] = useState<Session | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const current = getSession();
    setSession(current);
    setReady(true);
    if (!current) router.replace("/login");
    else if (!canAccess(current.role, allowedRoles)) router.replace("/");
  }, [allowedRoles, router]);

  if (!ready) return <div className="main">جار التحقق من الصلاحيات...</div>;
  if (!session || !canAccess(session.role, allowedRoles)) return null;
  return <>{children}</>;
}
