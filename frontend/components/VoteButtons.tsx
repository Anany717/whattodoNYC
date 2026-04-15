import type { PlanVoteValue } from "@/lib/types";

type Props = {
  value: PlanVoteValue | null;
  disabled?: boolean;
  onVote: (vote: PlanVoteValue) => Promise<void> | void;
};

const OPTIONS: Array<{ value: PlanVoteValue; label: string }> = [
  { value: "yes", label: "Yes" },
  { value: "maybe", label: "Maybe" },
  { value: "no", label: "No" },
];

export default function VoteButtons({ value, disabled, onVote }: Props) {
  return (
    <div className="flex flex-wrap gap-2">
      {OPTIONS.map((option) => {
        const active = value === option.value;
        return (
          <button
            key={option.value}
            type="button"
            disabled={disabled}
            onClick={() => void onVote(option.value)}
            className={`${active ? "btn-primary" : "btn-secondary"} px-3 py-2 text-sm disabled:cursor-not-allowed disabled:opacity-60`}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
