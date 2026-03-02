"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import type { RecommendationRequest } from "@/lib/types";

const DEFAULT_LAT = 40.7411;
const DEFAULT_LNG = -73.9897;

export default function SearchForm() {
  const router = useRouter();
  const [form, setForm] = useState<RecommendationRequest>({
    keywords: "cheap authentic thai",
    budget: 2,
    group_size: 2,
    preference: "either",
    lat: DEFAULT_LAT,
    lng: DEFAULT_LNG,
    radius_km: 5
  });
  const [loadingGeo, setLoadingGeo] = useState(false);

  const queryString = useMemo(() => {
    const params = new URLSearchParams({
      keywords: form.keywords,
      budget: String(form.budget),
      group_size: String(form.group_size),
      preference: form.preference,
      lat: String(form.lat),
      lng: String(form.lng),
      radius_km: String(form.radius_km)
    });
    return params.toString();
  }, [form]);

  const update = <K extends keyof RecommendationRequest>(key: K, value: RecommendationRequest[K]) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const useLocation = () => {
    if (!navigator.geolocation) {
      return;
    }
    setLoadingGeo(true);
    navigator.geolocation.getCurrentPosition(
      (position) => {
        update("lat", Number(position.coords.latitude.toFixed(5)));
        update("lng", Number(position.coords.longitude.toFixed(5)));
        setLoadingGeo(false);
      },
      () => setLoadingGeo(false),
      { enableHighAccuracy: true, timeout: 5000 }
    );
  };

  return (
    <form
      className="card mx-auto mt-8 w-full max-w-3xl space-y-5 p-6 shadow-lift"
      onSubmit={(event) => {
        event.preventDefault();
        router.push(`/results?${queryString}`);
      }}
    >
      <div>
        <label htmlFor="keywords" className="mb-1 block text-sm font-semibold text-slate-700">
          Keywords or mood
        </label>
        <input
          id="keywords"
          required
          value={form.keywords}
          onChange={(event) => update("keywords", event.target.value)}
          placeholder="romantic jazz rooftop"
          className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-slate-800 outline-none ring-brand-500 transition focus:ring-2"
        />
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div>
          <label htmlFor="budget" className="mb-1 block text-sm font-semibold text-slate-700">
            Budget
          </label>
          <select
            id="budget"
            value={form.budget}
            onChange={(event) => update("budget", Number(event.target.value) as 1 | 2 | 3 | 4)}
            className="w-full rounded-xl border border-slate-200 bg-white px-3 py-3"
          >
            <option value={1}>$</option>
            <option value={2}>$$</option>
            <option value={3}>$$$</option>
            <option value={4}>$$$$</option>
          </select>
        </div>

        <div>
          <label htmlFor="group" className="mb-1 block text-sm font-semibold text-slate-700">
            Group size
          </label>
          <input
            id="group"
            type="number"
            min={1}
            value={form.group_size}
            onChange={(event) => update("group_size", Number(event.target.value))}
            className="w-full rounded-xl border border-slate-200 bg-white px-3 py-3"
          />
        </div>

        <div>
          <label htmlFor="radius" className="mb-1 block text-sm font-semibold text-slate-700">
            Radius km
          </label>
          <input
            id="radius"
            type="number"
            min={0.5}
            step={0.5}
            value={form.radius_km}
            onChange={(event) => update("radius_km", Number(event.target.value))}
            className="w-full rounded-xl border border-slate-200 bg-white px-3 py-3"
          />
        </div>

        <div>
          <label htmlFor="preference" className="mb-1 block text-sm font-semibold text-slate-700">
            Indoor/outdoor
          </label>
          <select
            id="preference"
            value={form.preference}
            onChange={(event) =>
              update("preference", event.target.value as "indoor" | "outdoor" | "either")
            }
            className="w-full rounded-xl border border-slate-200 bg-white px-3 py-3"
          >
            <option value="either">Either</option>
            <option value="indoor">Indoor</option>
            <option value="outdoor">Outdoor</option>
          </select>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={useLocation}
          className="rounded-xl border border-brand-500 px-4 py-2 text-sm font-semibold text-brand-700 transition hover:bg-brand-50"
        >
          {loadingGeo ? "Locating..." : "Use my location"}
        </button>

        <div className="text-sm text-slate-600">
          Lat: {form.lat.toFixed(4)} | Lng: {form.lng.toFixed(4)}
        </div>
      </div>

      <button
        type="submit"
        className="w-full rounded-xl bg-brand-700 px-4 py-3 font-semibold text-white transition hover:bg-brand-500"
      >
        Find top picks
      </button>
    </form>
  );
}
