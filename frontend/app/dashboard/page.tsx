"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import ProtectedRoute from "@/components/ProtectedRoute";
import SellerStatsCard from "@/components/SellerStatsCard";
import { getAdminPlaces, getAdminUsers, getSellerPlaces, getSellerPromotions } from "@/lib/api";
import { getToken, loadCurrentUser } from "@/lib/auth";
import type { User } from "@/lib/types";

export default function DashboardPage() {
  const [user, setUser] = useState<User | null>(null);
  const [stats, setStats] = useState<{ managedPlaces: number; promotions: number; users: number; places: number }>({
    managedPlaces: 0,
    promotions: 0,
    users: 0,
    places: 0
  });

  useEffect(() => {
    const load = async () => {
      const token = getToken();
      if (!token) return;
      const me = await loadCurrentUser();
      setUser(me);
      if (!me) return;

      if (me.role === "seller") {
        const [places, promotions] = await Promise.all([getSellerPlaces(token), getSellerPromotions(token)]);
        setStats((prev) => ({ ...prev, managedPlaces: places.length, promotions: promotions.length }));
      }

      if (me.role === "admin") {
        const [users, places] = await Promise.all([getAdminUsers(token), getAdminPlaces(token)]);
        setStats((prev) => ({ ...prev, users: users.length, places: places.length }));
      }
    };

    load();
  }, []);

  return (
    <ProtectedRoute>
      <main className="mx-auto max-w-6xl px-4 py-8">
        <h1 className="font-display text-3xl font-bold text-slate-900">Dashboard</h1>
        <p className="mt-2 text-sm text-slate-600">Welcome back. Use this dashboard to jump into your role-specific tools.</p>

        <section className="mt-6 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {user?.role === "seller" ? (
            <>
              <SellerStatsCard label="Managed Places" value={stats.managedPlaces} />
              <SellerStatsCard label="Promotions" value={stats.promotions} />
            </>
          ) : null}
          {user?.role === "admin" ? (
            <>
              <SellerStatsCard label="Total Users" value={stats.users} />
              <SellerStatsCard label="Total Places" value={stats.places} />
            </>
          ) : null}
          {(user?.role === "customer" || user?.role === "reviewer") && (
            <>
              <SellerStatsCard label="Saved Lists" value={1} />
              <SellerStatsCard label="Review Goals" value={3} />
            </>
          )}
        </section>

        <section className="card mt-6 p-5">
          <h2 className="text-lg font-semibold text-slate-900">Quick links</h2>
          <div className="mt-4 flex flex-wrap gap-2">
            <Link href="/profile" className="btn-secondary px-3 py-2 text-sm">
              Profile
            </Link>
            <Link href="/saved-lists" className="btn-secondary px-3 py-2 text-sm">
              Saved Lists
            </Link>
            {user?.role === "seller" ? (
              <Link href="/seller/dashboard" className="btn-secondary px-3 py-2 text-sm">
                Seller Dashboard
              </Link>
            ) : null}
            {user?.role === "admin" ? (
              <Link href="/admin/dashboard" className="btn-secondary px-3 py-2 text-sm">
                Admin Dashboard
              </Link>
            ) : null}
          </div>
        </section>
      </main>
    </ProtectedRoute>
  );
}
