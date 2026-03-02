def test_register_login_and_me(client):
    register_payload = {
        "full_name": "Test User",
        "email": "test@example.com",
        "password": "strongpass123",
        "role": "customer",
    }
    register_resp = client.post("/auth/register", json=register_payload)
    assert register_resp.status_code == 200
    token = register_resp.json()["access_token"]
    assert token

    me_resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "test@example.com"

    login_resp = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "strongpass123"},
    )
    assert login_resp.status_code == 200
    assert login_resp.json()["access_token"]


def test_rbac_blocks_customer_from_creating_place(client):
    client.post(
        "/auth/register",
        json={
            "full_name": "Customer",
            "email": "customer@example.com",
            "password": "strongpass123",
            "role": "customer",
        },
    )
    login_resp = client.post(
        "/auth/login",
        json={"email": "customer@example.com", "password": "strongpass123"},
    )
    token = login_resp.json()["access_token"]

    create_resp = client.post(
        "/places",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "place_type": "restaurant",
            "name": "No Access Cafe",
            "lat": 40.71,
            "lng": -74.0,
            "price_level": 2,
        },
    )
    assert create_resp.status_code == 403
