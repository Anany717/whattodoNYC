"use client";

import { useEffect, useRef, useState } from "react";

import type { RecommendationItem } from "@/lib/types";

type StoredData = {
  request: { lat: number; lng: number };
  results: RecommendationItem[];
};

declare global {
  interface Window {
    google: any;
  }
}

export default function MapView() {
  const mapRef = useRef<HTMLDivElement | null>(null);
  const [results, setResults] = useState<RecommendationItem[]>([]);
  const [center, setCenter] = useState({ lat: 40.7411, lng: -73.9897 });
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const raw = localStorage.getItem("whattodo_results");
    if (!raw) {
      setError("No saved recommendations found. Run a search first.");
      return;
    }

    try {
      const parsed = JSON.parse(raw) as StoredData;
      setResults(parsed.results || []);
      if (parsed.request) {
        setCenter({ lat: parsed.request.lat, lng: parsed.request.lng });
      }
    } catch {
      setError("Could not parse saved map data.");
    }
  }, []);

  useEffect(() => {
    if (!mapRef.current || !results.length) {
      return;
    }

    const apiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;
    if (!apiKey) {
      setError("Missing NEXT_PUBLIC_GOOGLE_MAPS_API_KEY for map rendering.");
      return;
    }

    const scriptId = "google-maps-script";
    const existing = document.getElementById(scriptId);

    const loadMap = () => {
      const map = new window.google.maps.Map(mapRef.current, {
        center,
        zoom: 13
      });

      results.forEach((item) => {
        new window.google.maps.Marker({
          position: { lat: item.lat, lng: item.lng },
          map,
          title: item.name
        });
      });
    };

    if (existing) {
      if (window.google?.maps) {
        loadMap();
      } else {
        existing.addEventListener("load", loadMap, { once: true });
      }
      return;
    }

    const script = document.createElement("script");
    script.id = scriptId;
    script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}`;
    script.async = true;
    script.defer = true;
    script.onload = loadMap;
    document.body.appendChild(script);

    return () => {
      script.onload = null;
    };
  }, [center, results]);

  return (
    <section className="mx-auto max-w-5xl px-4 pb-14">
      <h1 className="mb-4 font-display text-3xl font-bold text-slate-900">Map View</h1>
      {error ? <p className="mb-3 text-sm text-red-600">{error}</p> : null}
      <div ref={mapRef} className="card h-[420px] w-full overflow-hidden border" />
      <div className="mt-4 grid gap-2 text-sm text-slate-700">
        {results.map((item, idx) => (
          <div key={item.place_id}>
            {idx + 1}. {item.name} ({item.distance_km} km)
          </div>
        ))}
      </div>
    </section>
  );
}
