"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import EmptyState from "@/components/EmptyState";
import PlaceCard from "@/components/PlaceCard";
import ProtectedRoute from "@/components/ProtectedRoute";
import SellerStatsCard from "@/components/SellerStatsCard";
import { createPlace, createPromotion, getSellerPlaces, getSellerPromotions } from "@/lib/api";
import { getToken } from "@/lib/auth";
import type { Place, PlaceType, Promotion } from "@/lib/types";

const DEFAULT_LAT = "40.7411";
const DEFAULT_LNG = "-73.9897";

export default function SellerDashboardPage() {
  const [places, setPlaces] = useState<Place[]>([]);
  const [promotions, setPromotions] = useState<Promotion[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const [promotionForm, setPromotionForm] = useState({
    place_id: "",
    title: "",
    description: "",
    boost_factor: 1.2,
    start_at: "",
    end_at: ""
  });
  const [placeForm, setPlaceForm] = useState({
    place_type: "restaurant" as PlaceType,
    name: "",
    formatted_address: "",
    neighborhood: "",
    lat: DEFAULT_LAT,
    lng: DEFAULT_LNG,
    price_level: "2",
    phone: "",
    website: ""
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
    if (!promotionForm.place_id && sellerPlaces[0]) {
      setPromotionForm((prev) => ({ ...prev, place_id: sellerPlaces[0].id }));
    }
  }, [promotionForm.place_id]);

  useEffect(() => {
    load().catch((err: Error) => setError(err.message));
  }, [load]);

  return (
    <ProtectedRoute allowedRoles={["seller", "admin"]}>
      <main className="mx-auto max-w-6xl space-y-6 px-4 py-8">
        <section className="relative overflow-hidden rounded-[32px] border border-white/70 bg-white/70 p-6 shadow-lift backdrop-blur-md">
          <div className="absolute -left-10 top-4 h-24 w-24 rounded-full bg-brand-100/80 blur-2xl" />
          <div className="absolute -right-10 -top-10 h-40 w-40 rounded-full bg-accent-500/20 blur-3xl" />
          <div className="relative">
            <p className="text-sm font-semibold uppercase tracking-[0.24em] text-brand-700">Seller Workspace</p>
            <h1 className="mt-2 font-display text-3xl font-bold text-slate-900">Manage places, then turn them into campaigns.</h1>
            <p className="mt-3 max-w-2xl text-sm text-slate-700">
              Create a place listing for your business, then launch promotions that help it surface higher in recommendations.
            </p>
          </div>
        </section>

        {error ? <p className="text-sm text-red-600">{error}</p> : null}
        {notice ? <p className="text-sm text-brand-700">{notice}</p> : null}

        <section className="grid gap-4 md:grid-cols-2">
          <SellerStatsCard label="Managed Places" value={places.length} />
          <SellerStatsCard label="Active Promotions" value={activePromotions} />
        </section>

        <section className="grid gap-6 xl:grid-cols-2">
          <article className="card p-6">
            <h2 className="font-display text-2xl font-semibold text-slate-900">Create place</h2>
            <p className="mt-2 text-sm text-slate-600">Add a new internal listing that you can immediately manage and promote.</p>

            <div className="mt-5 grid gap-3 md:grid-cols-2">
              <select
                value={placeForm.place_type}
                onChange={(event) => setPlaceForm((prev) => ({ ...prev, place_type: event.target.value as PlaceType }))}
                className="field-select"
              >
                <option value="restaurant">Restaurant</option>
                <option value="event">Event</option>
                <option value="activity">Activity</option>
              </select>
              <input
                value={placeForm.name}
                onChange={(event) => setPlaceForm((prev) => ({ ...prev, name: event.target.value }))}
                placeholder="Place name"
                className="field-input"
              />
              <input
                value={placeForm.formatted_address}
                onChange={(event) => setPlaceForm((prev) => ({ ...prev, formatted_address: event.target.value }))}
                placeholder="Street address"
                className="field-input md:col-span-2"
              />
              <input
                value={placeForm.neighborhood}
                onChange={(event) => setPlaceForm((prev) => ({ ...prev, neighborhood: event.target.value }))}
                placeholder="Neighborhood"
                className="field-input"
              />
              <select
                value={placeForm.price_level}
                onChange={(event) => setPlaceForm((prev) => ({ ...prev, price_level: event.target.value }))}
                className="field-select"
              >
                <option value="">Price level</option>
                <option value="1">$</option>
                <option value="2">$$</option>
                <option value="3">$$$</option>
                <option value="4">$$$$</option>
              </select>
              <input
                value={placeForm.lat}
                onChange={(event) => setPlaceForm((prev) => ({ ...prev, lat: event.target.value }))}
                placeholder="Latitude"
                className="field-input"
              />
              <input
                value={placeForm.lng}
                onChange={(event) => setPlaceForm((prev) => ({ ...prev, lng: event.target.value }))}
                placeholder="Longitude"
                className="field-input"
              />
              <input
                value={placeForm.phone}
                onChange={(event) => setPlaceForm((prev) => ({ ...prev, phone: event.target.value }))}
                placeholder="Phone"
                className="field-input"
              />
              <input
                value={placeForm.website}
                onChange={(event) => setPlaceForm((prev) => ({ ...prev, website: event.target.value }))}
                placeholder="Website"
                className="field-input"
              />
            </div>

            <button
              className="btn-primary mt-5"
              onClick={async () => {
                const token = getToken();
                if (!token) return;

                setError(null);
                setNotice(null);

                const lat = Number(placeForm.lat);
                const lng = Number(placeForm.lng);

                if (!placeForm.name.trim()) {
                  setError("Place name is required.");
                  return;
                }
                if (Number.isNaN(lat) || Number.isNaN(lng)) {
                  setError("Latitude and longitude must be valid numbers.");
                  return;
                }

                try {
                  const newPlace = await createPlace(token, {
                    place_type: placeForm.place_type,
                    name: placeForm.name.trim(),
                    formatted_address: placeForm.formatted_address.trim() || undefined,
                    neighborhood: placeForm.neighborhood.trim() || undefined,
                    lat,
                    lng,
                    price_level: placeForm.price_level ? Number(placeForm.price_level) : null,
                    phone: placeForm.phone.trim() || undefined,
                    website: placeForm.website.trim() || undefined
                  });
                  setPlaceForm({
                    place_type: "restaurant",
                    name: "",
                    formatted_address: "",
                    neighborhood: "",
                    lat: DEFAULT_LAT,
                    lng: DEFAULT_LNG,
                    price_level: "2",
                    phone: "",
                    website: ""
                  });
                  setPromotionForm((prev) => ({ ...prev, place_id: newPlace.id }));
                  setNotice(`${newPlace.name} is now in your managed places.`);
                  await load();
                } catch (err) {
                  setError((err as Error).message);
                }
              }}
            >
              Create place
            </button>
          </article>

          <article className="card p-6">
            <h2 className="font-display text-2xl font-semibold text-slate-900">Create promotion</h2>
            <p className="mt-2 text-sm text-slate-600">Pick one of your managed places and give it a temporary visibility boost.</p>

            <div className="mt-5 grid gap-3 md:grid-cols-2">
              <select
                value={promotionForm.place_id}
                onChange={(event) => setPromotionForm((prev) => ({ ...prev, place_id: event.target.value }))}
                className="field-select"
              >
                <option value="">Select place</option>
                {places.map((place) => (
                  <option key={place.id} value={place.id}>
                    {place.name}
                  </option>
                ))}
              </select>
              <input
                value={promotionForm.title}
                onChange={(event) => setPromotionForm((prev) => ({ ...prev, title: event.target.value }))}
                placeholder="Lunch special"
                className="field-input"
              />
              <input
                value={promotionForm.description}
                onChange={(event) => setPromotionForm((prev) => ({ ...prev, description: event.target.value }))}
                placeholder="Details"
                className="field-input md:col-span-2"
              />
              <input
                type="number"
                step={0.1}
                min={1}
                max={3}
                value={promotionForm.boost_factor}
                onChange={(event) => setPromotionForm((prev) => ({ ...prev, boost_factor: Number(event.target.value) }))}
                className="field-input"
              />
              <div className="hidden md:block" />
              <input
                type="datetime-local"
                value={promotionForm.start_at}
                onChange={(event) => setPromotionForm((prev) => ({ ...prev, start_at: event.target.value }))}
                className="field-input"
              />
              <input
                type="datetime-local"
                value={promotionForm.end_at}
                onChange={(event) => setPromotionForm((prev) => ({ ...prev, end_at: event.target.value }))}
                className="field-input"
              />
            </div>

            <button
              className="btn-primary mt-5"
              onClick={async () => {
                const token = getToken();
                if (!token) return;

                setError(null);
                setNotice(null);

                if (!promotionForm.place_id || !promotionForm.title.trim() || !promotionForm.start_at || !promotionForm.end_at) {
                  setError("Choose a place and fill in the promotion title and schedule.");
                  return;
                }

                try {
                  await createPromotion(token, {
                    place_id: promotionForm.place_id,
                    title: promotionForm.title.trim(),
                    description: promotionForm.description.trim() || undefined,
                    boost_factor: promotionForm.boost_factor,
                    start_at: new Date(promotionForm.start_at).toISOString(),
                    end_at: new Date(promotionForm.end_at).toISOString()
                  });
                  setPromotionForm((prev) => ({ ...prev, title: "", description: "", start_at: "", end_at: "" }));
                  setNotice("Promotion created successfully.");
                  await load();
                } catch (err) {
                  setError((err as Error).message);
                }
              }}
            >
              Create promotion
            </button>
          </article>
        </section>

        <section className="grid gap-4 lg:grid-cols-2">
          <article className="card space-y-3 p-6">
            <h2 className="font-display text-xl font-semibold text-slate-900">Managed places</h2>
            {places.length ? (
              places.map((place) => <PlaceCard key={place.id} place={place} />)
            ) : (
              <EmptyState title="No managed places" description="Create your first place above or claim an existing one." />
            )}
          </article>

          <article className="card space-y-3 p-6">
            <h2 className="font-display text-xl font-semibold text-slate-900">Promotions</h2>
            {promotions.length ? (
              promotions.map((promo) => (
                <div key={promo.id} className="rounded-xl border border-brand-100/80 bg-white/70 p-4">
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
