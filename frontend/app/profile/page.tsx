"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import EmptyState from "@/components/EmptyState";
import ProfileHeader from "@/components/ProfileHeader";
import ProtectedRoute from "@/components/ProtectedRoute";
import ReviewCard from "@/components/ReviewCard";
import SavedListCard from "@/components/SavedListCard";
import { getMyReviews, getSavedLists, getUserProfile, updateUserProfile } from "@/lib/api";
import { getToken } from "@/lib/auth";
import type { SavedList, User, UserReview } from "@/lib/types";

export default function ProfilePage() {
  const [user, setUser] = useState<User | null>(null);
  const [reviews, setReviews] = useState<UserReview[]>([]);
  const [savedLists, setSavedLists] = useState<SavedList[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [fullName, setFullName] = useState("");
  const [passwordPlaceholder, setPasswordPlaceholder] = useState("");

  const loadData = async () => {
    const token = getToken();
    if (!token) return;

    try {
      setLoading(true);
      const [profile, myReviews, lists] = await Promise.all([
        getUserProfile(token),
        getMyReviews(token),
        getSavedLists(token)
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
          <section className="rounded-2xl border border-slate-200 bg-white p-4">
            <h2 className="text-lg font-semibold text-slate-900">Reviewer activity</h2>
            <p className="mt-1 text-sm text-slate-600">
              You have posted {reviews.length} review{reviews.length === 1 ? "" : "s"}. Keep improving recommendation quality.
            </p>
          </section>
        ) : null}

        {user?.role === "seller" ? (
          <section className="rounded-2xl border border-slate-200 bg-white p-4">
            <h2 className="text-lg font-semibold text-slate-900">Seller tools</h2>
            <p className="mt-1 text-sm text-slate-600">Manage your places and promotions from the seller dashboard.</p>
            <Link
              href="/seller/dashboard"
              className="mt-3 inline-flex rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-700"
            >
              Open seller dashboard
            </Link>
          </section>
        ) : null}

        <section className="rounded-2xl border border-slate-200 bg-white p-6">
          <h2 className="text-xl font-semibold text-slate-900">Account settings</h2>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <label className="text-sm font-medium text-slate-700">
              Full name
              <input
                value={fullName}
                onChange={(event) => setFullName(event.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
              />
            </label>
            <label className="text-sm font-medium text-slate-700">
              Password change (optional)
              <input
                type="password"
                value={passwordPlaceholder}
                onChange={(event) => setPasswordPlaceholder(event.target.value)}
                placeholder="Enter new password"
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
              />
            </label>
          </div>
          <button
            onClick={onUpdate}
            className="mt-4 rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-700"
          >
            Save profile updates
          </button>
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-6">
          <h2 className="text-xl font-semibold text-slate-900">Recent reviews</h2>
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

        <section className="rounded-2xl border border-slate-200 bg-white p-6">
          <h2 className="text-xl font-semibold text-slate-900">Saved lists</h2>
          <div className="mt-4 grid gap-3 lg:grid-cols-2">
            {savedLists.length ? (
              savedLists.map((list) => <SavedListCard key={list.id} list={list} />)
            ) : (
              <EmptyState title="No saved lists" description="Create your first list from the saved lists page." />
            )}
          </div>
        </section>
      </main>
    </ProtectedRoute>
  );
}
