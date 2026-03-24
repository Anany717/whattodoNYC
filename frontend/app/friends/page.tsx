"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import EmptyState from "@/components/EmptyState";
import FriendRequestCard from "@/components/FriendRequestCard";
import ProtectedRoute from "@/components/ProtectedRoute";
import {
  acceptFriendRequest,
  declineFriendRequest,
  getFriendRequests,
  getFriends,
  removeFriend,
  searchUsers,
  sendFriendRequest,
} from "@/lib/api";
import { getToken } from "@/lib/auth";
import type { FriendRequestsResponse, FriendsListEntry, UserSummary } from "@/lib/types";

export default function FriendsPage() {
  const [friends, setFriends] = useState<FriendsListEntry[]>([]);
  const [requests, setRequests] = useState<FriendRequestsResponse>({ incoming: [], outgoing: [] });
  const [searchQuery, setSearchQuery] = useState("");
  const [results, setResults] = useState<UserSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchLoading, setSearchLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    const token = getToken();
    if (!token) return;
    setLoading(true);
    try {
      const [friendsData, requestData] = await Promise.all([
        getFriends(token),
        getFriendRequests(token),
      ]);
      setFriends(friendsData);
      setRequests(requestData);
      setError(null);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadData();
  }, []);

  const knownStatuses = useMemo(() => {
    const map = new Map<string, string>();
    friends.forEach((entry) => map.set(entry.friend.id, "friends"));
    requests.incoming.forEach((request) => map.set(request.requester.id, "incoming"));
    requests.outgoing.forEach((request) => map.set(request.addressee.id, "outgoing"));
    return map;
  }, [friends, requests]);

  const runSearch = async () => {
    const token = getToken();
    if (!token || !searchQuery.trim()) return;
    setSearchLoading(true);
    try {
      const matches = await searchUsers(token, searchQuery.trim());
      setResults(matches);
      setError(null);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSearchLoading(false);
    }
  };

  return (
    <ProtectedRoute>
      <main className="mx-auto max-w-6xl space-y-6 px-4 py-8">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.22em] text-brand-700">Friends</p>
            <h1 className="mt-1 font-display text-3xl font-bold text-slate-900">Build your planning circle</h1>
            <p className="mt-2 text-sm text-slate-600">Add friends, manage requests, and invite them into group plans.</p>
          </div>
          <Link href="/plans/new" className="btn-primary px-4 py-2 text-sm">
            Create a plan
          </Link>
        </div>

        {error ? <p className="text-sm text-red-600">{error}</p> : null}

        <section className="card p-5">
          <h2 className="text-lg font-semibold text-slate-900">Find friends in the app</h2>
          <div className="mt-3 flex flex-wrap gap-2">
            <input
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
              placeholder="Search by name or email"
              className="field-input flex-1 min-w-[260px]"
            />
            <button type="button" onClick={() => void runSearch()} className="btn-primary px-4 py-2 text-sm">
              {searchLoading ? "Searching..." : "Search users"}
            </button>
          </div>

          <div className="mt-4 grid gap-3 lg:grid-cols-2">
            {results.map((user) => {
              const relationship = knownStatuses.get(user.id);
              return (
                <article key={user.id} className="rounded-2xl border border-slate-100 bg-white/70 p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h3 className="font-medium text-slate-900">{user.full_name}</h3>
                      <p className="text-sm text-slate-500">{user.email}</p>
                    </div>
                    {relationship ? (
                      <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">
                        {relationship}
                      </span>
                    ) : (
                      <button
                        type="button"
                        className="btn-secondary px-3 py-2 text-sm"
                        onClick={async () => {
                          const token = getToken();
                          if (!token) return;
                          await sendFriendRequest(token, user.id);
                          await loadData();
                        }}
                      >
                        Add friend
                      </button>
                    )}
                  </div>
                </article>
              );
            })}
          </div>
        </section>

        <section className="grid gap-6 lg:grid-cols-2">
          <article className="card p-5">
            <h2 className="text-lg font-semibold text-slate-900">Friends</h2>
            <div className="mt-4 space-y-3">
              {loading ? <p className="text-sm text-slate-600">Loading friends...</p> : null}
              {!loading && friends.length === 0 ? (
                <EmptyState title="No friends yet" description="Send a few friend requests to start planning together." />
              ) : null}
              {friends.map((entry) => (
                <div key={entry.friendship_id} className="flex items-center justify-between gap-3 rounded-2xl border border-slate-100 bg-white/70 px-4 py-3">
                  <div>
                    <p className="font-medium text-slate-900">{entry.friend.full_name}</p>
                    <p className="text-sm text-slate-500">{entry.friend.email}</p>
                  </div>
                  <button
                    type="button"
                    onClick={async () => {
                      const token = getToken();
                      if (!token) return;
                      await removeFriend(token, entry.friend.id);
                      await loadData();
                    }}
                    className="btn-secondary px-3 py-2 text-sm"
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
          </article>

          <article className="card p-5">
            <h2 className="text-lg font-semibold text-slate-900">Incoming requests</h2>
            <div className="mt-4 space-y-3">
              {requests.incoming.length === 0 ? (
                <EmptyState title="No incoming requests" description="When someone adds you, it will show up here." />
              ) : (
                requests.incoming.map((request) => (
                  <FriendRequestCard
                    key={request.id}
                    friendship={request}
                    direction="incoming"
                    onAccept={async () => {
                      const token = getToken();
                      if (!token) return;
                      await acceptFriendRequest(token, request.id);
                      await loadData();
                    }}
                    onDecline={async () => {
                      const token = getToken();
                      if (!token) return;
                      await declineFriendRequest(token, request.id);
                      await loadData();
                    }}
                  />
                ))
              )}
            </div>

            <h2 className="mt-6 text-lg font-semibold text-slate-900">Outgoing requests</h2>
            <div className="mt-4 space-y-3">
              {requests.outgoing.length === 0 ? (
                <EmptyState title="No outgoing requests" description="Search for users to invite them into your circle." />
              ) : (
                requests.outgoing.map((request) => (
                  <FriendRequestCard key={request.id} friendship={request} direction="outgoing" />
                ))
              )}
            </div>
          </article>
        </section>
      </main>
    </ProtectedRoute>
  );
}
