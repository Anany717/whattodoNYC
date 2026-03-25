"use client";

import { useMemo, useState } from "react";

import { getPlaceImageUrl } from "@/lib/placeImages";

type Props = {
  place: {
    name: string;
    place_type?: string;
    neighborhood?: string | null;
    image_url?: string | null;
    google_photo_reference?: string | null;
  };
  aspectClassName?: string;
  className?: string;
};

const STEP_BACKDROPS: Record<string, string> = {
  restaurant: "from-amber-100 via-orange-50 to-rose-100",
  event: "from-sky-100 via-cyan-50 to-indigo-100",
  activity: "from-emerald-100 via-teal-50 to-lime-100",
};

export default function PlaceImage({
  place,
  aspectClassName = "aspect-[4/3]",
  className = "",
}: Props) {
  const [failed, setFailed] = useState(false);
  const imageUrl = useMemo(() => getPlaceImageUrl(place), [place]);
  const background =
    STEP_BACKDROPS[(place.place_type || "").toLowerCase()] || "from-brand-100 via-white to-amber-100";

  if (!imageUrl || failed) {
    return (
      <div
        className={`${aspectClassName} overflow-hidden rounded-[24px] bg-gradient-to-br ${background} ${className}`}
      >
        <div className="flex h-full flex-col justify-between p-4">
          <span className="rounded-full bg-white/75 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-700 backdrop-blur">
            {(place.place_type || "place").replaceAll("_", " ")}
          </span>
          <div>
            <p className="line-clamp-2 font-display text-xl font-semibold text-slate-900">
              {place.name}
            </p>
            {place.neighborhood ? (
              <p className="mt-1 text-sm text-slate-600">{place.neighborhood}</p>
            ) : null}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`${aspectClassName} overflow-hidden rounded-[24px] bg-slate-100 ${className}`}>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={imageUrl}
        alt={place.name}
        className="h-full w-full object-cover"
        loading="lazy"
        onError={() => setFailed(true)}
      />
    </div>
  );
}
