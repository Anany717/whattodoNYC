from __future__ import annotations

from datetime import datetime, timezone

from app.models import AuthenticityLabel, Place


def tag_names(place: Place) -> list[str]:
    return [place_tag.tag.name.lower() for place_tag in place.tags if place_tag.tag]


def average_rating(place: Place) -> float | None:
    if not place.reviews:
        return None
    return round(sum(review.rating_overall for review in place.reviews) / len(place.reviews), 2)


def review_count(place: Place) -> int:
    return len(place.reviews)


def authenticity_counts(place: Place) -> tuple[int, int]:
    authentic_count = sum(
        1 for vote in place.authenticity_votes if vote.label == AuthenticityLabel.authentic
    )
    touristy_count = sum(
        1 for vote in place.authenticity_votes if vote.label == AuthenticityLabel.touristy
    )
    return authentic_count, touristy_count


def authenticity_score(place: Place) -> float:
    authentic_count, touristy_count = authenticity_counts(place)
    total_votes = authentic_count + touristy_count
    return round(authentic_count / total_votes, 3) if total_votes else 0.5


def active_promotion_boost(place: Place, now: datetime | None = None) -> float:
    now = now or datetime.now(timezone.utc)
    active = [promo for promo in place.promotions if promo.start_at <= now <= promo.end_at]
    if not active:
        return 0.0
    boost = max(float(promo.boost_factor) for promo in active)
    return min(1.0, (boost - 1.0) / 2.0)


def is_open_now(place: Place, now: datetime | None = None) -> bool:
    if not place.hours:
        return True

    now = now or datetime.now(timezone.utc)
    day = now.weekday() % 7
    current_time = now.time().replace(tzinfo=None)

    today = [hour for hour in place.hours if hour.day_of_week == day]
    if not today:
        return True

    saw_opening_window = False
    for hour in today:
        if hour.is_closed:
            continue
        if hour.open_time is None or hour.close_time is None:
            return True
        saw_opening_window = True
        if hour.open_time <= current_time <= hour.close_time:
            return True

    return not saw_opening_window
