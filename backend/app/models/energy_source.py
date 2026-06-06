from __future__ import annotations

import uuid as _uuid

from sqlalchemy import Boolean, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, pk_uuid


class EnergySource(Base, TimestampMixin):
    """Referans tablosu: her enerji kaynağının CO2 emisyon faktörü."""

    __tablename__ = "energy_sources"

    id: Mapped[_uuid.UUID] = pk_uuid()
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    name_tr: Mapped[str | None] = mapped_column(String(150))
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)

    co2_factor_scope_1: Mapped[float | None] = mapped_column(Numeric(12, 6))
    co2_factor_scope_2: Mapped[float | None] = mapped_column(Numeric(12, 6))
    co2_factor_source: Mapped[str | None] = mapped_column(String(255))
    factor_year: Mapped[int | None] = mapped_column(Integer)

    is_renewable: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
