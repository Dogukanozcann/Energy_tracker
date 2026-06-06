from __future__ import annotations

import uuid as _uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, pk_uuid, utcnow


class Alert(Base, TimestampMixin):
    """Anomali tespiti, eşik ihlalleri, verimlilik uyarıları."""

    __tablename__ = "alerts"

    id: Mapped[_uuid.UUID] = pk_uuid()
    facility_id: Mapped[_uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    energy_consumption_id: Mapped[_uuid.UUID | None] = mapped_column(
        Uuid(), ForeignKey("energy_consumption.id", ondelete="SET NULL")
    )
    energy_source_id: Mapped[_uuid.UUID | None] = mapped_column(
        Uuid(), ForeignKey("energy_sources.id", ondelete="SET NULL")
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(20), default="medium")
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="new")

    detected_value: Mapped[float | None] = mapped_column(Numeric(14, 4))
    expected_value: Mapped[float | None] = mapped_column(Numeric(14, 4))
    threshold_value: Mapped[float | None] = mapped_column(Numeric(14, 4))
    deviation_percent: Mapped[float | None] = mapped_column(Numeric(6, 2))
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    recommendation_text: Mapped[str | None] = mapped_column(Text)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolved_by: Mapped[_uuid.UUID | None] = mapped_column(
        Uuid(), ForeignKey("users.id", ondelete="SET NULL")
    )

    parent_alert_id: Mapped[_uuid.UUID | None] = mapped_column(
        Uuid(), ForeignKey("alerts.id", ondelete="SET NULL")
    )
    is_auto_generated: Mapped[bool] = mapped_column(Boolean, default=True)

    # --- Relationships ---
    facility: Mapped["Facility"] = relationship("Facility", back_populates="alerts")

