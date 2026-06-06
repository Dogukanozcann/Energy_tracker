from __future__ import annotations

import uuid as _uuid
from datetime import date, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, pk_uuid, utcnow


class CarbonFootprintItem(Base):
    """
    Karbon ayak izi kalemleri.
    Her energy_consumption kaydı için hesaplanan karbon değeri.
    1 tüketim → en fazla 1 karbon kalemi (bkz. UNIQUE constraint).
    """

    __tablename__ = "carbon_footprint_items"

    id: Mapped[_uuid.UUID] = pk_uuid()
    energy_consumption_id: Mapped[_uuid.UUID] = mapped_column(
        Uuid(),
        ForeignKey("energy_consumption.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    energy_source_id: Mapped[_uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("energy_sources.id", ondelete="RESTRICT"), nullable=False
    )
    scope: Mapped[str] = mapped_column(String(10), nullable=False)  # scope_1 | scope_2 | scope_3

    consumption_amount: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False)
    consumption_unit: Mapped[str] = mapped_column(String(20), nullable=False)
    co2_factor_used: Mapped[float] = mapped_column(Numeric(12, 6), nullable=False)
    calculated_co2_kg: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False)
    factor_source: Mapped[str | None] = mapped_column(String(255))

    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    # --- Relationships ---
    energy_consumption: Mapped["EnergyConsumption"] = relationship(
        "EnergyConsumption", back_populates="carbon_footprint_item"
    )
    energy_source: Mapped["EnergySource"] = relationship()


class CarbonFootprint(Base, TimestampMixin):
    """
    Karbon ayak izi özetleri — AGGREGASYON TABLOSU.
    carbon_footprint_items + energy_consumption üzerinden periyodik olarak doldurulur.
    """

    __tablename__ = "carbon_footprints"

    id: Mapped[_uuid.UUID] = pk_uuid()
    facility_id: Mapped[_uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True
    )

    calculation_start: Mapped[date] = mapped_column(nullable=False)
    calculation_end: Mapped[date] = mapped_column(nullable=False)
    calculation_year: Mapped[int] = mapped_column(Integer, nullable=False)
    calculation_month: Mapped[int | None] = mapped_column(Integer)
    calculation_quarter: Mapped[int | None] = mapped_column(Integer)

    total_co2_kg: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    scope_1_co2_kg: Mapped[float | None] = mapped_column(Numeric(14, 2))
    scope_2_co2_kg: Mapped[float | None] = mapped_column(Numeric(14, 2))
    scope_3_co2_kg: Mapped[float | None] = mapped_column(Numeric(14, 2))

    intensity_per_area: Mapped[float | None] = mapped_column(Numeric(10, 4))
    intensity_per_revenue: Mapped[float | None] = mapped_column(Numeric(10, 4))

    methodology: Mapped[str] = mapped_column(String(50), default="ghg_protocol")
    status: Mapped[str] = mapped_column(String(20), default="draft")

    notes: Mapped[str | None] = mapped_column(Text)
    calculated_by_user: Mapped[_uuid.UUID | None] = mapped_column(
        Uuid(), ForeignKey("users.id", ondelete="SET NULL")
    )
    calculated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=utcnow)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # --- Relationships ---
    facility: Mapped["Facility"] = relationship("Facility", back_populates="carbon_footprints")

