export type UserRole = "customer" | "reviewer" | "seller" | "admin";
export type PlaceType = "restaurant" | "event" | "activity";
export type SearchSortBy =
  | "relevance"
  | "price_asc"
  | "price_desc"
  | "rating_desc"
  | "distance_asc"
  | "authenticity_desc";

export type User = {
  id: string;
  full_name: string;
  email: string;
  role: UserRole;
  created_at: string;
};

export type AuthTokenResponse = {
  access_token: string;
  token_type: "bearer";
};

export type Place = {
  id: string;
  google_place_id: string | null;
  source: "google" | "internal";
  place_type: PlaceType;
  name: string;
  formatted_address: string | null;
  neighborhood: string | null;
  lat: number;
  lng: number;
  price_level: number | null;
  phone: string | null;
  website: string | null;
  managed_by_user_id: string | null;
};

export type PlaceSearchItem = Place & {
  distance_km: number | null;
  average_rating: number | null;
  authenticity_score: number;
  review_count: number;
  relevance_score: number;
  match_summary: string | null;
};

export type PlaceDetail = {
  id: string;
  name: string;
  formatted_address: string | null;
  neighborhood: string | null;
  place_type: PlaceType;
  price_level: number | null;
  phone: string | null;
  website: string | null;
  lat: number;
  lng: number;
  tags: string[];
  average_rating: number | null;
  authenticity_score: number;
  review_count: number;
};

export type Review = {
  id: string;
  user_id: string;
  place_id: string;
  rating_overall: number;
  rating_value: number | null;
  rating_vibe: number | null;
  rating_groupfit: number | null;
  comment: string | null;
  created_at: string;
};

export type UserReview = Review & {
  place_name: string;
};

export type ReviewPayload = {
  place_id: string;
  rating_overall: number;
  rating_value?: number;
  rating_vibe?: number;
  rating_groupfit?: number;
  comment?: string;
};

export type ReviewUpdatePayload = {
  rating_overall: number;
  rating_value?: number;
  rating_vibe?: number;
  rating_groupfit?: number;
  comment?: string;
};

export type AuthenticitySummary = {
  place_id: string;
  authentic_count: number;
  touristy_count: number;
  score: number;
};

export type Promotion = {
  id: string;
  place_id: string;
  seller_user_id: string;
  title: string;
  description: string | null;
  boost_factor: number;
  start_at: string;
  end_at: string;
};

export type PromotionCreatePayload = {
  place_id: string;
  title: string;
  description?: string;
  boost_factor: number;
  start_at: string;
  end_at: string;
};

export type PlaceCreatePayload = {
  place_type: PlaceType;
  name: string;
  formatted_address?: string;
  neighborhood?: string;
  lat: number;
  lng: number;
  price_level?: number | null;
  phone?: string;
  website?: string;
};

export type SavedListItem = {
  list_id: string;
  place_id: string;
  created_at: string;
  place?: Place;
};

export type SavedList = {
  id: string;
  user_id: string;
  name: string;
  created_at: string;
  items: SavedListItem[];
};

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

export type PlaceSearchResponse = {
  items: PlaceSearchItem[];
  sort_by: SearchSortBy;
  google_results_used: boolean;
};
