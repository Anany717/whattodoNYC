import enum
import uuid
from datetime import datetime, time, timezone

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
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    reviews = relationship("Review", back_populates="user", cascade="all, delete-orphan")
    authenticity_votes = relationship("AuthenticityVote", back_populates="user", cascade="all, delete-orphan")
    saved_lists = relationship("SavedList", back_populates="user", cascade="all, delete-orphan")


class Place(Base):
    __tablename__ = "places"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    google_place_id: Mapped[str | None] = mapped_column(Text, unique=True, nullable=True)
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
    formatted_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    neighborhood: Mapped[str | None] = mapped_column(Text, nullable=True)
    lat: Mapped[float] = mapped_column(nullable=False)
    lng: Mapped[float] = mapped_column(nullable=False)
    price_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    phone: Mapped[str | None] = mapped_column(Text, nullable=True)
    website: Mapped[str | None] = mapped_column(Text, nullable=True)
    managed_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint("price_level IS NULL OR (price_level >= 1 AND price_level <= 4)", name="price_level_range"),
    )

    hours = relationship("PlaceHour", back_populates="place", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="place", cascade="all, delete-orphan")
    authenticity_votes = relationship("AuthenticityVote", back_populates="place", cascade="all, delete-orphan")
    tags = relationship("PlaceTag", back_populates="place", cascade="all, delete-orphan")
    promotions = relationship("Promotion", back_populates="place", cascade="all, delete-orphan")


class PlaceHour(Base):
    __tablename__ = "place_hours"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    place_id: Mapped[str] = mapped_column(String(36), ForeignKey("places.id"), nullable=False)
    day_of_week: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    open_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    close_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    is_closed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (UniqueConstraint("place_id", "day_of_week", name="uq_place_day"),)

    place = relationship("Place", back_populates="hours")


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    place_id: Mapped[str] = mapped_column(String(36), ForeignKey("places.id"), nullable=False)
    rating_overall: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    rating_value: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    rating_vibe: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    rating_groupfit: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "place_id", name="uq_review_user_place"),
        CheckConstraint("rating_overall BETWEEN 1 AND 5", name="rating_overall_range"),
        CheckConstraint("rating_value IS NULL OR rating_value BETWEEN 1 AND 5", name="rating_value_range"),
        CheckConstraint("rating_vibe IS NULL OR rating_vibe BETWEEN 1 AND 5", name="rating_vibe_range"),
        CheckConstraint("rating_groupfit IS NULL OR rating_groupfit BETWEEN 1 AND 5", name="rating_groupfit_range"),
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
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    __table_args__ = (UniqueConstraint("user_id", "place_id", name="uq_auth_vote_user_place"),)

    user = relationship("User", back_populates="authenticity_votes")
    place = relationship("Place", back_populates="authenticity_votes")


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
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    boost_factor: Mapped[float] = mapped_column(Numeric(3, 2), nullable=False)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint("boost_factor >= 1.00 AND boost_factor <= 3.00", name="boost_factor_range"),
    )

    place = relationship("Place", back_populates="promotions")


class WeatherSnapshot(Base):
    __tablename__ = "weather_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lat_bucket: Mapped[float] = mapped_column(nullable=False)
    lng_bucket: Mapped[float] = mapped_column(nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    data_json: Mapped[dict] = mapped_column(JSON, nullable=False)


class SavedList(Base):
    __tablename__ = "saved_lists"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_saved_list_user_name"),)

    user = relationship("User", back_populates="saved_lists")
    items = relationship("SavedListItem", back_populates="saved_list", cascade="all, delete-orphan")


class SavedListItem(Base):
    __tablename__ = "saved_list_items"

    list_id: Mapped[str] = mapped_column(String(36), ForeignKey("saved_lists.id"), primary_key=True)
    place_id: Mapped[str] = mapped_column(String(36), ForeignKey("places.id"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    saved_list = relationship("SavedList", back_populates="items")
