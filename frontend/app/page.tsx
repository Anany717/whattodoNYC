import SearchForm from "@/components/SearchForm";

export default function HomePage() {
  return (
    <main className="mx-auto max-w-6xl px-4 pb-16">
      <section className="relative overflow-hidden rounded-3xl border border-white/70 bg-white/70 px-6 py-10 shadow-lift backdrop-blur-md sm:px-10">
        <div className="absolute -left-8 top-6 h-24 w-24 rounded-full bg-brand-100/80 blur-2xl" />
        <div className="absolute -right-10 -top-10 h-36 w-36 rounded-full bg-accent-500/20 blur-2xl" />
        <h1 className="font-display text-4xl font-bold leading-tight text-slate-900 sm:text-5xl">
          Decide faster in NYC,
          <span className="text-brand-700"> with context-aware picks.</span>
        </h1>
        <p className="mt-3 max-w-2xl text-slate-700">
          Search by vibe, budget, group size, and location. Get ranked recommendations with quick, confident reasons.
        </p>
      </section>

      <SearchForm />
    </main>
  );
}
