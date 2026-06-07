from __future__ import annotations

import uuid as _uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, pk_uuid, utcnow


class EnergyConsumption(Base):
    """Ana zaman-serisi tablosu: tesis-enerji kaynağı çifti için anlık tüketim."""

    __tablename__ = "energy_consumption"

    id: Mapped[_uuid.UUID] = pk_uuid()
    facility_id: Mapped[_uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    energy_source_id: Mapped[_uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("energy_sources.id", ondelete="RESTRICT"), nullable=False
    )

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    consumption_value: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    cost: Mapped[float | None] = mapped_column(Numeric(12, 4))

    source: Mapped[str] = mapped_column(String(20), default="manual")
    consumption_type: Mapped[str] = mapped_column(String(20), default="consumption")  # consumption | production
    is_estimated: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text)
    external_id: Mapped[str | None] = mapped_column(String(255))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    # --- Relationships ---
    facility: Mapped["Facility"] = relationship("Facility", back_populates="energy_consumptions")
    energy_source: Mapped["EnergySource"] = relationship()
    carbon_footprint_item: Mapped["CarbonFootprintItem | None"] = relationship(
        "CarbonFootprintItem", back_populates="energy_consumption", uselist=False, cascade="all, delete-orphan"
    )

