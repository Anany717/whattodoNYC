import RoleBadge from "@/components/RoleBadge";
import type { User } from "@/lib/types";

type Props = {
  user: User;
};

export default function ProfileHeader({ user }: Props) {
  return (
    <section className="card relative overflow-hidden p-6">
      <div className="absolute right-0 top-0 h-24 w-24 rounded-full bg-accent-500/20 blur-2xl" />
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="relative">
          <h1 className="font-display text-2xl font-bold text-slate-900">{user.full_name}</h1>
          <p className="mt-1 text-sm text-slate-600">{user.email}</p>
          <p className="mt-1 text-xs text-slate-500">
            Joined {new Date(user.created_at).toLocaleDateString()}
          </p>
        </div>
        <RoleBadge role={user.role} />
      </div>
    </section>
  );
}
