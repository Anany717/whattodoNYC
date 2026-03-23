"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import SortDropdown from "@/components/SortDropdown";
import type { RecommendationRequest, SearchSortBy } from "@/lib/types";

const DEFAULT_LAT = 40.7411;
const DEFAULT_LNG = -73.9897;

type SearchFormValues = RecommendationRequest & {
  sort_by: SearchSortBy;
};

type Props = {
  initialValues?: Partial<SearchFormValues>;
  actionPath?: string;
  submitLabel?: string;
};

export default function SearchForm({
  initialValues,
  actionPath = "/search",
  submitLabel = "Search NYC",
}: Props) {
  const router = useRouter();
  const [form, setForm] = useState<SearchFormValues>({
    keywords: initialValues?.keywords || "cheap authentic thai",
    budget: initialValues?.budget || 2,
    group_size: initialValues?.group_size || 2,
    preference: initialValues?.preference || "either",
    lat: initialValues?.lat || DEFAULT_LAT,
    lng: initialValues?.lng || DEFAULT_LNG,
    radius_km: initialValues?.radius_km || 5,
    sort_by: initialValues?.sort_by || "relevance",
  });
  const [loadingGeo, setLoadingGeo] = useState(false);

  useEffect(() => {
    setForm({
      keywords: initialValues?.keywords || "cheap authentic thai",
      budget: initialValues?.budget || 2,
      group_size: initialValues?.group_size || 2,
      preference: initialValues?.preference || "either",
      lat: initialValues?.lat || DEFAULT_LAT,
      lng: initialValues?.lng || DEFAULT_LNG,
      radius_km: initialValues?.radius_km || 5,
      sort_by: initialValues?.sort_by || "relevance",
    });
  }, [
    initialValues?.budget,
    initialValues?.group_size,
    initialValues?.keywords,
    initialValues?.lat,
    initialValues?.lng,
    initialValues?.preference,
    initialValues?.radius_km,
    initialValues?.sort_by,
  ]);

  const queryString = useMemo(() => {
    const params = new URLSearchParams({
      keywords: form.keywords,
      budget: String(form.budget),
      group_size: String(form.group_size),
      preference: form.preference,
      lat: String(form.lat),
      lng: String(form.lng),
      radius_km: String(form.radius_km),
      sort_by: form.sort_by,
    });
    return params.toString();
  }, [form]);

  const update = <K extends keyof SearchFormValues>(key: K, value: SearchFormValues[K]) => {
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
      className="card mx-auto mt-8 w-full max-w-5xl space-y-5 p-6"
      onSubmit={(event) => {
        event.preventDefault();
        router.push(`${actionPath}?${queryString}`);
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
          className="field-input"
        />
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <div>
          <label htmlFor="budget" className="mb-1 block text-sm font-semibold text-slate-700">
            Budget
          </label>
          <select
            id="budget"
            value={form.budget}
            onChange={(event) => update("budget", Number(event.target.value) as 1 | 2 | 3 | 4)}
            className="field-select"
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
            className="field-input"
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
            className="field-input"
          />
        </div>

        <div>
          <label htmlFor="preference" className="mb-1 block text-sm font-semibold text-slate-700">
            Indoor/outdoor
          </label>
          <select
            id="preference"
            value={form.preference}
            onChange={(event) => update("preference", event.target.value as "indoor" | "outdoor" | "either")}
            className="field-select"
          >
            <option value="either">Either</option>
            <option value="indoor">Indoor</option>
            <option value="outdoor">Outdoor</option>
          </select>
        </div>

        <div>
          <label htmlFor="sort_by" className="mb-1 block text-sm font-semibold text-slate-700">
            Sort by
          </label>
          <SortDropdown value={form.sort_by} onChange={(value) => update("sort_by", value)} />
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-3">
          <button type="button" onClick={useLocation} className="btn-secondary px-4 py-2 text-sm">
            {loadingGeo ? "Locating..." : "Use my location"}
          </button>
          <div className="text-sm text-slate-600">
            Lat: {form.lat.toFixed(4)} | Lng: {form.lng.toFixed(4)}
          </div>
        </div>

        <button type="submit" className="btn-primary min-w-44">
          {submitLabel}
        </button>
      </div>
    </form>
  );
}
