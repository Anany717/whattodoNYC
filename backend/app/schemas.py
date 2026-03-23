from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models import AuthenticityLabel, PlaceSource, PlaceType, UserRole


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserBase(BaseModel):
    full_name: str
    email: EmailStr
    role: UserRole


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(UserBase):
    id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    full_name: str | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)


class PlaceCreate(BaseModel):
    place_type: PlaceType
    name: str
    formatted_address: str | None = None
    neighborhood: str | None = None
    lat: float
    lng: float
    price_level: int | None = Field(default=None, ge=1, le=4)
    phone: str | None = None
    website: str | None = None


class PlaceOut(BaseModel):
    id: str
    google_place_id: str | None
    google_primary_type: str | None = None
    google_rating: float | None = None
    google_user_ratings_total: int | None = None
    source: PlaceSource
    place_type: PlaceType
    name: str
    formatted_address: str | None
    neighborhood: str | None
    lat: float
    lng: float
    price_level: int | None
    phone: str | None
    website: str | None
    external_last_synced_at: datetime | None = None
    is_seed_data: bool = False
    is_cached_from_external: bool = False
    managed_by_user_id: str | None

    model_config = ConfigDict(from_attributes=True)


class PlaceDetailOut(BaseModel):
    id: str
    google_place_id: str | None = None
    google_primary_type: str | None = None
    google_rating: float | None = None
    google_user_ratings_total: int | None = None
    name: str
    formatted_address: str | None
    neighborhood: str | None
    place_type: PlaceType
    price_level: int | None
    phone: str | None
    website: str | None
    lat: float
    lng: float
    external_last_synced_at: datetime | None = None
    is_seed_data: bool = False
    is_cached_from_external: bool = False
    tags: list[str] = Field(default_factory=list)
    average_rating: float | None = None
    authenticity_score: float = 0.5
    review_count: int = 0


SearchSortBy = Literal[
    "relevance",
    "price_asc",
    "price_desc",
    "rating_desc",
    "distance_asc",
    "authenticity_desc",
]


class PlaceSearchItemOut(PlaceOut):
    distance_km: float | None = None
    average_rating: float | None = None
    authenticity_score: float = 0.5
    review_count: int = 0
    relevance_score: float = 0.0
    match_summary: str | None = None
    search_source: Literal["live_google", "cached_google", "internal"] = "internal"
    search_source_label: str | None = None
    is_live_result: bool = False


class PlaceSearchOut(BaseModel):
    items: list[PlaceSearchItemOut]
    sort_by: SearchSortBy = "relevance"
    google_results_used: bool = False
    live_search_attempted: bool = False
    live_search_succeeded: bool = False
    live_result_count: int = 0
    status_message: str | None = None


class ReviewCreate(BaseModel):
    place_id: str
    rating_overall: int = Field(ge=1, le=5)
    rating_value: int | None = Field(default=None, ge=1, le=5)
    rating_vibe: int | None = Field(default=None, ge=1, le=5)
    rating_groupfit: int | None = Field(default=None, ge=1, le=5)
    comment: str | None = None


class ReviewUpdate(BaseModel):
    rating_overall: int = Field(ge=1, le=5)
    rating_value: int | None = Field(default=None, ge=1, le=5)
    rating_vibe: int | None = Field(default=None, ge=1, le=5)
    rating_groupfit: int | None = Field(default=None, ge=1, le=5)
    comment: str | None = None


class ReviewOut(BaseModel):
    id: str
    user_id: str
    place_id: str
    rating_overall: int
    rating_value: int | None
    rating_vibe: int | None
    rating_groupfit: int | None
    comment: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserReviewOut(ReviewOut):
    place_name: str


class AuthenticityVoteIn(BaseModel):
    place_id: str
    label: AuthenticityLabel


class AuthenticityOut(BaseModel):
    place_id: str
    authentic_count: int
    touristy_count: int
    score: float


class PromotionCreate(BaseModel):
    place_id: str
    title: str
    description: str | None = None
    boost_factor: float = Field(ge=1.0, le=3.0)
    start_at: datetime
    end_at: datetime

    @field_validator("end_at")
    @classmethod
    def validate_window(cls, value: datetime, info):
        start_at = info.data.get("start_at")
        if start_at and value <= start_at:
            raise ValueError("end_at must be after start_at")
        return value


class PromotionOut(BaseModel):
    id: str
    place_id: str
    seller_user_id: str
    title: str
    description: str | None
    boost_factor: float
    start_at: datetime
    end_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SavedListCreate(BaseModel):
    name: str


class SavedListItemCreate(BaseModel):
    place_id: str


class SavedListItemOut(BaseModel):
    list_id: str
    place_id: str
    created_at: datetime
    place: PlaceOut | None = None

    model_config = ConfigDict(from_attributes=True)


class SavedListOut(BaseModel):
    id: str
    user_id: str
    name: str
    created_at: datetime
    items: list[SavedListItemOut] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class RecommendationRequest(BaseModel):
    keywords: str
    budget: int = Field(ge=1, le=4)
    group_size: int = Field(ge=1)
    preference: Literal["indoor", "outdoor", "either"]
    lat: float
    lng: float
    radius_km: float = Field(gt=0)


class RecommendationItem(BaseModel):
    place_id: str
    name: str
    price_level: int | None
    formatted_address: str | None = None
    source: PlaceSource
    google_rating: float | None = None
    google_user_ratings_total: int | None = None
    is_cached_from_external: bool = False
    lat: float
    lng: float
    distance_km: float
    score: float
    why: str


class RecommendationResponse(BaseModel):
    results: list[RecommendationItem]
