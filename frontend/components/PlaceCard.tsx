import Link from "next/link";

import type { Place, PlaceDetail, PlaceSearchItem, RecommendationItem } from "@/lib/types";

type PlaceLike = Place | PlaceDetail | PlaceSearchItem | RecommendationItem;

type Props = {
  place: PlaceLike;
  subtitle?: string;
  actions?: React.ReactNode;
};

export default function PlaceCard({ place, subtitle, actions }: Props) {
  const hasAddress = "formatted_address" in place;
  const hasType = "place_type" in place;
  const hasPrice = "price_level" in place;
  const placeLinkId = "place_id" in place ? place.place_id : place.id;
  const distanceKm = "distance_km" in place && typeof place.distance_km === "number" ? place.distance_km : null;
  const averageRating =
    "average_rating" in place && typeof place.average_rating === "number" ? place.average_rating : null;
  const authenticityValue =
    "authenticity_score" in place && typeof place.authenticity_score === "number"
      ? place.authenticity_score
      : null;
  const reviewCountValue =
    "review_count" in place && typeof place.review_count === "number" ? place.review_count : null;
  const googleRating =
    "google_rating" in place && typeof place.google_rating === "number" ? place.google_rating : null;
  const googleRatingsCount =
    "google_user_ratings_total" in place && typeof place.google_user_ratings_total === "number"
      ? place.google_user_ratings_total
      : null;
  const sourceLabel =
    "search_source_label" in place && place.search_source_label
      ? place.search_source_label
      : "source" in place && place.is_cached_from_external
        ? place.source === "google"
          ? "Google-sourced place"
          : "Externally refreshed"
        : null;

  return (
    <article className="card p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="font-display text-lg font-semibold text-slate-900">{place.name}</h3>
          {sourceLabel ? (
            <p className="mt-1 inline-flex rounded-full bg-brand-50 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide text-brand-700">
              {sourceLabel}
            </p>
          ) : null}
          {hasAddress && place.formatted_address ? (
            <p className="mt-1 text-sm text-slate-600">{place.formatted_address}</p>
          ) : null}
          {subtitle ? <p className="mt-1 text-sm text-slate-500">{subtitle}</p> : null}
          {hasType ? (
            <p className="mt-2 text-xs uppercase tracking-wide text-brand-700">{place.place_type}</p>
          ) : null}
        </div>

        <div className="text-right">
          {hasPrice && place.price_level ? (
            <p className="text-sm font-medium text-slate-700">{"$".repeat(place.price_level)}</p>
          ) : null}
          {distanceKm !== null ? (
            <p className="text-xs text-slate-500">{distanceKm.toFixed(2)} km</p>
          ) : null}
        </div>
      </div>

      {averageRating !== null || authenticityValue !== null || reviewCountValue !== null ? (
        <div className="mt-3 flex flex-wrap gap-3 text-xs text-slate-600">
          {averageRating !== null ? <span>Rating {averageRating.toFixed(1)}/5</span> : null}
          {googleRating !== null && reviewCountValue === 0 ? (
            <span>Google {googleRating.toFixed(1)}/5{googleRatingsCount ? ` (${googleRatingsCount.toLocaleString()})` : ""}</span>
          ) : null}
          {authenticityValue !== null ? <span>Authenticity {(authenticityValue * 100).toFixed(0)}%</span> : null}
          {reviewCountValue !== null ? <span>{reviewCountValue} reviews</span> : null}
        </div>
      ) : null}

      <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
        <Link
          href={`/places/${placeLinkId}`}
          className="btn-secondary px-3 py-2 text-sm"
        >
          View details
        </Link>
        {actions ? <div>{actions}</div> : null}
      </div>
    </article>
  );
}
