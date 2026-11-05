from fastapi.testclient import TestClient
from uuid import uuid4

from app.main import SERVICE, app, distance_m
from app.schemas import Translation

client = TestClient(app)


def test_haversine_same_point():
    assert distance_m(10.0, 106.0, 10.0, 106.0) == 0


def test_public_pois_only():
    response = client.get("/api/v1/pois")
    assert response.status_code == 200
    assert response.json()["total"] >= 12


def test_public_pois_can_be_loaded_across_pages():
    all_pois = []
    total = None
    page = 1
    while total is None or len(all_pois) < total:
        response = client.get(f"/api/v1/pois?page={page}&limit=100")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] or len(all_pois) >= data["total"]
        all_pois.extend(data["items"])
        total = data["total"]
        page += 1

    assert len(all_pois) == total
    assert len({poi["id"] for poi in all_pois}) == len(all_pois)


def test_public_pois_use_requested_translation_and_fallback(monkeypatch):
    poi_id = "dinh-doc-lap"
    original = SERVICE.pois[poi_id]
    english = Translation(
        language_code="en",
        name="Independence Palace",
        description="A landmark in Ho Chi Minh City.",
        narration_text="Welcome to Independence Palace.",
    )
    monkeypatch.setitem(
        SERVICE.pois,
        poi_id,
        original.model_copy(update={"translations": [original.translation, english]}),
    )

    translated = client.get("/api/v1/pois?lang=en&search=Independence")
    assert translated.status_code == 200
    result = next(item for item in translated.json()["items"] if item["id"] == poi_id)
    assert result["translation"]["language_code"] == "en"
    assert result["translation"]["name"] == "Independence Palace"

    fallback = client.get(f"/api/v1/pois/{poi_id}?lang=ja")
    assert fallback.status_code == 200
    assert fallback.json()["translation"]["language_code"] == "vi"


def test_nearby_qr_and_narration_respect_language(monkeypatch):
    poi_id = "dinh-doc-lap"
    original = SERVICE.pois[poi_id]
    english = Translation(
        language_code="en",
        name="Independence Palace",
        description="A landmark.",
        narration_text="Welcome.",
    )
    monkeypatch.setitem(
        SERVICE.pois,
        poi_id,
        original.model_copy(update={"translations": [original.translation, english]}),
    )

    qr = client.get(f"/api/v1/qr/{original.qr_code}?lang=en")
    assert qr.status_code == 200
    assert qr.json()["translation"]["name"] == "Independence Palace"

    narration = client.get(f"/api/v1/pois/{poi_id}/narration?lang=en")
    assert narration.status_code == 200
    assert narration.json()["narration_text"] == "Welcome."


def test_admin_can_add_translation_without_replacing_vietnamese(monkeypatch):
    poi_id = "dinh-doc-lap"
    original = SERVICE.pois[poi_id]
    monkeypatch.setitem(
        SERVICE.pois,
        poi_id,
        original.model_copy(update={"translations": [original.translation]}),
    )
    login = client.post(
        "/api/v1/auth/login",
        data={"username": "editor@cityecho.vn", "password": "editor123"},
    )
    token = login.json()["access_token"]
    response = client.patch(
        f"/api/v1/admin/pois/{poi_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "translation": {
                "language_code": "en",
                "name": "Independence Palace",
                "description": "A landmark.",
                "narration_text": "Welcome.",
            }
        },
    )
    assert response.status_code == 200
    assert response.json()["translation"]["language_code"] == "vi"

    vietnamese = client.get(f"/api/v1/pois/{poi_id}?lang=vi").json()
    english = client.get(f"/api/v1/pois/{poi_id}?lang=en").json()
    assert vietnamese["translation"]["name"] == original.translation.name
    assert english["translation"]["name"] == "Independence Palace"
    assert {item["language_code"] for item in english["translations"]} == {"vi", "en"}


def test_languages_endpoint_includes_common_languages():
    response = client.get("/api/v1/languages")
    assert response.status_code == 200
    assert {"vi", "en"}.issubset(response.json())


def test_admin_workflow():
    login = client.post("/api/v1/auth/login", data={"username": "editor@cityecho.vn", "password": "editor123"})
    assert login.status_code == 200
    token = login.json()["access_token"]
    response = client.post("/api/v1/admin/pois/ho-con-rua/submit", headers={"Authorization": f"Bearer {token}"})
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


def test_editor_can_update_poi_translation():
    login = client.post("/api/v1/auth/login", data={"username": "editor@cityecho.vn", "password": "editor123"})
    token = login.json()["access_token"]
    response = client.patch(
        "/api/v1/admin/pois/chua-ba",
        headers={"Authorization": f"Bearer {token}"},
        json={"translation": {"language_code": "vi", "name": "Chùa Bà cập nhật", "description": "Mô tả mới", "narration_text": "Nội dung mới"}},
    )
    assert response.status_code == 200
    assert response.json()["translation"]["name"] == "Chùa Bà cập nhật"


def test_qr_returns_only_published_poi():
    response = client.get("/api/v1/qr/CITYECHO-BINHTAY")
    assert response.status_code == 200
    assert response.json()["id"] == "cho-lon"
    assert client.get("/api/v1/qr/UNKNOWN-CODE").status_code == 404


def test_nearby_route_is_not_captured_by_poi_detail():
    response = client.get("/api/v1/pois/nearby?lat=10.7591&lng=106.6823")
    assert response.status_code == 200
    assert any(item["id"] == "sgu-main" for item in response.json())


def test_geofence_evaluate_selects_poi_inside_radius():
    response = client.get("/api/v1/geofence/evaluate?lat=10.7591&lng=106.6823")
    assert response.status_code == 200
    assert response.json()["candidate"]["id"] == "sgu-main"


def test_visitor_heartbeat_and_admin_session_overview():
    device_id = str(uuid4())
    heartbeat = client.post(
        "/api/v1/visitor-sessions/heartbeat",
        json={"device_id": device_id, "path": "/?join=1", "source": "QR"},
    )
    assert heartbeat.status_code == 200

    login = client.post(
        "/api/v1/auth/login",
        data={"username": "admin@cityecho.vn", "password": "admin123"},
    )
    token = login.json()["access_token"]
    response = client.get(
        "/api/v1/admin/analytics/visitor-sessions",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    session = next(item for item in data["sessions"] if item["device_id"] == device_id)
    assert session["is_active"] is True
    assert session["entry_source"] == "QR"
    assert data["active_count"] >= 1


def test_visitor_session_overview_requires_admin():
    response = client.get("/api/v1/admin/analytics/visitor-sessions")
    assert response.status_code == 401
