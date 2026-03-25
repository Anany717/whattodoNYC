type PlaceImageLike = {
  image_url?: string | null;
  google_photo_reference?: string | null;
};

const GOOGLE_MAPS_KEY = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;

export function getPlaceImageUrl(place: PlaceImageLike, maxWidth = 800): string | null {
  if (place.image_url) {
    return place.image_url;
  }

  if (place.google_photo_reference && GOOGLE_MAPS_KEY) {
    const params = new URLSearchParams({
      maxwidth: String(maxWidth),
      photo_reference: place.google_photo_reference,
      key: GOOGLE_MAPS_KEY,
    });
    return `https://maps.googleapis.com/maps/api/place/photo?${params.toString()}`;
  }

  return null;
}
