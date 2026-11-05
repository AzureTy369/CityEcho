from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.storage import (
    EventRecord,
    PersistentStore,
    PoiRecord,
    RoleRecord,
    UserRecord,
    VisitorSessionRecord,
)


def test_sqlite_store_persists_poi(tmp_path):
    store = PersistentStore(f"sqlite:///{tmp_path / 'cityecho.db'}")
    payload = {"id": "poi-test", "status": "DRAFT", "translation": {"name": "Kiểm thử"}}
    store.save_poi(payload)
    saved = store.load_pois()[0]
    assert saved["translation"]["name"] == "Kiểm thử"
    assert saved["translations"] == [
        {
            "language_code": "vi",
            "name": "Kiểm thử",
            "description": "",
            "narration_text": "",
        }
    ]


def test_sqlite_store_preserves_multiple_poi_translations(tmp_path):
    store = PersistentStore(f"sqlite:///{tmp_path / 'cityecho.db'}")
    vietnamese = {
        "language_code": "vi",
        "name": "Dinh Độc Lập",
        "description": "Mô tả tiếng Việt",
        "narration_text": "Thuyết minh tiếng Việt",
    }
    english = {
        "language_code": "en",
        "name": "Independence Palace",
        "description": "English description",
        "narration_text": "English narration",
    }
    store.save_poi({
        "id": "poi-multilingual",
        "status": "PUBLISHED",
        "translation": vietnamese,
        "translations": [vietnamese, english],
    })

    saved = store.load_pois()[0]
    assert saved["translation"] == vietnamese
    assert {item["language_code"]: item["name"] for item in saved["translations"]} == {
        "vi": "Dinh Độc Lập",
        "en": "Independence Palace",
    }


def test_sqlite_store_persists_events_and_audits(tmp_path):
    store = PersistentStore(f"sqlite:///{tmp_path / 'cityecho.db'}")
    store.save_poi(
        {
            "id": "poi-test",
            "category": "historical",
            "latitude": 10.0,
            "longitude": 106.0,
            "radius_m": 40,
            "priority": 3,
            "status": "PUBLISHED",
            "translation": {
                "language_code": "vi",
                "name": "POI kiểm thử",
                "description": "",
                "narration_text": "",
            },
        }
    )
    event = {"event_id": "event-test", "poi_id": "poi-test", "completed": True}
    audit = {"user": "admin@cityecho.vn", "action": "CREATE", "entity_id": "poi-test"}
    store.save_event(event)
    store.save_audit(audit)
    assert store.load_events() == [event]
    assert store.load_audits()[0]["action"] == "CREATE"


def test_poi_delete_is_restricted_when_dependent_rows_exist(tmp_path):
    store = PersistentStore(f"sqlite:///{tmp_path / 'cityecho.db'}")
    store.save_poi(
        {
            "id": "poi-protected",
            "category": "historical",
            "latitude": 10.0,
            "longitude": 106.0,
            "radius_m": 40,
            "priority": 3,
            "status": "PUBLISHED",
            "image_url": "/media/poi.png",
            "qr_code": "QR-POI-PROTECTED",
            "translation": {
                "language_code": "vi",
                "name": "POI được bảo vệ",
                "description": "",
                "narration_text": "",
            },
        }
    )
    store.save_event(
        {
            "event_id": "event-protected",
            "poi_id": "poi-protected",
            "source": "QR",
            "event_type": "start",
        }
    )

    with Session(store.engine) as session:
        poi = session.get(PoiRecord, "poi-protected")
        assert poi is not None
        session.delete(poi)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

    with Session(store.engine) as session:
        assert session.get(PoiRecord, "poi-protected") is not None
        assert session.get(EventRecord, "event-protected") is not None


def test_narration_history_restricts_poi_delete_without_content_rows(tmp_path):
    store = PersistentStore(f"sqlite:///{tmp_path / 'cityecho.db'}")
    store.save_poi(
        {
            "id": "poi-with-history",
            "category": "historical",
            "latitude": 10.0,
            "longitude": 106.0,
            "radius_m": 40,
            "priority": 3,
            "status": "PUBLISHED",
        }
    )
    store.save_event(
        {
            "event_id": "event-with-history",
            "poi_id": "poi-with-history",
            "source": "QR",
            "event_type": "start",
        }
    )

    with Session(store.engine) as session:
        poi = session.get(PoiRecord, "poi-with-history")
        assert poi is not None
        session.delete(poi)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()


def test_sqlite_store_persists_users(tmp_path):
    store = PersistentStore(f"sqlite:///{tmp_path / 'cityecho.db'}")
    user = {
        "id": "u-test",
        "full_name": "Người kiểm thử",
        "email": "test@cityecho.vn",
        "role": "editor",
        "password_hash": "hashed-password",
        "is_active": True,
    }
    store.save_user(user)
    assert store.load_users() == [user]


def test_store_seeds_roles_and_links_users(tmp_path):
    store = PersistentStore(f"sqlite:///{tmp_path / 'cityecho.db'}")
    store.save_user(
        {
            "id": "u-admin",
            "full_name": "Admin",
            "email": "admin@example.com",
            "role": "admin",
            "password_hash": "hashed-password",
            "is_active": True,
        }
    )

    with Session(store.engine) as session:
        roles = session.scalars(select(RoleRecord).order_by(RoleRecord.name)).all()
        admin = session.get(UserRecord, "u-admin")

    assert [role.name for role in roles] == ["admin", "editor"]
    assert admin is not None
    assert admin.role_id is not None


def test_sqlite_store_records_and_expires_visitor_sessions(tmp_path):
    store = PersistentStore(f"sqlite:///{tmp_path / 'cityecho.db'}")
    store.record_visitor_heartbeat(
        {
            "device_id": "12345678-1234-4234-8234-123456789abc",
            "path": "/?join=1",
            "source": "QR",
        }
    )

    sessions = store.list_visitor_sessions()

    assert len(sessions) == 1
    assert sessions[0]["entry_source"] == "QR"
    assert sessions[0]["is_active"] is True
    assert sessions[0]["last_path"] == "/?join=1"
    with Session(store.engine) as session:
        record = session.get(VisitorSessionRecord, sessions[0]["device_id"])
        assert record is not None
        record.last_seen_at = datetime.now(timezone.utc) - timedelta(seconds=59)
        session.commit()

    recent = store.list_visitor_sessions()
    assert recent[0]["is_active"] is True

    with Session(store.engine) as session:
        record = session.get(VisitorSessionRecord, sessions[0]["device_id"])
        assert record is not None
        record.last_seen_at = datetime.now(timezone.utc) - timedelta(seconds=61)
        session.commit()

    expired = store.list_visitor_sessions()
    assert expired[0]["is_active"] is False
    assert store.count_active_visitor_sessions() == 0

    store.record_visitor_heartbeat(
        {
            "device_id": sessions[0]["device_id"],
            "path": "/",
            "source": "DIRECT",
        }
    )
    refreshed = store.list_visitor_sessions()
    assert refreshed[0]["is_active"] is True
    assert refreshed[0]["entry_source"] == "QR"
    assert store.count_active_visitor_sessions() == 1
