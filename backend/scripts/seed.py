from __future__ import annotations

from sqlalchemy import select

from app.core.database import Base, SessionLocal, engine
from app.models import Place, PlaceSource, PlaceTag, PlaceType, Tag

SAMPLE_PLACES = [
    ("Xi'an Famous Foods", 40.7423, -73.9912, 1, ["authentic", "thai", "indoor"]),
    ("Los Tacos No.1", 40.7420, -74.0060, 1, ["authentic", "mexican", "quick-bite", "indoor"]),
    ("Smorgasburg", 40.7218, -73.9575, 2, ["outdoor", "food-market", "group-friendly"]),
    ("Brooklyn Bridge Park Kayaking", 40.7003, -73.9967, 2, ["outdoor", "activity", "adventure"]),
    ("The Met", 40.7794, -73.9632, 3, ["indoor", "culture", "activity"]),
    ("Comedy Cellar", 40.7301, -74.0021, 2, ["indoor", "nightlife", "group-friendly"]),
    ("Prince Street Pizza", 40.7231, -73.9948, 1, ["pizza", "authentic", "quick-bite"]),
    ("Bryant Park Winter Village", 40.7536, -73.9832, 2, ["outdoor", "seasonal", "event"]),
    ("Queens Night Market", 40.7459, -73.8458, 1, ["authentic", "outdoor", "group-friendly"]),
    ("Chelsea Market", 40.7423, -74.0060, 2, ["indoor", "food-hall", "group-friendly"]),
]


def upsert_tag(db, name: str) -> Tag:
    existing = db.scalar(select(Tag).where(Tag.name == name))
    if existing:
        return existing
    tag = Tag(name=name)
    db.add(tag)
    db.flush()
    return tag


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        for name, lat, lng, price, tags in SAMPLE_PLACES:
            existing = db.scalar(select(Place).where(Place.name == name))
            if existing:
                continue
            place = Place(
                source=PlaceSource.internal,
                place_type=PlaceType.activity if "activity" in tags else PlaceType.restaurant,
                name=name,
                formatted_address="NYC",
                neighborhood=None,
                lat=lat,
                lng=lng,
                price_level=price,
            )
            db.add(place)
            db.flush()
            for tag_name in tags:
                tag = upsert_tag(db, tag_name)
                db.add(PlaceTag(place_id=place.id, tag_id=tag.id))
        db.commit()
        print("Seed complete")
    finally:
        db.close()


if __name__ == "__main__":
    main()
