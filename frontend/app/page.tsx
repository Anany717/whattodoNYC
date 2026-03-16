import SearchForm from "@/components/SearchForm";

export default function HomePage() {
  return (
    <main className="mx-auto max-w-6xl px-4 pb-16">
      <section className="rounded-3xl border border-slate-200 bg-white px-6 py-10 shadow-sm sm:px-10">
        <h1 className="font-display text-4xl font-bold leading-tight text-slate-900 sm:text-5xl">
          Find the right NYC spot faster.
        </h1>
        <p className="mt-3 max-w-2xl text-slate-700">
          Search by vibe, budget, group size, and location. Get ranked recommendations with quick, clear reasons.
        </p>
      </section>

      <SearchForm />
    </main>
  );
}
