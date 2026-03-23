import Link from "next/link";

import type { SavedList } from "@/lib/types";

type Props = {
  list: SavedList;
  onRemoveItem?: (listId: string, placeId: string) => Promise<void>;
};

export default function SavedListCard({ list, onRemoveItem }: Props) {
  const previewItems = list.items.slice(0, 3);

  return (
    <article className="card p-4">
      <div className="mb-3 flex items-center justify-between gap-2">
        <h3 className="font-display text-lg font-semibold text-slate-900">{list.name}</h3>
        <span className="text-xs text-slate-500">{list.items.length} saved</span>
      </div>

      <div className="space-y-2">
        {previewItems.map((item) => (
          <div key={`${item.list_id}-${item.place_id}`} className="flex items-center justify-between gap-3">
            <div>
              <p className="text-sm font-medium text-slate-800">{item.place?.name || item.place_id}</p>
              <p className="text-xs text-slate-500">Saved {new Date(item.created_at).toLocaleDateString()}</p>
            </div>
            {onRemoveItem ? (
              <button
                onClick={() => onRemoveItem(list.id, item.place_id)}
                className="btn-secondary px-2 py-1 text-xs"
              >
                Remove
              </button>
            ) : null}
          </div>
        ))}
      </div>

      {list.items.length > previewItems.length ? (
        <p className="mt-3 text-xs text-slate-500">+{list.items.length - previewItems.length} more saved places</p>
      ) : null}

      <div className="mt-4 flex items-center justify-between gap-3">
        <p className="text-xs text-slate-500">Created {new Date(list.created_at).toLocaleDateString()}</p>
        <Link href={`/saved-lists/${list.id}`} className="btn-secondary px-3 py-2 text-sm">
          View list
        </Link>
      </div>
    </article>
  );
}
