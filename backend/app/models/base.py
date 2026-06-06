"""
SQLAlchemy declarative base.
Tüm ORM modelleri buradaki Base sınıfından türer.
"""

import uuid as _uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Uuid, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def pk_uuid() -> Uuid:
    """Her tablo için UUID primary key üreteci."""
    return mapped_column(
        Uuid(),  # SQLite ve PostgreSQL ile uyumlu
        primary_key=True,
        default=_uuid.uuid4,
    )


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    """created_at ve updated_at alanlarını ekler."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )
