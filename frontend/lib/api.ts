import type {
  AuthenticitySummary,
  AuthTokenResponse,
  Place,
  PlaceCreatePayload,
  PlaceDetail,
  PlaceSearchResponse,
  Promotion,
  PromotionCreatePayload,
  RecommendationRequest,
  RecommendationResponse,
  Review,
  ReviewPayload,
  ReviewUpdatePayload,
  SavedList,
  User,
  UserReview
} from "@/lib/types";

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init.headers || {})
    },
    cache: "no-store"
  });

  const text = await response.text();
  let body: unknown = null;
  if (text) {
    try {
      body = JSON.parse(text);
    } catch {
      body = text;
    }
  }

  if (!response.ok) {
    const detail = typeof body === "object" && body && "detail" in body ? (body as { detail: string }).detail : null;
    throw new Error(detail || `Request failed (${response.status})`);
  }

  return body as T;
}

function authHeaders(token: string) {
  return { Authorization: `Bearer ${token}` };
}

export function register(payload: {
  full_name: string;
  email: string;
  password: string;
  role: string;
}) {
  return request<AuthTokenResponse>("/auth/register", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function login(payload: { email: string; password: string }) {
  return request<AuthTokenResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function getMe(token: string) {
  return request<User>("/auth/me", {
    headers: authHeaders(token)
  });
}

export function getUserProfile(token: string) {
  return request<User>("/users/me", {
    headers: authHeaders(token)
  });
}

export function updateUserProfile(token: string, payload: { full_name?: string; password?: string }) {
  return request<User>("/users/me", {
    method: "PUT",
    headers: authHeaders(token),
    body: JSON.stringify(payload)
  });
}

export function getMyReviews(token: string) {
  return request<UserReview[]>("/users/me/reviews", {
    headers: authHeaders(token)
  });
}

export function fetchRecommendations(payload: RecommendationRequest) {
  return request<RecommendationResponse>("/recommendations", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function searchPlaces(params: {
  query?: string;
  lat?: number;
  lng?: number;
  radius_km?: number;
  price_level?: number;
  tag?: string;
  open_now?: boolean;
}) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") return;
    search.set(key, String(value));
  });
  return request<PlaceSearchResponse>(`/places/search?${search.toString()}`);
}

export function getPlace(placeId: string) {
  return request<PlaceDetail>(`/places/${placeId}`);
}

export function createPlace(token: string, payload: PlaceCreatePayload) {
  return request<Place>("/places", {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify(payload)
  });
}

export function getPlaceReviews(placeId: string) {
  return request<Review[]>(`/places/${placeId}/reviews`);
}

export function createReview(token: string, payload: ReviewPayload) {
  return request<Review>("/reviews", {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify(payload)
  });
}

export function updateReview(token: string, reviewId: string, payload: ReviewUpdatePayload) {
  return request<Review>(`/reviews/${reviewId}`, {
    method: "PUT",
    headers: authHeaders(token),
    body: JSON.stringify(payload)
  });
}

export function voteAuthenticity(token: string, place_id: string, label: "authentic" | "touristy") {
  return request<AuthenticitySummary>("/authenticity/vote", {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ place_id, label })
  });
}

export function getAuthenticity(placeId: string) {
  return request<AuthenticitySummary>(`/places/${placeId}/authenticity`);
}

export function getPlacePromotions(placeId: string) {
  return request<Promotion[]>(`/places/${placeId}/promotions`);
}

export function createSavedList(token: string, name: string) {
  return request<SavedList>("/saved-lists", {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ name })
  });
}

export function getSavedLists(token: string) {
  return request<SavedList[]>("/saved-lists", {
    headers: authHeaders(token)
  });
}

export function addSavedListItem(token: string, listId: string, placeId: string) {
  return request<SavedList>(`/saved-lists/${listId}/items`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ place_id: placeId })
  });
}

export function removeSavedListItem(token: string, listId: string, placeId: string) {
  return request<SavedList>(`/saved-lists/${listId}/items/${placeId}`, {
    method: "DELETE",
    headers: authHeaders(token)
  });
}

export function getSellerPlaces(token: string) {
  return request<Place[]>("/seller/places", {
    headers: authHeaders(token)
  });
}

export function getSellerPromotions(token: string) {
  return request<Promotion[]>("/seller/promotions", {
    headers: authHeaders(token)
  });
}

export function createPromotion(token: string, payload: PromotionCreatePayload) {
  return request<Promotion>("/promotions", {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify(payload)
  });
}

export function getAdminUsers(token: string) {
  return request<User[]>("/admin/users", {
    headers: authHeaders(token)
  });
}

export function getAdminPlaces(token: string) {
  return request<Place[]>("/admin/places", {
    headers: authHeaders(token)
  });
}
