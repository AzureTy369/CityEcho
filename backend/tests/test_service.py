from app.schemas import NarrationEvent, PoiInput, PoiUpdate, Translation
from app.services.cityecho_service import CityEchoService
from app.storage import PersistentStore


def test_service_persists_poi_and_nested_translation(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'cityecho.db'}"
    service = CityEchoService(PersistentStore(database_url))
    admin = service.user_by_email("admin@cityecho.vn")
    assert admin is not None

    poi = service.create_poi(
        PoiInput(
            latitude=10.7591,
            longitude=106.6823,
            translation=Translation(
                name="POI kiểm thử",
                description="Mô tả ban đầu",
                narration_text="Nội dung thuyết minh ban đầu",
            ),
        ),
        admin,
    )
    updated = service.update_poi(
        poi.id,
        PoiUpdate(
            translation=Translation(
                name="POI đã cập nhật",
                description="Mô tả mới",
                narration_text="Nội dung thuyết minh mới",
            )
        ),
        admin,
    )
    assert updated is not None

    restarted_service = CityEchoService(PersistentStore(database_url))
    persisted = restarted_service.find_poi(poi.id)
    assert persisted is not None
    assert persisted.translation.name == "POI đã cập nhật"


def test_service_uploads_media_and_persists_url(tmp_path, monkeypatch):
    monkeypatch.setenv("CITYECHO_MEDIA_DIR", str(tmp_path))
    service = CityEchoService(PersistentStore())
    admin = service.user_by_email("admin@cityecho.vn")
    assert admin is not None

    updated = service.upload_media(
        "sgu-main",
        "images",
        "campus.png",
        "image/png",
        b"png-data",
        admin,
    )

    assert updated is not None
    assert updated.image_url.startswith("/media/uploads/sgu-main/images-")
    assert len(list((tmp_path / "uploads" / "sgu-main").glob("*.png"))) == 1


def test_persistent_analytics_track_start_completion_source_duration_and_timeline(tmp_path):
    service = CityEchoService(
        PersistentStore(f"sqlite:///{tmp_path / 'cityecho.db'}")
    )

    start = NarrationEvent(
        event_id="analytics-start",
        poi_id="sgu-main",
        source="QR",
        event_type="start",
        session_id="analytics-test",
    )
    finish = NarrationEvent(
        event_id="analytics-finish",
        poi_id="sgu-main",
        source="QR",
        event_type="finish",
        duration_seconds=42,
        completed=True,
        session_id="analytics-test",
    )
    interrupted_start = NarrationEvent(
        event_id="analytics-interrupted-start",
        poi_id="sgu-main",
        source="MANUAL",
        event_type="start",
        session_id="analytics-test",
    )
    interrupted_finish = NarrationEvent(
        event_id="analytics-interrupted-finish",
        poi_id="sgu-main",
        source="MANUAL",
        event_type="finish",
        duration_seconds=15,
        completed=False,
        session_id="analytics-test",
    )
    assert service.record_event(start) is None
    assert service.record_event(finish) is None
    assert service.record_event(interrupted_start) is None
    assert service.record_event(interrupted_finish) is None

    overview = service.analytics_overview()
    timeline = service.events_timeline()

    assert overview["total_plays"] == 2
    assert overview["completed_plays"] == 1
    assert overview["completion_rate"] == 50
    assert overview["total_duration"] == 57
    assert overview["sources"]["QR"] == 1
    assert overview["top_pois"][0]["poi_id"] == "sgu-main"
    assert overview["top_pois"][0]["plays"] == 2
    assert sum(day["plays"] for day in timeline) == 2
