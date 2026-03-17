type Props = {
  label: string;
  value: number;
};

export default function SellerStatsCard({ label, value }: Props) {
  return (
    <article className="card relative overflow-hidden p-4">
      <div className="absolute right-0 top-0 h-20 w-20 rounded-full bg-brand-100/70 blur-2xl" />
      <p className="relative text-xs uppercase tracking-wide text-brand-700">{label}</p>
      <p className="relative mt-2 font-display text-3xl font-bold text-slate-900">{value}</p>
    </article>
  );
}
