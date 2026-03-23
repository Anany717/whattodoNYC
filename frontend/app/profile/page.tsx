"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import EmptyState from "@/components/EmptyState";
import PlaceCard from "@/components/PlaceCard";
import ProfileHeader from "@/components/ProfileHeader";
import ProtectedRoute from "@/components/ProtectedRoute";
import ReviewCard from "@/components/ReviewCard";
import SavedListCard from "@/components/SavedListCard";
import { getMyReviews, getMySavedLists, getUserProfile, updateUserProfile } from "@/lib/api";
import { getToken } from "@/lib/auth";
import type { Place, SavedList, User, UserReview } from "@/lib/types";

export default function ProfilePage() {
  const [user, setUser] = useState<User | null>(null);
  const [reviews, setReviews] = useState<UserReview[]>([]);
  const [savedLists, setSavedLists] = useState<SavedList[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [fullName, setFullName] = useState("");
  const [passwordPlaceholder, setPasswordPlaceholder] = useState("");

  const savedPlaces: Place[] = [];
  const seenPlaceIds = new Set<string>();
  savedLists.forEach((list) => {
    list.items.forEach((item) => {
      if (item.place && !seenPlaceIds.has(item.place.id)) {
        seenPlaceIds.add(item.place.id);
        savedPlaces.push(item.place);
      }
    });
  });

  const loadData = async () => {
    const token = getToken();
    if (!token) return;

    try {
      setLoading(true);
      const [profile, myReviews, lists] = await Promise.all([
        getUserProfile(token),
        getMyReviews(token),
        getMySavedLists(token)
      ]);
      setUser(profile);
      setFullName(profile.full_name);
      setReviews(myReviews);
      setSavedLists(lists);
      setError(null);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const onUpdate = async () => {
    const token = getToken();
    if (!token || !user) return;

    await updateUserProfile(token, {
      full_name: fullName,
      password: passwordPlaceholder || undefined
    });
    setPasswordPlaceholder("");
    await loadData();
  };

  return (
    <ProtectedRoute>
      <main className="mx-auto max-w-6xl space-y-6 px-4 py-8">
        {error ? <p className="text-sm text-red-600">{error}</p> : null}

        {user ? <ProfileHeader user={user} /> : null}

        {user?.role === "reviewer" ? (
          <section className="card p-4">
            <h2 className="text-lg font-semibold text-slate-900">Reviewer activity</h2>
            <p className="mt-1 text-sm text-slate-600">
              You have posted {reviews.length} review{reviews.length === 1 ? "" : "s"}. Keep improving recommendation quality.
            </p>
          </section>
        ) : null}

        {user?.role === "seller" ? (
          <section className="card p-4">
            <h2 className="text-lg font-semibold text-slate-900">Seller tools</h2>
            <p className="mt-1 text-sm text-slate-600">Manage your places and promotions from the seller dashboard.</p>
            <Link
              href="/seller/dashboard"
              className="btn-primary mt-3 px-4 py-2 text-sm"
            >
              Open seller dashboard
            </Link>
          </section>
        ) : null}

        <section className="card p-6">
          <h2 className="font-display text-xl font-semibold text-slate-900">Account settings</h2>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <label className="text-sm font-medium text-slate-700">
              Full name
              <input
                value={fullName}
                onChange={(event) => setFullName(event.target.value)}
                className="field-input mt-1"
              />
            </label>
            <label className="text-sm font-medium text-slate-700">
              Password change (optional)
              <input
                type="password"
                value={passwordPlaceholder}
                onChange={(event) => setPasswordPlaceholder(event.target.value)}
                placeholder="Enter new password"
                className="field-input mt-1"
              />
            </label>
          </div>
          <button
            onClick={onUpdate}
            className="btn-primary mt-4 px-4 py-2 text-sm"
          >
            Save profile updates
          </button>
        </section>

        <section className="card p-6">
          <h2 className="font-display text-xl font-semibold text-slate-900">Recent reviews</h2>
          <div className="mt-4 space-y-3">
            {loading ? <p className="text-sm text-slate-600">Loading...</p> : null}
            {!loading && reviews.length === 0 ? (
              <EmptyState title="No reviews yet" description="You have not submitted any reviews yet." />
            ) : null}
            {reviews.map((review) => (
              <ReviewCard key={review.id} review={review} />
            ))}
          </div>
        </section>

        <section className="card p-6">
          <h2 className="font-display text-xl font-semibold text-slate-900">Saved lists</h2>
          <div className="mt-4 grid gap-3 lg:grid-cols-2">
            {savedLists.length ? (
              savedLists.map((list) => <SavedListCard key={list.id} list={list} />)
            ) : (
              <EmptyState title="No saved lists" description="Create your first list from the saved lists page." />
            )}
          </div>
        </section>

        <section className="card p-6">
          <h2 className="font-display text-xl font-semibold text-slate-900">Saved places preview</h2>
          <div className="mt-4 grid gap-3 lg:grid-cols-2">
            {savedPlaces.length ? (
              savedPlaces.slice(0, 4).map((place) => <PlaceCard key={place.id} place={place} />)
            ) : (
              <EmptyState title="No saved places yet" description="Use the heart or bookmark on search results to start building lists." />
            )}
          </div>
        </section>
      </main>
    </ProtectedRoute>
  );
}
