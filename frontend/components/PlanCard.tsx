import Link from "next/link";

import type { PlanSummary } from "@/lib/types";

type Props = {
  plan: PlanSummary;
};

export default function PlanCard({ plan }: Props) {
  const itineraryPreview =
    (plan.final_itinerary.length ? plan.final_itinerary : plan.suggested_itinerary)
      .slice(0, 3)
      .map((item) => item.place.name);

  return (
    <article className="card p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-brand-700">{plan.status}</p>
          <h3 className="mt-1 font-display text-xl font-semibold text-slate-900">{plan.title}</h3>
          {plan.description ? <p className="mt-2 text-sm text-slate-600">{plan.description}</p> : null}
          <p className="mt-2 text-xs text-slate-500">Hosted by {plan.host.full_name}</p>
        </div>
        <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">
          {plan.member_count} members
        </span>
      </div>

      <div className="mt-4 flex flex-wrap gap-3 text-xs text-slate-600">
        <span>{plan.item_count} options</span>
        <span>{plan.selected_item_count} selected stops</span>
        <span>{plan.visibility === "shared" ? "Shared plan" : "Private plan"}</span>
      </div>

      {itineraryPreview.length ? (
        <div className="mt-4 rounded-2xl bg-brand-50 px-4 py-3 text-sm text-brand-800">
          {plan.final_itinerary.length ? "Final itinerary" : "Suggested itinerary"}:{" "}
          <span className="font-semibold">{itineraryPreview.join(" -> ")}</span>
        </div>
      ) : null}

      <div className="mt-5 flex items-center justify-between gap-3">
        <p className="text-xs text-slate-500">Updated {new Date(plan.updated_at).toLocaleString()}</p>
        <Link href={`/plans/${plan.id}`} className="btn-secondary px-3 py-2 text-sm">
          Open plan
        </Link>
      </div>
    </article>
  );
}
