from __future__ import annotations

import uuid as _uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, Uuid, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, pk_uuid, utcnow


class AuditLog(Base):
    """Admin işlem logları — kim, ne zaman, ne yaptı."""

    __tablename__ = "audit_logs"

    id: Mapped[_uuid.UUID] = pk_uuid()
    user_id: Mapped[_uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    user_email: Mapped[str | None] = mapped_column(String(255))
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # create | update | delete
    resource: Mapped[str] = mapped_column(String(50), nullable=False)  # energy_source | user | setting
    resource_id: Mapped[str | None] = mapped_column(String(100))
    details: Mapped[str | None] = mapped_column(Text)
    ip_address: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
