type PlaceImageLike = {
  name: string;
  place_type?: string | null;
  neighborhood?: string | null;
  image_url?: string | null;
  google_photo_reference?: string | null;
};

const GOOGLE_MAPS_KEY = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;

const PLACE_IMAGE_STYLES: Record<
  string,
  {
    start: string;
    end: string;
    accent: string;
    label: string;
  }
> = {
  restaurant: {
    start: "#fef3c7",
    end: "#fed7aa",
    accent: "#c2410c",
    label: "Restaurant",
  },
  event: {
    start: "#dbeafe",
    end: "#c7d2fe",
    accent: "#3730a3",
    label: "Event",
  },
  activity: {
    start: "#d1fae5",
    end: "#ccfbf1",
    accent: "#0f766e",
    label: "Activity",
  },
};

function escapeXml(value: string) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&apos;");
}

function fallbackStyle(placeType?: string | null) {
  return PLACE_IMAGE_STYLES[(placeType || "").toLowerCase()] || {
    start: "#e0f2fe",
    end: "#fef3c7",
    accent: "#0f766e",
    label: "Place",
  };
}

function buildGooglePhotoUrl(photoReference: string, maxWidth: number) {
  if (!GOOGLE_MAPS_KEY) {
    return null;
  }

  const params = new URLSearchParams({
    maxwidth: String(maxWidth),
    photoreference: photoReference,
    key: GOOGLE_MAPS_KEY,
  });
  return `https://maps.googleapis.com/maps/api/place/photo?${params.toString()}`;
}

export function getFallbackPlaceImageUrl(place: Pick<PlaceImageLike, "name" | "place_type" | "neighborhood">) {
  const style = fallbackStyle(place.place_type);
  const title = escapeXml(place.name);
  const subtitle = escapeXml(place.neighborhood || "NYC");
  const label = escapeXml(style.label);
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 900" role="img" aria-label="${title}">
      <defs>
        <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="${style.start}"/>
          <stop offset="100%" stop-color="${style.end}"/>
        </linearGradient>
      </defs>
      <rect width="1200" height="900" rx="48" fill="url(#bg)"/>
      <circle cx="960" cy="180" r="140" fill="rgba(255,255,255,0.3)"/>
      <circle cx="210" cy="720" r="180" fill="rgba(255,255,255,0.2)"/>
      <rect x="72" y="72" width="220" height="54" rx="27" fill="rgba(255,255,255,0.85)"/>
      <text x="182" y="107" text-anchor="middle" font-family="Arial, sans-serif" font-size="26" font-weight="700" letter-spacing="3" fill="${style.accent}">
        ${label.toUpperCase()}
      </text>
      <text x="72" y="700" font-family="Arial, sans-serif" font-size="74" font-weight="700" fill="#0f172a">
        ${title}
      </text>
      <text x="72" y="760" font-family="Arial, sans-serif" font-size="34" fill="#334155">
        ${subtitle}
      </text>
    </svg>
  `;
  return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`;
}

export function getPlaceImageUrl(place: PlaceImageLike, maxWidth = 800): string {
  if (place.image_url) {
    return place.image_url;
  }

  if (place.google_photo_reference) {
    const googlePhotoUrl = buildGooglePhotoUrl(place.google_photo_reference, maxWidth);
    if (googlePhotoUrl) {
      return googlePhotoUrl;
    }
  }

  return getFallbackPlaceImageUrl(place);
}
