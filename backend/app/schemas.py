from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


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
    language_code: str = Field(
        default="vi",
        min_length=2,
        max_length=10,
        pattern=r"^[a-zA-Z]{2,3}(?:-[a-zA-Z0-9]{2,8})?$",
    )
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
    translations: list[Translation] = Field(default_factory=list)
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
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class User(BaseModel):
    id: str
    full_name: str
    email: str
    role: Role
    is_active: bool = True


class DeviceHeartbeat(BaseModel):
    device_id: str = Field(pattern=r"^[a-f0-9-]{36}$")
    path: str = Field(default="/", max_length=512)
    source: str = Field(default="DIRECT", pattern=r"^(DIRECT|QR)$")
