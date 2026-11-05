"""
PostgreSQL repository and ORM models (SQLAlchemy).

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
from datetime import datetime, timedelta, timezone
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
    delete,
    event as sqlalchemy_event,
    select,
    update,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship


VISITOR_ACTIVE_WINDOW = timedelta(minutes=1)


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
        "PoiTranslationRecord", back_populates="poi", passive_deletes="all"
    )
    images: Mapped[list[PoiImageRecord]] = relationship(
        "PoiImageRecord", back_populates="poi", passive_deletes="all"
    )
    audios: Mapped[list[PoiAudioRecord]] = relationship(
        "PoiAudioRecord", back_populates="poi", passive_deletes="all"
    )
    qr_codes: Mapped[list[QrCodeRecord]] = relationship(
        "QrCodeRecord", back_populates="poi", passive_deletes="all"
    )
    narration_events: Mapped[list[EventRecord]] = relationship(
        "EventRecord", back_populates="poi", passive_deletes="all"
    )


# ---------------------------------------------------------------------------
# Bảng 5: poi_translations
# ---------------------------------------------------------------------------

class PoiTranslationRecord(Base):
    """Nội dung POI theo từng ngôn ngữ (vi / en / …)."""

    __tablename__ = "poi_translations"
    __table_args__ = (UniqueConstraint("poi_id", "language_code", name="uq_poi_lang"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    poi_id: Mapped[str] = mapped_column(ForeignKey("pois.id", ondelete="RESTRICT"), nullable=False)
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
    poi_id: Mapped[str] = mapped_column(ForeignKey("pois.id", ondelete="RESTRICT"), nullable=False)
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
    poi_id: Mapped[str] = mapped_column(ForeignKey("pois.id", ondelete="RESTRICT"), nullable=False)
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
    poi_id: Mapped[str] = mapped_column(ForeignKey("pois.id", ondelete="RESTRICT"), nullable=False)
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
    poi_id: Mapped[str] = mapped_column(
        ForeignKey("pois.id", ondelete="RESTRICT"), nullable=False
    )
    source: Mapped[str] = mapped_column(String(20), nullable=False)  # GPS | QR | MANUAL
    event_type: Mapped[str] = mapped_column(String(20), nullable=False)  # start | finish
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    session_id: Mapped[str] = mapped_column(String(120), default="anonymous")
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    poi: Mapped[PoiRecord] = relationship("PoiRecord", back_populates="narration_events")


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
# Bảng 11: visitor_sessions
# ---------------------------------------------------------------------------

class VisitorSessionRecord(Base):
    """Phiên truy cập ẩn danh theo trình duyệt, không lưu IP hay thông tin cá nhân."""

    __tablename__ = "visitor_sessions"

    device_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    last_path: Mapped[str] = mapped_column(String(512), default="/", nullable=False)
    entry_source: Mapped[str] = mapped_column(String(20), default="DIRECT", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


# ---------------------------------------------------------------------------
# PersistentStore – lớp repository truy cập CSDL
# ---------------------------------------------------------------------------

class PersistentStore:
    """
    Lớp truy cập dữ liệu được gọi từ application service.

    Nếu DATABASE_URL không được cấu hình, `enabled = False` và
    mọi phương thức trả về ngay lập tức (in-memory fallback).
    """

    def __init__(self, url: str | None = None):
        self.url = url or os.getenv("DATABASE_URL", "")
        self.enabled = bool(self.url)
        self.engine = create_engine(self.url, pool_pre_ping=True) if self.enabled else None
        if self.engine:
            if self.engine.dialect.name == "sqlite":
                @sqlalchemy_event.listens_for(self.engine, "connect")
                def enable_sqlite_foreign_keys(connection, _record):
                    cursor = connection.cursor()
                    cursor.execute("PRAGMA foreign_keys=ON")
                    cursor.close()

            Base.metadata.create_all(self.engine)
            self._seed_reference_data()

    # ------------------------------------------------------------------
    # Seed dữ liệu ban đầu
    # ------------------------------------------------------------------

    def _seed_reference_data(self) -> None:
        """Tạo các danh mục và vai trò mặc định nếu chưa có."""
        default_cats = [
            ("campus", "Trường học / Cơ sở giáo dục", "Campus"),
            ("religious", "Tôn giáo / Tín ngưỡng", "Religious"),
            ("market", "Chợ / Thương mại", "Market"),
            ("museum", "Bảo tàng / Di tích", "Museum"),
            ("historical", "Lịch sử", "Historical"),
            ("public-space", "Không gian công cộng", "Public Space"),
        ]
        with Session(self.engine) as session:
            default_roles = [
                ("admin", "Quản trị viên, toàn quyền quản lý hệ thống"),
                ("editor", "Biên tập viên, quản lý nội dung POI"),
            ]
            role_records: dict[str, RoleRecord] = {}
            for name, description in default_roles:
                role = session.scalar(select(RoleRecord).where(RoleRecord.name == name))
                if not role:
                    role = RoleRecord(name=name, description=description)
                    session.add(role)
                role_records[name] = role
            for slug, label_vi, label_en in default_cats:
                exists = session.scalar(select(CategoryRecord).where(CategoryRecord.slug == slug))
                if not exists:
                    session.add(CategoryRecord(slug=slug, label_vi=label_vi, label_en=label_en))
            session.flush()
            for user in session.scalars(select(UserRecord)).all():
                role = role_records.get(user.role)
                if role and user.role_id != role.id:
                    user.role_id = role.id
            session.commit()

    # ------------------------------------------------------------------
    # POI
    # ------------------------------------------------------------------

    def load_pois(self) -> list[dict[str, Any]]:
        if not self.engine:
            return []
        with Session(self.engine) as session:
            records = session.scalars(select(PoiRecord)).all()
            pois = []
            for record in records:
                payload = dict(record.payload)
                translations = [
                    {
                        "language_code": translation.language_code,
                        "name": translation.name,
                        "description": translation.description,
                        "narration_text": translation.narration_text,
                    }
                    for translation in record.translations
                ]
                if translations:
                    payload["translations"] = translations
                    vietnamese = next(
                        (item for item in translations if item["language_code"] == "vi"),
                        None,
                    )
                    if vietnamese:
                        payload["translation"] = vietnamese
                pois.append(payload)
            return pois

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

            # Sync bảng poi_translations without removing other languages.
            translation_data = list(payload.get("translations", []))
            primary_translation = payload.get("translation", {})
            if primary_translation:
                primary_language = primary_translation.get("language_code", "vi")
                if not any(
                    item.get("language_code", "vi") == primary_language
                    for item in translation_data
                ):
                    translation_data.append(primary_translation)
            for trans_data in translation_data:
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
        created_at = payload.get("created_at", datetime.now(timezone.utc))
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
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
                    created_at=created_at,
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
            role = session.scalar(select(RoleRecord).where(RoleRecord.name == payload["role"]))
            record = session.get(UserRecord, payload["id"])
            if record:
                record.full_name = payload["full_name"]
                record.email = payload["email"]
                record.role = payload["role"]
                record.role_id = role.id if role else None
                record.password_hash = payload["password_hash"]
                record.is_active = payload.get("is_active", True)
            else:
                session.add(
                    UserRecord(
                        id=payload["id"],
                        full_name=payload["full_name"],
                        email=payload["email"],
                        role=payload["role"],
                        role_id=role.id if role else None,
                        password_hash=payload["password_hash"],
                        is_active=payload.get("is_active", True),
                    )
                )
            session.commit()

    # ------------------------------------------------------------------
    # Anonymous website visitor sessions
    # ------------------------------------------------------------------

    def record_visitor_heartbeat(self, payload: dict[str, Any]) -> None:
        if not self.engine:
            return
        now = datetime.now(timezone.utc)
        active_since = now - VISITOR_ACTIVE_WINDOW
        with Session(self.engine) as session:
            session.execute(
                update(VisitorSessionRecord)
                .where(VisitorSessionRecord.last_seen_at < active_since)
                .values(is_active=False)
            )
            session.execute(
                delete(VisitorSessionRecord).where(
                    VisitorSessionRecord.last_seen_at < now - timedelta(days=30)
                )
            )
            values = {
                "device_id": payload["device_id"],
                "first_seen_at": now,
                "last_seen_at": now,
                "last_path": payload["path"],
                "entry_source": payload["source"],
                "is_active": True,
            }
            if self.engine.dialect.name == "postgresql":
                from sqlalchemy.dialects.postgresql import insert
            elif self.engine.dialect.name == "sqlite":
                from sqlalchemy.dialects.sqlite import insert
            else:
                raise RuntimeError(
                    f"Visitor session upsert is unsupported for {self.engine.dialect.name}"
                )
            statement = insert(VisitorSessionRecord).values(**values)
            session.execute(
                statement.on_conflict_do_update(
                    index_elements=[VisitorSessionRecord.device_id],
                    set_={
                        "last_seen_at": now,
                        "last_path": payload["path"],
                        "is_active": True,
                    },
                )
            )
            session.commit()

    def list_visitor_sessions(self, limit: int = 100) -> list[dict[str, Any]]:
        if not self.engine:
            return []
        active_since = datetime.now(timezone.utc) - VISITOR_ACTIVE_WINDOW
        with Session(self.engine) as session:
            session.execute(
                update(VisitorSessionRecord)
                .where(VisitorSessionRecord.last_seen_at < active_since)
                .values(is_active=False)
            )
            session.execute(
                delete(VisitorSessionRecord).where(
                    VisitorSessionRecord.last_seen_at
                    < datetime.now(timezone.utc) - timedelta(days=30)
                )
            )
            session.commit()
            records = session.scalars(
                select(VisitorSessionRecord)
                .order_by(VisitorSessionRecord.last_seen_at.desc())
                .limit(limit)
            ).all()
            return [
                {
                    "device_id": record.device_id,
                    "first_seen_at": record.first_seen_at.isoformat(),
                    "last_seen_at": record.last_seen_at.isoformat(),
                    "last_path": record.last_path,
                    "entry_source": record.entry_source,
                    "is_active": record.is_active,
                }
                for record in records
            ]

    def count_active_visitor_sessions(self) -> int:
        if not self.engine:
            return 0
        from sqlalchemy import func

        active_since = datetime.now(timezone.utc) - VISITOR_ACTIVE_WINDOW
        with Session(self.engine) as session:
            session.execute(
                update(VisitorSessionRecord)
                .where(VisitorSessionRecord.last_seen_at < active_since)
                .values(is_active=False)
            )
            session.commit()
            return session.scalar(
                select(func.count())
                .select_from(VisitorSessionRecord)
                .where(VisitorSessionRecord.is_active.is_(True))
            ) or 0

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

    def analytics_narration_summary(self) -> dict[str, int]:
        if not self.engine:
            return {"total_plays": 0, "completed_plays": 0, "total_duration": 0}
        from sqlalchemy import case, func

        with Session(self.engine) as session:
            row = session.execute(
                select(
                    func.count()
                    .filter(EventRecord.event_type == "start")
                    .label("total_plays"),
                    func.count()
                    .filter(EventRecord.completed.is_(True))
                    .label("completed_plays"),
                    func.coalesce(
                        func.sum(
                            case(
                                (EventRecord.event_type == "finish", EventRecord.duration_seconds),
                                else_=0,
                            )
                        ),
                        0,
                    ).label("total_duration"),
                )
            ).one()
            return {
                "total_plays": row.total_plays,
                "completed_plays": row.completed_plays,
                "total_duration": row.total_duration,
            }

    def analytics_events_timeline(self, days: int = 7) -> list[dict[str, Any]]:
        if not self.engine:
            return []
        from sqlalchemy import func

        first_day = datetime.now(timezone.utc).date() - timedelta(days=days - 1)
        with Session(self.engine) as session:
            rows = session.execute(
                select(
                    func.date(EventRecord.created_at).label("event_date"),
                    func.count().label("plays"),
                )
                .where(
                    EventRecord.event_type == "start",
                    EventRecord.created_at >= datetime.combine(
                        first_day, datetime.min.time(), timezone.utc
                    ),
                )
                .group_by(func.date(EventRecord.created_at))
            ).all()
        totals = {str(row.event_date): row.plays for row in rows}
        return [
            {
                "date": (first_day + timedelta(days=offset)).isoformat(),
                "plays": totals.get((first_day + timedelta(days=offset)).isoformat(), 0),
            }
            for offset in range(days)
        ]

    def analytics_top_pois(self, limit: int = 5) -> list[dict[str, Any]]:
        """Top POI theo lượt bắt đầu thuyết minh từ bảng narration_events."""
        if not self.engine:
            return []
        from sqlalchemy import func
        with Session(self.engine) as session:
            rows = session.execute(
                select(EventRecord.poi_id, func.count().label("plays"))
                .where(EventRecord.event_type == "start")
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
