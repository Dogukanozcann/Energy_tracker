"""
Karbon Ayak İzi Hesaplama Motoru.

Her enerji kaynağı tipine göre uygun formülü uygular:

  - factor (varsayılan):  CO2 = consumption_value * factor
  - fuel:                 CO2 = V * density * carbon_ratio * (44/12)  veya precomputed fuel_co2_per_liter
  - dual_unit:            CO2 = V * factor(unit) — birime göre scope_1 ya da scope_1_alt

Desteklenen kaynaklar ve formüller:
  Şebeke Elektriği:  E = V * 0.45 kg CO2e/kWh
  Doğalgaz (m³):     E = V * 2.02 kg CO2e/m³
  Doğalgaz (kWh):    E = V * 0.183 kg CO2e/kWh
  Dizel:             E = V * 2.64 kg CO2e/L  (V * 0.835 * 0.862 * 44/12)
  Benzin:            E = V * 2.36 kg CO2e/L  (V * 0.740 * 0.870 * 44/12)
  Su (m³):           E = V * 1.04 kg CO2e/m³
  Kömür / diğer:     E = V * factor (esnek)
  Güneş:             E = 0 (yenilenebilir, sıfır emisyon)
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.carbon_footprint import CarbonFootprintItem
from app.models.energy_consumption import EnergyConsumption
from app.models.energy_source import EnergySource
from app.models.facility import Facility


class CarbonCalculatorService:
    """Tüketim → Karbon hesaplama motoru."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ----------------------------------------------------------------
    # PUBLIC
    # ----------------------------------------------------------------

    async def calculate(
        self,
        consumption_id: UUID,
        user_id: UUID,
        force: bool = False,
    ) -> CarbonFootprintItem:
        q = (
            select(EnergyConsumption)
            .options(joinedload(EnergyConsumption.energy_source))
            .join(Facility, Facility.id == EnergyConsumption.facility_id)
            .where(
                EnergyConsumption.id == consumption_id,
                Facility.user_id == user_id,
            )
        )
        result = await self.db.execute(q)
        consumption = result.unique().scalar_one_or_none()

        if consumption is None:
            raise ValueError("Tüketim kaydı bulunamadı veya size ait değil.")

        return await self._calculate_internal(consumption, force)

    async def calculate_batch(
        self,
        facility_id: UUID,
        user_id: UUID,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        force: bool = False,
    ) -> tuple[int, float]:
        q_owner = select(Facility.id).where(
            Facility.id == facility_id, Facility.user_id == user_id
        )
        if (await self.db.execute(q_owner)).scalar_one_or_none() is None:
            raise ValueError("Tesis bulunamadı veya size ait değil.")

        filters = [EnergyConsumption.facility_id == facility_id]
        if date_from:
            filters.append(EnergyConsumption.recorded_at >= date_from)
        if date_to:
            filters.append(EnergyConsumption.recorded_at <= date_to)

        if not force:
            subq = (
                select(CarbonFootprintItem.energy_consumption_id)
                .where(CarbonFootprintItem.energy_consumption_id == EnergyConsumption.id)
                .exists()
            )
            filters.append(~subq)

        q = (
            select(EnergyConsumption)
            .options(joinedload(EnergyConsumption.energy_source))
            .where(*filters)
        )
        result = await self.db.execute(q)
        consumptions = list(result.unique().scalars().all())

        total_co2 = 0.0
        for c in consumptions:
            try:
                item = await self._calculate_internal(c, force=True)
                total_co2 += float(item.calculated_co2_kg)
            except (ValueError, ZeroDivisionError):
                continue

        return len(consumptions), total_co2

    # ----------------------------------------------------------------
    # HESAPLAMA ÇEKİRDEĞİ
    # ----------------------------------------------------------------

    async def _calculate_internal(
        self,
        consumption: EnergyConsumption,
        force: bool = False,
    ) -> CarbonFootprintItem:
        source: EnergySource = consumption.energy_source
        value = float(consumption.consumption_value)
        unit = consumption.unit

        # Kaynağın formula_type'ına göre hesapla
        scope, factor, calculated_co2 = self._apply_formula(source, value, unit)

        # Mevcut item var mı
        q = select(CarbonFootprintItem).where(
            CarbonFootprintItem.energy_consumption_id == consumption.id
        )
        existing = (await self.db.execute(q)).scalar_one_or_none()

        if existing and not force:
            return existing

        kwargs = dict(
            scope=scope,
            energy_source_id=source.id,
            consumption_amount=value,
            consumption_unit=unit,
            co2_factor_used=factor,
            calculated_co2_kg=round(calculated_co2, 4),
            factor_source=source.co2_factor_source,
        )

        if existing:
            for k, v in kwargs.items():
                setattr(existing, k, v)
            item = existing
        else:
            item = CarbonFootprintItem(
                energy_consumption_id=consumption.id,
                **kwargs,
            )
            self.db.add(item)

        await self.db.flush()
        return item

    # ----------------------------------------------------------------
    # FORMÜL SEÇİCİ
    # ----------------------------------------------------------------

    @staticmethod
    def _apply_formula(source: EnergySource, value: float, unit: str) -> tuple[str, float, float]:
        formula = source.formula_type or "factor"

        if formula == "dual_unit":
            return _calc_dual_unit(source, value, unit)

        if formula == "fuel":
            return _calc_fuel(source, value)

        # factor (varsayılan)
        return _calc_factor(source, value)


# ====================================================================
# FORMÜL İŞLEVLERİ
# ====================================================================


def _calc_factor(source: EnergySource, value: float) -> tuple[str, float, float]:
    """E = V * EF — en basit çarpan yöntemi."""
    if source.co2_factor_scope_1 is not None:
        scope = "scope_1"
        factor = float(source.co2_factor_scope_1)
    elif source.co2_factor_scope_2 is not None:
        scope = "scope_2"
        factor = float(source.co2_factor_scope_2)
    else:
        scope = "scope_3"
        factor = 0.0
    return scope, factor, value * factor


def _calc_dual_unit(source: EnergySource, value: float, unit: str) -> tuple[str, float, float]:
    """Birime göre factor seç — doğalgaz m³→2.02, kWh→0.183 gibi."""
    if source.co2_factor_scope_1 is not None:
        base_scope = "scope_1"
        base_factor = float(source.co2_factor_scope_1)
        alt_factor = float(source.co2_factor_scope_1_alt) if source.co2_factor_scope_1_alt is not None else None
    elif source.co2_factor_scope_2 is not None:
        base_scope = "scope_2"
        base_factor = float(source.co2_factor_scope_2)
        alt_factor = float(source.co2_factor_scope_2_alt) if source.co2_factor_scope_2_alt is not None else None
    else:
        return "scope_3", 0.0, 0.0

    alt_unit = source.unit_alt or ""

    if unit == alt_unit and alt_factor is not None:
        return base_scope, alt_factor, value * alt_factor

    return base_scope, base_factor, value * base_factor


def _calc_fuel(source: EnergySource, value: float) -> tuple[str, float, float]:
    """
    Araç yakıtı formülü:  E_CO2 = V * p * C * (44/12)

    V: tüketim (litre)
    p: yoğunluk (kg/L) — diesel=0.835, gasoline=0.740
    C: karbon oranı — diesel=0.862, gasoline=0.870

    Eğer fuel_co2_per_liter ön hesaplanmışsa doğrudan onu kullan.
    """
    scope = "scope_1"

    precomputed = float(source.fuel_co2_per_liter) if source.fuel_co2_per_liter is not None else None
    if precomputed is not None:
        return scope, precomputed, value * precomputed

    density = float(source.fuel_density) if source.fuel_density else 0.0
    carbon = float(source.fuel_carbon_ratio) if source.fuel_carbon_ratio else 0.0

    if density <= 0 or carbon <= 0:
        return scope, 0.0, 0.0

    factor = density * carbon * (44.0 / 12.0)
    return scope, round(factor, 4), value * factor
