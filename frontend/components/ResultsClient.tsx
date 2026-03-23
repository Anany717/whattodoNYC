"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";

import PlaceCard from "@/components/PlaceCard";
import ResultCard from "@/components/ResultCard";
import SaveActions from "@/components/SaveActions";
import SearchForm from "@/components/SearchForm";
import { fetchRecommendations, searchPlaces } from "@/lib/api";
import type {
  PlaceSearchItem,
  RecommendationItem,
  RecommendationRequest,
  SearchSortBy,
} from "@/lib/types";

function toRequest(params: URLSearchParams): RecommendationRequest {
  return {
    keywords: params.get("keywords") || "cheap authentic thai",
    budget: Number(params.get("budget") || 2) as 1 | 2 | 3 | 4,
    group_size: Number(params.get("group_size") || 2),
    preference: (params.get("preference") as "indoor" | "outdoor" | "either") || "either",
    lat: Number(params.get("lat") || 40.7411),
    lng: Number(params.get("lng") || -73.9897),
    radius_km: Number(params.get("radius_km") || 5),
  };
}

function toSortBy(params: URLSearchParams): SearchSortBy {
  return (params.get("sort_by") as SearchSortBy) || "relevance";
}

function sortLabel(sortBy: SearchSortBy) {
  switch (sortBy) {
    case "price_asc":
      return "Price: low to high";
    case "price_desc":
      return "Price: high to low";
    case "rating_desc":
      return "Top rated";
    case "distance_asc":
      return "Closest first";
    case "authenticity_desc":
      return "Most authentic";
    default:
      return "Best match";
  }
}

export default function ResultsClient() {
  const params = useSearchParams();
  const request = useMemo(() => toRequest(params), [params]);
  const sortBy = useMemo(() => toSortBy(params), [params]);
  const [results, setResults] = useState<RecommendationItem[]>([]);
  const [searchResults, setSearchResults] = useState<PlaceSearchItem[]>([]);
  const [recommendationError, setRecommendationError] = useState<string | null>(null);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [googleUsed, setGoogleUsed] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    setRecommendationError(null);
    setSearchError(null);

    Promise.allSettled([
      fetchRecommendations(request),
      searchPlaces({
        query: request.keywords,
        lat: request.lat,
        lng: request.lng,
        radius_km: request.radius_km,
        price_level: request.budget,
        sort_by: sortBy,
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
          setRecommendationError(
            recommendationResult.reason instanceof Error
              ? recommendationResult.reason.message
              : "Could not load recommendations."
          );
        }

        if (searchResult.status === "fulfilled") {
          setSearchResults(searchResult.value.items);
          setGoogleUsed(searchResult.value.google_results_used);
        } else {
          setSearchError(
            searchResult.reason instanceof Error ? searchResult.reason.message : "Could not load search results."
          );
        }
      })
      .finally(() => {
        if (!mounted) return;
        setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, [request, sortBy]);

  return (
    <section className="mx-auto max-w-6xl px-4 pb-14">
      <div className="mb-6">
        <div className="rounded-[30px] border border-white/70 bg-white/70 p-6 shadow-lift backdrop-blur-md">
          <p className="text-sm font-semibold uppercase tracking-[0.22em] text-brand-700">Search NYC</p>
          <h1 className="mt-2 font-display text-3xl font-bold text-slate-900">Find the best fit, then decide quickly.</h1>
          <p className="mt-2 max-w-3xl text-sm text-slate-600">
            Search by vibe, budget, and group size. We rank recommendations separately from the broader search results so you can see both the best overall picks and the wider field.
          </p>
        </div>
        <SearchForm initialValues={{ ...request, sort_by: sortBy }} submitLabel="Update search" />
      </div>

      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="font-display text-2xl font-semibold text-slate-900">Top recommendations</h2>
          <p className="mt-1 text-sm text-slate-600">Best overall fit for your request, with keyword match carrying the most weight.</p>
        </div>
        <Link href="/map" className="btn-primary px-4 py-2 text-sm">
          Open map view
        </Link>
      </div>

      {loading ? <p className="text-sm text-slate-600">Loading results...</p> : null}
      {recommendationError ? <p className="mb-3 text-sm text-red-600">{recommendationError}</p> : null}

      <div className="space-y-4">
        {results.map((item, index) => (
          <ResultCard key={item.place_id} item={item} rank={index + 1} />
        ))}
      </div>

      <section className="mt-12">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="font-display text-2xl font-semibold text-slate-900">Search results</h2>
            <p className="mt-1 text-sm text-slate-600">
              Sorted by {sortLabel(sortBy)}. {googleUsed ? "Expanded with nearby live place matches when our local catalog was thin." : "Using our local place catalog."}
            </p>
          </div>
          <span className="rounded-full bg-brand-50 px-3 py-1 text-xs font-semibold text-brand-700">
            {searchResults.length} results
          </span>
        </div>

        {searchError ? <p className="mb-3 text-sm text-red-600">{searchError}</p> : null}

        <div className="grid gap-4 lg:grid-cols-2">
          {searchResults.length ? (
            searchResults.map((place) => (
              <PlaceCard
                key={place.id}
                place={place}
                subtitle={place.match_summary || undefined}
                actions={<SaveActions placeId={place.id} />}
              />
            ))
          ) : (
            <p className="text-sm text-slate-600">No search matches yet. Try broadening the keyword or radius.</p>
          )}
        </div>
      </section>
    </section>
  );
}
