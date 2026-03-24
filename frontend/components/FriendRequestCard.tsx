import type { Friendship } from "@/lib/types";

type Props = {
  friendship: Friendship;
  direction: "incoming" | "outgoing";
  onAccept?: () => Promise<void>;
  onDecline?: () => Promise<void>;
};

export default function FriendRequestCard({ friendship, direction, onAccept, onDecline }: Props) {
  const otherUser = direction === "incoming" ? friendship.requester : friendship.addressee;

  return (
    <article className="card p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="font-medium text-slate-900">{otherUser.full_name}</h3>
          <p className="text-sm text-slate-500">{otherUser.email}</p>
          <p className="mt-1 text-xs text-slate-500">
            {direction === "incoming" ? "Wants to plan with you" : "Pending your friend request"}
          </p>
        </div>
        <span className="rounded-full bg-brand-50 px-2.5 py-1 text-xs font-semibold uppercase tracking-wide text-brand-700">
          {friendship.status}
        </span>
      </div>

      {direction === "incoming" ? (
        <div className="mt-4 flex flex-wrap gap-2">
          <button type="button" onClick={() => void onAccept?.()} className="btn-primary px-3 py-2 text-sm">
            Accept
          </button>
          <button type="button" onClick={() => void onDecline?.()} className="btn-secondary px-3 py-2 text-sm">
            Decline
          </button>
        </div>
      ) : null}
    </article>
  );
}
