from __future__ import annotations

import os
import re
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

IMAGE_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/gif": ".gif", "image/svg+xml": ".svg"}
AUDIO_TYPES = {"audio/mpeg": ".mp3", "audio/wav": ".wav", "audio/x-wav": ".wav", "audio/ogg": ".ogg", "audio/webm": ".webm", "audio/mp4": ".m4a", "audio/aac": ".aac"}
ALLOWED_KINDS = {"images", "audios"}
SAFE_ID = re.compile(r"^[A-Za-z0-9_-]{1,100}$")
MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_AUDIO_BYTES = 20 * 1024 * 1024


def media_root() -> Path:
    return Path(os.getenv("CITYECHO_MEDIA_DIR") or Path(__file__).resolve().parent.parent / "media")


def public_url(relative: str) -> str:
    return f"/media/{relative.replace(os.sep, '/')}"


def _safe_stem(name: str) -> str:
    stem = re.sub(r"[^a-z0-9_-]+", "-", Path(name).stem.lower()).strip("-")
    return stem[:40] or "file"


def save_upload(file: UploadFile, kind: str, poi_id: str, payload: bytes) -> tuple[str, int]:
    if kind not in ALLOWED_KINDS:
        raise HTTPException(status_code=422, detail="Loại media không được hỗ trợ")
    if not SAFE_ID.fullmatch(poi_id):
        raise HTTPException(status_code=422, detail="Mã POI không hợp lệ")
    types = IMAGE_TYPES if kind == "images" else AUDIO_TYPES
    limit = MAX_IMAGE_BYTES if kind == "images" else MAX_AUDIO_BYTES
    content_type = (file.content_type or "").split(";")[0].strip().lower()
    suffix = types.get(content_type)
    if not suffix:
        raise HTTPException(status_code=422, detail=f"Định dạng {kind} không được hỗ trợ")
    if not payload:
        raise HTTPException(status_code=422, detail="File rỗng")
    if len(payload) > limit:
        raise HTTPException(status_code=422, detail="File vượt quá dung lượng cho phép")
    folder = media_root() / "uploads" / poi_id
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{kind}-{_safe_stem(file.filename or kind)}-{uuid.uuid4().hex[:8]}{suffix}"
    path.write_bytes(payload)
    return public_url(path.relative_to(media_root()).as_posix()), len(payload)
