import type { SavedList } from "@/lib/types";

type Props = {
  list: SavedList;
  onRemoveItem?: (listId: string, placeId: string) => Promise<void>;
};

export default function SavedListCard({ list, onRemoveItem }: Props) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-4">
      <div className="mb-3 flex items-center justify-between gap-2">
        <h3 className="text-lg font-semibold text-slate-900">{list.name}</h3>
        <span className="text-xs text-slate-500">{list.items.length} saved</span>
      </div>

      <div className="space-y-2">
        {list.items.map((item) => (
          <div key={`${item.list_id}-${item.place_id}`} className="flex items-center justify-between gap-3">
            <div>
              <p className="text-sm font-medium text-slate-800">{item.place?.name || item.place_id}</p>
              <p className="text-xs text-slate-500">Saved {new Date(item.created_at).toLocaleDateString()}</p>
            </div>
            {onRemoveItem ? (
              <button
                onClick={() => onRemoveItem(list.id, item.place_id)}
                className="rounded-lg border border-slate-300 px-2 py-1 text-xs font-medium text-slate-700 hover:bg-slate-100"
              >
                Remove
              </button>
            ) : null}
          </div>
        ))}
      </div>
    </article>
  );
}
