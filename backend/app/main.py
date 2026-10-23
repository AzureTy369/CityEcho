from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum
from math import atan2, cos, radians, sin, sqrt
from typing import Optional
from uuid import uuid4

import jwt
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from pydantic import BaseModel, Field

app = FastAPI(title="CityEcho API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:4173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET = "cityecho-demo-secret-change-in-production"
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


def _poi(
    id: str,
    category: str,
    name: str,
    description: str,
    narration: str,
    lat: float,
    lng: float,
    priority: int,
    qr: str,
    image: str,
) -> Poi:
    return Poi(
        id=id,
        category=category,
        latitude=lat,
        longitude=lng,
        radius_m=40,
        priority=priority,
        status=PoiStatus.PUBLISHED,
        translation=Translation(name=name, description=description, narration_text=narration),
        qr_code=qr,
        image_url=image,
    )


POIS: dict[str, Poi] = {
    "sgu-main": _poi(
        "sgu-main",
        "campus",
        "Trường Đại học Sài Gòn",
        "Không gian giáo dục lâu đời giữa lòng Quận 5, gắn với nhiều lớp ký ức đô thị.",
        "Chào mừng bạn đến với CityEcho. Đây là điểm khởi đầu để khám phá những câu chuyện quanh SGU.",
        10.7591,
        106.6823,
        5,
        "CITYECHO-SGU",
        "https://images.unsplash.com/photo-1564981797816-1043664bf78d?auto=format&fit=crop&w=1200&q=80",
    ),
    "chua-ba": _poi(
        "chua-ba",
        "religious",
        "Chùa Bà Thiên Hậu",
        "Ngôi chùa người Hoa nổi tiếng với kiến trúc cổ và các mảng chạm tinh xảo.",
        "Bạn đang đứng trước Chùa Bà Thiên Hậu, một điểm giao thoa văn hóa đặc sắc của khu Chợ Lớn.",
        10.7548,
        106.6639,
        5,
        "CITYECHO-THIENHAU",
        "https://images.unsplash.com/photo-1548013146-72479768bada?auto=format&fit=crop&w=1200&q=80",
    ),
    "cho-lon": _poi(
        "cho-lon",
        "market",
        "Chợ Bình Tây",
        "Biểu tượng thương mại của Chợ Lớn với tháp đồng hồ và sân trong rộng.",
        "Chợ Bình Tây được xây dựng đầu thế kỷ 20, là nơi lưu giữ nhịp sống thương hồ của thành phố.",
        10.7527,
        106.6504,
        4,
        "CITYECHO-BINHTAY",
        "https://images.unsplash.com/photo-1518005020951-eccb494ad742?auto=format&fit=crop&w=1200&q=80",
    ),
    "ho-con-rua": _poi(
        "ho-con-rua",
        "public-space",
        "Hồ Con Rùa",
        "Không gian công cộng quen thuộc, nơi các tuyến đường trung tâm gặp nhau.",
        "Hồ Con Rùa là một lát cắt đời sống đô thị, đặc biệt sôi động vào buổi tối.",
        10.7827,
        106.6953,
        3,
        "CITYECHO-HOCRUA",
        "https://images.unsplash.com/photo-1523731407965-2430cd12f5e4?auto=format&fit=crop&w=1200&q=80",
    ),
}

USERS = {
    "admin@cityecho.vn": (User(id="u-admin", full_name="CityEcho Admin", email="admin@cityecho.vn", role=Role.ADMIN), pwd_context.hash("admin123")),
    "editor@cityecho.vn": (User(id="u-editor", full_name="Biên tập viên", email="editor@cityecho.vn", role=Role.EDITOR), pwd_context.hash("editor123")),
}
EVENTS: list[NarrationEvent] = []
AUDIT_LOGS: list[dict] = []


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


@app.get("/api/v1/pois/{poi_id}")
def get_poi(poi_id: str):
    poi = POIS.get(poi_id)
    if not poi or poi.status != PoiStatus.PUBLISHED:
        raise HTTPException(status_code=404, detail="Không tìm thấy địa điểm")
    return poi


@app.get("/api/v1/pois/nearby")
def nearby(lat: float = Query(..., ge=-90, le=90), lng: float = Query(..., ge=-180, le=180)):
    result = []
    for poi in POIS.values():
        if poi.status != PoiStatus.PUBLISHED:
            continue
        item = poi.model_copy(update={"distance_m": round(distance_m(lat, lng, poi.latitude, poi.longitude), 1)})
        if item.distance_m <= 5000:
            result.append(item)
    return sorted(result, key=lambda p: (-p.priority, p.distance_m or 0))


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
    return {"accepted": True, "event_id": event.event_id}


@app.post("/api/v1/geofence/evaluate")
def evaluate_geofence(lat: float = Query(...), lng: float = Query(...)):
    candidates = [p for p in nearby(lat, lng) if p.distance_m is not None and p.distance_m <= p.radius_m]
    return {"candidate": candidates[0] if candidates else None, "candidates": candidates}


@app.get("/api/v1/admin/pois")
def admin_pois(user: User = Depends(require_roles(Role.ADMIN, Role.EDITOR))):
    del user
    return list(POIS.values())


@app.post("/api/v1/admin/pois", status_code=201)
def create_poi(payload: PoiInput, user: User = Depends(require_roles(Role.ADMIN, Role.EDITOR))):
    poi_id = str(uuid4())
    poi = Poi(id=poi_id, **payload.model_dump(), status=PoiStatus.DRAFT, qr_code=f"CITYECHO-{poi_id[:8].upper()}")
    POIS[poi_id] = poi
    AUDIT_LOGS.append({"user": user.email, "action": "CREATE", "entity_id": poi_id, "at": datetime.now(timezone.utc).isoformat()})
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
    AUDIT_LOGS.append({"user": user.email, "action": "UPDATE", "entity_id": poi_id, "at": datetime.now(timezone.utc).isoformat()})
    return updated


def update_status(poi_id: str, new_status: PoiStatus, user: User) -> Poi:
    poi = POIS.get(poi_id)
    if not poi:
        raise HTTPException(status_code=404, detail="Không tìm thấy POI")
    POIS[poi_id] = poi.model_copy(update={"status": new_status})
    AUDIT_LOGS.append({"user": user.email, "action": new_status.value, "entity_id": poi_id, "at": datetime.now(timezone.utc).isoformat()})
    return POIS[poi_id]


@app.post("/api/v1/admin/pois/{poi_id}/submit")
def submit_poi(poi_id: str, user: User = Depends(require_roles(Role.ADMIN, Role.EDITOR))):
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
    sources = {source: sum(e.source == source for e in started) for source in ("GPS", "QR", "MANUAL")}
    top = sorted(
        ({"poi_id": poi.id, "name": poi.translation.name, "plays": sum(e.poi_id == poi.id for e in completed)} for poi in POIS.values()),
        key=lambda item: item["plays"],
        reverse=True,
    )
    return {
        "total_plays": len(started),
        "completed_plays": len(completed),
        "completion_rate": round(len(completed) / len(started) * 100, 1) if started else 0,
        "total_duration": sum(e.duration_seconds for e in completed),
        "sources": sources,
        "top_pois": top[:5],
    }


@app.get("/api/v1/admin/audit-logs")
def audit_logs(user: User = Depends(require_roles(Role.ADMIN))):
    del user
    return AUDIT_LOGS[-100:]
