"use client";

import { useEffect, useState } from "react";
import { useCallback } from "react";

import EmptyState from "@/components/EmptyState";
import ProtectedRoute from "@/components/ProtectedRoute";
import SavedListCard from "@/components/SavedListCard";
import { addSavedListItem, createSavedList, getSavedLists, removeSavedListItem } from "@/lib/api";
import { getToken } from "@/lib/auth";
import type { SavedList } from "@/lib/types";

export default function SavedListsPage() {
  const [lists, setLists] = useState<SavedList[]>([]);
  const [newListName, setNewListName] = useState("");
  const [selectedListId, setSelectedListId] = useState("");
  const [placeIdInput, setPlaceIdInput] = useState("");
  const [error, setError] = useState<string | null>(null);

  const loadLists = useCallback(async () => {
    const token = getToken();
    if (!token) return;
    const data = await getSavedLists(token);
    setLists(data);
    setSelectedListId((prev) => prev || data[0]?.id || "");
  }, []);

  useEffect(() => {
    loadLists().catch((err: Error) => setError(err.message));
  }, [loadLists]);

  return (
    <ProtectedRoute>
      <main className="mx-auto max-w-6xl space-y-6 px-4 py-8">
        <h1 className="text-3xl font-bold text-slate-900">Saved Lists</h1>
        <p className="text-sm text-slate-600">Organize places by trips, neighborhoods, or moods.</p>

        {error ? <p className="text-sm text-red-600">{error}</p> : null}

        <section className="grid gap-4 lg:grid-cols-2">
          <article className="rounded-2xl border border-slate-200 bg-white p-5">
            <h2 className="text-lg font-semibold text-slate-900">Create list</h2>
            <div className="mt-3 flex gap-2">
              <input
                value={newListName}
                onChange={(event) => setNewListName(event.target.value)}
                placeholder="Weekend food run"
                className="flex-1 rounded-lg border border-slate-300 px-3 py-2"
              />
              <button
                className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-700"
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

          <article className="rounded-2xl border border-slate-200 bg-white p-5">
            <h2 className="text-lg font-semibold text-slate-900">Add place by ID</h2>
            <p className="mt-1 text-xs text-slate-500">Add a place directly using its ID from a place details page.</p>
            <div className="mt-3 grid gap-2 sm:grid-cols-[1fr,1fr,auto]">
              <select
                value={selectedListId}
                onChange={(event) => setSelectedListId(event.target.value)}
                className="rounded-lg border border-slate-300 px-3 py-2"
              >
                <option value="">Select list</option>
                {lists.map((list) => (
                  <option key={list.id} value={list.id}>
                    {list.name}
                  </option>
                ))}
              </select>
              <input
                value={placeIdInput}
                onChange={(event) => setPlaceIdInput(event.target.value)}
                placeholder="Place UUID"
                className="rounded-lg border border-slate-300 px-3 py-2"
              />
              <button
                className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100"
                onClick={async () => {
                  const token = getToken();
                  if (!token || !selectedListId || !placeIdInput.trim()) return;
                  await addSavedListItem(token, selectedListId, placeIdInput.trim());
                  setPlaceIdInput("");
                  await loadLists();
                }}
              >
                Save
              </button>
            </div>
          </article>
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
