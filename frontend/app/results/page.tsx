import { Suspense } from "react";

import ResultsClient from "@/components/ResultsClient";

export default function ResultsPage() {
  return (
    <Suspense fallback={<div className="mx-auto max-w-5xl px-4 py-10 text-sm text-slate-600">Loading...</div>}>
      <ResultsClient />
    </Suspense>
  );
}
