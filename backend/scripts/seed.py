from __future__ import annotations

from sqlalchemy import select

from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models import (
    Place,
    PlaceSource,
    PlaceTag,
    PlaceType,
    Tag,
    User,
    UserRole,
)

DEMO_ADMIN_EMAIL = "admin@whattodonyc.local"
DEMO_ADMIN_PASSWORD = "AdminDemo123!"
DEMO_ADMIN_NAME = "Demo Admin"


def seed_record(
    *,
    name: str,
    place_type: PlaceType,
    formatted_address: str,
    neighborhood: str,
    lat: float,
    lng: float,
    price_level: int | None,
    tags: list[str],
    phone: str | None = None,
    website: str | None = None,
) -> dict:
    return {
        "name": name,
        "place_type": place_type,
        "formatted_address": formatted_address,
        "neighborhood": neighborhood,
        "lat": lat,
        "lng": lng,
        "price_level": price_level,
        "tags": tags,
        "phone": phone,
        "website": website,
    }


SEED_RECORDS = [
    seed_record(
        name="Xi'an Famous Foods",
        place_type=PlaceType.restaurant,
        formatted_address="24 W 45th St, New York, NY",
        neighborhood="Midtown",
        lat=40.7564,
        lng=-73.9819,
        price_level=1,
        tags=["authentic", "xian", "noodles", "spicy", "quick-bite", "indoor"],
    ),
    seed_record(
        name="Los Tacos No. 1",
        place_type=PlaceType.restaurant,
        formatted_address="75 9th Ave, New York, NY",
        neighborhood="Chelsea",
        lat=40.7423,
        lng=-74.0061,
        price_level=1,
        tags=["authentic", "mexican", "tacos", "quick-bite", "indoor"],
    ),
    seed_record(
        name="Prince Street Pizza",
        place_type=PlaceType.restaurant,
        formatted_address="27 Prince St, New York, NY",
        neighborhood="Nolita",
        lat=40.7231,
        lng=-73.9948,
        price_level=1,
        tags=["pizza", "late-night", "iconic", "quick-bite", "indoor"],
    ),
    seed_record(
        name="L'Industrie Pizzeria",
        place_type=PlaceType.restaurant,
        formatted_address="254 S 2nd St, Brooklyn, NY",
        neighborhood="Williamsburg",
        lat=40.7118,
        lng=-73.9577,
        price_level=2,
        tags=["pizza", "brooklyn", "casual", "indoor"],
    ),
    seed_record(
        name="Katz's Delicatessen",
        place_type=PlaceType.restaurant,
        formatted_address="205 E Houston St, New York, NY",
        neighborhood="Lower East Side",
        lat=40.7223,
        lng=-73.9874,
        price_level=2,
        tags=["deli", "classic", "authentic", "group-friendly", "indoor"],
    ),
    seed_record(
        name="Russ & Daughters Cafe",
        place_type=PlaceType.restaurant,
        formatted_address="127 Orchard St, New York, NY",
        neighborhood="Lower East Side",
        lat=40.7199,
        lng=-73.9882,
        price_level=3,
        tags=["brunch", "bagels", "seafood", "classic", "indoor"],
    ),
    seed_record(
        name="Thai Diner",
        place_type=PlaceType.restaurant,
        formatted_address="186 Mott St, New York, NY",
        neighborhood="Nolita",
        lat=40.7213,
        lng=-73.9950,
        price_level=2,
        tags=["thai", "authentic", "brunch", "trendy", "indoor"],
    ),
    seed_record(
        name="Saigon Social",
        place_type=PlaceType.restaurant,
        formatted_address="172 Orchard St, New York, NY",
        neighborhood="Lower East Side",
        lat=40.7212,
        lng=-73.9888,
        price_level=2,
        tags=["vietnamese", "authentic", "indoor", "date-night"],
    ),
    seed_record(
        name="Veselka",
        place_type=PlaceType.restaurant,
        formatted_address="144 2nd Ave, New York, NY",
        neighborhood="East Village",
        lat=40.7299,
        lng=-73.9867,
        price_level=2,
        tags=["ukrainian", "comfort-food", "late-night", "indoor"],
    ),
    seed_record(
        name="Lucali",
        place_type=PlaceType.restaurant,
        formatted_address="575 Henry St, Brooklyn, NY",
        neighborhood="Carroll Gardens",
        lat=40.6818,
        lng=-73.9956,
        price_level=3,
        tags=["pizza", "date-night", "brooklyn", "indoor"],
    ),
    seed_record(
        name="Joe's Shanghai",
        place_type=PlaceType.restaurant,
        formatted_address="46 Bowery, New York, NY",
        neighborhood="Chinatown",
        lat=40.7154,
        lng=-73.9971,
        price_level=2,
        tags=["chinese", "soup-dumplings", "authentic", "group-friendly", "indoor"],
    ),
    seed_record(
        name="Sushi Nakazawa",
        place_type=PlaceType.restaurant,
        formatted_address="23 Commerce St, New York, NY",
        neighborhood="West Village",
        lat=40.7336,
        lng=-74.0052,
        price_level=4,
        tags=["sushi", "omakase", "date-night", "indoor"],
    ),
    seed_record(
        name="Via Carota",
        place_type=PlaceType.restaurant,
        formatted_address="51 Grove St, New York, NY",
        neighborhood="West Village",
        lat=40.7311,
        lng=-74.0036,
        price_level=3,
        tags=["italian", "date-night", "trendy", "indoor"],
    ),
    seed_record(
        name="Tonchin New York",
        place_type=PlaceType.restaurant,
        formatted_address="13 W 36th St, New York, NY",
        neighborhood="Midtown",
        lat=40.7498,
        lng=-73.9855,
        price_level=3,
        tags=["ramen", "japanese", "indoor", "group-friendly"],
    ),
    seed_record(
        name="Mama's TOO!",
        place_type=PlaceType.restaurant,
        formatted_address="2750 Broadway, New York, NY",
        neighborhood="Upper West Side",
        lat=40.8001,
        lng=-73.9684,
        price_level=2,
        tags=["pizza", "casual", "quick-bite", "indoor"],
    ),
    seed_record(
        name="John's of Bleecker Street",
        place_type=PlaceType.restaurant,
        formatted_address="278 Bleecker St, New York, NY",
        neighborhood="West Village",
        lat=40.7316,
        lng=-74.0033,
        price_level=2,
        tags=["pizza", "classic", "group-friendly", "indoor"],
    ),
    seed_record(
        name="Levain Bakery",
        place_type=PlaceType.restaurant,
        formatted_address="167 W 74th St, New York, NY",
        neighborhood="Upper West Side",
        lat=40.7799,
        lng=-73.9784,
        price_level=1,
        tags=["bakery", "dessert", "cookies", "quick-bite", "indoor"],
    ),
    seed_record(
        name="COTE Korean Steakhouse",
        place_type=PlaceType.restaurant,
        formatted_address="16 W 22nd St, New York, NY",
        neighborhood="Flatiron",
        lat=40.7411,
        lng=-73.9913,
        price_level=4,
        tags=["korean", "steakhouse", "date-night", "group-friendly", "indoor"],
    ),
    seed_record(
        name="Golden Diner",
        place_type=PlaceType.restaurant,
        formatted_address="123 Madison St, New York, NY",
        neighborhood="Chinatown",
        lat=40.7136,
        lng=-73.9899,
        price_level=2,
        tags=["diner", "asian-american", "brunch", "indoor"],
    ),
    seed_record(
        name="Emily Brooklyn",
        place_type=PlaceType.restaurant,
        formatted_address="919 Fulton St, Brooklyn, NY",
        neighborhood="Clinton Hill",
        lat=40.6838,
        lng=-73.9685,
        price_level=3,
        tags=["burger", "pizza", "date-night", "brooklyn", "indoor"],
    ),
    seed_record(
        name="Oxomoco",
        place_type=PlaceType.restaurant,
        formatted_address="128 Greenpoint Ave, Brooklyn, NY",
        neighborhood="Greenpoint",
        lat=40.7291,
        lng=-73.9548,
        price_level=3,
        tags=["mexican", "wood-fired", "date-night", "indoor"],
    ),
    seed_record(
        name="Roberta's",
        place_type=PlaceType.restaurant,
        formatted_address="261 Moore St, Brooklyn, NY",
        neighborhood="Bushwick",
        lat=40.7051,
        lng=-73.9339,
        price_level=2,
        tags=["pizza", "brooklyn", "trendy", "group-friendly", "indoor"],
    ),
    seed_record(
        name="Hometown Bar-B-Que",
        place_type=PlaceType.restaurant,
        formatted_address="454 Van Brunt St, Brooklyn, NY",
        neighborhood="Red Hook",
        lat=40.6738,
        lng=-74.0166,
        price_level=2,
        tags=["barbecue", "group-friendly", "outdoor", "indoor"],
    ),
    seed_record(
        name="Di Fara Pizza",
        place_type=PlaceType.restaurant,
        formatted_address="1424 Avenue J, Brooklyn, NY",
        neighborhood="Midwood",
        lat=40.6254,
        lng=-73.9608,
        price_level=2,
        tags=["pizza", "classic", "brooklyn", "indoor"],
    ),
    seed_record(
        name="Adda Indian Canteen",
        place_type=PlaceType.restaurant,
        formatted_address="31-31 Thomson Ave, Queens, NY",
        neighborhood="Long Island City",
        lat=40.7445,
        lng=-73.9354,
        price_level=2,
        tags=["indian", "authentic", "spicy", "indoor"],
    ),
    seed_record(
        name="Birria-Landia Jackson Heights",
        place_type=PlaceType.restaurant,
        formatted_address="78th St and Roosevelt Ave, Queens, NY",
        neighborhood="Jackson Heights",
        lat=40.7462,
        lng=-73.8895,
        price_level=1,
        tags=["mexican", "birria", "street-food", "authentic", "outdoor"],
    ),
    seed_record(
        name="Court Street Grocers",
        place_type=PlaceType.restaurant,
        formatted_address="485 Court St, Brooklyn, NY",
        neighborhood="Carroll Gardens",
        lat=40.6800,
        lng=-73.9962,
        price_level=2,
        tags=["sandwiches", "casual", "quick-bite", "indoor"],
    ),
    seed_record(
        name="Clinton St. Baking Company",
        place_type=PlaceType.restaurant,
        formatted_address="4 Clinton St, New York, NY",
        neighborhood="Lower East Side",
        lat=40.7214,
        lng=-73.9839,
        price_level=2,
        tags=["brunch", "pancakes", "popular", "indoor"],
    ),
    seed_record(
        name="S&P Lunch",
        place_type=PlaceType.restaurant,
        formatted_address="174 5th Ave, New York, NY",
        neighborhood="Flatiron",
        lat=40.7420,
        lng=-73.9896,
        price_level=2,
        tags=["deli", "sandwiches", "retro", "quick-bite", "indoor"],
    ),
    seed_record(
        name="Radio Bakery",
        place_type=PlaceType.restaurant,
        formatted_address="135 India St, Brooklyn, NY",
        neighborhood="Greenpoint",
        lat=40.7302,
        lng=-73.9541,
        price_level=2,
        tags=["bakery", "coffee", "pastries", "indoor"],
    ),
    seed_record(
        name="SummerStage Central Park",
        place_type=PlaceType.event,
        formatted_address="Rumsey Playfield, Central Park, New York, NY",
        neighborhood="Upper East Side",
        lat=40.7726,
        lng=-73.9702,
        price_level=1,
        tags=["outdoor", "music", "festival", "summer", "group-friendly"],
    ),
    seed_record(
        name="Bryant Park Movie Nights",
        place_type=PlaceType.event,
        formatted_address="Bryant Park, New York, NY",
        neighborhood="Midtown",
        lat=40.7536,
        lng=-73.9832,
        price_level=1,
        tags=["outdoor", "movies", "free", "nightlife", "group-friendly"],
    ),
    seed_record(
        name="Rooftop Films at Industry City",
        place_type=PlaceType.event,
        formatted_address="220 36th St, Brooklyn, NY",
        neighborhood="Sunset Park",
        lat=40.6560,
        lng=-74.0088,
        price_level=2,
        tags=["outdoor", "film", "rooftop", "date-night", "summer"],
    ),
    seed_record(
        name="Winter Jazzfest Marathon",
        place_type=PlaceType.event,
        formatted_address="Various venues in Manhattan, New York, NY",
        neighborhood="Greenwich Village",
        lat=40.7306,
        lng=-73.9975,
        price_level=3,
        tags=["indoor", "jazz", "festival", "music", "nightlife"],
    ),
    seed_record(
        name="Japan Fes East Village",
        place_type=PlaceType.event,
        formatted_address="4th Ave and St Marks Pl, New York, NY",
        neighborhood="East Village",
        lat=40.7291,
        lng=-73.9887,
        price_level=1,
        tags=["outdoor", "street-food", "japanese", "festival", "group-friendly"],
    ),
    seed_record(
        name="Brooklyn Flea DUMBO",
        place_type=PlaceType.event,
        formatted_address="Pearl Plaza, Brooklyn, NY",
        neighborhood="DUMBO",
        lat=40.7035,
        lng=-73.9890,
        price_level=1,
        tags=["outdoor", "shopping", "vintage", "market", "weekend"],
    ),
    seed_record(
        name="Queens Night Market",
        place_type=PlaceType.event,
        formatted_address="47-01 111th St, Queens, NY",
        neighborhood="Corona",
        lat=40.7464,
        lng=-73.8468,
        price_level=1,
        tags=["outdoor", "night-market", "street-food", "authentic", "group-friendly"],
    ),
    seed_record(
        name="Bronx Night Market",
        place_type=PlaceType.event,
        formatted_address="1 Fordham Plaza, Bronx, NY",
        neighborhood="Fordham",
        lat=40.8616,
        lng=-73.8905,
        price_level=1,
        tags=["outdoor", "night-market", "music", "food", "group-friendly"],
    ),
    seed_record(
        name="Holiday Train Show at NYBG",
        place_type=PlaceType.event,
        formatted_address="2900 Southern Blvd, Bronx, NY",
        neighborhood="Belmont",
        lat=40.8623,
        lng=-73.8801,
        price_level=3,
        tags=["indoor", "holiday", "family-friendly", "seasonal", "culture"],
    ),
    seed_record(
        name="Smorgasburg Williamsburg",
        place_type=PlaceType.event,
        formatted_address="90 Kent Ave, Brooklyn, NY",
        neighborhood="Williamsburg",
        lat=40.7218,
        lng=-73.9575,
        price_level=2,
        tags=["outdoor", "food-market", "weekend", "group-friendly", "festival"],
    ),
    seed_record(
        name="Brooklyn Bridge Park Kayaking",
        place_type=PlaceType.activity,
        formatted_address="Pier 2, Brooklyn Bridge Park, Brooklyn, NY",
        neighborhood="Brooklyn Heights",
        lat=40.6998,
        lng=-73.9972,
        price_level=2,
        tags=["outdoor", "waterfront", "kayaking", "adventure", "summer"],
    ),
    seed_record(
        name="The Metropolitan Museum of Art",
        place_type=PlaceType.activity,
        formatted_address="1000 5th Ave, New York, NY",
        neighborhood="Upper East Side",
        lat=40.7794,
        lng=-73.9632,
        price_level=3,
        tags=["indoor", "museum", "culture", "art", "classic"],
    ),
    seed_record(
        name="The High Line Sunset Walk",
        place_type=PlaceType.activity,
        formatted_address="Gansevoort St, New York, NY",
        neighborhood="Chelsea",
        lat=40.7479,
        lng=-74.0049,
        price_level=1,
        tags=["outdoor", "walk", "sunset", "scenic", "date-night"],
    ),
    seed_record(
        name="Top of the Rock Observation Deck",
        place_type=PlaceType.activity,
        formatted_address="30 Rockefeller Plaza, New York, NY",
        neighborhood="Midtown",
        lat=40.7591,
        lng=-73.9799,
        price_level=3,
        tags=["indoor", "viewpoint", "skyline", "tourist-friendly", "date-night"],
    ),
    seed_record(
        name="Governors Island Bike Ride",
        place_type=PlaceType.activity,
        formatted_address="Governors Island, New York, NY",
        neighborhood="Governors Island",
        lat=40.6895,
        lng=-74.0168,
        price_level=2,
        tags=["outdoor", "biking", "waterfront", "adventure", "group-friendly"],
    ),
    seed_record(
        name="Rockaway Surf Session",
        place_type=PlaceType.activity,
        formatted_address="96-01 Shore Front Pkwy, Queens, NY",
        neighborhood="Rockaway Beach",
        lat=40.5843,
        lng=-73.8205,
        price_level=3,
        tags=["outdoor", "surfing", "beach", "adventure", "summer"],
    ),
    seed_record(
        name="Edge Hudson Yards Sky Deck",
        place_type=PlaceType.activity,
        formatted_address="30 Hudson Yards, New York, NY",
        neighborhood="Hudson Yards",
        lat=40.7539,
        lng=-74.0016,
        price_level=4,
        tags=["indoor", "viewpoint", "skyline", "thrill", "date-night"],
    ),
    seed_record(
        name="Prospect Park Pedal Boats",
        place_type=PlaceType.activity,
        formatted_address="171 East Dr, Brooklyn, NY",
        neighborhood="Prospect Park",
        lat=40.6603,
        lng=-73.9690,
        price_level=2,
        tags=["outdoor", "boats", "lake", "family-friendly", "group-friendly"],
    ),
    seed_record(
        name="Chelsea Piers Bowling",
        place_type=PlaceType.activity,
        formatted_address="62 Chelsea Piers, New York, NY",
        neighborhood="Chelsea",
        lat=40.7464,
        lng=-74.0082,
        price_level=2,
        tags=["indoor", "bowling", "nightlife", "group-friendly", "games"],
    ),
    seed_record(
        name="Museum of Modern Art",
        place_type=PlaceType.activity,
        formatted_address="11 W 53rd St, New York, NY",
        neighborhood="Midtown",
        lat=40.7614,
        lng=-73.9776,
        price_level=3,
        tags=["indoor", "museum", "art", "culture", "classic"],
    ),
]


def upsert_tag(db, name: str) -> Tag:
    existing = db.scalar(select(Tag).where(Tag.name == name))
    if existing:
        return existing
    tag = Tag(name=name)
    db.add(tag)
    db.flush()
    return tag


def sync_place_tags(db, place: Place, tag_names: list[str]) -> None:
    desired_tag_ids = set()
    for tag_name in tag_names:
        tag = upsert_tag(db, tag_name)
        desired_tag_ids.add(tag.id)

    existing_relations = {place_tag.tag_id: place_tag for place_tag in list(place.tags)}

    for tag_id in desired_tag_ids:
        if tag_id not in existing_relations:
            db.add(PlaceTag(place_id=place.id, tag_id=tag_id))

    for tag_id, relation in existing_relations.items():
        if tag_id not in desired_tag_ids:
            db.delete(relation)


def upsert_place(db, record: dict) -> None:
    place = db.scalar(select(Place).where(Place.name == record["name"]))

    if not place:
        place = Place(
            name=record["name"], source=PlaceSource.internal, place_type=record["place_type"]
        )
        db.add(place)

    place.source = PlaceSource.internal
    place.place_type = record["place_type"]
    place.formatted_address = record["formatted_address"]
    place.neighborhood = record["neighborhood"]
    place.lat = record["lat"]
    place.lng = record["lng"]
    place.price_level = record["price_level"]
    place.phone = record["phone"]
    place.website = record["website"]
    place.is_seed_data = True

    db.add(place)
    db.flush()
    sync_place_tags(db, place, record["tags"])


def upsert_demo_admin(db) -> None:
    admin_user = db.scalar(select(User).where(User.email == DEMO_ADMIN_EMAIL))

    if not admin_user:
        admin_user = User(
            full_name=DEMO_ADMIN_NAME,
            email=DEMO_ADMIN_EMAIL,
            password_hash=hash_password(DEMO_ADMIN_PASSWORD),
            role=UserRole.admin,
        )
        db.add(admin_user)
        db.flush()
        return

    admin_user.full_name = DEMO_ADMIN_NAME
    admin_user.role = UserRole.admin
    admin_user.password_hash = hash_password(DEMO_ADMIN_PASSWORD)
    db.add(admin_user)
    db.flush()


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        for record in SEED_RECORDS:
            upsert_place(db, record)
        upsert_demo_admin(db)

        db.commit()

        restaurant_count = sum(
            1 for record in SEED_RECORDS if record["place_type"] == PlaceType.restaurant
        )
        event_count = sum(1 for record in SEED_RECORDS if record["place_type"] == PlaceType.event)
        activity_count = sum(
            1 for record in SEED_RECORDS if record["place_type"] == PlaceType.activity
        )
        print(
            f"Seed complete: {len(SEED_RECORDS)} total entries "
            f"({restaurant_count} restaurants, {event_count} events, {activity_count} activities)"
        )
        print(f"Demo admin login: {DEMO_ADMIN_EMAIL} / {DEMO_ADMIN_PASSWORD}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
