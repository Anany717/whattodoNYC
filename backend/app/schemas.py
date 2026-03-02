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
    managed_by_user_id: str | None

    model_config = ConfigDict(from_attributes=True)


class PlaceSearchOut(BaseModel):
    items: list[PlaceOut]


class ReviewCreate(BaseModel):
    place_id: str
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
    lat: float
    lng: float
    distance_km: float
    score: float
    why: str


class RecommendationResponse(BaseModel):
    results: list[RecommendationItem]
