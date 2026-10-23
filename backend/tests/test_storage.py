from app.storage import PersistentStore


def test_sqlite_store_persists_poi(tmp_path):
    store = PersistentStore(f"sqlite:///{tmp_path / 'cityecho.db'}")
    payload = {"id": "poi-test", "status": "DRAFT", "translation": {"name": "Kiểm thử"}}
    store.save_poi(payload)
    assert store.load_pois() == [payload]


def test_sqlite_store_persists_events_and_audits(tmp_path):
    store = PersistentStore(f"sqlite:///{tmp_path / 'cityecho.db'}")
    event = {"event_id": "event-test", "poi_id": "poi-test", "completed": True}
    audit = {"user": "admin@cityecho.vn", "action": "CREATE", "entity_id": "poi-test"}
    store.save_event(event)
    store.save_audit(audit)
    assert store.load_events() == [event]
    assert store.load_audits()[0]["action"] == "CREATE"
