from app.core.database import SessionLocal
from app.models import Place, PlaceSource, PlaceTag, PlaceType, Review, Tag, User, UserRole
from app.services.google_places import GooglePlacesFetchResult


def _tag(db, name: str) -> Tag:
    tag = Tag(name=name)
    db.add(tag)
    db.flush()
    return tag


def _seed_search_places() -> tuple[str, str, str]:
    db = SessionLocal()
    try:
        jazz = _tag(db, "jazz")
        rooftop = _tag(db, "rooftop")
        thai = _tag(db, "thai")
        kayaking = _tag(db, "kayaking")
        outdoor = _tag(db, "outdoor")

        event_place = Place(
            source=PlaceSource.internal,
            place_type=PlaceType.event,
            name="Midtown Rooftop Jazz Session",
            formatted_address="230 W 44th St, New York, NY",
            neighborhood="Midtown",
            lat=40.7584,
            lng=-73.9892,
            price_level=2,
        )
        restaurant_place = Place(
            source=PlaceSource.internal,
            place_type=PlaceType.restaurant,
            name="Queens Thai Table",
            formatted_address="31-02 Broadway, Queens, NY",
            neighborhood="Astoria",
            lat=40.7616,
            lng=-73.9256,
            price_level=2,
        )
        activity_place = Place(
            source=PlaceSource.internal,
            place_type=PlaceType.activity,
            name="DUMBO Kayak Launch",
            formatted_address="1 Water St, Brooklyn, NY",
            neighborhood="DUMBO",
            lat=40.7027,
            lng=-73.9891,
            price_level=2,
        )
        db.add_all([event_place, restaurant_place, activity_place])
        db.flush()

        db.add_all(
            [
                PlaceTag(place_id=event_place.id, tag_id=jazz.id),
                PlaceTag(place_id=event_place.id, tag_id=rooftop.id),
                PlaceTag(place_id=restaurant_place.id, tag_id=thai.id),
                PlaceTag(place_id=activity_place.id, tag_id=kayaking.id),
                PlaceTag(place_id=activity_place.id, tag_id=outdoor.id),
            ]
        )
        db.commit()
        return event_place.id, restaurant_place.id, activity_place.id
    finally:
        db.close()


def test_search_matches_tags_neighborhood_and_type(client):
    event_place_id, restaurant_place_id, activity_place_id = _seed_search_places()

    event_search = client.get("/places/search", params={"query": "jazz rooftop midtown event"})
    assert event_search.status_code == 200
    event_items = event_search.json()["items"]
    assert event_items[0]["id"] == event_place_id

    restaurant_search = client.get("/places/search", params={"query": "thai astoria restaurant"})
    assert restaurant_search.status_code == 200
    restaurant_items = restaurant_search.json()["items"]
    assert restaurant_items[0]["id"] == restaurant_place_id

    activity_search = client.get("/places/search", params={"query": "kayaking dumbo activity"})
    assert activity_search.status_code == 200
    activity_items = activity_search.json()["items"]
    assert activity_items[0]["id"] == activity_place_id


def test_search_sorting_supports_price_rating_and_distance(client):
    db = SessionLocal()
    try:
        pizza = _tag(db, "pizza")
        user = User(
            full_name="Reviewer",
            email="reviewer@example.com",
            password_hash="hash",
            role=UserRole.customer,
        )
        db.add(user)
        db.flush()

        cheap = Place(
            source=PlaceSource.internal,
            place_type=PlaceType.restaurant,
            name="Cheap Pizza Corner",
            formatted_address="1 Main St, New York, NY",
            neighborhood="Midtown",
            lat=40.7415,
            lng=-73.9901,
            price_level=1,
        )
        premium = Place(
            source=PlaceSource.internal,
            place_type=PlaceType.restaurant,
            name="Premium Pizza Room",
            formatted_address="15 Main St, New York, NY",
            neighborhood="Midtown",
            lat=40.7435,
            lng=-73.9898,
            price_level=4,
        )
        closest = Place(
            source=PlaceSource.internal,
            place_type=PlaceType.restaurant,
            name="Closest Pizza Slice",
            formatted_address="10 Main St, New York, NY",
            neighborhood="Midtown",
            lat=40.7412,
            lng=-73.9898,
            price_level=2,
        )
        db.add_all([cheap, premium, closest])
        db.flush()

        for place in [cheap, premium, closest]:
            db.add(PlaceTag(place_id=place.id, tag_id=pizza.id))

        db.add_all(
            [
                Review(user_id=user.id, place_id=cheap.id, rating_overall=3),
                Review(user_id=user.id, place_id=premium.id, rating_overall=5),
                Review(user_id=user.id, place_id=closest.id, rating_overall=4),
            ]
        )
        db.commit()
    finally:
        db.close()

    price_search = client.get("/places/search", params={"query": "pizza", "sort_by": "price_asc"})
    assert price_search.status_code == 200
    assert price_search.json()["sort_by"] == "price_asc"
    assert price_search.json()["items"][0]["name"] == "Cheap Pizza Corner"

    rating_search = client.get(
        "/places/search",
        params={"query": "pizza", "sort_by": "rating_desc"},
    )
    assert rating_search.status_code == 200
    assert rating_search.json()["items"][0]["name"] == "Premium Pizza Room"

    distance_search = client.get(
        "/places/search",
        params={
            "query": "pizza",
            "sort_by": "distance_asc",
            "lat": 40.7411,
            "lng": -73.9897,
            "radius_km": 5,
        },
    )
    assert distance_search.status_code == 200
    assert distance_search.json()["items"][0]["name"] == "Closest Pizza Slice"


def test_search_attempts_live_google_even_when_internal_matches_exist(client, monkeypatch):
    _seed_search_places()
    call_log = {"count": 0}

    def fake_google_search(db, *, query, lat, lng, radius_km, limit):
        call_log["count"] += 1
        live_place = Place(
            google_place_id="google-live-thai-1",
            google_primary_type="restaurant",
            google_rating=4.7,
            google_user_ratings_total=820,
            source=PlaceSource.google,
            place_type=PlaceType.restaurant,
            name="Live East Village Thai Kitchen",
            formatted_address="99 2nd Ave, New York, NY",
            neighborhood="East Village",
            lat=40.7274,
            lng=-73.9871,
            price_level=2,
            is_cached_from_external=True,
        )
        db.add(live_place)
        db.flush()
        return GooglePlacesFetchResult(
            places=[live_place], attempted=True, succeeded=True, error=None
        )

    monkeypatch.setattr(
        "app.services.search_service.fetch_and_cache_google_places", fake_google_search
    )

    response = client.get(
        "/places/search",
        params={
            "query": "thai east village",
            "lat": 40.728,
            "lng": -73.986,
            "radius_km": 5,
        },
    )
    assert response.status_code == 200
    payload = response.json()

    assert call_log["count"] == 1
    assert payload["live_search_attempted"] is True
    assert payload["live_search_succeeded"] is True
    assert payload["live_result_count"] == 1
    assert any(item["search_source"] == "live_google" for item in payload["items"])
    assert any(item["name"] == "Live East Village Thai Kitchen" for item in payload["items"])


def test_search_falls_back_cleanly_when_google_search_fails(client, monkeypatch):
    _, restaurant_place_id, _ = _seed_search_places()

    def fake_google_failure(db, *, query, lat, lng, radius_km, limit):
        return GooglePlacesFetchResult(
            places=[],
            attempted=True,
            succeeded=False,
            error="temporary outage",
        )

    monkeypatch.setattr(
        "app.services.search_service.fetch_and_cache_google_places", fake_google_failure
    )

    response = client.get(
        "/places/search",
        params={
            "query": "thai astoria",
            "lat": 40.7616,
            "lng": -73.9256,
            "radius_km": 5,
        },
    )
    assert response.status_code == 200
    payload = response.json()

    assert payload["google_results_used"] is False
    assert payload["live_search_attempted"] is True
    assert payload["live_search_succeeded"] is False
    assert "Showing cached/local results instead" in (payload["status_message"] or "")
    assert payload["items"][0]["id"] == restaurant_place_id
