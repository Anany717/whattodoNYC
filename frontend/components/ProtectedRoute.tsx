"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import EmptyState from "@/components/EmptyState";
import { getToken, hasRole, loadCurrentUser } from "@/lib/auth";
import type { User, UserRole } from "@/lib/types";

type Props = {
  children: React.ReactNode;
  allowedRoles?: UserRole[];
};

export default function ProtectedRoute({ children, allowedRoles }: Props) {
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState<User | null>(null);
  const router = useRouter();

  useEffect(() => {
    let mounted = true;
    const token = getToken();
    if (!token) {
      router.replace("/login");
      return;
    }

    loadCurrentUser().then((currentUser) => {
      if (!mounted) return;
      setUser(currentUser);
      setLoading(false);
      if (!currentUser) {
        router.replace("/login");
      }
    });

    return () => {
      mounted = false;
    };
  }, [router]);

  if (loading) {
    return <div className="mx-auto max-w-5xl px-4 py-12 text-sm text-slate-600">Loading...</div>;
  }

  if (!user) {
    return null;
  }

  if (allowedRoles && !hasRole(user, allowedRoles)) {
    return (
      <div className="mx-auto max-w-5xl px-4 py-12">
        <EmptyState
          title="Access denied"
          description="Your account role does not have permission to view this page."
        />
      </div>
    );
  }

  return <>{children}</>;
}
