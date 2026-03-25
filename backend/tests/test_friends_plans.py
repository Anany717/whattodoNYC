from app.core.database import SessionLocal
from app.models import Place, PlaceSource, PlaceType


def _register_and_login(client, idx: int) -> tuple[str, dict]:
    email = f"planner{idx}@example.com"
    client.post(
        "/auth/register",
        json={
            "full_name": f"Planner {idx}",
            "email": email,
            "password": "strongpass123",
            "role": "customer",
        },
    )
    login = client.post("/auth/login", json={"email": email, "password": "strongpass123"})
    token = login.json()["access_token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    return token, me.json()


def _seed_place(name: str, lat: float, lng: float) -> str:
    db = SessionLocal()
    try:
        place = Place(
            source=PlaceSource.internal,
            place_type=PlaceType.restaurant,
            name=name,
            formatted_address=f"{name} Address, New York, NY",
            neighborhood="Manhattan",
            lat=lat,
            lng=lng,
            price_level=2,
        )
        db.add(place)
        db.commit()
        return place.id
    finally:
        db.close()


def test_friend_request_and_accept_flow(client):
    token_1, user_1 = _register_and_login(client, 1)
    token_2, user_2 = _register_and_login(client, 2)

    send_request = client.post(
        "/friends/request",
        headers={"Authorization": f"Bearer {token_1}"},
        json={"addressee_user_id": user_2["id"]},
    )
    assert send_request.status_code == 200
    request_id = send_request.json()["id"]

    incoming = client.get("/friends/requests", headers={"Authorization": f"Bearer {token_2}"})
    assert incoming.status_code == 200
    assert incoming.json()["incoming"][0]["id"] == request_id

    accept = client.post(
        f"/friends/request/{request_id}/accept",
        headers={"Authorization": f"Bearer {token_2}"},
    )
    assert accept.status_code == 200
    assert accept.json()["status"] == "accepted"

    friends_1 = client.get("/friends", headers={"Authorization": f"Bearer {token_1}"})
    friends_2 = client.get("/friends", headers={"Authorization": f"Bearer {token_2}"})
    assert friends_1.status_code == 200
    assert friends_2.status_code == 200
    assert friends_1.json()[0]["friend"]["id"] == user_2["id"]
    assert friends_2.json()[0]["friend"]["id"] == user_1["id"]


def test_plan_voting_and_finalization_flow(client):
    host_token, host = _register_and_login(client, 10)
    guest_token, guest = _register_and_login(client, 11)

    request = client.post(
        "/friends/request",
        headers={"Authorization": f"Bearer {host_token}"},
        json={"addressee_user_id": guest["id"]},
    )
    request_id = request.json()["id"]
    client.post(
        f"/friends/request/{request_id}/accept",
        headers={"Authorization": f"Bearer {guest_token}"},
    )

    place_1 = _seed_place("Planning Pizza", 40.74, -73.99)
    place_2 = _seed_place("Planning Museum", 40.75, -73.98)

    plan_response = client.post(
        "/plans",
        headers={"Authorization": f"Bearer {host_token}"},
        json={
            "title": "Friday Night Plan",
            "description": "Pick one spot for the group.",
            "visibility": "shared",
            "invited_user_ids": [guest["id"]],
        },
    )
    assert plan_response.status_code == 200
    plan_id = plan_response.json()["id"]
    assert len(plan_response.json()["members"]) == 2

    add_first = client.post(
        f"/plans/{plan_id}/items",
        headers={"Authorization": f"Bearer {host_token}"},
        json={"place_id": place_1, "step_type": "food", "order_index": 0, "notes": "Late-night pizza option"},
    )
    assert add_first.status_code == 200
    add_second = client.post(
        f"/plans/{plan_id}/items",
        headers={"Authorization": f"Bearer {host_token}"},
        json={"place_id": place_2, "step_type": "activity", "order_index": 1, "notes": "Indoor backup plan"},
    )
    assert add_second.status_code == 200

    items = client.get(f"/plans/{plan_id}/items", headers={"Authorization": f"Bearer {host_token}"})
    assert items.status_code == 200
    item_ids = {item["place_id"]: item["id"] for item in items.json()}

    client.post(
        f"/plans/items/{item_ids[place_1]}/vote",
        headers={"Authorization": f"Bearer {host_token}"},
        json={"vote": "yes"},
    )
    client.post(
        f"/plans/items/{item_ids[place_2]}/vote",
        headers={"Authorization": f"Bearer {host_token}"},
        json={"vote": "maybe"},
    )
    client.post(
        f"/plans/items/{item_ids[place_1]}/vote",
        headers={"Authorization": f"Bearer {guest_token}"},
        json={"vote": "yes"},
    )
    client.post(
        f"/plans/items/{item_ids[place_2]}/vote",
        headers={"Authorization": f"Bearer {guest_token}"},
        json={"vote": "no"},
    )

    summary = client.get(
        f"/plans/{plan_id}/votes-summary",
        headers={"Authorization": f"Bearer {host_token}"},
    )
    assert summary.status_code == 200
    assert summary.json()["leading_choice"]["place_id"] == place_1
    assert len(summary.json()["suggested_itinerary"]) == 2

    select_first = client.put(
        f"/plans/{plan_id}/items/{item_ids[place_1]}",
        headers={"Authorization": f"Bearer {host_token}"},
        json={"is_selected": True},
    )
    assert select_first.status_code == 200
    select_second = client.put(
        f"/plans/{plan_id}/items/{item_ids[place_2]}",
        headers={"Authorization": f"Bearer {host_token}"},
        json={"is_selected": True},
    )
    assert select_second.status_code == 200

    finalize = client.post(
        f"/plans/{plan_id}/finalize",
        headers={"Authorization": f"Bearer {host_token}"},
        json={},
    )
    assert finalize.status_code == 200
    assert finalize.json()["final_choice"]["place_id"] == place_1
    assert len(finalize.json()["final_itinerary"]) == 2
    assert finalize.json()["final_itinerary"][0]["place_id"] == place_1
    assert finalize.json()["final_itinerary"][1]["place_id"] == place_2

    final_choice = client.get(
        f"/plans/{plan_id}/final-choice",
        headers={"Authorization": f"Bearer {guest_token}"},
    )
    assert final_choice.status_code == 200
    assert final_choice.json()["final_choice"]["place_id"] == place_1
    assert len(final_choice.json()["final_itinerary"]) == 2
