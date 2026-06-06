"""
Karbon Ayak İzi Aggregasyon Servisi.

carbon_footprint_items + energy_consumption verilerini kullanarak
periyodik (aylık/yıllık) özet raporları oluşturur ve
carbon_footprints tablosuna yazar.
"""

from calendar import monthrange
from datetime import date, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.carbon_footprint import CarbonFootprint, CarbonFootprintItem
from app.models.energy_consumption import EnergyConsumption
from app.models.facility import Facility


class CarbonFootprintService:
    """Periyodik karbon özeti aggregasyon servisi."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_monthly(
        self,
        facility_id: UUID,
        user_id: UUID,
        year: int,
        month: int,
    ) -> CarbonFootprint:
        """
        Belirli bir ay için karbon özeti oluşturur/günceller.

        Parametreler:
          facility_id: Tesis ID
          user_id:     Ownership doğrulaması
          year:        Yıl (örn. 2026)
          month:       Ay (1-12)

        Dönüş: CarbonFootprint (yeni veya güncellenmiş)
        """
        return await self._generate(facility_id, user_id, year, month=month)

    async def generate_yearly(
        self,
        facility_id: UUID,
        user_id: UUID,
        year: int,
    ) -> CarbonFootprint:
        """
        Belirli bir yıl için karbon özeti oluşturur/günceller.
        """
        return await self._generate(facility_id, user_id, year, month=None)

    async def list_footprints(
        self,
        facility_id: UUID,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[CarbonFootprint], int]:
        """Tesise ait karbon özetlerini listeler (yeniden eskiye)."""
        q_owner = select(Facility.id).where(
            Facility.id == facility_id, Facility.user_id == user_id
        )
        if (await self.db.execute(q_owner)).scalar_one_or_none() is None:
            raise ValueError("Tesis bulunamadı veya size ait değil.")

        count_q = select(func.count(CarbonFootprint.id)).where(
            CarbonFootprint.facility_id == facility_id
        )
        total = (await self.db.execute(count_q)).scalar_one()

        q = (
            select(CarbonFootprint)
            .where(CarbonFootprint.facility_id == facility_id)
            .order_by(CarbonFootprint.calculation_year.desc(),
                      CarbonFootprint.calculation_month.desc().nullslast())
            .offset(skip)
            .limit(limit)
        )
        items = list((await self.db.execute(q)).scalars().all())
        return items, total

    # ----------------------------------------------------------------
    # INTERNAL
    # ----------------------------------------------------------------

    async def _generate(
        self,
        facility_id: UUID,
        user_id: UUID,
        year: int,
        month: int | None = None,
    ) -> CarbonFootprint:
        """Ortak aggregasyon mantığı."""
        # Ownership kontrolü
        q_owner = select(Facility.id).where(
            Facility.id == facility_id, Facility.user_id == user_id
        )
        if (await self.db.execute(q_owner)).scalar_one_or_none() is None:
            raise ValueError("Tesis bulunamadı veya size ait değil.")

        # Dönem aralığını belirle
        if month:
            start_date = date(year, month, 1)
            end_date = date(year, month, monthrange(year, month)[1])
            quarter = (month - 1) // 3 + 1
        else:
            start_date = date(year, 1, 1)
            end_date = date(year, 12, 31)
            quarter = None

        # Item'lardan aggregasyon yap
        # NOT: cfi = carbon_footprint_items (alias)
        agg_q = (
            select(
                func.coalesce(func.sum(CarbonFootprintItem.calculated_co2_kg), 0),
                func.coalesce(
                    func.sum(CarbonFootprintItem.calculated_co2_kg)
                    .filter(CarbonFootprintItem.scope == "scope_1"),
                    0,
                ),
                func.coalesce(
                    func.sum(CarbonFootprintItem.calculated_co2_kg)
                    .filter(CarbonFootprintItem.scope == "scope_2"),
                    0,
                ),
                func.coalesce(
                    func.sum(CarbonFootprintItem.calculated_co2_kg)
                    .filter(CarbonFootprintItem.scope == "scope_3"),
                    0,
                ),
            )
            .select_from(CarbonFootprintItem)
            .join(
                EnergyConsumption,
                EnergyConsumption.id == CarbonFootprintItem.energy_consumption_id,
            )
            .where(
                EnergyConsumption.facility_id == facility_id,
                EnergyConsumption.recorded_at >= start_date,
                EnergyConsumption.recorded_at < end_date + timedelta(days=1),
            )
        )
        result = await self.db.execute(agg_q)
        total, s1, s2, s3 = result.one()
        total = float(total)
        s1 = float(s1)
        s2 = float(s2)
        s3 = float(s3)

        # İntensite metrikleri
        facility_q = select(Facility).where(Facility.id == facility_id)
        fac = (await self.db.execute(facility_q)).scalar_one()
        intensity_area = (
            round(total / float(fac.area_sqm), 4)
            if fac.area_sqm and float(fac.area_sqm) > 0
            else None
        )

        # Mevcut kaydı bul veya oluştur
        filters = [
            CarbonFootprint.facility_id == facility_id,
            CarbonFootprint.calculation_year == year,
        ]
        if month:
            filters.append(CarbonFootprint.calculation_month == month)
        else:
            filters.append(CarbonFootprint.calculation_month.is_(None))

        q = select(CarbonFootprint).where(*filters)
        existing = (await self.db.execute(q)).scalar_one_or_none()

        if existing:
            existing.total_co2_kg = total
            existing.scope_1_co2_kg = s1
            existing.scope_2_co2_kg = s2
            existing.scope_3_co2_kg = s3
            existing.intensity_per_area = intensity_area
            footprint = existing
        else:
            footprint = CarbonFootprint(
                facility_id=facility_id,
                calculation_start=start_date,
                calculation_end=end_date,
                calculation_year=year,
                calculation_month=month,
                calculation_quarter=quarter,
                total_co2_kg=total,
                scope_1_co2_kg=s1 if s1 > 0 else None,
                scope_2_co2_kg=s2 if s2 > 0 else None,
                scope_3_co2_kg=s3 if s3 > 0 else None,
                intensity_per_area=intensity_area,
            )
            self.db.add(footprint)

        await self.db.flush()
        return footprint
