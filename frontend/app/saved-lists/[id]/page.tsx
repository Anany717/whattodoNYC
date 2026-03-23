"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import EmptyState from "@/components/EmptyState";
import ProtectedRoute from "@/components/ProtectedRoute";
import { getSavedList, removeSavedListItem } from "@/lib/api";
import { getToken } from "@/lib/auth";
import type { SavedList } from "@/lib/types";

export default function SavedListDetailPage() {
  const params = useParams<{ id: string }>();
  const [savedList, setSavedList] = useState<SavedList | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const loadList = useCallback(async () => {
    const token = getToken();
    if (!token) return;
    setLoading(true);
    try {
      const list = await getSavedList(token, params.id);
      setSavedList(list);
      setError(null);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, [params.id]);

  useEffect(() => {
    void loadList();
  }, [loadList]);

  return (
    <ProtectedRoute>
      <main className="mx-auto max-w-5xl space-y-6 px-4 py-8">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.22em] text-brand-700">Saved List</p>
            <h1 className="mt-1 font-display text-3xl font-bold text-slate-900">
              {savedList?.name || "Saved places"}
            </h1>
          </div>
          <Link href="/saved-lists" className="btn-secondary px-4 py-2 text-sm">
            Back to lists
          </Link>
        </div>

        {loading ? <p className="text-sm text-slate-600">Loading list...</p> : null}
        {error ? <p className="text-sm text-red-600">{error}</p> : null}

        {!loading && !savedList ? (
          <EmptyState title="List not found" description="This saved list could not be loaded." />
        ) : null}

        {savedList ? (
          <section className="grid gap-3">
            {savedList.items.length ? (
              savedList.items.map((item) => (
                <article key={`${item.list_id}-${item.place_id}`} className="card flex flex-wrap items-center justify-between gap-4 p-5">
                  <div>
                    <p className="font-display text-lg font-semibold text-slate-900">{item.place?.name || item.place_id}</p>
                    <p className="mt-1 text-sm text-slate-600">{item.place?.formatted_address || "Address unavailable"}</p>
                    <p className="mt-1 text-xs text-slate-500">Saved {new Date(item.created_at).toLocaleString()}</p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {item.place ? (
                      <Link href={`/places/${item.place.id}`} className="btn-secondary px-3 py-2 text-sm">
                        View place
                      </Link>
                    ) : null}
                    <button
                      className="btn-primary px-3 py-2 text-sm"
                      onClick={async () => {
                        const token = getToken();
                        if (!token) return;
                        await removeSavedListItem(token, savedList.id, item.place_id);
                        await loadList();
                      }}
                    >
                      Remove
                    </button>
                  </div>
                </article>
              ))
            ) : (
              <EmptyState title="No places in this list" description="Go back to Saved Lists or Search to add some places." />
            )}
          </section>
        ) : null}
      </main>
    </ProtectedRoute>
  );
}
