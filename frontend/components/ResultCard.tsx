import Link from "next/link";

import PlaceImage from "@/components/PlaceImage";
import SaveActions from "@/components/SaveActions";
import type { RecommendationItem } from "@/lib/types";

type Props = {
  item: RecommendationItem;
  rank: number;
};

export default function ResultCard({ item, rank }: Props) {
  return (
    <article className="card p-5 transition hover:-translate-y-0.5">
      <PlaceImage
        place={{
          name: item.name,
          place_type: item.place_type,
          image_url: item.image_url,
          google_photo_reference: item.google_photo_reference,
        }}
        aspectClassName="aspect-[16/9]"
        className="mb-4"
      />
      <div className="mb-3 flex items-start justify-between gap-3">
        <div>
          <h3 className="font-display text-xl text-slate-900">
            {rank}. {item.name}
          </h3>
          <div className="mt-2 flex flex-wrap gap-2">
            <span className="rounded-full bg-brand-100 px-3 py-1 text-xs font-semibold text-brand-700">
              Score {item.score.toFixed(3)}
            </span>
            {item.is_cached_from_external ? (
              <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-700">
                Live Google-backed
              </span>
            ) : null}
          </div>
        </div>
      </div>
      {item.formatted_address ? <p className="mb-2 text-sm text-slate-600">{item.formatted_address}</p> : null}
      <div className="mb-2 text-sm text-slate-700">
        Price: {item.price_level ? "$".repeat(item.price_level) : "N/A"} | Distance: {item.distance_km} km
      </div>
      {typeof item.google_rating === "number" ? (
        <p className="mb-2 text-sm text-slate-700">
          Google rating: {item.google_rating.toFixed(1)}
          {item.google_user_ratings_total ? ` from ${item.google_user_ratings_total.toLocaleString()} ratings` : ""}
        </p>
      ) : null}
      <p className="text-sm text-slate-800">Why this: {item.why}</p>
      <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
        <Link
          href={`/places/${item.place_id}`}
          className="btn-secondary px-3 py-2 text-sm"
        >
          View details
        </Link>
        <SaveActions placeId={item.place_id} />
      </div>
    </article>
  );
}
