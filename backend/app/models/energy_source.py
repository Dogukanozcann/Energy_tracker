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

    # Hesaplama tipi: factor | fuel | dual_unit
    #   factor    → co2_factor * consumption_value (varsayılan)
    #   fuel      → V * density * carbon_ratio * (44/12) — formül içinde hesaplanır
    #   dual_unit → unit'e göre scope_1 ya da scope_1_alt kullanılır
    formula_type: Mapped[str] = mapped_column(String(20), default="factor")

    # Ana emisyon faktörleri
    co2_factor_scope_1: Mapped[float | None] = mapped_column(Numeric(12, 6))
    co2_factor_scope_2: Mapped[float | None] = mapped_column(Numeric(12, 6))
    co2_factor_source: Mapped[str | None] = mapped_column(String(255))
    factor_year: Mapped[int | None] = mapped_column(Integer)

    # Alternatif birim için ikinci faktör (dual_unit tipi için)
    # Örn: doğalgaz m³→2.02, kWh→0.183
    unit_alt: Mapped[str | None] = mapped_column(String(20))
    co2_factor_scope_1_alt: Mapped[float | None] = mapped_column(Numeric(12, 6))
    co2_factor_scope_2_alt: Mapped[float | None] = mapped_column(Numeric(12, 6))

    # Yakıt tipi parametreleri (fuel tipi için)
    # Dizel: density=0.835, carbon_ratio=0.862
    # Benzin: density=0.740, carbon_ratio=0.870
    fuel_density: Mapped[float | None] = mapped_column(Numeric(8, 4))       # kg/L
    fuel_carbon_ratio: Mapped[float | None] = mapped_column(Numeric(6, 4))  # %
    fuel_co2_per_liter: Mapped[float | None] = mapped_column(Numeric(8, 4)) # Ön hesaplanmış kg CO2e/L

    is_renewable: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
