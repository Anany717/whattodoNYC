from __future__ import annotations

import enum
import uuid
from datetime import datetime, time, timezone
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

# SQLAlchemy on our Python 3.9 runtime still needs `Optional[...]` here.
# ruff: noqa: UP007


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UserRole(str, enum.Enum):
    customer = "customer"
    reviewer = "reviewer"
    seller = "seller"
    admin = "admin"


class PlaceSource(str, enum.Enum):
    google = "google"
    internal = "internal"


class PlaceType(str, enum.Enum):
    restaurant = "restaurant"
    event = "event"
    activity = "activity"


class AuthenticityLabel(str, enum.Enum):
    authentic = "authentic"
    touristy = "touristy"


class FriendshipStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    declined = "declined"
    blocked = "blocked"


class PlanStatus(str, enum.Enum):
    draft = "draft"
    active = "active"
    finalized = "finalized"
    archived = "archived"


class PlanVisibility(str, enum.Enum):
    private = "private"
    shared = "shared"


class PlanMemberRole(str, enum.Enum):
    host = "host"
    collaborator = "collaborator"


class PlanVoteValue(str, enum.Enum):
    yes = "yes"
    no = "no"
    maybe = "maybe"


enum_values = lambda enum_cls: [item.value for item in enum_cls]  # noqa: E731


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False, values_callable=enum_values),
        nullable=False,
        default=UserRole.customer,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )

    reviews = relationship("Review", back_populates="user", cascade="all, delete-orphan")
    authenticity_votes = relationship(
        "AuthenticityVote",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    saved_lists = relationship("SavedList", back_populates="user", cascade="all, delete-orphan")
    sent_friend_requests = relationship(
        "Friendship",
        foreign_keys="Friendship.requester_user_id",
        back_populates="requester",
        cascade="all, delete-orphan",
    )
    received_friend_requests = relationship(
        "Friendship",
        foreign_keys="Friendship.addressee_user_id",
        back_populates="addressee",
        cascade="all, delete-orphan",
    )
    hosted_plans = relationship(
        "Plan",
        foreign_keys="Plan.host_user_id",
        back_populates="host",
        cascade="all, delete-orphan",
    )
    plan_memberships = relationship(
        "PlanMember",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    added_plan_items = relationship(
        "PlanItem",
        foreign_keys="PlanItem.added_by_user_id",
        back_populates="added_by_user",
    )
    plan_item_votes = relationship(
        "PlanItemVote",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Place(Base):
    __tablename__ = "places"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    google_place_id: Mapped[Optional[str]] = mapped_column(Text, unique=True, nullable=True)
    google_primary_type: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    google_rating: Mapped[Optional[float]] = mapped_column(nullable=True)
    google_user_ratings_total: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source: Mapped[PlaceSource] = mapped_column(
        Enum(PlaceSource, native_enum=False, values_callable=enum_values),
        nullable=False,
        default=PlaceSource.internal,
    )
    place_type: Mapped[PlaceType] = mapped_column(
        Enum(PlaceType, native_enum=False, values_callable=enum_values),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    formatted_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    neighborhood: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    lat: Mapped[float] = mapped_column(nullable=False)
    lng: Mapped[float] = mapped_column(nullable=False)
    price_level: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    website: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    external_last_synced_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    external_raw_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_seed_data: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_cached_from_external: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    managed_by_user_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "price_level IS NULL OR (price_level >= 1 AND price_level <= 4)",
            name="price_level_range",
        ),
    )

    hours = relationship("PlaceHour", back_populates="place", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="place", cascade="all, delete-orphan")
    authenticity_votes = relationship(
        "AuthenticityVote",
        back_populates="place",
        cascade="all, delete-orphan",
    )
    tags = relationship("PlaceTag", back_populates="place", cascade="all, delete-orphan")
    promotions = relationship("Promotion", back_populates="place", cascade="all, delete-orphan")
    saved_list_items = relationship(
        "SavedListItem",
        back_populates="place",
        cascade="all, delete-orphan",
    )
    plan_items = relationship("PlanItem", back_populates="place", cascade="all, delete-orphan")
    finalized_in_plans = relationship(
        "Plan",
        foreign_keys="Plan.final_place_id",
        back_populates="final_place",
    )


class PlaceHour(Base):
    __tablename__ = "place_hours"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    place_id: Mapped[str] = mapped_column(String(36), ForeignKey("places.id"), nullable=False)
    day_of_week: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    open_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    close_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    is_closed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (UniqueConstraint("place_id", "day_of_week", name="uq_place_day"),)

    place = relationship("Place", back_populates="hours")


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    place_id: Mapped[str] = mapped_column(String(36), ForeignKey("places.id"), nullable=False)
    rating_overall: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    rating_value: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    rating_vibe: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    rating_groupfit: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("user_id", "place_id", name="uq_review_user_place"),
        CheckConstraint("rating_overall BETWEEN 1 AND 5", name="rating_overall_range"),
        CheckConstraint(
            "rating_value IS NULL OR rating_value BETWEEN 1 AND 5",
            name="rating_value_range",
        ),
        CheckConstraint(
            "rating_vibe IS NULL OR rating_vibe BETWEEN 1 AND 5",
            name="rating_vibe_range",
        ),
        CheckConstraint(
            "rating_groupfit IS NULL OR rating_groupfit BETWEEN 1 AND 5",
            name="rating_groupfit_range",
        ),
    )

    user = relationship("User", back_populates="reviews")
    place = relationship("Place", back_populates="reviews")


class AuthenticityVote(Base):
    __tablename__ = "authenticity_votes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    place_id: Mapped[str] = mapped_column(String(36), ForeignKey("places.id"), nullable=False)
    label: Mapped[AuthenticityLabel] = mapped_column(
        Enum(AuthenticityLabel, native_enum=False, values_callable=enum_values),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )

    __table_args__ = (UniqueConstraint("user_id", "place_id", name="uq_auth_vote_user_place"),)

    user = relationship("User", back_populates="authenticity_votes")
    place = relationship("Place", back_populates="authenticity_votes")


class Friendship(Base):
    __tablename__ = "friendships"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    requester_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    addressee_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    status: Mapped[FriendshipStatus] = mapped_column(
        Enum(FriendshipStatus, native_enum=False, values_callable=enum_values),
        nullable=False,
        default=FriendshipStatus.pending,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("requester_user_id", "addressee_user_id", name="uq_friendship_direction"),
        CheckConstraint("requester_user_id <> addressee_user_id", name="friendship_not_self"),
    )

    requester = relationship(
        "User",
        foreign_keys=[requester_user_id],
        back_populates="sent_friend_requests",
    )
    addressee = relationship(
        "User",
        foreign_keys=[addressee_user_id],
        back_populates="received_friend_requests",
    )


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(Text, unique=True, nullable=False)

    place_tags = relationship("PlaceTag", back_populates="tag", cascade="all, delete-orphan")


class PlaceTag(Base):
    __tablename__ = "place_tags"

    place_id: Mapped[str] = mapped_column(String(36), ForeignKey("places.id"), primary_key=True)
    tag_id: Mapped[str] = mapped_column(String(36), ForeignKey("tags.id"), primary_key=True)

    place = relationship("Place", back_populates="tags")
    tag = relationship("Tag", back_populates="place_tags")


class Promotion(Base):
    __tablename__ = "promotions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    place_id: Mapped[str] = mapped_column(String(36), ForeignKey("places.id"), nullable=False)
    seller_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    boost_factor: Mapped[float] = mapped_column(Numeric(3, 2), nullable=False)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint("boost_factor >= 1.00 AND boost_factor <= 3.00", name="boost_factor_range"),
    )

    place = relationship("Place", back_populates="promotions")


class WeatherSnapshot(Base):
    __tablename__ = "weather_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lat_bucket: Mapped[float] = mapped_column(nullable=False)
    lng_bucket: Mapped[float] = mapped_column(nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )
    data_json: Mapped[dict] = mapped_column(JSON, nullable=False)


class SavedList(Base):
    __tablename__ = "saved_lists"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )

    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_saved_list_user_name"),)

    user = relationship("User", back_populates="saved_lists")
    items = relationship("SavedListItem", back_populates="saved_list", cascade="all, delete-orphan")


class SavedListItem(Base):
    __tablename__ = "saved_list_items"

    list_id: Mapped[str] = mapped_column(String(36), ForeignKey("saved_lists.id"), primary_key=True)
    place_id: Mapped[str] = mapped_column(String(36), ForeignKey("places.id"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )

    saved_list = relationship("SavedList", back_populates="items")
    place = relationship("Place", back_populates="saved_list_items")


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    host_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[PlanStatus] = mapped_column(
        Enum(PlanStatus, native_enum=False, values_callable=enum_values),
        nullable=False,
        default=PlanStatus.draft,
    )
    visibility: Mapped[PlanVisibility] = mapped_column(
        Enum(PlanVisibility, native_enum=False, values_callable=enum_values),
        nullable=False,
        default=PlanVisibility.shared,
    )
    final_place_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("places.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )

    host = relationship("User", foreign_keys=[host_user_id], back_populates="hosted_plans")
    final_place = relationship("Place", foreign_keys=[final_place_id], back_populates="finalized_in_plans")
    members = relationship("PlanMember", back_populates="plan", cascade="all, delete-orphan")
    items = relationship("PlanItem", back_populates="plan", cascade="all, delete-orphan")


class PlanMember(Base):
    __tablename__ = "plan_members"

    plan_id: Mapped[str] = mapped_column(String(36), ForeignKey("plans.id"), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), primary_key=True)
    role: Mapped[PlanMemberRole] = mapped_column(
        Enum(PlanMemberRole, native_enum=False, values_callable=enum_values),
        nullable=False,
        default=PlanMemberRole.collaborator,
    )
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    plan = relationship("Plan", back_populates="members")
    user = relationship("User", back_populates="plan_memberships")


class PlanItem(Base):
    __tablename__ = "plan_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    plan_id: Mapped[str] = mapped_column(String(36), ForeignKey("plans.id"), nullable=False)
    place_id: Mapped[str] = mapped_column(String(36), ForeignKey("places.id"), nullable=False)
    added_by_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    __table_args__ = (UniqueConstraint("plan_id", "place_id", name="uq_plan_item_plan_place"),)

    plan = relationship("Plan", back_populates="items")
    place = relationship("Place", back_populates="plan_items")
    added_by_user = relationship("User", foreign_keys=[added_by_user_id], back_populates="added_plan_items")
    votes = relationship("PlanItemVote", back_populates="plan_item", cascade="all, delete-orphan")


class PlanItemVote(Base):
    __tablename__ = "plan_item_votes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    plan_item_id: Mapped[str] = mapped_column(String(36), ForeignKey("plan_items.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    vote: Mapped[PlanVoteValue] = mapped_column(
        Enum(PlanVoteValue, native_enum=False, values_callable=enum_values),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )

    __table_args__ = (UniqueConstraint("plan_item_id", "user_id", name="uq_plan_item_vote_user"),)

    plan_item = relationship("PlanItem", back_populates="votes")
    user = relationship("User", back_populates="plan_item_votes")
