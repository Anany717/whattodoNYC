"use client";

import { useEffect, useState } from "react";

import ProtectedRoute from "@/components/ProtectedRoute";
import SellerStatsCard from "@/components/SellerStatsCard";
import { getAdminPlaces, getAdminUsers, getPlaceReviews } from "@/lib/api";
import { getToken } from "@/lib/auth";
import type { Place, User } from "@/lib/types";

export default function AdminDashboardPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [places, setPlaces] = useState<Place[]>([]);
  const [totalReviews, setTotalReviews] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      const token = getToken();
      if (!token) return;

      const [allUsers, allPlaces] = await Promise.all([getAdminUsers(token), getAdminPlaces(token)]);
      setUsers(allUsers);
      setPlaces(allPlaces);

      const reviewCounts = await Promise.all(allPlaces.slice(0, 20).map((place) => getPlaceReviews(place.id)));
      setTotalReviews(reviewCounts.reduce((sum, reviews) => sum + reviews.length, 0));
    };

    load().catch((err: Error) => setError(err.message));
  }, []);

  return (
    <ProtectedRoute allowedRoles={["admin"]}>
      <main className="mx-auto max-w-6xl space-y-6 px-4 py-8">
        <h1 className="text-3xl font-bold text-slate-900">Admin Dashboard</h1>
        <p className="text-sm text-slate-600">Platform overview with moderation-ready management sections.</p>
        {error ? <p className="text-sm text-red-600">{error}</p> : null}

        <section className="grid gap-4 md:grid-cols-3">
          <SellerStatsCard label="Total Users" value={users.length} />
          <SellerStatsCard label="Total Places" value={places.length} />
          <SellerStatsCard label="Total Reviews" value={totalReviews} />
        </section>

        <section className="grid gap-4 lg:grid-cols-2">
          <article className="rounded-2xl border border-slate-200 bg-white p-6">
            <h2 className="text-xl font-semibold text-slate-900">Users</h2>
            <div className="mt-3 overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-left text-slate-500">
                    <th className="pb-2">Name</th>
                    <th className="pb-2">Email</th>
                    <th className="pb-2">Role</th>
                  </tr>
                </thead>
                <tbody>
                  {users.slice(0, 8).map((user) => (
                    <tr key={user.id} className="border-b border-slate-100">
                      <td className="py-2">{user.full_name}</td>
                      <td className="py-2">{user.email}</td>
                      <td className="py-2">{user.role}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </article>

          <article className="rounded-2xl border border-slate-200 bg-white p-6">
            <h2 className="text-xl font-semibold text-slate-900">Places</h2>
            <div className="mt-3 overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-left text-slate-500">
                    <th className="pb-2">Name</th>
                    <th className="pb-2">Type</th>
                    <th className="pb-2">Price</th>
                  </tr>
                </thead>
                <tbody>
                  {places.slice(0, 8).map((place) => (
                    <tr key={place.id} className="border-b border-slate-100">
                      <td className="py-2">{place.name}</td>
                      <td className="py-2">{place.place_type}</td>
                      <td className="py-2">{place.price_level ? "$".repeat(place.price_level) : "N/A"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </article>
        </section>
      </main>
    </ProtectedRoute>
  );
}
