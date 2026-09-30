"use client";

export type Role = "user" | "reviewer" | "admin";

export type Session = {
  token: string;
  email: string;
  role: Role;
};

const STORAGE_KEY = "coptic-admin-session";

export function decodeJwtPayload(token: string): Record<string, unknown> | null {
  try {
    const parts = token.split(".");
    if (parts.length < 2) return null;
    const base64 = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split("")
        .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
        .join("")
    );
    return JSON.parse(jsonPayload);
  } catch {
    return null;
  }
}

export function inferRole(email: string, token?: string): Role {
  if (token) {
    const payload = decodeJwtPayload(token);
    if (payload && typeof payload.role === "string") {
      const r = payload.role.toLowerCase();
      if (r === "admin") return "admin";
      if (r === "reviewer") return "reviewer";
      return "user";
    }
  }
  const normalized = email.trim().toLowerCase();
  if (normalized === "admin@example.com" || normalized.startsWith("admin@")) return "admin";
  if (normalized === "reviewer@example.com" || normalized.startsWith("reviewer@")) return "reviewer";
  return "user";
}

export function saveSession(session: Session) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
}

export function getSession(): Session | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return null;
  try {
    const session = JSON.parse(raw) as Session;
    if (session?.token) {
      const payload = decodeJwtPayload(session.token);
      if (payload && typeof payload.exp === "number" && Date.now() >= payload.exp * 1000) {
        clearSession();
        return null;
      }
    }
    return session;
  } catch {
    clearSession();
    return null;
  }
}

export function clearSession() {
  localStorage.removeItem(STORAGE_KEY);
}

export function canAccess(role: Role, allowed: Role[]) {
  return allowed.includes(role);
}
