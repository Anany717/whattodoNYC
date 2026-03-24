"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import EmptyState from "@/components/EmptyState";
import PlanItemCard from "@/components/PlanItemCard";
import PlanMemberList from "@/components/PlanMemberList";
import ProtectedRoute from "@/components/ProtectedRoute";
import {
  addPlanItem,
  deletePlanItem,
  finalizePlan,
  getFriends,
  getPlan,
  invitePlanMember,
  searchPlaces,
  voteOnPlanItem,
} from "@/lib/api";
import { getToken, loadCurrentUser } from "@/lib/auth";
import type { FriendsListEntry, PlaceSearchItem, Plan, PlanVoteValue, User } from "@/lib/types";

const DEFAULT_LAT = 40.7411;
const DEFAULT_LNG = -73.9897;

export default function PlanDetailPage() {
  const params = useParams<{ id: string }>();
  const [plan, setPlan] = useState<Plan | null>(null);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [friends, setFriends] = useState<FriendsListEntry[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchNote, setSearchNote] = useState("");
  const [searchResults, setSearchResults] = useState<PlaceSearchItem[]>([]);
  const [inviteUserId, setInviteUserId] = useState("");
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    const token = getToken();
    if (!token) return;
    setLoading(true);
    try {
      const [planData, friendsData, me] = await Promise.all([
        getPlan(token, params.id),
        getFriends(token),
        loadCurrentUser(),
      ]);
      setPlan(planData);
      setFriends(friendsData);
      setCurrentUser(me);
      setError(null);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, [params.id]);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const availableFriends = useMemo(() => {
    if (!plan) return friends;
    const memberIds = new Set(plan.members.map((member) => member.user_id));
    return friends.filter((entry) => !memberIds.has(entry.friend.id));
  }, [friends, plan]);

  const isHost = currentUser?.id && plan?.host_user_id === currentUser.id;

  return (
    <ProtectedRoute>
      <main className="mx-auto max-w-6xl space-y-6 px-4 py-8">
        {loading ? <p className="text-sm text-slate-600">Loading plan...</p> : null}
        {error ? <p className="text-sm text-red-600">{error}</p> : null}

        {!loading && !plan ? <EmptyState title="Plan not found" description="This plan could not be loaded." /> : null}

        {plan ? (
          <>
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <p className="text-sm font-semibold uppercase tracking-[0.22em] text-brand-700">{plan.status}</p>
                <h1 className="mt-1 font-display text-3xl font-bold text-slate-900">{plan.title}</h1>
                {plan.description ? <p className="mt-2 max-w-3xl text-sm text-slate-600">{plan.description}</p> : null}
                <p className="mt-2 text-xs text-slate-500">Hosted by {plan.host.full_name}</p>
              </div>
              <Link href="/plans" className="btn-secondary px-4 py-2 text-sm">
                Back to plans
              </Link>
            </div>

            {plan.final_choice ? (
              <section className="card border border-emerald-100 bg-emerald-50/70 p-5">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-700">Final plan</p>
                <h2 className="mt-1 font-display text-2xl font-semibold text-slate-900">{plan.final_choice.place.name}</h2>
                <p className="mt-1 text-sm text-slate-600">{plan.final_choice.place.formatted_address}</p>
              </section>
            ) : plan.leading_choice ? (
              <section className="card border border-brand-100 bg-brand-50/70 p-5">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-brand-700">Currently leading</p>
                <h2 className="mt-1 font-display text-2xl font-semibold text-slate-900">{plan.leading_choice.place.name}</h2>
                <p className="mt-1 text-sm text-slate-600">Based on the current yes/no/maybe vote balance.</p>
              </section>
            ) : null}

            <section className="grid gap-6 lg:grid-cols-[1.25fr_0.75fr]">
              <div className="space-y-6">
                <article className="card p-5">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <h2 className="text-lg font-semibold text-slate-900">Add options to this plan</h2>
                      <p className="mt-1 text-sm text-slate-600">Search NYC places and add candidates for the group vote.</p>
                    </div>
                  </div>
                  <div className="mt-4 grid gap-3 sm:grid-cols-[1fr_220px_auto]">
                    <input
                      value={searchQuery}
                      onChange={(event) => setSearchQuery(event.target.value)}
                      placeholder="Search restaurants, bars, museums, events..."
                      className="field-input"
                    />
                    <input
                      value={searchNote}
                      onChange={(event) => setSearchNote(event.target.value)}
                      placeholder="Optional note"
                      className="field-input"
                    />
                    <button
                      type="button"
                      className="btn-primary px-4 py-2 text-sm"
                      onClick={async () => {
                        if (!searchQuery.trim()) return;
                        setSearching(true);
                        try {
                          const response = await searchPlaces({
                            query: searchQuery.trim(),
                            lat: DEFAULT_LAT,
                            lng: DEFAULT_LNG,
                            radius_km: 12,
                            sort_by: "relevance",
                          });
                          setSearchResults(response.items);
                          setError(null);
                        } catch (err) {
                          setError((err as Error).message);
                        } finally {
                          setSearching(false);
                        }
                      }}
                    >
                      {searching ? "Searching..." : "Search places"}
                    </button>
                  </div>

                  <div className="mt-4 grid gap-3">
                    {searchResults.map((result) => (
                      <article key={result.id} className="rounded-2xl border border-slate-100 bg-white/70 p-4">
                        <div className="flex flex-wrap items-start justify-between gap-3">
                          <div>
                            <h3 className="font-medium text-slate-900">{result.name}</h3>
                            <p className="text-sm text-slate-500">{result.formatted_address}</p>
                          </div>
                          <button
                            type="button"
                            className="btn-secondary px-3 py-2 text-sm"
                            onClick={async () => {
                              const token = getToken();
                              if (!token) return;
                              await addPlanItem(token, plan.id, {
                                place_id: result.id,
                                notes: searchNote.trim() || undefined,
                              });
                              setSearchNote("");
                              await loadData();
                            }}
                          >
                            Add to plan
                          </button>
                        </div>
                      </article>
                    ))}
                  </div>
                </article>

                <section className="space-y-4">
                  <div className="flex items-center justify-between gap-3">
                    <h2 className="font-display text-2xl font-semibold text-slate-900">Candidate options</h2>
                    <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
                      {plan.items.length} options
                    </span>
                  </div>
                  {plan.items.length ? (
                    plan.items.map((item) => (
                      <PlanItemCard
                        key={item.id}
                        item={item}
                        isHost={Boolean(isHost)}
                        onVote={async (vote: PlanVoteValue) => {
                          const token = getToken();
                          if (!token) return;
                          await voteOnPlanItem(token, item.id, vote);
                          await loadData();
                        }}
                        onFinalize={
                          isHost
                            ? async () => {
                                const token = getToken();
                                if (!token) return;
                                await finalizePlan(token, plan.id, item.id);
                                await loadData();
                              }
                            : undefined
                        }
                        onRemove={
                          isHost
                            ? async () => {
                                const token = getToken();
                                if (!token) return;
                                await deletePlanItem(token, plan.id, item.id);
                                await loadData();
                              }
                            : undefined
                        }
                      />
                    ))
                  ) : (
                    <EmptyState title="No options yet" description="Search for places above and add a few candidates for the group." />
                  )}
                </section>
              </div>

              <div className="space-y-6">
                <article className="card p-5">
                  <h2 className="text-lg font-semibold text-slate-900">Members</h2>
                  <p className="mt-1 text-sm text-slate-600">Everyone here can view the plan and vote on the options.</p>
                  <div className="mt-4">
                    <PlanMemberList members={plan.members} />
                  </div>
                </article>

                {isHost ? (
                  <article className="card p-5">
                    <h2 className="text-lg font-semibold text-slate-900">Invite a friend</h2>
                    <p className="mt-1 text-sm text-slate-600">Only accepted friends can be added into this plan.</p>
                    {availableFriends.length ? (
                      <>
                        <select value={inviteUserId} onChange={(event) => setInviteUserId(event.target.value)} className="field-select mt-4">
                          <option value="">Select a friend</option>
                          {availableFriends.map((entry) => (
                            <option key={entry.friend.id} value={entry.friend.id}>
                              {entry.friend.full_name}
                            </option>
                          ))}
                        </select>
                        <button
                          type="button"
                          className="btn-primary mt-3 px-4 py-2 text-sm"
                          onClick={async () => {
                            const token = getToken();
                            if (!token || !inviteUserId) return;
                            await invitePlanMember(token, plan.id, inviteUserId);
                            setInviteUserId("");
                            await loadData();
                          }}
                        >
                          Invite to plan
                        </button>
                      </>
                    ) : (
                      <p className="mt-4 text-sm text-slate-500">All of your current friends are already in this plan, or you need to add more friends first.</p>
                    )}
                  </article>
                ) : null}
              </div>
            </section>
          </>
        ) : null}
      </main>
    </ProtectedRoute>
  );
}
