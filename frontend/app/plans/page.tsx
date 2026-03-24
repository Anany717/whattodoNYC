"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import EmptyState from "@/components/EmptyState";
import PlanCard from "@/components/PlanCard";
import ProtectedRoute from "@/components/ProtectedRoute";
import { getPlans } from "@/lib/api";
import { getToken } from "@/lib/auth";
import type { PlanSummary } from "@/lib/types";

export default function PlansPage() {
  const [plans, setPlans] = useState<PlanSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      const token = getToken();
      if (!token) return;
      setLoading(true);
      try {
        const data = await getPlans(token);
        setPlans(data);
        setError(null);
      } catch (err) {
        setError((err as Error).message);
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, []);

  const activePlans = useMemo(() => plans.filter((plan) => plan.status !== "finalized"), [plans]);
  const finalizedPlans = useMemo(() => plans.filter((plan) => plan.status === "finalized"), [plans]);

  return (
    <ProtectedRoute>
      <main className="mx-auto max-w-6xl space-y-6 px-4 py-8">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.22em] text-brand-700">Plans</p>
            <h1 className="mt-1 font-display text-3xl font-bold text-slate-900">Coordinate the group plan</h1>
            <p className="mt-2 text-sm text-slate-600">Create collaborative plans, invite friends, vote on options, and lock in the winner.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link href="/friends" className="btn-secondary px-4 py-2 text-sm">
              Manage friends
            </Link>
            <Link href="/plans/new" className="btn-primary px-4 py-2 text-sm">
              New plan
            </Link>
          </div>
        </div>

        {error ? <p className="text-sm text-red-600">{error}</p> : null}
        {loading ? <p className="text-sm text-slate-600">Loading plans...</p> : null}

        <section className="space-y-3">
          <h2 className="font-display text-2xl font-semibold text-slate-900">Active plans</h2>
          <div className="grid gap-4 lg:grid-cols-2">
            {activePlans.length ? (
              activePlans.map((plan) => <PlanCard key={plan.id} plan={plan} />)
            ) : (
              <EmptyState title="No active plans" description="Start a new group plan and invite friends to vote on places." />
            )}
          </div>
        </section>

        <section className="space-y-3">
          <h2 className="font-display text-2xl font-semibold text-slate-900">Finalized plans</h2>
          <div className="grid gap-4 lg:grid-cols-2">
            {finalizedPlans.length ? (
              finalizedPlans.map((plan) => <PlanCard key={plan.id} plan={plan} />)
            ) : (
              <EmptyState title="Nothing finalized yet" description="Finalized plans will appear here once the host locks in a winner." />
            )}
          </div>
        </section>
      </main>
    </ProtectedRoute>
  );
}
