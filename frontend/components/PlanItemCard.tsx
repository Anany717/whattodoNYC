import Link from "next/link";

import PlaceImage from "@/components/PlaceImage";
import VoteButtons from "@/components/VoteButtons";
import type { PlanItem, PlanStepType, PlanVoteValue } from "@/lib/types";

type Props = {
  item: PlanItem;
  isHost?: boolean;
  onVote: (vote: PlanVoteValue) => Promise<void>;
  onStepTypeChange?: (stepType: PlanStepType) => Promise<void>;
  onToggleSelected?: () => Promise<void>;
  onMoveUp?: () => Promise<void>;
  onMoveDown?: () => Promise<void>;
  onRemove?: () => Promise<void>;
};

export default function PlanItemCard({
  item,
  isHost,
  onVote,
  onStepTypeChange,
  onToggleSelected,
  onMoveUp,
  onMoveDown,
  onRemove,
}: Props) {
  return (
    <article className="card p-5">
      <div className="grid gap-4 lg:grid-cols-[220px_1fr]">
        <PlaceImage place={item.place} aspectClassName="aspect-[4/3]" />

        <div>
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <div className="flex flex-wrap gap-2">
                <span className="rounded-full bg-brand-100 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-brand-700">
                  {item.step_type}
                </span>
                <span className="rounded-full bg-slate-100 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-700">
                  Stop {item.order_index + 1}
                </span>
                {item.is_selected ? (
                  <span className="rounded-full bg-emerald-100 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-emerald-700">
                    In itinerary
                  </span>
                ) : null}
              </div>
              <h3 className="mt-3 font-display text-xl font-semibold text-slate-900">{item.place.name}</h3>
              <p className="mt-1 text-sm text-slate-600">{item.place.formatted_address || "Address unavailable"}</p>
              <p className="mt-1 text-xs uppercase tracking-wide text-brand-700">{item.place.place_type}</p>
            </div>
            <Link href={`/places/${item.place.id}`} className="btn-secondary px-3 py-2 text-sm">
              View place
            </Link>
          </div>

          {item.notes ? <p className="mt-3 text-sm text-slate-700">{item.notes}</p> : null}

          {isHost && onStepTypeChange ? (
            <div className="mt-4 max-w-[220px]">
              <label className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
                Stop type
                <select
                  value={item.step_type}
                  onChange={(event) => void onStepTypeChange(event.target.value as PlanStepType)}
                  className="field-select mt-2"
                >
                  <option value="food">Food</option>
                  <option value="activity">Activity</option>
                  <option value="dessert">Dessert</option>
                  <option value="drinks">Drinks</option>
                  <option value="custom">Custom</option>
                </select>
              </label>
            </div>
          ) : null}

          <div className="mt-4 grid gap-2 text-sm sm:grid-cols-4">
            <div className="rounded-2xl bg-emerald-50 px-3 py-2 text-emerald-700">Yes: {item.vote_summary.yes_count}</div>
            <div className="rounded-2xl bg-amber-50 px-3 py-2 text-amber-700">Maybe: {item.vote_summary.maybe_count}</div>
            <div className="rounded-2xl bg-rose-50 px-3 py-2 text-rose-700">No: {item.vote_summary.no_count}</div>
            <div className="rounded-2xl bg-slate-100 px-3 py-2 text-slate-700">Total: {item.vote_summary.total_votes}</div>
          </div>

          <div className="mt-4">
            <p className="mb-2 text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Your vote</p>
            <VoteButtons value={item.vote_summary.current_user_vote} onVote={onVote} />
          </div>

          <div className="mt-5">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Votes from the group</p>
            <div className="mt-2 flex flex-wrap gap-2">
              {item.votes.length ? (
                item.votes.map((vote) => (
                  <span key={vote.id} className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs text-slate-700">
                    {vote.user.full_name}: {vote.vote}
                  </span>
                ))
              ) : (
                <span className="text-sm text-slate-500">No votes yet.</span>
              )}
            </div>
          </div>

          <div className="mt-5 flex flex-wrap items-center justify-between gap-3">
            <p className="text-xs text-slate-500">Added by {item.added_by_user.full_name}</p>
            <div className="flex flex-wrap gap-2">
              {isHost && onMoveUp ? (
                <button type="button" onClick={() => void onMoveUp()} className="btn-secondary px-3 py-2 text-sm">
                  Move up
                </button>
              ) : null}
              {isHost && onMoveDown ? (
                <button type="button" onClick={() => void onMoveDown()} className="btn-secondary px-3 py-2 text-sm">
                  Move down
                </button>
              ) : null}
              {isHost && onToggleSelected ? (
                <button type="button" onClick={() => void onToggleSelected()} className="btn-primary px-3 py-2 text-sm">
                  {item.is_selected ? "Remove from itinerary" : "Add to itinerary"}
                </button>
              ) : null}
              {isHost && onRemove ? (
                <button type="button" onClick={() => void onRemove()} className="btn-secondary px-3 py-2 text-sm">
                  Remove option
                </button>
              ) : null}
            </div>
          </div>
        </div>
      </div>
    </article>
  );
}
