import Link from "next/link";

import VoteButtons from "@/components/VoteButtons";
import type { PlanItem, PlanVoteValue } from "@/lib/types";

type Props = {
  item: PlanItem;
  isHost?: boolean;
  onVote: (vote: PlanVoteValue) => Promise<void>;
  onFinalize?: () => Promise<void>;
  onRemove?: () => Promise<void>;
};

export default function PlanItemCard({ item, isHost, onVote, onFinalize, onRemove }: Props) {
  return (
    <article className="card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="font-display text-xl font-semibold text-slate-900">{item.place.name}</h3>
          <p className="mt-1 text-sm text-slate-600">{item.place.formatted_address || "Address unavailable"}</p>
          <p className="mt-1 text-xs uppercase tracking-wide text-brand-700">{item.place.place_type}</p>
        </div>
        <Link href={`/places/${item.place.id}`} className="btn-secondary px-3 py-2 text-sm">
          View place
        </Link>
      </div>

      {item.notes ? <p className="mt-3 text-sm text-slate-700">{item.notes}</p> : null}

      <div className="mt-4 grid gap-2 sm:grid-cols-4 text-sm">
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
          {isHost && onFinalize ? (
            <button type="button" onClick={() => void onFinalize()} className="btn-primary px-3 py-2 text-sm">
              Finalize this option
            </button>
          ) : null}
          {isHost && onRemove ? (
            <button type="button" onClick={() => void onRemove()} className="btn-secondary px-3 py-2 text-sm">
              Remove option
            </button>
          ) : null}
        </div>
      </div>
    </article>
  );
}
