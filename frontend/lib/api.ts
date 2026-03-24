import type {
  AuthenticitySummary,
  AuthTokenResponse,
  FinalChoiceResponse,
  FriendRequestsResponse,
  FriendsListEntry,
  Friendship,
  Place,
  PlaceCreatePayload,
  PlaceDetail,
  PlaceSearchResponse,
  Plan,
  PlanCreatePayload,
  PlanItem,
  PlanSummary,
  PlanUpdatePayload,
  PlanVoteValue,
  PlanVotesSummaryResponse,
  Promotion,
  PromotionCreatePayload,
  RecommendationRequest,
  RecommendationResponse,
  Review,
  ReviewPayload,
  ReviewUpdatePayload,
  SavedList,
  SearchSortBy,
  User,
  UserReview,
  UserSummary,
} from "@/lib/types";

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

function extractErrorMessage(body: unknown): string | null {
  if (!body) return null;

  if (typeof body === "string") {
    const trimmed = body.trim();
    return trimmed || null;
  }

  if (Array.isArray(body)) {
    const parts = body.map(extractErrorMessage).filter((part): part is string => Boolean(part));
    return parts.length ? parts.join("; ") : null;
  }

  if (typeof body === "object") {
    const record = body as Record<string, unknown>;

    if ("detail" in record) {
      return extractErrorMessage(record.detail);
    }

    if (typeof record.message === "string") {
      return record.message;
    }

    if (typeof record.msg === "string") {
      const location = Array.isArray(record.loc)
        ? record.loc
            .filter((item): item is string | number => typeof item === "string" || typeof item === "number")
            .join(".")
        : null;

      return location ? `${location}: ${record.msg}` : record.msg;
    }
  }

  return null;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init.headers || {}),
    },
    cache: "no-store",
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
    const detail = extractErrorMessage(body);
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
    body: JSON.stringify(payload),
  });
}

export function login(payload: { email: string; password: string }) {
  return request<AuthTokenResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getMe(token: string) {
  return request<User>("/auth/me", {
    headers: authHeaders(token),
  });
}

export function getUserProfile(token: string) {
  return request<User>("/users/me", {
    headers: authHeaders(token),
  });
}

export function updateUserProfile(token: string, payload: { full_name?: string; password?: string }) {
  return request<User>("/users/me", {
    method: "PUT",
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  });
}

export function getMyReviews(token: string) {
  return request<UserReview[]>("/users/me/reviews", {
    headers: authHeaders(token),
  });
}

export function getMySavedLists(token: string) {
  return request<SavedList[]>("/users/me/saved-lists", {
    headers: authHeaders(token),
  });
}

export function fetchRecommendations(payload: RecommendationRequest) {
  return request<RecommendationResponse>("/recommendations", {
    method: "POST",
    body: JSON.stringify(payload),
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
  sort_by?: SearchSortBy;
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
    body: JSON.stringify(payload),
  });
}

export function getPlaceReviews(placeId: string) {
  return request<Review[]>(`/places/${placeId}/reviews`);
}

export function createReview(token: string, payload: ReviewPayload) {
  return request<Review>("/reviews", {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  });
}

export function updateReview(token: string, reviewId: string, payload: ReviewUpdatePayload) {
  return request<Review>(`/reviews/${reviewId}`, {
    method: "PUT",
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  });
}

export function deleteReview(token: string, reviewId: string) {
  return request<void>(`/reviews/${reviewId}`, {
    method: "DELETE",
    headers: authHeaders(token),
  });
}

export function voteAuthenticity(token: string, place_id: string, label: "authentic" | "touristy") {
  return request<AuthenticitySummary>("/authenticity/vote", {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ place_id, label }),
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
    body: JSON.stringify({ name }),
  });
}

export function getSavedLists(token: string) {
  return request<SavedList[]>("/saved-lists", {
    headers: authHeaders(token),
  });
}

export function getSavedList(token: string, listId: string) {
  return request<SavedList>(`/saved-lists/${listId}`, {
    headers: authHeaders(token),
  });
}

export function addSavedListItem(token: string, listId: string, placeId: string) {
  return request<SavedList>(`/saved-lists/${listId}/items`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ place_id: placeId }),
  });
}

export function removeSavedListItem(token: string, listId: string, placeId: string) {
  return request<SavedList>(`/saved-lists/${listId}/items/${placeId}`, {
    method: "DELETE",
    headers: authHeaders(token),
  });
}

export function searchUsers(token: string, query: string) {
  const search = new URLSearchParams({ query });
  return request<UserSummary[]>(`/friends/search?${search.toString()}`, {
    headers: authHeaders(token),
  });
}

export function getFriends(token: string) {
  return request<FriendsListEntry[]>("/friends", {
    headers: authHeaders(token),
  });
}

export function getFriendRequests(token: string) {
  return request<FriendRequestsResponse>("/friends/requests", {
    headers: authHeaders(token),
  });
}

export function sendFriendRequest(token: string, addresseeUserId: string) {
  return request<Friendship>("/friends/request", {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ addressee_user_id: addresseeUserId }),
  });
}

export function acceptFriendRequest(token: string, requestId: string) {
  return request<Friendship>(`/friends/request/${requestId}/accept`, {
    method: "POST",
    headers: authHeaders(token),
  });
}

export function declineFriendRequest(token: string, requestId: string) {
  return request<Friendship>(`/friends/request/${requestId}/decline`, {
    method: "POST",
    headers: authHeaders(token),
  });
}

export function removeFriend(token: string, friendId: string) {
  return request<void>(`/friends/${friendId}`, {
    method: "DELETE",
    headers: authHeaders(token),
  });
}

export function getPlans(token: string) {
  return request<PlanSummary[]>("/plans", {
    headers: authHeaders(token),
  });
}

export function createPlan(token: string, payload: PlanCreatePayload) {
  return request<Plan>("/plans", {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  });
}

export function getPlan(token: string, planId: string) {
  return request<Plan>(`/plans/${planId}`, {
    headers: authHeaders(token),
  });
}

export function updatePlan(token: string, planId: string, payload: PlanUpdatePayload) {
  return request<Plan>(`/plans/${planId}`, {
    method: "PUT",
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  });
}

export function deletePlan(token: string, planId: string) {
  return request<void>(`/plans/${planId}`, {
    method: "DELETE",
    headers: authHeaders(token),
  });
}

export function invitePlanMember(token: string, planId: string, userId: string) {
  return request<Plan>(`/plans/${planId}/invite`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ user_id: userId }),
  });
}

export function getPlanMembers(token: string, planId: string) {
  return request<Plan["members"]>(`/plans/${planId}/members`, {
    headers: authHeaders(token),
  });
}

export function removePlanMember(token: string, planId: string, userId: string) {
  return request<void>(`/plans/${planId}/members/${userId}`, {
    method: "DELETE",
    headers: authHeaders(token),
  });
}

export function addPlanItem(token: string, planId: string, payload: { place_id: string; notes?: string }) {
  return request<Plan>(`/plans/${planId}/items`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  });
}

export function getPlanItems(token: string, planId: string) {
  return request<PlanItem[]>(`/plans/${planId}/items`, {
    headers: authHeaders(token),
  });
}

export function deletePlanItem(token: string, planId: string, planItemId: string) {
  return request<void>(`/plans/${planId}/items/${planItemId}`, {
    method: "DELETE",
    headers: authHeaders(token),
  });
}

export function voteOnPlanItem(token: string, planItemId: string, vote: PlanVoteValue) {
  return request<PlanItem>(`/plans/items/${planItemId}/vote`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ vote }),
  });
}

export function updatePlanItemVote(token: string, planItemId: string, vote: PlanVoteValue) {
  return request<PlanItem>(`/plans/items/${planItemId}/vote`, {
    method: "PUT",
    headers: authHeaders(token),
    body: JSON.stringify({ vote }),
  });
}

export function getPlanVotesSummary(token: string, planId: string) {
  return request<PlanVotesSummaryResponse>(`/plans/${planId}/votes-summary`, {
    headers: authHeaders(token),
  });
}

export function finalizePlan(token: string, planId: string, planItemId?: string) {
  return request<FinalChoiceResponse>(`/plans/${planId}/finalize`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify(planItemId ? { plan_item_id: planItemId } : {}),
  });
}

export function getPlanFinalChoice(token: string, planId: string) {
  return request<FinalChoiceResponse>(`/plans/${planId}/final-choice`, {
    headers: authHeaders(token),
  });
}

export function getSellerPlaces(token: string) {
  return request<Place[]>("/seller/places", {
    headers: authHeaders(token),
  });
}

export function getSellerPromotions(token: string) {
  return request<Promotion[]>("/seller/promotions", {
    headers: authHeaders(token),
  });
}

export function createPromotion(token: string, payload: PromotionCreatePayload) {
  return request<Promotion>("/promotions", {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  });
}

export function getAdminUsers(token: string) {
  return request<User[]>("/admin/users", {
    headers: authHeaders(token),
  });
}

export function getAdminPlaces(token: string) {
  return request<Place[]>("/admin/places", {
    headers: authHeaders(token),
  });
}

export function getAdminReviews(token: string) {
  return request<Review[]>("/admin/reviews", {
    headers: authHeaders(token),
  });
}
