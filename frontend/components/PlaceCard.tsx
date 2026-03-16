import Link from "next/link";

import type { Place, PlaceDetail, RecommendationItem } from "@/lib/types";

type PlaceLike = Place | PlaceDetail | RecommendationItem;

type Props = {
  place: PlaceLike;
  subtitle?: string;
};

export default function PlaceCard({ place, subtitle }: Props) {
  const hasDistance = "distance_km" in place;
  const hasAddress = "formatted_address" in place;
  const hasType = "place_type" in place;
  const hasPrice = "price_level" in place;
  const placeLinkId = "place_id" in place ? place.place_id : place.id;

  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold text-slate-900">{place.name}</h3>
          {hasAddress && place.formatted_address ? (
            <p className="mt-1 text-sm text-slate-600">{place.formatted_address}</p>
          ) : null}
          {subtitle ? <p className="mt-1 text-sm text-slate-500">{subtitle}</p> : null}
          {hasType ? (
            <p className="mt-2 text-xs uppercase tracking-wide text-slate-500">{place.place_type}</p>
          ) : null}
        </div>

        <div className="text-right">
          {hasPrice && place.price_level ? (
            <p className="text-sm font-medium text-slate-700">{"$".repeat(place.price_level)}</p>
          ) : null}
          {hasDistance ? <p className="text-xs text-slate-500">{place.distance_km.toFixed(2)} km</p> : null}
        </div>
      </div>

      <div className="mt-4">
        <Link
          href={`/places/${placeLinkId}`}
          className="inline-flex rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100"
        >
          View details
        </Link>
      </div>
    </article>
  );
}
