"use client";

import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import EmptyState from "@/components/EmptyState";
import ReviewCard from "@/components/ReviewCard";
import ReviewForm from "@/components/ReviewForm";
import SaveActions from "@/components/SaveActions";
import {
  createReview,
  getAuthenticity,
  getPlace,
  getPlacePromotions,
  getPlaceReviews,
  updateReview,
  voteAuthenticity,
} from "@/lib/api";
import { getToken, loadCurrentUser } from "@/lib/auth";
import type { PlaceDetail, Promotion, Review, User } from "@/lib/types";

export default function PlaceDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const placeId = params.id;

  const [user, setUser] = useState<User | null>(null);
  const [place, setPlace] = useState<PlaceDetail | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [promotions, setPromotions] = useState<Promotion[]>([]);
  const [authenticityScore, setAuthenticityScore] = useState<number>(0.5);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [showReviewForm, setShowReviewForm] = useState(false);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [placeData, reviewData, authenticityData, promotionsData, currentUser] = await Promise.all([
        getPlace(placeId),
        getPlaceReviews(placeId),
        getAuthenticity(placeId),
        getPlacePromotions(placeId),
        loadCurrentUser()
      ]);
      setPlace(placeData);
      setReviews(reviewData);
      setAuthenticityScore(authenticityData.score);
      setPromotions(promotionsData);
      setUser(currentUser);
      setError(null);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, [placeId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const myReview = useMemo(() => {
    if (!user) return null;
    return reviews.find((review) => review.user_id === user.id) || null;
  }, [reviews, user]);

  const submitReview = async (payload: {
    rating_overall: number;
    rating_value?: number;
    rating_vibe?: number;
    rating_groupfit?: number;
    comment?: string;
  }) => {
    const token = getToken();
    if (!token) {
      router.push("/login");
      return;
    }

    if (myReview) {
      await updateReview(token, myReview.id, payload);
    } else {
      await createReview(token, { place_id: placeId, ...payload });
    }

    setShowReviewForm(false);
    await loadData();
  };

  const castVote = async (label: "authentic" | "touristy") => {
    const token = getToken();
    if (!token) {
      router.push("/login");
      return;
    }
    await voteAuthenticity(token, placeId, label);
    await loadData();
  };

  if (loading) {
    return <main className="mx-auto max-w-6xl px-4 py-10 text-sm text-slate-600">Loading place...</main>;
  }

  if (error || !place) {
    return (
      <main className="mx-auto max-w-6xl px-4 py-10">
        <EmptyState title="Place unavailable" description={error || "Could not load this place."} />
      </main>
    );
  }

  return (
    <main className="mx-auto grid max-w-6xl gap-6 px-4 py-8 lg:grid-cols-[2fr,1fr]">
      <section className="space-y-6">
        <article className="card p-6">
          <h1 className="font-display text-3xl font-bold text-slate-900">{place.name}</h1>
          <div className="mt-3 flex flex-wrap gap-2">
            {place.is_cached_from_external ? (
              <span className="rounded-full bg-brand-50 px-3 py-1 text-xs font-semibold text-brand-700">
                Google-backed place data
              </span>
            ) : null}
            {place.is_seed_data ? (
              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
                Local catalog listing
              </span>
            ) : null}
          </div>
          <p className="mt-2 text-sm text-slate-600">{place.formatted_address || "Address unavailable"}</p>

          <div className="mt-4 grid gap-3 text-sm text-slate-700 sm:grid-cols-2 lg:grid-cols-3">
            <p>
              <span className="font-semibold">Neighborhood:</span> {place.neighborhood || "N/A"}
            </p>
            <p>
              <span className="font-semibold">Type:</span> {place.place_type}
            </p>
            <p>
              <span className="font-semibold">Price:</span> {place.price_level ? "$".repeat(place.price_level) : "N/A"}
            </p>
            <p>
              <span className="font-semibold">Average rating:</span>{" "}
              {place.average_rating ? `${place.average_rating}/5` : "No ratings"}
            </p>
            <p>
              <span className="font-semibold">Authenticity score:</span> {authenticityScore.toFixed(2)}
            </p>
            <p>
              <span className="font-semibold">Review count:</span> {place.review_count}
            </p>
            <p>
              <span className="font-semibold">Google rating:</span>{" "}
              {typeof place.google_rating === "number"
                ? `${place.google_rating.toFixed(1)}${place.google_user_ratings_total ? ` (${place.google_user_ratings_total.toLocaleString()} ratings)` : ""}`
                : "N/A"}
            </p>
            <p>
              <span className="font-semibold">Last synced:</span>{" "}
              {place.external_last_synced_at ? new Date(place.external_last_synced_at).toLocaleString() : "N/A"}
            </p>
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            {place.tags.length ? (
              place.tags.map((tag) => (
                <span key={tag} className="rounded-full border border-brand-100 bg-brand-50/80 px-3 py-1 text-xs text-brand-700">
                  {tag}
                </span>
              ))
            ) : (
              <span className="text-xs text-slate-500">No tags available</span>
            )}
          </div>
        </article>

        <article className="card p-6">
          <h2 className="font-display text-xl font-semibold text-slate-900">Reviews</h2>
          <div className="mt-4 space-y-3">
            {reviews.length ? (
              reviews.map((review) => (
                <ReviewCard
                  key={review.id}
                  review={review}
                  canEdit={Boolean(user && user.id === review.user_id)}
                  onEdit={() => setShowReviewForm(true)}
                />
              ))
            ) : (
              <EmptyState title="No reviews yet" description="Be the first to share your experience." />
            )}
          </div>
        </article>
      </section>

      <aside className="space-y-6">
        <article className="card p-5">
          <h3 className="font-display text-lg font-semibold text-slate-900">Actions</h3>
          <div className="mt-4 space-y-2">
            <button
              className="btn-primary w-full px-4 py-2 text-sm"
              onClick={() => {
                if (!user) {
                  router.push("/login");
                  return;
                }
                setShowReviewForm((prev) => !prev);
              }}
            >
              {myReview ? "Edit your review" : "Write review"}
            </button>

            <div className="rounded-2xl border border-brand-100 bg-brand-50/70 p-3">
              <p className="text-sm font-semibold text-slate-900">Save this place</p>
              <p className="mt-1 text-xs text-slate-600">Use the heart for Favorites or the bookmark to choose a list.</p>
              <div className="mt-3">
                <SaveActions placeId={placeId} />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <button
                className="btn-secondary px-4 py-2 text-sm"
                onClick={() => castVote("authentic")}
              >
                Vote authentic
              </button>
              <button
                className="btn-secondary px-4 py-2 text-sm"
                onClick={() => castVote("touristy")}
              >
                Vote touristy
              </button>
            </div>
          </div>

          {showReviewForm ? (
            <div className="mt-4">
              <ReviewForm
                initialValues={
                  myReview
                    ? {
                        rating_overall: myReview.rating_overall,
                        rating_value: myReview.rating_value || undefined,
                        rating_vibe: myReview.rating_vibe || undefined,
                        rating_groupfit: myReview.rating_groupfit || undefined,
                        comment: myReview.comment || ""
                      }
                    : undefined
                }
                submitLabel={myReview ? "Update Review" : "Submit Review"}
                onSubmit={submitReview}
              />
            </div>
          ) : null}
        </article>

        <article className="card p-5">
          <h3 className="font-display text-lg font-semibold text-slate-900">Active Promotions</h3>
          <div className="mt-3 space-y-2">
            {promotions.length ? (
              promotions.map((promo) => (
                <div key={promo.id} className="rounded-xl border border-brand-100/80 bg-white/70 p-3">
                  <p className="text-sm font-semibold text-slate-800">{promo.title}</p>
                  <p className="text-xs text-slate-600">{promo.description || "No description"}</p>
                  <p className="mt-1 text-xs text-slate-500">
                    Boost {promo.boost_factor.toFixed(2)} • Ends {new Date(promo.end_at).toLocaleString()}
                  </p>
                </div>
              ))
            ) : (
              <p className="text-sm text-slate-600">No active promotions.</p>
            )}
          </div>
        </article>
      </aside>
    </main>
  );
}
