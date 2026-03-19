"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";

import PlaceCard from "@/components/PlaceCard";
import ResultCard from "@/components/ResultCard";
import SaveActions from "@/components/SaveActions";
import { fetchRecommendations, searchPlaces } from "@/lib/api";
import type { Place, RecommendationItem, RecommendationRequest } from "@/lib/types";

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
  const [placeMatches, setPlaceMatches] = useState<Place[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    setError(null);
    setSearchError(null);

    Promise.allSettled([
      fetchRecommendations(request),
      searchPlaces({
        query: request.keywords,
        lat: request.lat,
        lng: request.lng,
        radius_km: request.radius_km,
        price_level: request.budget,
      }),
    ])
      .then(([recommendationResult, searchResult]) => {
        if (!mounted) return;

        if (recommendationResult.status === "fulfilled") {
          setResults(recommendationResult.value.results);
          localStorage.setItem(
            "whattodo_results",
            JSON.stringify({ generatedAt: new Date().toISOString(), request, results: recommendationResult.value.results })
          );
        } else {
          setError(recommendationResult.reason instanceof Error ? recommendationResult.reason.message : "Could not load recommendations.");
        }

        if (searchResult.status === "fulfilled") {
          const recommendationIds = new Set(
            recommendationResult.status === "fulfilled"
              ? recommendationResult.value.results.map((item) => item.place_id)
              : []
          );
          setPlaceMatches(searchResult.value.items.filter((place) => !recommendationIds.has(place.id)).slice(0, 8));
        } else {
          setSearchError(searchResult.reason instanceof Error ? searchResult.reason.message : "Could not load place matches.");
        }
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
          className="btn-primary px-4 py-2 text-sm"
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

      <section className="mt-10">
        <div className="mb-4">
          <h2 className="font-display text-2xl font-semibold text-slate-900">More places matching your filters</h2>
          <p className="mt-1 text-sm text-slate-600">
            This search combines our local catalog with Google-backed cached matches when nearby results are limited.
          </p>
        </div>

        {searchError ? <p className="mb-3 text-sm text-red-600">{searchError}</p> : null}

        <div className="grid gap-4 lg:grid-cols-2">
          {placeMatches.length ? (
            placeMatches.map((place) => (
              <PlaceCard
                key={place.id}
                place={place}
                actions={<SaveActions placeId={place.id} />}
              />
            ))
          ) : (
            <p className="text-sm text-slate-600">No extra matches beyond the ranked recommendations yet.</p>
          )}
        </div>
      </section>
    </section>
  );
}
