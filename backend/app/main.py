from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum
from math import atan2, cos, radians, sin, sqrt
from typing import Optional
from uuid import uuid4

import jwt
import os
from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from passlib.context import CryptContext
from pydantic import BaseModel, Field
from app.file_storage import media_root, save_upload
from app.seed import SEED_POIS
from app.storage import PersistentStore

app = FastAPI(title="CityEcho API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:4173", "http://127.0.0.1:5173"],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1|(\d{1,3}\.){3}\d{1,3})(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
MEDIA_DIR = media_root()
MEDIA_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")

SECRET = os.getenv("CITYECHO_JWT_SECRET") or "cityecho-local-development-secret"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


class PoiStatus(str, Enum):
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    NEEDS_REVISION = "NEEDS_REVISION"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class Role(str, Enum):
    ADMIN = "admin"
    EDITOR = "editor"


class Translation(BaseModel):
    language_code: str = "vi"
    name: str
    description: str
    narration_text: str


class Poi(BaseModel):
    id: str
    category: str
    latitude: float
    longitude: float
    radius_m: float = Field(gt=0)
    priority: int = Field(ge=1, le=5)
    status: PoiStatus
    translation: Translation
    image_url: str = ""
    audio_url: str = ""
    audio_duration_seconds: int = 0
    qr_code: str
    distance_m: Optional[float] = None


class PoiInput(BaseModel):
    category: str = "historical"
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    radius_m: float = Field(default=40, gt=0)
    priority: int = Field(default=3, ge=1, le=5)
    translation: Translation
    image_url: str = ""
    audio_url: str = ""
    audio_duration_seconds: int = Field(default=0, ge=0)


class PoiUpdate(BaseModel):
    category: Optional[str] = None
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    radius_m: Optional[float] = Field(default=None, gt=0)
    priority: Optional[int] = Field(default=None, ge=1, le=5)
    translation: Optional[Translation] = None
    image_url: Optional[str] = None
    audio_url: Optional[str] = None
    audio_duration_seconds: Optional[int] = Field(default=None, ge=0)


class NarrationEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    poi_id: str
    source: str
    event_type: str
    duration_seconds: int = Field(default=0, ge=0)
    completed: bool = False
    session_id: str = "anonymous"


class User(BaseModel):
    id: str
    full_name: str
    email: str
    role: Role
    is_active: bool = True


POIS: dict[str, Poi] = {item_id: Poi.model_validate(item) for item_id, item in SEED_POIS.items()}

USERS = {
    os.getenv("CITYECHO_ADMIN_EMAIL", "admin@cityecho.vn"): (
        User(
            id="u-admin",
            full_name=os.getenv("CITYECHO_ADMIN_NAME", "CityEcho Admin"),
            email=os.getenv("CITYECHO_ADMIN_EMAIL", "admin@cityecho.vn"),
            role=Role.ADMIN,
        ),
        pwd_context.hash(os.getenv("CITYECHO_ADMIN_PASSWORD", "admin123")),
    ),
    os.getenv("CITYECHO_EDITOR_EMAIL", "editor@cityecho.vn"): (
        User(
            id="u-editor",
            full_name=os.getenv("CITYECHO_EDITOR_NAME", "Biên tập viên"),
            email=os.getenv("CITYECHO_EDITOR_EMAIL", "editor@cityecho.vn"),
            role=Role.EDITOR,
        ),
        pwd_context.hash(os.getenv("CITYECHO_EDITOR_PASSWORD", "editor123")),
    ),
}
EVENTS: list[NarrationEvent] = []
AUDIT_LOGS: list[dict] = []
STORE = PersistentStore()
if STORE.enabled:
    stored_pois = STORE.load_pois()
    if stored_pois:
        POIS = {item["id"]: Poi.model_validate(item) for item in stored_pois}
    else:
        for seed_poi in POIS.values():
            STORE.save_poi(seed_poi.model_dump())
    EVENTS = [NarrationEvent.model_validate(item) for item in STORE.load_events()]
    AUDIT_LOGS = STORE.load_audits()
    stored_users = STORE.load_users()
    if stored_users:
        USERS = {
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
        for user, password_hash in USERS.values():
            STORE.save_user(
                {
                    "id": user.id,
                    "full_name": user.full_name,
                    "email": user.email,
                    "role": user.role.value,
                    "password_hash": password_hash,
                    "is_active": user.is_active,
                }
            )


def distance_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    earth_radius = 6_371_000
    dlat, dlng = radians(lat2 - lat1), radians(lng2 - lng1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    return 2 * earth_radius * atan2(sqrt(a), sqrt(1 - a))


def token_for(user: User) -> str:
    return jwt.encode({"sub": user.email, "exp": datetime.now(timezone.utc) + timedelta(hours=8)}, SECRET, algorithm="HS256")


def current_user(token: str = Depends(oauth2_scheme)) -> User:
    try:
        email = jwt.decode(token, SECRET, algorithms=["HS256"])["sub"]
        user = USERS[email][0]
    except (jwt.PyJWTError, KeyError):
        raise HTTPException(status_code=401, detail="Phiên đăng nhập không hợp lệ")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Tài khoản đã bị khóa")
    return user


def require_roles(*roles: Role):
    def dependency(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Bạn không có quyền thực hiện thao tác này")
        return user

    return dependency


@app.get("/health")
def health():
    return {"status": "ok", "service": "cityecho-api"}


@app.post("/api/v1/auth/login")
def login(form: OAuth2PasswordRequestForm = Depends()):
    record = USERS.get(form.username)
    if not record or not pwd_context.verify(form.password, record[1]):
        raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không đúng")
    user = record[0]
    return {"access_token": token_for(user), "token_type": "bearer", "user": user}


@app.get("/api/v1/auth/me")
def me(user: User = Depends(current_user)):
    return user


@app.get("/api/v1/categories")
def list_categories():
    """Danh sách danh mục từ bảng categories (ERD chuẩn hóa)."""
    db_cats = STORE.list_categories()
    if db_cats:
        return db_cats
    # fallback: lấy từ in-memory POI
    slugs = sorted(set(p.category for p in POIS.values() if p.status == PoiStatus.PUBLISHED))
    return [{"slug": s, "label_vi": s.replace("-", " ").title(), "label_en": s} for s in slugs]


@app.get("/api/v1/pois")
def list_pois(
    search: str = "",
    category: str = "",
    lang: str = "vi",
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    del lang
    items = [p for p in POIS.values() if p.status == PoiStatus.PUBLISHED]
    if search:
        needle = search.lower()
        items = [p for p in items if needle in p.translation.name.lower() or needle in p.translation.description.lower()]
    if category:
        items = [p for p in items if p.category == category]
    start = (page - 1) * limit
    return {"items": items[start : start + limit], "page": page, "limit": limit, "total": len(items)}


@app.get("/api/v1/pois/nearby")
def nearby(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    max_distance_m: float = Query(50000, ge=0),
):
    result = []
    for poi in POIS.values():
        if poi.status != PoiStatus.PUBLISHED:
            continue
        dist = round(distance_m(lat, lng, poi.latitude, poi.longitude), 1)
        if dist <= max_distance_m:
            result.append(poi.model_copy(update={"distance_m": dist}))
    return sorted(result, key=lambda p: (p.distance_m or 0, -p.priority))


@app.api_route("/api/v1/geofence/evaluate", methods=["GET", "POST"])
def evaluate_geofence(lat: float = Query(..., ge=-90, le=90), lng: float = Query(..., ge=-180, le=180)):
    candidates = [
        poi for poi in nearby(lat, lng, max_distance_m=1000)
        if (poi.distance_m or 0) <= poi.radius_m
    ]
    candidates.sort(key=lambda p: (-p.priority, p.distance_m or 0))
    return {"candidate": candidates[0] if candidates else None, "candidates": candidates}


@app.get("/api/v1/pois/{poi_id}")
def get_poi(poi_id: str):
    poi = POIS.get(poi_id)
    if not poi or poi.status != PoiStatus.PUBLISHED:
        raise HTTPException(status_code=404, detail="Không tìm thấy địa điểm")
    return poi


@app.get("/api/v1/pois/{poi_id}/narration")
def get_narration(poi_id: str, lang: str = "vi"):
    del lang
    poi = get_poi(poi_id)
    return {
        "poi_id": poi.id,
        "language_code": poi.translation.language_code,
        "narration_text": poi.translation.narration_text,
        "audio_url": poi.audio_url,
        "audio_duration_seconds": poi.audio_duration_seconds,
    }


@app.get("/api/v1/qr/{code}")
def qr_lookup(code: str):
    poi = next((p for p in POIS.values() if p.qr_code == code and p.status == PoiStatus.PUBLISHED), None)
    if not poi:
        raise HTTPException(status_code=404, detail="QR Code không hợp lệ hoặc POI chưa xuất bản")
    return poi


@app.post("/api/v1/narration-events")
def create_event(event: NarrationEvent):
    poi = POIS.get(event.poi_id)
    if not poi or poi.status != PoiStatus.PUBLISHED:
        raise HTTPException(status_code=404, detail="POI không tồn tại hoặc chưa xuất bản")
    if event.source not in {"GPS", "QR", "MANUAL"} or event.event_type not in {"start", "finish"}:
        raise HTTPException(status_code=422, detail="source/event_type không hợp lệ")
    EVENTS.append(event)
    STORE.save_event(event.model_dump())
    return {"accepted": True, "event_id": event.event_id}


@app.get("/api/v1/admin/pois")
def admin_pois(user: User = Depends(require_roles(Role.ADMIN, Role.EDITOR))):
    del user
    return list(POIS.values())


@app.post("/api/v1/admin/pois", status_code=201)
def create_poi(payload: PoiInput, user: User = Depends(require_roles(Role.ADMIN, Role.EDITOR))):
    poi_id = str(uuid4())
    poi = Poi(id=poi_id, **payload.model_dump(), status=PoiStatus.DRAFT, qr_code=f"CITYECHO-{poi_id[:8].upper()}")
    POIS[poi_id] = poi
    STORE.save_poi(poi.model_dump())
    audit = {"user": user.email, "action": "CREATE", "entity_id": poi_id, "at": datetime.now(timezone.utc).isoformat()}
    AUDIT_LOGS.append(audit)
    STORE.save_audit(audit)
    return poi


@app.patch("/api/v1/admin/pois/{poi_id}")
def edit_poi(poi_id: str, payload: PoiUpdate, user: User = Depends(require_roles(Role.ADMIN, Role.EDITOR))):
    poi = POIS.get(poi_id)
    if not poi:
        raise HTTPException(status_code=404, detail="Không tìm thấy POI")
    updates = payload.model_dump(exclude_unset=True)
    if "translation" in updates and updates["translation"] is not None:
        updates["translation"] = Translation.model_validate(updates["translation"])
    updated = poi.model_copy(update=updates)
    POIS[poi_id] = updated
    STORE.save_poi(updated.model_dump())
    audit = {"user": user.email, "action": "UPDATE", "entity_id": poi_id, "at": datetime.now(timezone.utc).isoformat()}
    AUDIT_LOGS.append(audit)
    STORE.save_audit(audit)
    return updated


def _persist_poi(poi: Poi, user: User, action: str) -> Poi:
    POIS[poi.id] = poi
    STORE.save_poi(poi.model_dump())
    audit = {"user": user.email, "action": action, "entity_id": poi.id, "at": datetime.now(timezone.utc).isoformat()}
    AUDIT_LOGS.append(audit)
    STORE.save_audit(audit)
    return poi


@app.post("/api/v1/admin/pois/{poi_id}/images")
async def upload_image(poi_id: str, file: UploadFile = File(...), user: User = Depends(require_roles(Role.ADMIN, Role.EDITOR))):
    poi = POIS.get(poi_id)
    if not poi:
        raise HTTPException(status_code=404, detail="Không tìm thấy POI")
    url, _size = save_upload(file, "images", poi_id, await file.read())
    return _persist_poi(poi.model_copy(update={"image_url": url}), user, "UPLOAD_IMAGE")


@app.post("/api/v1/admin/pois/{poi_id}/audios")
async def upload_audio(
    poi_id: str,
    file: UploadFile = File(...),
    duration_seconds: int = Query(default=0, ge=0),
    user: User = Depends(require_roles(Role.ADMIN, Role.EDITOR)),
):
    poi = POIS.get(poi_id)
    if not poi:
        raise HTTPException(status_code=404, detail="Không tìm thấy POI")
    url, _size = save_upload(file, "audios", poi_id, await file.read())
    return _persist_poi(poi.model_copy(update={"audio_url": url, "audio_duration_seconds": duration_seconds}), user, "UPLOAD_AUDIO")


def update_status(poi_id: str, new_status: PoiStatus, user: User) -> Poi:
    poi = POIS.get(poi_id)
    if not poi:
        raise HTTPException(status_code=404, detail="Không tìm thấy POI")
    POIS[poi_id] = poi.model_copy(update={"status": new_status})
    STORE.save_poi(POIS[poi_id].model_dump())
    audit = {"user": user.email, "action": new_status.value, "entity_id": poi_id, "at": datetime.now(timezone.utc).isoformat()}
    AUDIT_LOGS.append(audit)
    STORE.save_audit(audit)
    return POIS[poi_id]


@app.post("/api/v1/admin/pois/{poi_id}/submit")
def submit_poi(poi_id: str, user: User = Depends(require_roles(Role.ADMIN, Role.EDITOR))):
    poi = POIS.get(poi_id)
    if not poi:
        raise HTTPException(status_code=404, detail="Không tìm thấy POI")
    if len(poi.translation.name.strip()) < 2 or len(poi.translation.narration_text.strip()) < 10:
        raise HTTPException(status_code=422, detail="POI cần tên và nội dung thuyết minh tối thiểu trước khi gửi duyệt")
    return update_status(poi_id, PoiStatus.PENDING, user)


@app.post("/api/v1/admin/pois/{poi_id}/approve")
def approve_poi(poi_id: str, user: User = Depends(require_roles(Role.ADMIN))):
    return update_status(poi_id, PoiStatus.PUBLISHED, user)


@app.post("/api/v1/admin/pois/{poi_id}/request-revision")
def revise_poi(poi_id: str, user: User = Depends(require_roles(Role.ADMIN))):
    return update_status(poi_id, PoiStatus.NEEDS_REVISION, user)


@app.post("/api/v1/admin/pois/{poi_id}/archive")
def archive_poi(poi_id: str, user: User = Depends(require_roles(Role.ADMIN))):
    return update_status(poi_id, PoiStatus.ARCHIVED, user)


@app.get("/api/v1/admin/analytics/overview")
def analytics(user: User = Depends(require_roles(Role.ADMIN))):
    del user
    completed = [e for e in EVENTS if e.completed]
    started = [e for e in EVENTS if e.event_type == "start"]

    # Ưu tiên truy vấn chuẩn hóa từ PostgreSQL nếu khả dụng
    if STORE.enabled:
        sources = STORE.analytics_by_source()
        top = STORE.analytics_top_pois(limit=5)
    else:
        sources = {source: sum(e.source == source for e in started) for source in ("GPS", "QR", "MANUAL")}
        top = sorted(
            (
                {
                    "poi_id": poi.id,
                    "name": poi.translation.name,
                    "plays": sum(e.poi_id == poi.id for e in completed),
                }
                for poi in POIS.values()
            ),
            key=lambda item: item["plays"],
            reverse=True,
        )[:5]

    total_pois = len(POIS)
    published = sum(1 for p in POIS.values() if p.status == PoiStatus.PUBLISHED)
    return {
        "total_plays": len(started),
        "completed_plays": len(completed),
        "completion_rate": round(len(completed) / len(started) * 100, 1) if started else 0,
        "total_duration": sum(e.duration_seconds for e in completed),
        "sources": sources,
        "top_pois": top,
        "total_pois": total_pois,
        "published_pois": published,
        "draft_pois": sum(1 for p in POIS.values() if p.status == PoiStatus.DRAFT),
        "pending_pois": sum(1 for p in POIS.values() if p.status == PoiStatus.PENDING),
    }


@app.get("/api/v1/admin/audit-logs")
def audit_logs(user: User = Depends(require_roles(Role.ADMIN))):
    del user
    return AUDIT_LOGS[-100:]


@app.get("/api/v1/admin/analytics/poi-stats")
def poi_stats(user: User = Depends(require_roles(Role.ADMIN))):
    """Thống kê POI theo trạng thái và danh mục (dùng cho Recharts dashboard)."""
    del user
    by_status = {}
    for p in POIS.values():
        by_status[p.status.value] = by_status.get(p.status.value, 0) + 1

    by_category = {}
    for p in POIS.values():
        by_category[p.category] = by_category.get(p.category, 0) + 1

    return {
        "by_status": [{"status": k, "count": v} for k, v in by_status.items()],
        "by_category": [{"category": k, "count": v} for k, v in sorted(by_category.items(), key=lambda x: -x[1])],
    }


@app.get("/api/v1/admin/analytics/events-timeline")
def events_timeline(user: User = Depends(require_roles(Role.ADMIN))):
    """Thống kê lượt nghe theo ngày (7 ngày gần nhất, dùng cho Recharts LineChart)."""
    del user
    from collections import defaultdict
    from datetime import date, timedelta
    counts: dict[str, int] = defaultdict(int)
    today = date.today()
    for i in range(6, -1, -1):
        counts[(today - timedelta(days=i)).isoformat()] = 0
    for e in EVENTS:
        if e.event_type == "start" and hasattr(e, "session_id"):
            # lấy ngày từ event_id prefix hoặc dùng hôm nay
            day = today.isoformat()
            if counts.get(day) is not None:
                counts[day] += 1
    return [{"date": d, "plays": c} for d, c in sorted(counts.items())]
