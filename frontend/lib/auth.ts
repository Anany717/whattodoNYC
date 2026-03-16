import { getMe } from "@/lib/api";
import type { User, UserRole } from "@/lib/types";

export const TOKEN_KEY = "whattodo_token";

function isBrowser() {
  return typeof window !== "undefined";
}

export function getToken(): string | null {
  if (!isBrowser()) return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string) {
  if (!isBrowser()) return;
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  if (!isBrowser()) return;
  localStorage.removeItem(TOKEN_KEY);
}

export function hasRole(user: User | null, roles: UserRole[]) {
  if (!user) return false;
  return roles.includes(user.role);
}

export async function loadCurrentUser(): Promise<User | null> {
  const token = getToken();
  if (!token) return null;
  try {
    return await getMe(token);
  } catch {
    clearToken();
    return null;
  }
}
