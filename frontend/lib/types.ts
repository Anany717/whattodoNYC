export type RecommendationRequest = {
  keywords: string;
  budget: 1 | 2 | 3 | 4;
  group_size: number;
  preference: "indoor" | "outdoor" | "either";
  lat: number;
  lng: number;
  radius_km: number;
};

export type RecommendationItem = {
  place_id: string;
  name: string;
  price_level: number | null;
  lat: number;
  lng: number;
  distance_km: number;
  score: number;
  why: string;
};

export type RecommendationResponse = {
  results: RecommendationItem[];
};
