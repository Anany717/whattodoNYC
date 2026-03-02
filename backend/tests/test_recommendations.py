from app.core.database import SessionLocal
from app.models import Place, PlaceSource, PlaceTag, PlaceType, Tag


def _seed_places():
    db = SessionLocal()
    try:
        authentic = Tag(name="authentic")
        thai = Tag(name="thai")
        indoor = Tag(name="indoor")
        db.add_all([authentic, thai, indoor])
        db.flush()

        place_a = Place(
            source=PlaceSource.internal,
            place_type=PlaceType.restaurant,
            name="Near Thai Express",
            formatted_address="Manhattan",
            neighborhood="Midtown",
            lat=40.7500,
            lng=-73.9900,
            price_level=2,
        )
        place_b = Place(
            source=PlaceSource.internal,
            place_type=PlaceType.restaurant,
            name="Authentic Thai Spot",
            formatted_address="Manhattan",
            neighborhood="Kips Bay",
            lat=40.7440,
            lng=-73.9800,
            price_level=2,
        )
        db.add_all([place_a, place_b])
        db.flush()

        for place in [place_a, place_b]:
            db.add(PlaceTag(place_id=place.id, tag_id=thai.id))
            db.add(PlaceTag(place_id=place.id, tag_id=indoor.id))
        db.add(PlaceTag(place_id=place_b.id, tag_id=authentic.id))

        db.commit()
        return place_a.id, place_b.id
    finally:
        db.close()


def _register_and_login(client, idx: int) -> str:
    email = f"user{idx}@example.com"
    client.post(
        "/auth/register",
        json={
            "full_name": f"User {idx}",
            "email": email,
            "password": "strongpass123",
            "role": "customer",
        },
    )
    login = client.post("/auth/login", json={"email": email, "password": "strongpass123"})
    return login.json()["access_token"]


def _request_recommendations(client):
    return client.post(
        "/recommendations",
        json={
            "keywords": "authentic thai",
            "budget": 2,
            "group_size": 4,
            "preference": "indoor",
            "lat": 40.748,
            "lng": -73.987,
            "radius_km": 5,
        },
    )


def test_reviews_and_authenticity_influence_ranking(client):
    place_a_id, place_b_id = _seed_places()

    baseline = _request_recommendations(client)
    assert baseline.status_code == 200
    baseline_results = baseline.json()["results"]
    assert len(baseline_results) >= 2

    tokens = [_register_and_login(client, idx) for idx in [1, 2, 3]]

    for token in tokens:
        headers = {"Authorization": f"Bearer {token}"}
        review_resp = client.post(
            "/reviews",
            headers=headers,
            json={
                "place_id": place_b_id,
                "rating_overall": 5,
                "rating_value": 5,
                "rating_vibe": 5,
                "rating_groupfit": 5,
                "comment": "Excellent",
            },
        )
        assert review_resp.status_code == 200

        vote_resp = client.post(
            "/authenticity/vote",
            headers=headers,
            json={"place_id": place_b_id, "label": "authentic"},
        )
        assert vote_resp.status_code == 200

    post = _request_recommendations(client)
    assert post.status_code == 200
    post_results = post.json()["results"]

    assert post_results[0]["place_id"] == place_b_id
    assert "authenticity" in post_results[0]["why"] or "highly rated" in post_results[0]["why"]

    baseline_map = {row["place_id"]: row["score"] for row in baseline_results}
    post_map = {row["place_id"]: row["score"] for row in post_results}
    assert post_map[place_b_id] > baseline_map[place_b_id]
    assert place_a_id in baseline_map
