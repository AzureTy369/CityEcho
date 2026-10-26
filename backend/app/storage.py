"""
storage.py – Persistent storage layer (PostgreSQL via SQLAlchemy).

Schema chuẩn hoá ERD:
  roles            – vai trò hệ thống (admin / editor)
  users            – tài khoản CMS
  categories       – danh mục POI
  pois             – bảng gốc địa điểm
  poi_translations – bản dịch nội dung POI (N ngôn ngữ)
  poi_images       – ảnh đại diện / gallery POI
  poi_audios       – file âm thanh thuyết minh POI
  qr_codes         – mã QR của POI
  narration_events – lượt nghe thuyết minh (GPS / QR / MANUAL)
  audit_logs       – nhật ký thao tác CMS

Nếu DATABASE_URL không được set, toàn bộ lớp storage trả về rỗng và
ứng dụng tiếp tục chạy với bộ nhớ tạm (in-memory fallback).
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    select,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Bảng 1: roles
# ---------------------------------------------------------------------------

class RoleRecord(Base):
    """Vai trò người dùng (admin, editor)."""

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(255), default="")

    users: Mapped[list[UserRecord]] = relationship("UserRecord", back_populates="role_ref")


# ---------------------------------------------------------------------------
# Bảng 2: users
# ---------------------------------------------------------------------------

class UserRecord(Base):
    """Tài khoản CMS."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    # role lưu tên vai trò (admin/editor) để tương thích legacy; role_id là FK chuẩn
    role: Mapped[str] = mapped_column(String(40), nullable=False)
    role_id: Mapped[int | None] = mapped_column(ForeignKey("roles.id"), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    role_ref: Mapped[RoleRecord | None] = relationship("RoleRecord", back_populates="users")
    audit_logs: Mapped[list[AuditRecord]] = relationship("AuditRecord", back_populates="user_ref")


# ---------------------------------------------------------------------------
# Bảng 3: categories
# ---------------------------------------------------------------------------

class CategoryRecord(Base):
    """Danh mục địa điểm (campus, religious, market, museum…)."""

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    label_vi: Mapped[str] = mapped_column(String(120), nullable=False)
    label_en: Mapped[str] = mapped_column(String(120), default="")
    icon: Mapped[str] = mapped_column(String(60), default="")

    pois: Mapped[list[PoiRecord]] = relationship("PoiRecord", back_populates="category_ref")


# ---------------------------------------------------------------------------
# Bảng 4: pois (bảng gốc)
# ---------------------------------------------------------------------------

class PoiRecord(Base):
    """Địa điểm POI – bảng gốc lưu tọa độ, trạng thái, ưu tiên."""

    __tablename__ = "pois"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    category: Mapped[str] = mapped_column(String(60), nullable=False)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    radius_m: Mapped[float] = mapped_column(Float, default=40.0)
    priority: Mapped[int] = mapped_column(Integer, default=3)
    status: Mapped[str] = mapped_column(String(30), default="DRAFT")
    # payload JSON giữ nguyên để in-memory/fallback hoạt động liền mạch
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    category_ref: Mapped[CategoryRecord | None] = relationship("CategoryRecord", back_populates="pois")
    translations: Mapped[list[PoiTranslationRecord]] = relationship(
        "PoiTranslationRecord", back_populates="poi", cascade="all, delete-orphan"
    )
    images: Mapped[list[PoiImageRecord]] = relationship(
        "PoiImageRecord", back_populates="poi", cascade="all, delete-orphan"
    )
    audios: Mapped[list[PoiAudioRecord]] = relationship(
        "PoiAudioRecord", back_populates="poi", cascade="all, delete-orphan"
    )
    qr_codes: Mapped[list[QrCodeRecord]] = relationship(
        "QrCodeRecord", back_populates="poi", cascade="all, delete-orphan"
    )


# ---------------------------------------------------------------------------
# Bảng 5: poi_translations
# ---------------------------------------------------------------------------

class PoiTranslationRecord(Base):
    """Nội dung POI theo từng ngôn ngữ (vi / en / …)."""

    __tablename__ = "poi_translations"
    __table_args__ = (UniqueConstraint("poi_id", "language_code", name="uq_poi_lang"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    poi_id: Mapped[str] = mapped_column(ForeignKey("pois.id", ondelete="CASCADE"), nullable=False)
    language_code: Mapped[str] = mapped_column(String(10), nullable=False, default="vi")
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    narration_text: Mapped[str] = mapped_column(Text, default="")

    poi: Mapped[PoiRecord] = relationship("PoiRecord", back_populates="translations")


# ---------------------------------------------------------------------------
# Bảng 6: poi_images
# ---------------------------------------------------------------------------

class PoiImageRecord(Base):
    """Ảnh của POI (đại diện và gallery)."""

    __tablename__ = "poi_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    poi_id: Mapped[str] = mapped_column(ForeignKey("pois.id", ondelete="CASCADE"), nullable=False)
    url: Mapped[str] = mapped_column(String(512), nullable=False)
    alt_text: Mapped[str] = mapped_column(String(255), default="")
    is_cover: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    poi: Mapped[PoiRecord] = relationship("PoiRecord", back_populates="images")


# ---------------------------------------------------------------------------
# Bảng 7: poi_audios
# ---------------------------------------------------------------------------

class PoiAudioRecord(Base):
    """File âm thanh thuyết minh của POI."""

    __tablename__ = "poi_audios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    poi_id: Mapped[str] = mapped_column(ForeignKey("pois.id", ondelete="CASCADE"), nullable=False)
    language_code: Mapped[str] = mapped_column(String(10), default="vi")
    url: Mapped[str] = mapped_column(String(512), nullable=False)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    poi: Mapped[PoiRecord] = relationship("PoiRecord", back_populates="audios")


# ---------------------------------------------------------------------------
# Bảng 8: qr_codes
# ---------------------------------------------------------------------------

class QrCodeRecord(Base):
    """Mã QR của POI."""

    __tablename__ = "qr_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    poi_id: Mapped[str] = mapped_column(ForeignKey("pois.id", ondelete="CASCADE"), nullable=False)
    code: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    poi: Mapped[PoiRecord] = relationship("PoiRecord", back_populates="qr_codes")


# ---------------------------------------------------------------------------
# Bảng 9: narration_events
# ---------------------------------------------------------------------------

class EventRecord(Base):
    """Lượt nghe thuyết minh (start / finish)."""

    __tablename__ = "narration_events"

    event_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    poi_id: Mapped[str] = mapped_column(String(100), nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False)  # GPS | QR | MANUAL
    event_type: Mapped[str] = mapped_column(String(20), nullable=False)  # start | finish
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    session_id: Mapped[str] = mapped_column(String(120), default="anonymous")
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


# ---------------------------------------------------------------------------
# Bảng 10: audit_logs
# ---------------------------------------------------------------------------

class AuditRecord(Base):
    """Nhật ký thao tác CMS."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_email: Mapped[str] = mapped_column(String(255), nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(100), nullable=False)
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user_ref: Mapped[UserRecord | None] = relationship("UserRecord", back_populates="audit_logs")


# ---------------------------------------------------------------------------
# PersistentStore – lớp dịch vụ truy cập CSDL
# ---------------------------------------------------------------------------

class PersistentStore:
    """
    Lớp trung gian giữa API (main.py) và PostgreSQL.

    Nếu DATABASE_URL không được cấu hình, `enabled = False` và
    mọi phương thức trả về ngay lập tức (in-memory fallback).
    """

    def __init__(self, url: str | None = None):
        self.url = url or os.getenv("DATABASE_URL", "")
        self.enabled = bool(self.url)
        self.engine = create_engine(self.url, pool_pre_ping=True) if self.enabled else None
        if self.engine:
            Base.metadata.create_all(self.engine)
            self._seed_categories()

    # ------------------------------------------------------------------
    # Seed dữ liệu ban đầu
    # ------------------------------------------------------------------

    def _seed_categories(self) -> None:
        """Tạo các danh mục mặc định nếu chưa có."""
        default_cats = [
            ("campus", "Trường học / Cơ sở giáo dục", "Campus"),
            ("religious", "Tôn giáo / Tín ngưỡng", "Religious"),
            ("market", "Chợ / Thương mại", "Market"),
            ("museum", "Bảo tàng / Di tích", "Museum"),
            ("historical", "Lịch sử", "Historical"),
            ("public-space", "Không gian công cộng", "Public Space"),
        ]
        with Session(self.engine) as session:
            for slug, label_vi, label_en in default_cats:
                exists = session.scalar(select(CategoryRecord).where(CategoryRecord.slug == slug))
                if not exists:
                    session.add(CategoryRecord(slug=slug, label_vi=label_vi, label_en=label_en))
            session.commit()

    # ------------------------------------------------------------------
    # POI
    # ------------------------------------------------------------------

    def load_pois(self) -> list[dict[str, Any]]:
        if not self.engine:
            return []
        with Session(self.engine) as session:
            return [r.payload for r in session.scalars(select(PoiRecord)).all()]

    def save_poi(self, payload: dict[str, Any]) -> None:
        if not self.engine:
            return
        with Session(self.engine) as session:
            record = session.get(PoiRecord, payload["id"])
            if record:
                record.payload = payload
                record.category = payload.get("category", record.category)
                record.latitude = payload.get("latitude", record.latitude)
                record.longitude = payload.get("longitude", record.longitude)
                record.radius_m = payload.get("radius_m", record.radius_m)
                record.priority = payload.get("priority", record.priority)
                record.status = payload.get("status", record.status)
                record.updated_at = datetime.now(timezone.utc)
            else:
                record = PoiRecord(
                    id=payload["id"],
                    payload=payload,
                    category=payload.get("category", ""),
                    latitude=payload.get("latitude", 0.0),
                    longitude=payload.get("longitude", 0.0),
                    radius_m=payload.get("radius_m", 40.0),
                    priority=payload.get("priority", 3),
                    status=payload.get("status", "DRAFT"),
                )
                session.add(record)
            session.flush()

            # Sync bảng poi_translations
            trans_data = payload.get("translation", {})
            if trans_data:
                lang = trans_data.get("language_code", "vi")
                existing_trans = session.scalar(
                    select(PoiTranslationRecord).where(
                        PoiTranslationRecord.poi_id == payload["id"],
                        PoiTranslationRecord.language_code == lang,
                    )
                )
                if existing_trans:
                    existing_trans.name = trans_data.get("name", existing_trans.name)
                    existing_trans.description = trans_data.get("description", existing_trans.description)
                    existing_trans.narration_text = trans_data.get("narration_text", existing_trans.narration_text)
                else:
                    session.add(
                        PoiTranslationRecord(
                            poi_id=payload["id"],
                            language_code=lang,
                            name=trans_data.get("name", ""),
                            description=trans_data.get("description", ""),
                            narration_text=trans_data.get("narration_text", ""),
                        )
                    )

            # Sync bảng poi_images
            image_url = payload.get("image_url", "")
            if image_url:
                existing_cover = session.scalar(
                    select(PoiImageRecord).where(
                        PoiImageRecord.poi_id == payload["id"],
                        PoiImageRecord.is_cover == True,  # noqa: E712
                    )
                )
                if existing_cover:
                    existing_cover.url = image_url
                else:
                    session.add(PoiImageRecord(poi_id=payload["id"], url=image_url, is_cover=True))

            # Sync bảng poi_audios
            audio_url = payload.get("audio_url", "")
            if audio_url:
                existing_audio = session.scalar(
                    select(PoiAudioRecord).where(PoiAudioRecord.poi_id == payload["id"])
                )
                if existing_audio:
                    existing_audio.url = audio_url
                    existing_audio.duration_seconds = payload.get("audio_duration_seconds", 0)
                else:
                    session.add(
                        PoiAudioRecord(
                            poi_id=payload["id"],
                            url=audio_url,
                            duration_seconds=payload.get("audio_duration_seconds", 0),
                        )
                    )

            # Sync bảng qr_codes
            qr_code = payload.get("qr_code", "")
            if qr_code:
                existing_qr = session.scalar(
                    select(QrCodeRecord).where(QrCodeRecord.poi_id == payload["id"])
                )
                if not existing_qr:
                    session.add(QrCodeRecord(poi_id=payload["id"], code=qr_code))

            session.commit()

    # ------------------------------------------------------------------
    # Narration events
    # ------------------------------------------------------------------

    def load_events(self) -> list[dict[str, Any]]:
        if not self.engine:
            return []
        with Session(self.engine) as session:
            return [r.payload for r in session.scalars(select(EventRecord)).all()]

    def save_event(self, payload: dict[str, Any]) -> None:
        if not self.engine:
            return
        with Session(self.engine) as session:
            session.add(
                EventRecord(
                    event_id=payload["event_id"],
                    poi_id=payload.get("poi_id", ""),
                    source=payload.get("source", "MANUAL"),
                    event_type=payload.get("event_type", "start"),
                    duration_seconds=payload.get("duration_seconds", 0),
                    completed=payload.get("completed", False),
                    session_id=payload.get("session_id", "anonymous"),
                    payload=payload,
                )
            )
            session.commit()

    # ------------------------------------------------------------------
    # Audit logs
    # ------------------------------------------------------------------

    def load_audits(self) -> list[dict[str, Any]]:
        if not self.engine:
            return []
        with Session(self.engine) as session:
            return [
                {
                    "user": r.user_email,
                    "action": r.action,
                    "entity_id": r.entity_id,
                    "note": r.note,
                    "at": r.created_at.isoformat(),
                }
                for r in session.scalars(select(AuditRecord).order_by(AuditRecord.id)).all()
            ]

    def save_audit(self, payload: dict[str, Any]) -> None:
        if not self.engine:
            return
        with Session(self.engine) as session:
            session.add(
                AuditRecord(
                    user_email=payload["user"],
                    action=payload["action"],
                    entity_id=payload["entity_id"],
                    note=payload.get("note", ""),
                )
            )
            session.commit()

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------

    def load_users(self) -> list[dict[str, Any]]:
        if not self.engine:
            return []
        with Session(self.engine) as session:
            return [
                {
                    "id": r.id,
                    "full_name": r.full_name,
                    "email": r.email,
                    "role": r.role,
                    "password_hash": r.password_hash,
                    "is_active": r.is_active,
                }
                for r in session.scalars(select(UserRecord).order_by(UserRecord.email)).all()
            ]

    def save_user(self, payload: dict[str, Any]) -> None:
        if not self.engine:
            return
        with Session(self.engine) as session:
            record = session.get(UserRecord, payload["id"])
            if record:
                record.full_name = payload["full_name"]
                record.email = payload["email"]
                record.role = payload["role"]
                record.password_hash = payload["password_hash"]
                record.is_active = payload.get("is_active", True)
            else:
                session.add(
                    UserRecord(
                        id=payload["id"],
                        full_name=payload["full_name"],
                        email=payload["email"],
                        role=payload["role"],
                        password_hash=payload["password_hash"],
                        is_active=payload.get("is_active", True),
                    )
                )
            session.commit()

    # ------------------------------------------------------------------
    # Truy vấn thống kê chuẩn hóa (dùng cho dashboard ERD)
    # ------------------------------------------------------------------

    def analytics_by_source(self) -> dict[str, int]:
        """Thống kê lượt nghe theo nguồn từ bảng narration_events chuẩn hóa."""
        if not self.engine:
            return {}
        from sqlalchemy import func, text
        with Session(self.engine) as session:
            rows = session.execute(
                select(EventRecord.source, func.count().label("cnt"))
                .where(EventRecord.event_type == "start")
                .group_by(EventRecord.source)
            ).all()
            return {row.source: row.cnt for row in rows}

    def analytics_top_pois(self, limit: int = 5) -> list[dict[str, Any]]:
        """Top POI theo lượt hoàn thành từ bảng narration_events."""
        if not self.engine:
            return []
        from sqlalchemy import func
        with Session(self.engine) as session:
            rows = session.execute(
                select(EventRecord.poi_id, func.count().label("plays"))
                .where(EventRecord.completed == True)  # noqa: E712
                .group_by(EventRecord.poi_id)
                .order_by(func.count().desc())
                .limit(limit)
            ).all()
            result = []
            for row in rows:
                poi = session.get(PoiRecord, row.poi_id)
                name = poi.payload.get("translation", {}).get("name", row.poi_id) if poi else row.poi_id
                result.append({"poi_id": row.poi_id, "name": name, "plays": row.plays})
            return result

    def list_categories(self) -> list[dict[str, Any]]:
        """Danh sách danh mục từ bảng categories."""
        if not self.engine:
            return []
        with Session(self.engine) as session:
            return [
                {"slug": r.slug, "label_vi": r.label_vi, "label_en": r.label_en}
                for r in session.scalars(select(CategoryRecord)).all()
            ]
