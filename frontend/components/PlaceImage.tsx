"use client";

import { useEffect, useMemo, useState } from "react";

import { getFallbackPlaceImageUrl, getPlaceImageUrl } from "@/lib/placeImages";

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

export default function PlaceImage({
  place,
  aspectClassName = "aspect-[16/10]",
  className = "",
}: Props) {
  const resolvedImageUrl = useMemo(() => getPlaceImageUrl(place), [place]);
  const fallbackImageUrl = useMemo(() => getFallbackPlaceImageUrl(place), [place]);
  const [src, setSrc] = useState(resolvedImageUrl);

  useEffect(() => {
    setSrc(resolvedImageUrl);
  }, [resolvedImageUrl]);

  return (
    <div className={`${aspectClassName} overflow-hidden rounded-[24px] bg-slate-100 ${className}`}>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={src}
        alt={place.name}
        className="h-full w-full object-cover"
        loading="lazy"
        onError={() => {
          if (src !== fallbackImageUrl) {
            setSrc(fallbackImageUrl);
          }
        }}
      />
    </div>
  );
}
