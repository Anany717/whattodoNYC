"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import EmptyState from "@/components/EmptyState";
import PlaceCard from "@/components/PlaceCard";
import ProtectedRoute from "@/components/ProtectedRoute";
import SellerStatsCard from "@/components/SellerStatsCard";
import { createPromotion, getSellerPlaces, getSellerPromotions } from "@/lib/api";
import { getToken } from "@/lib/auth";
import type { Place, Promotion } from "@/lib/types";

export default function SellerDashboardPage() {
  const [places, setPlaces] = useState<Place[]>([]);
  const [promotions, setPromotions] = useState<Promotion[]>([]);
  const [error, setError] = useState<string | null>(null);

  const [form, setForm] = useState({
    place_id: "",
    title: "",
    description: "",
    boost_factor: 1.2,
    start_at: "",
    end_at: ""
  });

  const activePromotions = useMemo(() => {
    const now = Date.now();
    return promotions.filter((promo) => new Date(promo.start_at).getTime() <= now && new Date(promo.end_at).getTime() >= now).length;
  }, [promotions]);

  const load = useCallback(async () => {
    const token = getToken();
    if (!token) return;
    const [sellerPlaces, sellerPromotions] = await Promise.all([getSellerPlaces(token), getSellerPromotions(token)]);
    setPlaces(sellerPlaces);
    setPromotions(sellerPromotions);
    if (!form.place_id && sellerPlaces[0]) {
      setForm((prev) => ({ ...prev, place_id: sellerPlaces[0].id }));
    }
  }, [form.place_id]);

  useEffect(() => {
    load().catch((err: Error) => setError(err.message));
  }, [load]);

  return (
    <ProtectedRoute allowedRoles={["seller"]}>
      <main className="mx-auto max-w-6xl space-y-6 px-4 py-8">
        <h1 className="text-3xl font-bold text-slate-900">Seller Dashboard</h1>
        {error ? <p className="text-sm text-red-600">{error}</p> : null}

        <section className="grid gap-4 md:grid-cols-2">
          <SellerStatsCard label="Managed Places" value={places.length} />
          <SellerStatsCard label="Active Promotions" value={activePromotions} />
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-6">
          <h2 className="text-xl font-semibold text-slate-900">Create promotion</h2>
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <select
              value={form.place_id}
              onChange={(event) => setForm((prev) => ({ ...prev, place_id: event.target.value }))}
              className="rounded-lg border border-slate-300 px-3 py-2"
            >
              <option value="">Select place</option>
              {places.map((place) => (
                <option key={place.id} value={place.id}>
                  {place.name}
                </option>
              ))}
            </select>
            <input
              value={form.title}
              onChange={(event) => setForm((prev) => ({ ...prev, title: event.target.value }))}
              placeholder="Lunch special"
              className="rounded-lg border border-slate-300 px-3 py-2"
            />
            <input
              value={form.description}
              onChange={(event) => setForm((prev) => ({ ...prev, description: event.target.value }))}
              placeholder="Details"
              className="rounded-lg border border-slate-300 px-3 py-2"
            />
            <input
              type="number"
              step={0.1}
              min={1}
              max={3}
              value={form.boost_factor}
              onChange={(event) => setForm((prev) => ({ ...prev, boost_factor: Number(event.target.value) }))}
              className="rounded-lg border border-slate-300 px-3 py-2"
            />
            <input
              type="datetime-local"
              value={form.start_at}
              onChange={(event) => setForm((prev) => ({ ...prev, start_at: event.target.value }))}
              className="rounded-lg border border-slate-300 px-3 py-2"
            />
            <input
              type="datetime-local"
              value={form.end_at}
              onChange={(event) => setForm((prev) => ({ ...prev, end_at: event.target.value }))}
              className="rounded-lg border border-slate-300 px-3 py-2"
            />
          </div>

          <button
            className="mt-4 rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-700"
            onClick={async () => {
              const token = getToken();
              if (!token) return;
              await createPromotion(token, {
                place_id: form.place_id,
                title: form.title,
                description: form.description,
                boost_factor: form.boost_factor,
                start_at: new Date(form.start_at).toISOString(),
                end_at: new Date(form.end_at).toISOString()
              });
              setForm((prev) => ({ ...prev, title: "", description: "", start_at: "", end_at: "" }));
              await load();
            }}
          >
            Create promotion
          </button>
        </section>

        <section className="grid gap-4 lg:grid-cols-2">
          <article className="space-y-3 rounded-2xl border border-slate-200 bg-white p-6">
            <h2 className="text-xl font-semibold text-slate-900">Managed places</h2>
            {places.length ? (
              places.map((place) => <PlaceCard key={place.id} place={place} />)
            ) : (
              <EmptyState title="No managed places" description="Claim places to manage them here." />
            )}
          </article>

          <article className="space-y-3 rounded-2xl border border-slate-200 bg-white p-6">
            <h2 className="text-xl font-semibold text-slate-900">Promotions</h2>
            {promotions.length ? (
              promotions.map((promo) => (
                <div key={promo.id} className="rounded-xl border border-slate-200 p-4">
                  <p className="font-semibold text-slate-900">{promo.title}</p>
                  <p className="text-sm text-slate-600">{promo.description || "No description"}</p>
                  <p className="mt-1 text-xs text-slate-500">
                    Boost {promo.boost_factor.toFixed(2)} • {new Date(promo.start_at).toLocaleString()} - {new Date(promo.end_at).toLocaleString()}
                  </p>
                </div>
              ))
            ) : (
              <EmptyState title="No promotions yet" description="Create your first promotion above." />
            )}
          </article>
        </section>
      </main>
    </ProtectedRoute>
  );
}
