from app.core.database import SessionLocal
from app.models import Place, PlaceSource, PlaceType


def _register_and_login(client) -> str:
    client.post(
        "/auth/register",
        json={
            "full_name": "Profile User",
            "email": "profile@example.com",
            "password": "strongpass123",
            "role": "customer",
        },
    )
    login = client.post(
        "/auth/login",
        json={"email": "profile@example.com", "password": "strongpass123"},
    )
    return login.json()["access_token"]


def _seed_place() -> str:
    db = SessionLocal()
    try:
        place = Place(
            source=PlaceSource.internal,
            place_type=PlaceType.restaurant,
            name="Saved Place Cafe",
            formatted_address="5 W 21st St, New York, NY",
            neighborhood="Flatiron",
            lat=40.7410,
            lng=-73.9895,
            price_level=2,
        )
        db.add(place)
        db.commit()
        return place.id
    finally:
        db.close()


def test_profile_saved_lists_endpoint_returns_saved_items(client):
    token = _register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}
    place_id = _seed_place()

    create_list = client.post("/saved-lists", headers=headers, json={"name": "Favorites"})
    assert create_list.status_code == 200
    list_id = create_list.json()["id"]

    add_item = client.post(
        f"/saved-lists/{list_id}/items",
        headers=headers,
        json={"place_id": place_id},
    )
    assert add_item.status_code == 200

    profile_lists = client.get("/users/me/saved-lists", headers=headers)
    assert profile_lists.status_code == 200
    assert profile_lists.json()[0]["items"][0]["place_id"] == place_id

    list_detail = client.get(f"/saved-lists/{list_id}", headers=headers)
    assert list_detail.status_code == 200
    assert list_detail.json()["items"][0]["place_id"] == place_id
