import type { Review, UserReview } from "@/lib/types";

type Props = {
  review: Review | UserReview;
  canEdit?: boolean;
  onEdit?: (review: Review | UserReview) => void;
};

function metricLabel(label: string, value: number | null) {
  return `${label}: ${value ?? "N/A"}`;
}

export default function ReviewCard({ review, canEdit, onEdit }: Props) {
  const placeName = "place_name" in review ? review.place_name : null;
  return (
    <article className="card p-4">
      <div className="mb-2 flex items-start justify-between gap-3">
        <div>
          {placeName ? <p className="text-sm font-semibold text-brand-700">{placeName}</p> : null}
          <p className="text-sm font-semibold text-slate-900">Overall: {review.rating_overall}/5</p>
          <p className="text-xs text-slate-500">{new Date(review.created_at).toLocaleString()}</p>
        </div>
        {canEdit && onEdit ? (
          <button
            className="btn-secondary px-2 py-1 text-xs"
            onClick={() => onEdit(review)}
          >
            Edit
          </button>
        ) : null}
      </div>

      <p className="text-sm text-slate-700">{review.comment || "No comment provided."}</p>
      <div className="mt-3 grid gap-1 text-xs text-slate-600 sm:grid-cols-3">
        <p>{metricLabel("Value", review.rating_value)}</p>
        <p>{metricLabel("Vibe", review.rating_vibe)}</p>
        <p>{metricLabel("Group fit", review.rating_groupfit)}</p>
      </div>
    </article>
  );
}
