"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { clearToken, loadCurrentUser } from "@/lib/auth";
import type { User } from "@/lib/types";

function NavLink({ href, label, active }: { href: string; label: string; active: boolean }) {
  return (
    <Link
      href={href}
      className={`rounded-lg px-3 py-2 text-sm font-medium transition ${
        active ? "bg-slate-900 text-white" : "text-slate-700 hover:bg-slate-100"
      }`}
    >
      {label}
    </Link>
  );
}

export default function Navbar() {
  const [user, setUser] = useState<User | null>(null);
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    let mounted = true;
    loadCurrentUser().then((u) => {
      if (!mounted) return;
      setUser(u);
    });
    return () => {
      mounted = false;
    };
  }, [pathname]);

  const links = useMemo(() => {
    const base = [
      { href: "/", label: "Home" },
      { href: "/results", label: "Results" },
      { href: "/map", label: "Map" }
    ];

    if (!user) {
      return base;
    }

    const authed = [
      ...base,
      { href: "/dashboard", label: "Dashboard" },
      { href: "/saved-lists", label: "Saved Lists" },
      { href: "/profile", label: "Profile" }
    ];

    if (user.role === "seller") {
      authed.push({ href: "/seller/dashboard", label: "Seller" });
    }
    if (user.role === "admin") {
      authed.push({ href: "/admin/dashboard", label: "Admin" });
    }

    return authed;
  }, [user]);

  return (
    <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/90 backdrop-blur">
      <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-4 py-3">
        <Link href="/" className="text-2xl font-bold tracking-tight text-slate-900">
          WhatToDo NYC
        </Link>

        <nav className="flex flex-wrap items-center gap-2">
          {links.map((link) => (
            <NavLink key={link.href} href={link.href} label={link.label} active={pathname === link.href} />
          ))}

          {!user ? (
            <>
              <NavLink href="/login" label="Login" active={pathname === "/login"} />
              <NavLink href="/register" label="Register" active={pathname === "/register"} />
            </>
          ) : (
            <button
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100"
              onClick={() => {
                clearToken();
                router.push("/login");
              }}
            >
              Logout
            </button>
          )}
        </nav>
      </div>
    </header>
  );
}
