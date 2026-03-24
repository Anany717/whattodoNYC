import type { PlanMember } from "@/lib/types";

type Props = {
  members: PlanMember[];
};

export default function PlanMemberList({ members }: Props) {
  return (
    <div className="space-y-3">
      {members.map((member) => (
        <div key={member.user_id} className="flex items-center justify-between gap-3 rounded-2xl border border-slate-100 bg-white/70 px-4 py-3">
          <div>
            <p className="font-medium text-slate-900">{member.user.full_name}</p>
            <p className="text-xs text-slate-500">{member.user.email}</p>
          </div>
          <span className="rounded-full bg-brand-50 px-2.5 py-1 text-xs font-semibold uppercase tracking-wide text-brand-700">
            {member.role}
          </span>
        </div>
      ))}
    </div>
  );
}
