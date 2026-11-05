from __future__ import annotations

import os
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from math import atan2, cos, radians, sin, sqrt
from typing import Any, Literal
from uuid import uuid4

import jwt
from passlib.context import CryptContext

from app.schemas import (
    NarrationEvent,
    Poi,
    PoiInput,
    PoiStatus,
    PoiUpdate,
    Role,
    Translation,
    User,
)
from app.file_storage import save_media_file
from app.seed import SEED_POIS
from app.storage import VISITOR_ACTIVE_WINDOW, PersistentStore


class CityEchoService:
    """Business rules and application state, independent of HTTP routes."""

    def __init__(self, store: PersistentStore | None = None):
        self.store = store or PersistentStore()
        self.secret = os.getenv("CITYECHO_JWT_SECRET") or "cityecho-local-development-secret"
        self.password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.pois = {item_id: Poi.model_validate(item) for item_id, item in SEED_POIS.items()}
        self.events: list[NarrationEvent] = []
        self.audit_entries: list[dict[str, Any]] = []
        self.visitor_sessions: dict[str, dict[str, Any]] = {}
        self.users = self._default_users()
        self._load_persistent_state()

    def _default_users(self) -> dict[str, tuple[User, str]]:
        admin_email = os.getenv("CITYECHO_ADMIN_EMAIL", "admin@cityecho.vn")
        editor_email = os.getenv("CITYECHO_EDITOR_EMAIL", "editor@cityecho.vn")
        defaults = (
            (
                User(
                    id="u-admin",
                    full_name=os.getenv("CITYECHO_ADMIN_NAME", "CityEcho Admin"),
                    email=admin_email,
                    role=Role.ADMIN,
                ),
                os.getenv("CITYECHO_ADMIN_PASSWORD", "admin123"),
            ),
            (
                User(
                    id="u-editor",
                    full_name=os.getenv("CITYECHO_EDITOR_NAME", "Biên tập viên"),
                    email=editor_email,
                    role=Role.EDITOR,
                ),
                os.getenv("CITYECHO_EDITOR_PASSWORD", "editor123"),
            ),
        )
        return {
            user.email: (user, self.password_context.hash(password))
            for user, password in defaults
        }

    def _load_persistent_state(self) -> None:
        if not self.store.enabled:
            return

        stored_pois = self.store.load_pois()
        if stored_pois:
            self.pois = {item["id"]: Poi.model_validate(item) for item in stored_pois}
        else:
            for poi in self.pois.values():
                self.store.save_poi(poi.model_dump())

        self.events = [
            NarrationEvent.model_validate(item) for item in self.store.load_events()
        ]
        self.audit_entries = self.store.load_audits()
        stored_users = self.store.load_users()
        if stored_users:
            self.users = {
                item["email"]: (
                    User(
                        id=item["id"],
                        full_name=item["full_name"],
                        email=item["email"],
                        role=Role(item["role"]),
                        is_active=item["is_active"],
                    ),
                    item["password_hash"],
                )
                for item in stored_users
            }
        else:
            for user, password_hash in self.users.values():
                self.store.save_user(
                    {
                        "id": user.id,
                        "full_name": user.full_name,
                        "email": user.email,
                        "role": user.role.value,
                        "password_hash": password_hash,
                        "is_active": user.is_active,
                    }
                )

    def authenticate(self, email: str, password: str) -> User | None:
        record = self.users.get(email)
        if not record or not self.password_context.verify(password, record[1]):
            return None
        return record[0]

    def token_for(self, user: User) -> str:
        return jwt.encode(
            {
                "sub": user.email,
                "exp": datetime.now(timezone.utc).timestamp() + 8 * 60 * 60,
            },
            self.secret,
            algorithm="HS256",
        )

    def user_for_token(self, token: str) -> User | None:
        try:
            email = jwt.decode(token, self.secret, algorithms=["HS256"])["sub"]
            user = self.users[email][0]
        except (jwt.PyJWTError, KeyError):
            return None
        return user if user.is_active else None

    def user_by_email(self, email: str) -> User | None:
        record = self.users.get(email)
        return record[0] if record else None

    def record_visitor_heartbeat(
        self, device_id: str, path: str, source: str
    ) -> None:
        self.store.record_visitor_heartbeat(
            {"device_id": device_id, "path": path, "source": source}
        )
        if not self.store.enabled:
            now = datetime.now(timezone.utc)
            session = self.visitor_sessions.get(device_id)
            if session:
                session.update(last_seen_at=now, last_path=path, is_active=True)
            else:
                self.visitor_sessions[device_id] = {
                    "device_id": device_id,
                    "first_seen_at": now,
                    "last_seen_at": now,
                    "last_path": path,
                    "entry_source": source,
                    "is_active": True,
                }

    def visitor_session_overview(self) -> dict[str, Any]:
        if self.store.enabled:
            sessions = self.store.list_visitor_sessions(limit=100)
            active_count = self.store.count_active_visitor_sessions()
        else:
            now = datetime.now(timezone.utc)
            active_since = now - VISITOR_ACTIVE_WINDOW
            sessions = []
            for record in self.visitor_sessions.values():
                record["is_active"] = record["last_seen_at"] >= active_since
                sessions.append(
                    {
                        **record,
                        "first_seen_at": record["first_seen_at"].isoformat(),
                        "last_seen_at": record["last_seen_at"].isoformat(),
                    }
                )
            sessions.sort(key=lambda record: record["last_seen_at"], reverse=True)
            active_count = sum(1 for session in self.visitor_sessions.values() if session["is_active"])
            sessions = sessions[:100]
        return {"active_count": active_count, "sessions": sessions}

    def list_categories(self) -> list[dict[str, str]]:
        categories = self.store.list_categories()
        if categories:
            return categories
        slugs = sorted(
            {
                poi.category
                for poi in self.pois.values()
                if poi.status == PoiStatus.PUBLISHED
            }
        )
        return [
            {"slug": slug, "label_vi": slug.replace("-", " ").title(), "label_en": slug}
            for slug in slugs
        ]

    def list_public_pois(
        self, search: str, category: str, page: int, limit: int, lang: str = "vi"
    ) -> dict[str, Any]:
        items = [
            self.poi_in_language(poi, lang)
            for poi in self.pois.values()
            if poi.status == PoiStatus.PUBLISHED
        ]
        if search:
            needle = search.lower()
            items = [
                poi
                for poi in items
                if needle in poi.translation.name.lower()
                or needle in poi.translation.description.lower()
            ]
        if category:
            items = [poi for poi in items if poi.category == category]
        start = (page - 1) * limit
        return {
            "items": items[start : start + limit],
            "page": page,
            "limit": limit,
            "total": len(items),
        }

    @staticmethod
    def poi_translations(poi: Poi) -> list[Translation]:
        translations = {item.language_code.lower(): item for item in poi.translations}
        translations.setdefault(poi.translation.language_code.lower(), poi.translation)
        return list(translations.values())

    @classmethod
    def poi_in_language(cls, poi: Poi, lang: str) -> Poi:
        translations = cls.poi_translations(poi)
        by_language = {item.language_code.lower(): item for item in translations}
        requested = lang.strip().lower()
        selected = by_language.get(requested) or by_language.get("vi") or poi.translation
        return poi.model_copy(update={"translation": selected, "translations": translations})

    def available_languages(self) -> list[str]:
        languages = {"vi", "en"}
        for poi in self.pois.values():
            languages.update(
                item.language_code.lower() for item in self.poi_translations(poi)
            )
        return sorted(languages)

    def all_pois(self) -> list[Poi]:
        return list(self.pois.values())

    def find_poi(self, poi_id: str) -> Poi | None:
        return self.pois.get(poi_id)

    @staticmethod
    def distance_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        earth_radius = 6_371_000
        dlat, dlng = radians(lat2 - lat1), radians(lng2 - lng1)
        a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
        return 2 * earth_radius * atan2(sqrt(a), sqrt(1 - a))

    def nearby(
        self, lat: float, lng: float, max_distance_m: float, lang: str = "vi"
    ) -> list[Poi]:
        result = []
        for stored_poi in self.pois.values():
            poi = self.poi_in_language(stored_poi, lang)
            if poi.status != PoiStatus.PUBLISHED:
                continue
            distance = round(self.distance_m(lat, lng, poi.latitude, poi.longitude), 1)
            if distance <= max_distance_m:
                result.append(poi.model_copy(update={"distance_m": distance}))
        return sorted(result, key=lambda poi: (poi.distance_m or 0, -poi.priority))

    def evaluate_geofence(
        self, lat: float, lng: float, lang: str = "vi"
    ) -> dict[str, Any]:
        candidates = [
            poi for poi in self.nearby(lat, lng, 1000, lang)
            if (poi.distance_m or 0) <= poi.radius_m
        ]
        candidates.sort(key=lambda poi: (-poi.priority, poi.distance_m or 0))
        return {
            "candidate": candidates[0] if candidates else None,
            "candidates": candidates,
        }

    def get_published_poi(self, poi_id: str, lang: str = "vi") -> Poi | None:
        poi = self.pois.get(poi_id)
        return (
            self.poi_in_language(poi, lang)
            if poi and poi.status == PoiStatus.PUBLISHED
            else None
        )

    def find_poi_by_qr(self, code: str, lang: str = "vi") -> Poi | None:
        return next(
            (
                self.poi_in_language(poi, lang) for poi in self.pois.values()
                if poi.qr_code == code and poi.status == PoiStatus.PUBLISHED
            ),
            None,
        )

    def record_event(self, event: NarrationEvent) -> Literal["not_found", "invalid"] | None:
        poi = self.get_published_poi(event.poi_id)
        if not poi:
            return "not_found"
        if event.source not in {"GPS", "QR", "MANUAL"} or event.event_type not in {"start", "finish"}:
            return "invalid"
        self.events.append(event)
        self.store.save_event(event.model_dump(mode="json"))
        return None

    def create_poi(self, payload: PoiInput, user: User) -> Poi:
        poi_id = str(uuid4())
        poi = Poi(
            id=poi_id,
            **payload.model_dump(),
            status=PoiStatus.DRAFT,
            qr_code=f"CITYECHO-{poi_id[:8].upper()}",
        )
        poi = poi.model_copy(update={"translations": [poi.translation]})
        return self._persist_poi(poi, user, "CREATE")

    def update_poi(self, poi_id: str, payload: PoiUpdate, user: User) -> Poi | None:
        poi = self.pois.get(poi_id)
        if not poi:
            return None
        updates = payload.model_dump(exclude_unset=True)
        if "translation" in updates and updates["translation"] is not None:
            translation = Translation.model_validate(updates["translation"])
            translations = {
                item.language_code.lower(): item
                for item in self.poi_translations(poi)
            }
            translations[translation.language_code.lower()] = translation
            updates["translations"] = list(translations.values())
            if translation.language_code.lower() == "vi":
                updates["translation"] = translation
            else:
                updates.pop("translation")
        updated = poi.model_copy(update=updates)
        return self._persist_poi(updated, user, "UPDATE")

    def update_media(
        self,
        poi_id: str,
        field: Literal["image_url", "audio_url"],
        url: str,
        user: User,
        duration_seconds: int = 0,
    ) -> Poi | None:
        poi = self.pois.get(poi_id)
        if not poi:
            return None
        changes: dict[str, Any] = {field: url}
        action = "UPLOAD_IMAGE" if field == "image_url" else "UPLOAD_AUDIO"
        if field == "audio_url":
            changes["audio_duration_seconds"] = duration_seconds
        return self._persist_poi(poi.model_copy(update=changes), user, action)

    def upload_media(
        self,
        poi_id: str,
        kind: Literal["images", "audios"],
        filename: str,
        content_type: str | None,
        content: bytes,
        user: User,
        duration_seconds: int = 0,
    ) -> Poi | None:
        if not self.find_poi(poi_id):
            return None
        url, _size = save_media_file(filename, content_type, kind, poi_id, content)
        field: Literal["image_url", "audio_url"] = "image_url" if kind == "images" else "audio_url"
        return self.update_media(poi_id, field, url, user, duration_seconds)

    def submit_poi(self, poi_id: str, user: User) -> tuple[Poi | None, str | None]:
        poi = self.pois.get(poi_id)
        if not poi:
            return None, "Không tìm thấy POI"
        if len(poi.translation.name.strip()) < 2 or len(poi.translation.narration_text.strip()) < 10:
            return None, "POI cần tên và nội dung thuyết minh tối thiểu trước khi gửi duyệt"
        return self._set_status(poi, PoiStatus.PENDING, user), None

    def set_poi_status(
        self, poi_id: str, status: PoiStatus, user: User
    ) -> Poi | None:
        poi = self.pois.get(poi_id)
        if not poi:
            return None
        return self._set_status(poi, status, user)

    def _set_status(self, poi: Poi, status: PoiStatus, user: User) -> Poi:
        return self._persist_poi(poi.model_copy(update={"status": status}), user, status.value)

    def _persist_poi(self, poi: Poi, user: User, action: str) -> Poi:
        self.pois[poi.id] = poi
        self.store.save_poi(poi.model_dump())
        audit = {
            "user": user.email,
            "action": action,
            "entity_id": poi.id,
            "at": datetime.now(timezone.utc).isoformat(),
        }
        self.audit_entries.append(audit)
        self.store.save_audit(audit)
        return poi

    def recent_audits(self) -> list[dict[str, Any]]:
        return self.audit_entries[-100:]

    def analytics_overview(self) -> dict[str, Any]:
        if self.store.enabled:
            summary = self.store.analytics_narration_summary()
            sources = self.store.analytics_by_source()
            top = self.store.analytics_top_pois(limit=5)
        else:
            completed = [event for event in self.events if event.completed]
            started = [event for event in self.events if event.event_type == "start"]
            summary = {
                "total_plays": len(started),
                "completed_plays": len(completed),
                "total_duration": sum(event.duration_seconds for event in completed),
            }
            sources = {
                source: sum(event.source == source for event in started)
                for source in ("GPS", "QR", "MANUAL")
            }
            top = sorted(
                (
                    {
                        "poi_id": poi.id,
                        "name": poi.translation.name,
                        "plays": sum(event.poi_id == poi.id for event in completed),
                    }
                    for poi in self.pois.values()
                ),
                key=lambda item: item["plays"],
                reverse=True,
            )[:5]
        total_plays = summary["total_plays"]
        completed_plays = summary["completed_plays"]
        return {
            "total_plays": total_plays,
            "completed_plays": completed_plays,
            "completion_rate": round(completed_plays / total_plays * 100, 1) if total_plays else 0,
            "total_duration": summary["total_duration"],
            "sources": sources,
            "top_pois": top,
            "total_pois": len(self.pois),
            "published_pois": sum(poi.status == PoiStatus.PUBLISHED for poi in self.pois.values()),
            "draft_pois": sum(poi.status == PoiStatus.DRAFT for poi in self.pois.values()),
            "pending_pois": sum(poi.status == PoiStatus.PENDING for poi in self.pois.values()),
        }

    def poi_stats(self) -> dict[str, list[dict[str, Any]]]:
        by_status: dict[str, int] = {}
        by_category: dict[str, int] = {}
        for poi in self.pois.values():
            by_status[poi.status.value] = by_status.get(poi.status.value, 0) + 1
            by_category[poi.category] = by_category.get(poi.category, 0) + 1
        return {
            "by_status": [
                {"status": status, "count": count}
                for status, count in by_status.items()
            ],
            "by_category": [
                {"category": category, "count": count}
                for category, count in sorted(by_category.items(), key=lambda item: -item[1])
            ],
        }

    def events_timeline(self) -> list[dict[str, Any]]:
        if self.store.enabled:
            return self.store.analytics_events_timeline()
        counts: dict[str, int] = defaultdict(int)
        today = datetime.now(timezone.utc).date()
        for day_offset in range(6, -1, -1):
            counts[(today - timedelta(days=day_offset)).isoformat()] = 0
        for event in self.events:
            if event.event_type == "start":
                day = event.created_at.astimezone(timezone.utc).date().isoformat()
                if day in counts:
                    counts[day] += 1
        return [{"date": day, "plays": count} for day, count in sorted(counts.items())]
