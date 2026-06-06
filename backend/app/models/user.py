from __future__ import annotations

import uuid as _uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, pk_uuid


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[_uuid.UUID] = pk_uuid()
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20))

    company_name: Mapped[str | None] = mapped_column(String(255))
    tax_id: Mapped[str | None] = mapped_column(String(50))
    sector: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str] = mapped_column(String(100), default="Türkiye")
    city: Mapped[str | None] = mapped_column(String(100))
    district: Mapped[str | None] = mapped_column(String(100))

    user_type: Mapped[str] = mapped_column(String(20), default="individual")   # individual | business
    role: Mapped[str] = mapped_column(String(20), default="viewer")            # admin | viewer | operator
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    verification_token: Mapped[str | None] = mapped_column(String(255))
    reset_token: Mapped[str | None] = mapped_column(String(255))
    reset_token_expires: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # --- Relationships ---
    preferences: Mapped["UserPreference"] = relationship(
        "UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    facilities: Mapped[list["Facility"]] = relationship(
        "Facility", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"


class UserPreference(Base, TimestampMixin):
    __tablename__ = "user_preferences"

    id: Mapped[_uuid.UUID] = pk_uuid()
    user_id: Mapped[_uuid.UUID] = mapped_column(
        Uuid(),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    language: Mapped[str] = mapped_column(String(10), default="tr")
    timezone: Mapped[str] = mapped_column(String(50), default="Europe/Istanbul")
    energy_unit: Mapped[str] = mapped_column(String(20), default="kWh")
    currency: Mapped[str] = mapped_column(String(10), default="TRY")
    daily_digest: Mapped[bool] = mapped_column(Boolean, default=False)

    email_alerts: Mapped[bool] = mapped_column(Boolean, default=True)
    push_alerts: Mapped[bool] = mapped_column(Boolean, default=False)
    alert_categories: Mapped[dict] = mapped_column(JSON, default=lambda: ["anomaly", "threshold_breach"])

    weekly_report: Mapped[bool] = mapped_column(Boolean, default=True)
    monthly_goal_co2: Mapped[float | None] = mapped_column(
        Numeric(12, 2), comment="Aylık CO2 hedefi (kg)"
    )

    # --- Relationships ---
    user: Mapped["User"] = relationship("User", back_populates="preferences")
