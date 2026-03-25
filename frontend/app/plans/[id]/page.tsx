"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import EmptyState from "@/components/EmptyState";
import PlaceImage from "@/components/PlaceImage";
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
  reorderPlanItems,
  searchPlaces,
  updatePlanItem,
  voteOnPlanItem,
} from "@/lib/api";
import { getToken, loadCurrentUser } from "@/lib/auth";
import type {
  FriendsListEntry,
  PlaceSearchItem,
  Plan,
  PlanItem,
  PlanStepType,
  PlanVoteValue,
  User,
} from "@/lib/types";

const DEFAULT_LAT = 40.7411;
const DEFAULT_LNG = -73.9897;

const STEP_OPTIONS: Array<{ value: PlanStepType; label: string }> = [
  { value: "food", label: "Food" },
  { value: "activity", label: "Activity" },
  { value: "dessert", label: "Dessert" },
  { value: "drinks", label: "Drinks" },
  { value: "custom", label: "Custom" },
];

export default function PlanDetailPage() {
  const params = useParams<{ id: string }>();
  const [plan, setPlan] = useState<Plan | null>(null);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [friends, setFriends] = useState<FriendsListEntry[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchNote, setSearchNote] = useState("");
  const [newStepType, setNewStepType] = useState<PlanStepType>("food");
  const [addSelectedNow, setAddSelectedNow] = useState(false);
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

  const isHost = Boolean(currentUser?.id && plan?.host_user_id === currentUser.id);
  const orderedItems = useMemo(
    () =>
      [...(plan?.items || [])].sort((left, right) =>
        left.order_index === right.order_index
          ? left.created_at.localeCompare(right.created_at)
          : left.order_index - right.order_index
      ),
    [plan?.items]
  );
  const itineraryItems = plan?.final_itinerary.length ? plan.final_itinerary : plan?.suggested_itinerary || [];

  const moveItem = useCallback(
    async (itemId: string, direction: -1 | 1) => {
      if (!plan) return;
      const token = getToken();
      if (!token) return;

      const items = [...orderedItems];
      const currentIndex = items.findIndex((item) => item.id === itemId);
      const targetIndex = currentIndex + direction;
      if (currentIndex < 0 || targetIndex < 0 || targetIndex >= items.length) return;

      const reordered = [...items];
      const [moved] = reordered.splice(currentIndex, 1);
      reordered.splice(targetIndex, 0, moved);

      await reorderPlanItems(token, plan.id, {
        items: reordered.map((item, index) => ({ item_id: item.id, order_index: index })),
      });
      await loadData();
    },
    [loadData, orderedItems, plan]
  );

  const renderItineraryStops = (items: PlanItem[], emptyTitle: string, emptyDescription: string) => {
    if (!items.length) {
      return <EmptyState title={emptyTitle} description={emptyDescription} />;
    }

    return (
      <div className="space-y-3">
        {items.map((item, index) => (
          <article key={item.id} className="card p-4">
            <div className="grid gap-4 md:grid-cols-[160px_1fr]">
              <PlaceImage place={item.place} aspectClassName="aspect-[4/3]" />
              <div className="flex flex-col justify-between gap-3">
                <div>
                  <div className="flex flex-wrap gap-2">
                    <span className="rounded-full bg-slate-100 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-700">
                      Stop {index + 1}
                    </span>
                    <span className="rounded-full bg-brand-100 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-brand-700">
                      {item.step_type}
                    </span>
                  </div>
                  <h3 className="mt-3 font-display text-xl font-semibold text-slate-900">{item.place.name}</h3>
                  <p className="mt-1 text-sm text-slate-600">{item.place.formatted_address}</p>
                  {item.notes ? <p className="mt-2 text-sm text-slate-700">{item.notes}</p> : null}
                </div>
                <div className="flex flex-wrap items-center justify-between gap-3 text-xs text-slate-500">
                  <span>
                    Votes: {item.vote_summary.yes_count} yes / {item.vote_summary.maybe_count} maybe / {item.vote_summary.no_count} no
                  </span>
                  <Link href={`/places/${item.place.id}`} className="btn-secondary px-3 py-2 text-sm">
                    View place
                  </Link>
                </div>
              </div>
            </div>
          </article>
        ))}
      </div>
    );
  };

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

            <section className="grid gap-6 lg:grid-cols-[1.15fr_0.85fr]">
              <article className="card border border-emerald-100 bg-emerald-50/70 p-5">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-700">
                  {plan.final_itinerary.length ? "Final itinerary" : "Suggested itinerary"}
                </p>
                <h2 className="mt-1 font-display text-2xl font-semibold text-slate-900">
                  {plan.final_itinerary.length ? "The group outing is locked in." : "Here is the current best outing flow."}
                </h2>
                <p className="mt-2 text-sm text-slate-600">
                  {plan.final_itinerary.length
                    ? "These are the selected stops for the night, ordered as the itinerary."
                    : "We pick the strongest option in each stop type, then keep the order easy to follow."}
                </p>
              </article>

              <article className="card p-5">
                <h2 className="text-lg font-semibold text-slate-900">Itinerary summary</h2>
                <div className="mt-4 flex flex-wrap gap-2">
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
                    {plan.members.length} members
                  </span>
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
                    {plan.items.length} candidate stops
                  </span>
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
                    {plan.final_itinerary.length || plan.suggested_itinerary.length} itinerary stops
                  </span>
                </div>
                {isHost ? (
                  <div className="mt-4 flex flex-wrap gap-2">
                    <button
                      type="button"
                      className="btn-primary px-4 py-2 text-sm"
                      onClick={async () => {
                        const token = getToken();
                        if (!token) return;
                        const selectedIds = orderedItems.filter((item) => item.is_selected).map((item) => item.id);
                        await finalizePlan(token, plan.id, selectedIds.length ? selectedIds : undefined);
                        await loadData();
                      }}
                    >
                      {plan.final_itinerary.length ? "Refresh finalized itinerary" : "Finalize itinerary"}
                    </button>
                    <button
                      type="button"
                      className="btn-secondary px-4 py-2 text-sm"
                      onClick={async () => {
                        const token = getToken();
                        if (!token) return;
                        await finalizePlan(token, plan.id);
                        await loadData();
                      }}
                    >
                      Auto-build from votes
                    </button>
                  </div>
                ) : null}
              </article>
            </section>

            <section className="space-y-4">
              <div className="flex items-center justify-between gap-3">
                <h2 className="font-display text-2xl font-semibold text-slate-900">
                  {plan.final_itinerary.length ? "Final outing timeline" : "Current outing timeline"}
                </h2>
                <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
                  {itineraryItems.length} stops
                </span>
              </div>
              {renderItineraryStops(
                itineraryItems,
                "No itinerary yet",
                "Add places, mark the best ones for the outing, and the itinerary will appear here."
              )}
            </section>

            <section className="grid gap-6 lg:grid-cols-[1.25fr_0.75fr]">
              <div className="space-y-6">
                <article className="card p-5">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <h2 className="text-lg font-semibold text-slate-900">Add stops to this outing</h2>
                      <p className="mt-1 text-sm text-slate-600">
                        Search NYC places, tag them as food, activity, dessert, drinks, or custom, and build the night out.
                      </p>
                    </div>
                  </div>
                  <div className="mt-4 grid gap-3 xl:grid-cols-[1fr_220px_180px_auto]">
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
                    <select
                      value={newStepType}
                      onChange={(event) => setNewStepType(event.target.value as PlanStepType)}
                      className="field-select"
                    >
                      {STEP_OPTIONS.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
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
                  <label className="mt-3 flex items-center gap-2 text-sm text-slate-600">
                    <input
                      type="checkbox"
                      checked={addSelectedNow}
                      onChange={(event) => setAddSelectedNow(event.target.checked)}
                    />
                    Add new stops directly into the itinerary
                  </label>

                  <div className="mt-4 grid gap-3">
                    {searchResults.map((result) => (
                      <article key={result.id} className="rounded-2xl border border-slate-100 bg-white/70 p-4">
                        <div className="grid gap-4 md:grid-cols-[180px_1fr]">
                          <PlaceImage place={result} aspectClassName="aspect-[4/3]" />
                          <div className="flex flex-col justify-between gap-3">
                            <div>
                              <div className="flex flex-wrap gap-2">
                                <span className="rounded-full bg-brand-100 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-brand-700">
                                  {newStepType}
                                </span>
                                {result.search_source_label ? (
                                  <span className="rounded-full bg-slate-100 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-700">
                                    {result.search_source_label}
                                  </span>
                                ) : null}
                              </div>
                              <h3 className="mt-3 font-medium text-slate-900">{result.name}</h3>
                              <p className="text-sm text-slate-500">{result.formatted_address}</p>
                              {result.match_summary ? <p className="mt-2 text-sm text-slate-600">{result.match_summary}</p> : null}
                            </div>
                            <div className="flex flex-wrap items-center justify-between gap-3">
                              <div className="text-xs text-slate-500">
                                {result.price_level ? "$".repeat(result.price_level) : "Price unknown"}
                                {typeof result.google_rating === "number" ? ` • Google ${result.google_rating.toFixed(1)}` : ""}
                              </div>
                              <button
                                type="button"
                                className="btn-secondary px-3 py-2 text-sm"
                                onClick={async () => {
                                  const token = getToken();
                                  if (!token) return;
                                  await addPlanItem(token, plan.id, {
                                    place_id: result.id,
                                    step_type: newStepType,
                                    is_selected: addSelectedNow,
                                    notes: searchNote.trim() || undefined,
                                  });
                                  setSearchNote("");
                                  await loadData();
                                }}
                              >
                                Add to plan
                              </button>
                            </div>
                          </div>
                        </div>
                      </article>
                    ))}
                  </div>
                </article>

                <section className="space-y-4">
                  <div className="flex items-center justify-between gap-3">
                    <h2 className="font-display text-2xl font-semibold text-slate-900">Candidate stops</h2>
                    <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
                      {plan.items.length} options
                    </span>
                  </div>
                  {orderedItems.length ? (
                    orderedItems.map((item, index) => (
                      <PlanItemCard
                        key={item.id}
                        item={item}
                        isHost={isHost}
                        onVote={async (vote: PlanVoteValue) => {
                          const token = getToken();
                          if (!token) return;
                          await voteOnPlanItem(token, item.id, vote);
                          await loadData();
                        }}
                        onStepTypeChange={
                          isHost
                            ? async (stepType) => {
                                const token = getToken();
                                if (!token) return;
                                await updatePlanItem(token, plan.id, item.id, { step_type: stepType });
                                await loadData();
                              }
                            : undefined
                        }
                        onToggleSelected={
                          isHost
                            ? async () => {
                                const token = getToken();
                                if (!token) return;
                                await updatePlanItem(token, plan.id, item.id, { is_selected: !item.is_selected });
                                await loadData();
                              }
                            : undefined
                        }
                        onMoveUp={
                          isHost && index > 0
                            ? async () => {
                                await moveItem(item.id, -1);
                              }
                            : undefined
                        }
                        onMoveDown={
                          isHost && index < orderedItems.length - 1
                            ? async () => {
                                await moveItem(item.id, 1);
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
                    <EmptyState title="No stops yet" description="Search for places above and add a few food or activity options for the group." />
                  )}
                </section>
              </div>

              <div className="space-y-6">
                <article className="card p-5">
                  <h2 className="text-lg font-semibold text-slate-900">Members</h2>
                  <p className="mt-1 text-sm text-slate-600">Everyone here can view the outing and vote on candidate stops.</p>
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
                      <p className="mt-4 text-sm text-slate-500">
                        All of your current friends are already in this plan, or you need to add more friends first.
                      </p>
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
