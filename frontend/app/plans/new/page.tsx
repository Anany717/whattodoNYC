"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import ProtectedRoute from "@/components/ProtectedRoute";
import { createPlan, getFriends } from "@/lib/api";
import { getToken } from "@/lib/auth";
import type { FriendsListEntry, PlanVisibility } from "@/lib/types";

export default function NewPlanPage() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [visibility, setVisibility] = useState<PlanVisibility>("shared");
  const [friends, setFriends] = useState<FriendsListEntry[]>([]);
  const [selectedFriendIds, setSelectedFriendIds] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      const token = getToken();
      if (!token) return;
      try {
        setFriends(await getFriends(token));
      } catch (err) {
        setError((err as Error).message);
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, []);

  return (
    <ProtectedRoute>
      <main className="mx-auto max-w-3xl space-y-6 px-4 py-8">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.22em] text-brand-700">Create plan</p>
          <h1 className="mt-1 font-display text-3xl font-bold text-slate-900">Start a collaborative outing</h1>
          <p className="mt-2 text-sm text-slate-600">Give the plan a name, add context, and invite a few friends right away.</p>
        </div>

        {error ? <p className="text-sm text-red-600">{error}</p> : null}

        <section className="card p-6 space-y-4">
          <label className="block text-sm font-medium text-slate-700">
            Title
            <input value={title} onChange={(event) => setTitle(event.target.value)} className="field-input mt-1" placeholder="Saturday food crawl" />
          </label>

          <label className="block text-sm font-medium text-slate-700">
            Description
            <textarea value={description} onChange={(event) => setDescription(event.target.value)} className="field-input mt-1 min-h-[110px]" placeholder="Trying to pick one dinner spot before the group chat explodes." />
          </label>

          <label className="block text-sm font-medium text-slate-700">
            Visibility
            <select value={visibility} onChange={(event) => setVisibility(event.target.value as PlanVisibility)} className="field-select mt-1">
              <option value="shared">Shared</option>
              <option value="private">Private</option>
            </select>
          </label>

          <div>
            <p className="text-sm font-medium text-slate-700">Invite friends</p>
            <div className="mt-2 grid gap-2 sm:grid-cols-2">
              {loading ? <p className="text-sm text-slate-500">Loading friends...</p> : null}
              {!loading && friends.length === 0 ? <p className="text-sm text-slate-500">Add friends first from the Friends page.</p> : null}
              {friends.map((entry) => (
                <label key={entry.friendship_id} className="flex items-center gap-3 rounded-2xl border border-slate-100 bg-white/70 px-4 py-3 text-sm text-slate-700">
                  <input
                    type="checkbox"
                    checked={selectedFriendIds.includes(entry.friend.id)}
                    onChange={(event) => {
                      setSelectedFriendIds((current) =>
                        event.target.checked
                          ? [...current, entry.friend.id]
                          : current.filter((id) => id !== entry.friend.id)
                      );
                    }}
                  />
                  <span>{entry.friend.full_name}</span>
                </label>
              ))}
            </div>
          </div>

          <button
            type="button"
            disabled={submitting}
            onClick={async () => {
              const token = getToken();
              if (!token) return;
              if (!title.trim()) {
                setError("Give your plan a title.");
                return;
              }
              setSubmitting(true);
              try {
                const plan = await createPlan(token, {
                  title: title.trim(),
                  description: description.trim() || undefined,
                  visibility,
                  invited_user_ids: selectedFriendIds,
                });
                router.push(`/plans/${plan.id}`);
              } catch (err) {
                setError((err as Error).message);
              } finally {
                setSubmitting(false);
              }
            }}
            className="btn-primary px-4 py-2 text-sm"
          >
            {submitting ? "Creating..." : "Create plan"}
          </button>
        </section>
      </main>
    </ProtectedRoute>
  );
}
