"""
Karbon Ayak İzi Hesaplama Motoru.

GHG Protocol metodolojisine göre her enerji tüketim kaydının
karbon karşılığını hesaplar ve carbon_footprint_items tablosuna yazar.

Hesaplama mantığı:
  - Enerji kaynağının co2_factor_scope_1 varsa → Scope 1 (doğrudan yakıt)
  - co2_factor_scope_2 varsa → Scope 2 (satın alınan elektrik)
  - Hiçbiri yoksa → Scope 3 (tedarik zinciri, varsayılan 0)
  - calculated_co2_kg = consumption_value * ilgili factor
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
    # PUBLIC: tek kayıt hesaplama
    # ----------------------------------------------------------------

    async def calculate(
        self,
        consumption_id: UUID,
        user_id: UUID,
        force: bool = False,
    ) -> CarbonFootprintItem:
        """
        Bir tüketim kaydının karbon ayak izini hesaplar.

        Parametreler:
          consumption_id: Hesaplanacak tüketim kaydı ID'si
          user_id:        Ownership doğrulaması için kullanıcı
          force:          True = mevcut item varsa üzerine yaz

        Dönüş: CarbonFootprintItem (yeni veya güncellenmiş)
        """
        # Tüketim kaydını energy_source ile birlikte getir
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

    # ----------------------------------------------------------------
    # PUBLIC: toplu hesaplama
    # ----------------------------------------------------------------

    async def calculate_batch(
        self,
        facility_id: UUID,
        user_id: UUID,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        force: bool = False,
    ) -> tuple[int, float]:
        """
        Bir tesisteki hesaplanmamış (veya force=True ise tüm) tüketim
        kayıtları için karbon hesaplaması yapar.

        Dönüş: (işlenen_kayıt_sayısı, toplam_co2_kg)
        """
        # Ownership kontrolü
        q_owner = select(Facility.id).where(
            Facility.id == facility_id, Facility.user_id == user_id
        )
        if (await self.db.execute(q_owner)).scalar_one_or_none() is None:
            raise ValueError("Tesis bulunamadı veya size ait değil.")

        # Hesaplanacak tüketim kayıtlarını bul
        filters = [EnergyConsumption.facility_id == facility_id]
        if date_from:
            filters.append(EnergyConsumption.recorded_at >= date_from)
        if date_to:
            filters.append(EnergyConsumption.recorded_at <= date_to)

        if not force:
            # Sadece henüz item'i olmayanları hesapla
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
    # INTERNAL: hesaplama çekirdeği
    # ----------------------------------------------------------------

    async def _calculate_internal(
        self,
        consumption: EnergyConsumption,
        force: bool = False,
    ) -> CarbonFootprintItem:
        """
        Bir EnergyConsumption kaydını alır, scope ve faktör belirler,
        carbon_footprint_item oluşturur veya günceller.
        """
        source: EnergySource = consumption.energy_source

        # Scope ve faktör belirleme (öncelik: Scope 1 > Scope 2 > Scope 3)
        if source.co2_factor_scope_1 is not None:
            scope = "scope_1"
            factor = float(source.co2_factor_scope_1)
        elif source.co2_factor_scope_2 is not None:
            scope = "scope_2"
            factor = float(source.co2_factor_scope_2)
        else:
            scope = "scope_3"
            factor = 0.0

        calculated_co2 = float(consumption.consumption_value) * factor

        # Mevcut item var mı kontrol et
        q = select(CarbonFootprintItem).where(
            CarbonFootprintItem.energy_consumption_id == consumption.id
        )
        existing = (await self.db.execute(q)).scalar_one_or_none()

        if existing and not force:
            # Zaten hesaplanmış, force=False ise dokunma
            return existing

        if existing:
            # Güncelle
            existing.scope = scope
            existing.energy_source_id = source.id
            existing.consumption_amount = float(consumption.consumption_value)
            existing.consumption_unit = consumption.unit
            existing.co2_factor_used = factor
            existing.calculated_co2_kg = calculated_co2
            existing.factor_source = source.co2_factor_source
            item = existing
        else:
            # Yeni oluştur
            item = CarbonFootprintItem(
                energy_consumption_id=consumption.id,
                energy_source_id=source.id,
                scope=scope,
                consumption_amount=float(consumption.consumption_value),
                consumption_unit=consumption.unit,
                co2_factor_used=factor,
                calculated_co2_kg=calculated_co2,
                factor_source=source.co2_factor_source,
            )
            self.db.add(item)

        await self.db.flush()
        return item
