from __future__ import annotations

import uuid as _uuid
from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, pk_uuid


class Action(Base, TimestampMixin):
    """AI destekli tasarruf önerileri (Aksiyon Motoru)."""

    __tablename__ = "actions"

    id: Mapped[_uuid.UUID] = pk_uuid()
    facility_id: Mapped[_uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    priority: Mapped[str] = mapped_column(String(20), default="medium")
    status: Mapped[str] = mapped_column(String(20), default="pending")

    estimated_saving_co2_kg: Mapped[float | None] = mapped_column(Numeric(12, 2))
    estimated_saving_cost: Mapped[float | None] = mapped_column(Numeric(12, 2))
    estimated_investment_cost: Mapped[float | None] = mapped_column(Numeric(12, 2))
    roi_estimate: Mapped[float | None] = mapped_column(Numeric(6, 2))
    payback_months: Mapped[int | None] = mapped_column(Integer)

    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=True)
    ai_confidence_score: Mapped[float | None] = mapped_column(Numeric(4, 2))
    source_data_summary: Mapped[str | None] = mapped_column(Text)

    assigned_to: Mapped[_uuid.UUID | None] = mapped_column(
        Uuid(), ForeignKey("users.id", ondelete="SET NULL")
    )
    implementation_notes: Mapped[str | None] = mapped_column(Text)
    implementation_date: Mapped[date | None] = mapped_column(Date)
    implemented_by: Mapped[_uuid.UUID | None] = mapped_column(
        Uuid(), ForeignKey("users.id", ondelete="SET NULL")
    )

    # --- Relationships ---
    facility: Mapped["Facility"] = relationship("Facility", back_populates="actions")

