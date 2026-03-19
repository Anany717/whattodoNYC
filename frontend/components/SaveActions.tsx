"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { addSavedListItem, createSavedList, getSavedLists, removeSavedListItem } from "@/lib/api";
import { getToken } from "@/lib/auth";
import type { SavedList } from "@/lib/types";

const FAVORITES_NAME = "Favorites";

type Props = {
  placeId: string;
  onChange?: () => void | Promise<void>;
};

function HeartIcon({ filled }: { filled: boolean }) {
  return (
    <svg viewBox="0 0 24 24" className="h-4 w-4" fill={filled ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2">
      <path d="M12 21s-6.7-4.35-9.33-8.15C.9 10.3 1.5 6.9 4.6 5.44c2.06-.97 4.36-.29 5.78 1.39L12 8.42l1.62-1.59c1.42-1.68 3.72-2.36 5.78-1.39 3.1 1.46 3.7 4.86 1.93 7.41C18.7 16.65 12 21 12 21Z" />
    </svg>
  );
}

function BookmarkIcon({ filled }: { filled: boolean }) {
  return (
    <svg viewBox="0 0 24 24" className="h-4 w-4" fill={filled ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2">
      <path d="M6 3h12v18l-6-4-6 4V3Z" />
    </svg>
  );
}

function listContainsPlace(list: SavedList, placeId: string) {
  return list.items.some((item) => item.place_id === placeId);
}

export default function SaveActions({ placeId, onChange }: Props) {
  const router = useRouter();
  const [lists, setLists] = useState<SavedList[]>([]);
  const [openMenu, setOpenMenu] = useState(false);
  const [newListName, setNewListName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let active = true;

    async function loadLists() {
      const token = getToken();
      if (!token) {
        if (active) {
          setLists([]);
          setError(null);
        }
        return;
      }

      try {
        const data = await getSavedLists(token);
        if (active) {
          setLists(data);
        }
      } catch (err) {
        if (active) {
          setError((err as Error).message);
        }
      }
    }

    void loadLists();

    return () => {
      active = false;
    };
  }, [placeId]);

  const favoritesList = useMemo(
    () => lists.find((list) => list.name.toLowerCase() === FAVORITES_NAME.toLowerCase()) || null,
    [lists]
  );
  const isFavorited = favoritesList ? listContainsPlace(favoritesList, placeId) : false;
  const customLists = useMemo(
    () => lists.filter((list) => list.name.toLowerCase() !== FAVORITES_NAME.toLowerCase()),
    [lists]
  );
  const savedInCustomListCount = customLists.filter((list) => listContainsPlace(list, placeId)).length;

  async function notifyChange() {
    if (onChange) {
      await onChange();
    }
  }

  async function refreshLists(token?: string) {
    const authToken = token ?? getToken();
    if (!authToken) {
      setLists([]);
      return [];
    }
    const data = await getSavedLists(authToken);
    setLists(data);
    return data;
  }

  async function requireAuth() {
    const token = getToken();
    if (!token) {
      router.push("/login");
      return null;
    }
    return token;
  }

  async function ensureFavoritesList(token: string) {
    let currentLists = lists.length ? lists : await refreshLists(token);
    let favorites = currentLists.find((list) => list.name.toLowerCase() === FAVORITES_NAME.toLowerCase()) || null;

    if (!favorites) {
      await createSavedList(token, FAVORITES_NAME);
      currentLists = await refreshLists(token);
      favorites = currentLists.find((list) => list.name.toLowerCase() === FAVORITES_NAME.toLowerCase()) || null;
    }

    return favorites;
  }

  async function toggleFavorite() {
    const token = await requireAuth();
    if (!token) return;

    setBusy(true);
    setError(null);
    try {
      const favorites = await ensureFavoritesList(token);
      if (!favorites) return;

      if (listContainsPlace(favorites, placeId)) {
        await removeSavedListItem(token, favorites.id, placeId);
      } else {
        await addSavedListItem(token, favorites.id, placeId);
      }

      await refreshLists(token);
      await notifyChange();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function toggleList(list: SavedList) {
    const token = await requireAuth();
    if (!token) return;

    setBusy(true);
    setError(null);
    try {
      if (listContainsPlace(list, placeId)) {
        await removeSavedListItem(token, list.id, placeId);
      } else {
        await addSavedListItem(token, list.id, placeId);
      }

      await refreshLists(token);
      await notifyChange();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function createListAndSave() {
    const token = await requireAuth();
    if (!token || !newListName.trim()) return;

    setBusy(true);
    setError(null);
    try {
      await createSavedList(token, newListName.trim());
      const updatedLists = await refreshLists(token);
      const createdList =
        updatedLists.find((list) => list.name.toLowerCase() === newListName.trim().toLowerCase()) || null;

      if (createdList && !listContainsPlace(createdList, placeId)) {
        await addSavedListItem(token, createdList.id, placeId);
      }

      await refreshLists(token);
      setNewListName("");
      setOpenMenu(false);
      await notifyChange();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="relative">
      <div className="flex items-center gap-2">
        <button
          type="button"
          aria-label={isFavorited ? "Remove from favorites" : "Save to favorites"}
          title={isFavorited ? "Remove from Favorites" : "Save to Favorites"}
          onClick={() => void toggleFavorite()}
          disabled={busy}
          className={`rounded-full border p-2 transition ${
            isFavorited
              ? "border-brand-700 bg-brand-700 text-white"
              : "border-brand-100 bg-white/80 text-brand-700 hover:bg-brand-50"
          }`}
        >
          <HeartIcon filled={isFavorited} />
        </button>

        <button
          type="button"
          aria-label="Save to list"
          title="Save to a specific list"
          onClick={() => {
            if (!getToken()) {
              router.push("/login");
              return;
            }
            setOpenMenu((prev) => !prev);
          }}
          className={`rounded-full border p-2 transition ${
            savedInCustomListCount
              ? "border-accent-700 bg-accent-500 text-white"
              : "border-brand-100 bg-white/80 text-brand-700 hover:bg-brand-50"
          }`}
        >
          <BookmarkIcon filled={savedInCustomListCount > 0} />
        </button>
      </div>

      {openMenu ? (
        <div className="card absolute right-0 top-full z-20 mt-2 w-72 p-3">
          <p className="text-sm font-semibold text-slate-900">Save to list</p>
          <p className="mt-1 text-xs text-slate-500">Heart saves to Favorites. Bookmark lets you manage custom lists.</p>

          <div className="mt-3 space-y-2">
            {customLists.length ? (
              customLists.map((list) => {
                const saved = listContainsPlace(list, placeId);
                return (
                  <button
                    key={list.id}
                    type="button"
                    onClick={() => void toggleList(list)}
                    disabled={busy}
                    className={`flex w-full items-center justify-between rounded-xl border px-3 py-2 text-sm transition ${
                      saved
                        ? "border-brand-500 bg-brand-50 text-brand-700"
                        : "border-slate-200 bg-white/80 text-slate-700 hover:border-brand-100 hover:bg-brand-50"
                    }`}
                  >
                    <span>{list.name}</span>
                    <span>{saved ? "Remove" : "Save"}</span>
                  </button>
                );
              })
            ) : (
              <p className="text-xs text-slate-500">No custom lists yet. Create one below.</p>
            )}
          </div>

          <div className="mt-3 flex gap-2">
            <input
              value={newListName}
              onChange={(event) => setNewListName(event.target.value)}
              placeholder="New list name"
              className="field-input flex-1 px-3 py-2 text-sm"
            />
            <button
              type="button"
              onClick={() => void createListAndSave()}
              disabled={busy || !newListName.trim()}
              className="btn-primary px-3 py-2 text-sm disabled:opacity-60"
            >
              Create
            </button>
          </div>
        </div>
      ) : null}

      {error ? <p className="mt-2 max-w-72 text-xs text-red-600">{error}</p> : null}
    </div>
  );
}
