from __future__ import annotations

import uuid as _uuid

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, pk_uuid


class SystemSetting(Base, TimestampMixin):
    """Anahtar-değer sistem ayarları. Admin panelden yönetilir."""

    __tablename__ = "system_settings"

    id: Mapped[_uuid.UUID] = pk_uuid()
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(50), default="general")
