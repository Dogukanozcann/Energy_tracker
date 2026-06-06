from __future__ import annotations

import uuid as _uuid

from sqlalchemy import Boolean, ForeignKey, Numeric, String, Text
from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, pk_uuid


class Facility(Base, TimestampMixin):
    __tablename__ = "facilities"

    id: Mapped[_uuid.UUID] = pk_uuid()
    user_id: Mapped[_uuid.UUID] = mapped_column(
        Uuid(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    facility_type: Mapped[str] = mapped_column(String(50), default="office")

    address: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(String(100))
    district: Mapped[str | None] = mapped_column(String(100))
    postal_code: Mapped[str | None] = mapped_column(String(20))
    country: Mapped[str] = mapped_column(String(100), default="Türkiye")

    area_sqm: Mapped[float | None] = mapped_column(Numeric(12, 2))
    heated_area_sqm: Mapped[float | None] = mapped_column(Numeric(12, 2))
    num_floors: Mapped[int | None] = mapped_column()
    num_occupants: Mapped[int | None] = mapped_column()
    operating_hours: Mapped[float | None] = mapped_column(Numeric(4, 2))

    latitude: Mapped[float | None] = mapped_column(Numeric(10, 7))
    longitude: Mapped[float | None] = mapped_column(Numeric(10, 7))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    logo_url: Mapped[str | None] = mapped_column(Text)

    # --- Relationships ---
    user: Mapped["User"] = relationship("User", back_populates="facilities")
    energy_consumptions: Mapped[list["EnergyConsumption"]] = relationship(
        "EnergyConsumption", back_populates="facility", cascade="all, delete-orphan"
    )
    carbon_footprints: Mapped[list["CarbonFootprint"]] = relationship(
        "CarbonFootprint", back_populates="facility", cascade="all, delete-orphan"
    )
    alerts: Mapped[list["Alert"]] = relationship(
        "Alert", back_populates="facility", cascade="all, delete-orphan"
    )
    actions: Mapped[list["Action"]] = relationship(
        "Action", back_populates="facility", cascade="all, delete-orphan"
    )

