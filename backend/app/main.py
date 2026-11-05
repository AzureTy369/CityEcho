from __future__ import annotations

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles

import jwt

from app.file_storage import media_root
from app.schemas import (
    DeviceHeartbeat,
    NarrationEvent,
    Poi,
    PoiInput,
    PoiStatus,
    PoiUpdate,
    Role,
    Translation,
    User,
)
from app.services.cityecho_service import CityEchoService

app = FastAPI(title="CityEcho API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:4173", "http://127.0.0.1:5173"],
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
MEDIA_DIR = media_root()
MEDIA_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")

SERVICE = CityEchoService()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def distance_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    return SERVICE.distance_m(lat1, lng1, lat2, lng2)


def current_user(token: str = Depends(oauth2_scheme)) -> User:
    try:
        email = jwt.decode(token, SERVICE.secret, algorithms=["HS256"])["sub"]
    except (jwt.PyJWTError, KeyError):
        raise HTTPException(status_code=401, detail="Phiên đăng nhập không hợp lệ")
    user = SERVICE.user_by_email(email)
    if not user:
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


@app.post("/api/v1/visitor-sessions/heartbeat")
def visitor_heartbeat(payload: DeviceHeartbeat):
    SERVICE.record_visitor_heartbeat(payload.device_id, payload.path, payload.source)
    return {"accepted": True}


@app.post("/api/v1/auth/login")
def login(form: OAuth2PasswordRequestForm = Depends()):
    user = SERVICE.authenticate(form.username, form.password)
    if not user:
        raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không đúng")
    return {
        "access_token": SERVICE.token_for(user),
        "token_type": "bearer",
        "user": user,
    }


@app.get("/api/v1/auth/me")
def me(user: User = Depends(current_user)):
    return user


@app.get("/api/v1/categories")
def list_categories():
    return SERVICE.list_categories()

@app.get("/api/v1/languages")
def list_languages():
    return SERVICE.available_languages()


@app.get("/api/v1/pois")
def list_pois(
    search: str = "",
    category: str = "",
    lang: str = "vi",
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    return SERVICE.list_public_pois(search, category, page, limit, lang)


@app.get("/api/v1/pois/nearby")
def nearby(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    max_distance_m: float = Query(50000, ge=0),
    lang: str = "vi",
):
    return SERVICE.nearby(lat, lng, max_distance_m, lang)


@app.api_route("/api/v1/geofence/evaluate", methods=["GET", "POST"])
def evaluate_geofence(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    lang: str = "vi",
):
    return SERVICE.evaluate_geofence(lat, lng, lang)


@app.get("/api/v1/pois/{poi_id}")
def get_poi(poi_id: str, lang: str = "vi"):
    poi = SERVICE.get_published_poi(poi_id, lang)
    if not poi:
        raise HTTPException(status_code=404, detail="Không tìm thấy địa điểm")
    return poi


@app.get("/api/v1/pois/{poi_id}/narration")
def get_narration(poi_id: str, lang: str = "vi"):
    poi = SERVICE.get_published_poi(poi_id, lang)
    if not poi:
        raise HTTPException(status_code=404, detail="Không tìm thấy địa điểm")
    return {
        "poi_id": poi.id,
        "language_code": poi.translation.language_code,
        "narration_text": poi.translation.narration_text,
        "audio_url": poi.audio_url,
        "audio_duration_seconds": poi.audio_duration_seconds,
    }


@app.get("/api/v1/qr/{code}")
def qr_lookup(code: str, lang: str = "vi"):
    poi = SERVICE.find_poi_by_qr(code, lang)
    if not poi:
        raise HTTPException(status_code=404, detail="QR Code không hợp lệ hoặc POI chưa xuất bản")
    return poi


@app.post("/api/v1/narration-events")
def create_event(event: NarrationEvent):
    result = SERVICE.record_event(event)
    if result == "not_found":
        raise HTTPException(status_code=404, detail="POI không tồn tại hoặc chưa xuất bản")
    if result == "invalid":
        raise HTTPException(status_code=422, detail="source/event_type không hợp lệ")
    return {"accepted": True, "event_id": event.event_id}


@app.get("/api/v1/admin/pois")
def admin_pois(user: User = Depends(require_roles(Role.ADMIN, Role.EDITOR))):
    del user
    return SERVICE.all_pois()


@app.post("/api/v1/admin/pois", status_code=201)
def create_poi(payload: PoiInput, user: User = Depends(require_roles(Role.ADMIN, Role.EDITOR))):
    return SERVICE.create_poi(payload, user)


@app.patch("/api/v1/admin/pois/{poi_id}")
def edit_poi(
    poi_id: str,
    payload: PoiUpdate,
    user: User = Depends(require_roles(Role.ADMIN, Role.EDITOR)),
):
    poi = SERVICE.update_poi(poi_id, payload, user)
    if not poi:
        raise HTTPException(status_code=404, detail="Không tìm thấy POI")
    return poi


@app.post("/api/v1/admin/pois/{poi_id}/images")
async def upload_image(
    poi_id: str,
    file: UploadFile = File(...),
    user: User = Depends(require_roles(Role.ADMIN, Role.EDITOR)),
):
    if not SERVICE.find_poi(poi_id):
        raise HTTPException(status_code=404, detail="Không tìm thấy POI")
    poi = SERVICE.upload_media(
        poi_id, "images", file.filename or "", file.content_type, await file.read(), user
    )
    if not poi:
        raise HTTPException(status_code=404, detail="Không tìm thấy POI")
    return poi


@app.post("/api/v1/admin/pois/{poi_id}/audios")
async def upload_audio(
    poi_id: str,
    file: UploadFile = File(...),
    duration_seconds: int = Query(default=0, ge=0),
    user: User = Depends(require_roles(Role.ADMIN, Role.EDITOR)),
):
    if not SERVICE.find_poi(poi_id):
        raise HTTPException(status_code=404, detail="Không tìm thấy POI")
    poi = SERVICE.upload_media(
        poi_id,
        "audios",
        file.filename or "",
        file.content_type,
        await file.read(),
        user,
        duration_seconds,
    )
    if not poi:
        raise HTTPException(status_code=404, detail="Không tìm thấy POI")
    return poi


@app.post("/api/v1/admin/pois/{poi_id}/submit")
def submit_poi(poi_id: str, user: User = Depends(require_roles(Role.ADMIN, Role.EDITOR))):
    if not SERVICE.find_poi(poi_id):
        raise HTTPException(status_code=404, detail="Không tìm thấy POI")
    poi, error = SERVICE.submit_poi(poi_id, user)
    if error:
        raise HTTPException(status_code=422, detail=error)
    return poi


@app.post("/api/v1/admin/pois/{poi_id}/approve")
def approve_poi(poi_id: str, user: User = Depends(require_roles(Role.ADMIN))):
    poi = SERVICE.set_poi_status(poi_id, PoiStatus.PUBLISHED, user)
    if not poi:
        raise HTTPException(status_code=404, detail="Không tìm thấy POI")
    return poi


@app.post("/api/v1/admin/pois/{poi_id}/request-revision")
def revise_poi(poi_id: str, user: User = Depends(require_roles(Role.ADMIN))):
    poi = SERVICE.set_poi_status(poi_id, PoiStatus.NEEDS_REVISION, user)
    if not poi:
        raise HTTPException(status_code=404, detail="Không tìm thấy POI")
    return poi


@app.post("/api/v1/admin/pois/{poi_id}/archive")
def archive_poi(poi_id: str, user: User = Depends(require_roles(Role.ADMIN))):
    poi = SERVICE.set_poi_status(poi_id, PoiStatus.ARCHIVED, user)
    if not poi:
        raise HTTPException(status_code=404, detail="Không tìm thấy POI")
    return poi


@app.get("/api/v1/admin/analytics/overview")
def analytics(user: User = Depends(require_roles(Role.ADMIN))):
    del user
    return SERVICE.analytics_overview()


@app.get("/api/v1/admin/audit-logs")
def audit_logs(user: User = Depends(require_roles(Role.ADMIN))):
    del user
    return SERVICE.recent_audits()


@app.get("/api/v1/admin/analytics/poi-stats")
def poi_stats(user: User = Depends(require_roles(Role.ADMIN))):
    del user
    return SERVICE.poi_stats()


@app.get("/api/v1/admin/analytics/events-timeline")
def events_timeline(user: User = Depends(require_roles(Role.ADMIN))):
    del user
    return SERVICE.events_timeline()


@app.get("/api/v1/admin/analytics/visitor-sessions")
def visitor_sessions(user: User = Depends(require_roles(Role.ADMIN))):
    del user
    return SERVICE.visitor_session_overview()
