import Link from "next/link";

import type { RecommendationItem } from "@/lib/types";

type Props = {
  item: RecommendationItem;
  rank: number;
};

export default function ResultCard({ item, rank }: Props) {
  return (
    <article className="card p-5 shadow-sm transition hover:-translate-y-0.5">
      <div className="mb-3 flex items-start justify-between gap-3">
        <h3 className="font-display text-xl text-slate-900">
          {rank}. {item.name}
        </h3>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
          Score {item.score.toFixed(3)}
        </span>
      </div>
      <div className="mb-2 text-sm text-slate-700">
        Price: {item.price_level ? "$".repeat(item.price_level) : "N/A"} | Distance: {item.distance_km} km
      </div>
      <p className="text-sm text-slate-800">Why this: {item.why}</p>
      <div className="mt-4">
        <Link
          href={`/places/${item.place_id}`}
          className="inline-flex rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100"
        >
          View details
        </Link>
      </div>
    </article>
  );
}
