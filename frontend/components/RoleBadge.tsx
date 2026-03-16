import type { UserRole } from "@/lib/types";

type Props = {
  role: UserRole;
};

export default function RoleBadge({ role }: Props) {
  const label = role[0].toUpperCase() + role.slice(1);
  return (
    <span className="inline-flex rounded-full border border-slate-300 bg-slate-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-slate-700">
      {label}
    </span>
  );
}
