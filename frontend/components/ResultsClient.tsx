"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";

import ResultCard from "@/components/ResultCard";
import { fetchRecommendations } from "@/lib/api";
import type { RecommendationItem, RecommendationRequest } from "@/lib/types";

function toRequest(params: URLSearchParams): RecommendationRequest {
  return {
    keywords: params.get("keywords") || "cheap authentic thai",
    budget: Number(params.get("budget") || 2) as 1 | 2 | 3 | 4,
    group_size: Number(params.get("group_size") || 2),
    preference: (params.get("preference") as "indoor" | "outdoor" | "either") || "either",
    lat: Number(params.get("lat") || 40.7411),
    lng: Number(params.get("lng") || -73.9897),
    radius_km: Number(params.get("radius_km") || 5)
  };
}

export default function ResultsClient() {
  const params = useSearchParams();
  const request = useMemo(() => toRequest(params), [params]);
  const [results, setResults] = useState<RecommendationItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    setError(null);

    fetchRecommendations(request)
      .then((response) => {
        if (!mounted) return;
        setResults(response.results);
        localStorage.setItem(
          "whattodo_results",
          JSON.stringify({ generatedAt: new Date().toISOString(), request, results: response.results })
        );
      })
      .catch((err: Error) => {
        if (!mounted) return;
        setError(err.message);
      })
      .finally(() => {
        if (!mounted) return;
        setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, [request]);

  return (
    <section className="mx-auto max-w-5xl px-4 pb-14">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <h1 className="font-display text-3xl font-bold text-slate-900">Top NYC Picks</h1>
        <Link
          href="/map"
          className="rounded-xl bg-accent-700 px-4 py-2 text-sm font-semibold text-white hover:bg-accent-500"
        >
          Open map view
        </Link>
      </div>

      {loading ? <p>Loading recommendations...</p> : null}
      {error ? <p className="text-red-600">{error}</p> : null}

      <div className="space-y-4">
        {results.map((item, index) => (
          <ResultCard key={item.place_id} item={item} rank={index + 1} />
        ))}
      </div>
    </section>
  );
}
