import RoleBadge from "@/components/RoleBadge";
import type { User } from "@/lib/types";

type Props = {
  user: User;
};

export default function ProfileHeader({ user }: Props) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{user.full_name}</h1>
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
