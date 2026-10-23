from fastapi.testclient import TestClient

from app.main import app, distance_m

client = TestClient(app)


def test_haversine_same_point():
    assert distance_m(10.0, 106.0, 10.0, 106.0) == 0


def test_public_pois_only():
    response = client.get("/api/v1/pois")
    assert response.status_code == 200
    assert response.json()["total"] >= 4


def test_admin_workflow():
    login = client.post("/api/v1/auth/login", data={"username": "editor@cityecho.vn", "password": "editor123"})
    assert login.status_code == 200
    token = login.json()["access_token"]
    response = client.post("/api/v1/admin/pois/sgu-main/submit", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200


def test_admin_analytics_counts_events():
    login = client.post("/api/v1/auth/login", data={"username": "admin@cityecho.vn", "password": "admin123"})
    token = login.json()["access_token"]
    client.post("/api/v1/narration-events", json={"poi_id": "chua-ba", "source": "QR", "event_type": "start"})
    client.post("/api/v1/narration-events", json={"poi_id": "chua-ba", "source": "QR", "event_type": "finish", "completed": True, "duration_seconds": 30})
    response = client.get("/api/v1/admin/analytics/overview", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["total_plays"] >= 1
    assert response.json()["sources"]["QR"] >= 1
