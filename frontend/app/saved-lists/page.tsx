"use client";

import { useCallback, useEffect, useState } from "react";

import EmptyState from "@/components/EmptyState";
import PlaceCard from "@/components/PlaceCard";
import ProtectedRoute from "@/components/ProtectedRoute";
import SaveActions from "@/components/SaveActions";
import SavedListCard from "@/components/SavedListCard";
import { createSavedList, getMySavedLists, removeSavedListItem, searchPlaces } from "@/lib/api";
import { getToken } from "@/lib/auth";
import type { Place, SavedList } from "@/lib/types";

const DEFAULT_LAT = 40.7411;
const DEFAULT_LNG = -73.9897;

export default function SavedListsPage() {
  const [lists, setLists] = useState<SavedList[]>([]);
  const [newListName, setNewListName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchPriceLevel, setSearchPriceLevel] = useState("");
  const [searchRadiusKm, setSearchRadiusKm] = useState(5);
  const [searchLat, setSearchLat] = useState(DEFAULT_LAT);
  const [searchLng, setSearchLng] = useState(DEFAULT_LNG);
  const [searchResults, setSearchResults] = useState<Place[]>([]);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [searchLoading, setSearchLoading] = useState(false);
  const [loadingGeo, setLoadingGeo] = useState(false);

  const loadLists = useCallback(async () => {
    const token = getToken();
    if (!token) return;
    const data = await getMySavedLists(token);
    setLists(data);
  }, []);

  const runSearch = useCallback(async () => {
    setSearchLoading(true);
    setSearchError(null);
    try {
      const response = await searchPlaces({
        query: searchQuery || undefined,
        lat: searchLat,
        lng: searchLng,
        radius_km: searchRadiusKm,
        price_level: searchPriceLevel ? Number(searchPriceLevel) : undefined,
      });
      setSearchResults(response.items);
    } catch (err) {
      setSearchError((err as Error).message);
    } finally {
      setSearchLoading(false);
    }
  }, [searchLat, searchLng, searchPriceLevel, searchQuery, searchRadiusKm]);

  useEffect(() => {
    loadLists().catch((err: Error) => setError(err.message));
  }, [loadLists]);

  useEffect(() => {
    let active = true;

    async function loadInitialResults() {
      setSearchLoading(true);
      setSearchError(null);
      try {
        const response = await searchPlaces({
          lat: DEFAULT_LAT,
          lng: DEFAULT_LNG,
          radius_km: 5,
        });
        if (active) {
          setSearchResults(response.items);
        }
      } catch (err) {
        if (active) {
          setSearchError((err as Error).message);
        }
      } finally {
        if (active) {
          setSearchLoading(false);
        }
      }
    }

    void loadInitialResults();

    return () => {
      active = false;
    };
  }, []);

  const useLocation = () => {
    if (!navigator.geolocation) {
      return;
    }
    setLoadingGeo(true);
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setSearchLat(Number(position.coords.latitude.toFixed(5)));
        setSearchLng(Number(position.coords.longitude.toFixed(5)));
        setLoadingGeo(false);
      },
      () => setLoadingGeo(false),
      { enableHighAccuracy: true, timeout: 5000 }
    );
  };

  return (
    <ProtectedRoute>
      <main className="mx-auto max-w-6xl space-y-6 px-4 py-8">
        <h1 className="font-display text-3xl font-bold text-slate-900">Private Saved Lists</h1>
        <p className="text-sm text-slate-600">Keep personal bookmarks here, or use Plans when you want to coordinate with friends.</p>

        {error ? <p className="text-sm text-red-600">{error}</p> : null}

        <section className="grid gap-4 lg:grid-cols-2">
          <article className="card p-5">
            <h2 className="text-lg font-semibold text-slate-900">Create list</h2>
            <div className="mt-3 flex gap-2">
              <input
                value={newListName}
                onChange={(event) => setNewListName(event.target.value)}
                placeholder="Weekend food run"
                className="field-input flex-1"
              />
              <button
                className="btn-primary px-4 py-2 text-sm"
                onClick={async () => {
                  const token = getToken();
                  if (!token || !newListName.trim()) return;
                  await createSavedList(token, newListName.trim());
                  setNewListName("");
                  await loadLists();
                }}
              >
                Add
              </button>
            </div>
          </article>

          <article className="card p-5">
            <h2 className="text-lg font-semibold text-slate-900">Browse places to save</h2>
            <p className="mt-1 text-xs text-slate-500">Use filters, then save with the heart for Favorites or the bookmark for specific lists.</p>
            <div className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
              <input
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
                placeholder="thai, jazz, rooftop..."
                className="field-input"
              />
              <select
                value={searchPriceLevel}
                onChange={(event) => setSearchPriceLevel(event.target.value)}
                className="field-select"
              >
                <option value="">Any budget</option>
                <option value="1">$</option>
                <option value="2">$$</option>
                <option value="3">$$$</option>
                <option value="4">$$$$</option>
              </select>
              <input
                type="number"
                min={0.5}
                step={0.5}
                value={searchRadiusKm}
                onChange={(event) => setSearchRadiusKm(Number(event.target.value))}
                className="field-input"
              />
              <button
                className="btn-primary px-4 py-2 text-sm"
                onClick={() => void runSearch()}
              >
                Search
              </button>
            </div>

            <div className="mt-3 flex flex-wrap items-center gap-3 text-sm text-slate-600">
              <button
                type="button"
                onClick={useLocation}
                className="btn-secondary px-4 py-2 text-sm"
              >
                {loadingGeo ? "Locating..." : "Use my location"}
              </button>
              <span>
                Lat: {searchLat.toFixed(4)} | Lng: {searchLng.toFixed(4)}
              </span>
            </div>
          </article>
        </section>

        <section className="space-y-3">
          <div className="flex items-center justify-between gap-3">
            <h2 className="font-display text-2xl font-semibold text-slate-900">Search results</h2>
            {searchLoading ? <p className="text-sm text-slate-500">Searching places...</p> : null}
          </div>
          {searchError ? <p className="text-sm text-red-600">{searchError}</p> : null}
          <div className="grid gap-3 lg:grid-cols-2">
            {searchResults.length ? (
              searchResults.map((place) => (
                <PlaceCard
                  key={place.id}
                  place={place}
                  actions={<SaveActions placeId={place.id} onChange={loadLists} />}
                />
              ))
            ) : (
              <EmptyState title="No places found" description="Try a broader keyword, a wider radius, or a different budget." />
            )}
          </div>
        </section>

        <section className="grid gap-3 lg:grid-cols-2">
          {lists.length ? (
            lists.map((list) => (
              <SavedListCard
                key={list.id}
                list={list}
                onRemoveItem={async (listId, placeId) => {
                  const token = getToken();
                  if (!token) return;
                  await removeSavedListItem(token, listId, placeId);
                  await loadLists();
                }}
              />
            ))
          ) : (
            <EmptyState title="No saved lists yet" description="Create a list to start saving places." />
          )}
        </section>
      </main>
    </ProtectedRoute>
  );
}
