export type UserRole = "customer" | "reviewer" | "seller" | "admin";
export type PlaceType = "restaurant" | "event" | "activity";
export type SearchSortBy =
  | "relevance"
  | "price_asc"
  | "price_desc"
  | "rating_desc"
  | "distance_asc"
  | "authenticity_desc";
export type FriendshipStatus = "pending" | "accepted" | "declined" | "blocked";
export type PlanStatus = "draft" | "active" | "finalized" | "archived";
export type PlanVisibility = "private" | "shared";
export type PlanMemberRole = "host" | "collaborator";
export type PlanVoteValue = "yes" | "no" | "maybe";

export type UserSummary = {
  id: string;
  full_name: string;
  email: string;
  role: UserRole;
};

export type User = UserSummary & {
  created_at: string;
};

export type AuthTokenResponse = {
  access_token: string;
  token_type: "bearer";
};

export type Place = {
  id: string;
  google_place_id: string | null;
  google_primary_type: string | null;
  google_rating: number | null;
  google_user_ratings_total: number | null;
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
  external_last_synced_at: string | null;
  is_seed_data: boolean;
  is_cached_from_external: boolean;
  managed_by_user_id: string | null;
};

export type PlaceSearchItem = Place & {
  distance_km: number | null;
  average_rating: number | null;
  authenticity_score: number;
  review_count: number;
  relevance_score: number;
  match_summary: string | null;
  search_source: "live_google" | "cached_google" | "internal";
  search_source_label: string | null;
  is_live_result: boolean;
};

export type PlaceDetail = {
  id: string;
  google_place_id: string | null;
  google_primary_type: string | null;
  google_rating: number | null;
  google_user_ratings_total: number | null;
  name: string;
  formatted_address: string | null;
  neighborhood: string | null;
  place_type: PlaceType;
  price_level: number | null;
  phone: string | null;
  website: string | null;
  lat: number;
  lng: number;
  external_last_synced_at: string | null;
  is_seed_data: boolean;
  is_cached_from_external: boolean;
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

export type Friendship = {
  id: string;
  requester_user_id: string;
  addressee_user_id: string;
  status: FriendshipStatus;
  created_at: string;
  updated_at: string;
  requester: UserSummary;
  addressee: UserSummary;
};

export type FriendsListEntry = {
  friendship_id: string;
  friend: UserSummary;
  created_at: string;
};

export type FriendRequestsResponse = {
  incoming: Friendship[];
  outgoing: Friendship[];
};

export type VoteSummary = {
  yes_count: number;
  no_count: number;
  maybe_count: number;
  total_votes: number;
  current_user_vote: PlanVoteValue | null;
};

export type PlanItemVote = {
  id: string;
  plan_item_id: string;
  user_id: string;
  vote: PlanVoteValue;
  created_at: string;
  updated_at: string;
  user: UserSummary;
};

export type PlanMember = {
  plan_id: string;
  user_id: string;
  role: PlanMemberRole;
  joined_at: string;
  user: UserSummary;
};

export type PlanItem = {
  id: string;
  plan_id: string;
  place_id: string;
  added_by_user_id: string;
  notes: string | null;
  created_at: string;
  place: Place;
  added_by_user: UserSummary;
  votes: PlanItemVote[];
  vote_summary: VoteSummary;
};

export type Plan = {
  id: string;
  host_user_id: string;
  title: string;
  description: string | null;
  status: PlanStatus;
  visibility: PlanVisibility;
  final_place_id: string | null;
  created_at: string;
  updated_at: string;
  host: UserSummary;
  members: PlanMember[];
  items: PlanItem[];
  final_choice: PlanItem | null;
  leading_choice: PlanItem | null;
};

export type PlanSummary = {
  id: string;
  host_user_id: string;
  title: string;
  description: string | null;
  status: PlanStatus;
  visibility: PlanVisibility;
  final_place_id: string | null;
  created_at: string;
  updated_at: string;
  host: UserSummary;
  member_count: number;
  item_count: number;
  final_choice: PlanItem | null;
  leading_choice: PlanItem | null;
};

export type PlanVotesSummaryResponse = {
  plan_id: string;
  items: PlanItem[];
  leading_choice: PlanItem | null;
};

export type FinalChoiceResponse = {
  plan_id: string;
  status: PlanStatus;
  final_choice: PlanItem | null;
  leading_choice: PlanItem | null;
};

export type PlanCreatePayload = {
  title: string;
  description?: string;
  visibility?: PlanVisibility;
  invited_user_ids?: string[];
};

export type PlanUpdatePayload = {
  title?: string;
  description?: string;
  status?: PlanStatus;
  visibility?: PlanVisibility;
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
  formatted_address: string | null;
  source: "google" | "internal";
  google_rating: number | null;
  google_user_ratings_total: number | null;
  is_cached_from_external: boolean;
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
  live_search_attempted: boolean;
  live_search_succeeded: boolean;
  live_result_count: number;
  status_message: string | null;
};
