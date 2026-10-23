from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, DateTime, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class Base(DeclarativeBase):
    pass


class PoiRecord(Base):
    __tablename__ = "pois"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class EventRecord(Base):
    __tablename__ = "narration_events"

    event_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class AuditRecord(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_email: Mapped[str] = mapped_column(String(255), nullable=False)
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class UserRecord(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    role: Mapped[str] = mapped_column(String(40), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)


class PersistentStore:
    def __init__(self, url: str | None = None):
        self.url = url or os.getenv("DATABASE_URL", "")
        self.enabled = bool(self.url)
        self.engine = create_engine(self.url, pool_pre_ping=True) if self.enabled else None
        if self.engine:
            Base.metadata.create_all(self.engine)

    def load_pois(self) -> list[dict[str, Any]]:
        if not self.engine:
            return []
        with Session(self.engine) as session:
            return [record.payload for record in session.scalars(select(PoiRecord)).all()]

    def load_events(self) -> list[dict[str, Any]]:
        if not self.engine:
            return []
        with Session(self.engine) as session:
            return [record.payload for record in session.scalars(select(EventRecord)).all()]

    def load_audits(self) -> list[dict[str, Any]]:
        if not self.engine:
            return []
        with Session(self.engine) as session:
            return [
                {"user": record.user_email, "action": record.action, "entity_id": record.entity_id, "at": record.created_at.isoformat()}
                for record in session.scalars(select(AuditRecord).order_by(AuditRecord.id)).all()
            ]

    def save_poi(self, payload: dict[str, Any]) -> None:
        if not self.engine:
            return
        with Session(self.engine) as session:
            record = session.get(PoiRecord, payload["id"])
            if record:
                record.payload = payload
                record.updated_at = datetime.now(timezone.utc)
            else:
                session.add(PoiRecord(id=payload["id"], payload=payload))
            session.commit()

    def save_event(self, payload: dict[str, Any]) -> None:
        if not self.engine:
            return
        with Session(self.engine) as session:
            session.add(EventRecord(event_id=payload["event_id"], payload=payload))
            session.commit()

    def save_audit(self, payload: dict[str, Any]) -> None:
        if not self.engine:
            return
        with Session(self.engine) as session:
            session.add(AuditRecord(user_email=payload["user"], action=payload["action"], entity_id=payload["entity_id"]))
            session.commit()

    def load_users(self) -> list[dict[str, Any]]:
        if not self.engine:
            return []
        with Session(self.engine) as session:
            return [
                {
                    "id": record.id,
                    "full_name": record.full_name,
                    "email": record.email,
                    "role": record.role,
                    "password_hash": record.password_hash,
                    "is_active": record.is_active,
                }
                for record in session.scalars(select(UserRecord).order_by(UserRecord.email)).all()
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
                session.add(UserRecord(**payload))
            session.commit()
