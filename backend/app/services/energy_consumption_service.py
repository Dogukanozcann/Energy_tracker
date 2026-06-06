from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.energy_consumption import EnergyConsumption
from app.models.facility import Facility
from app.schemas.energy_consumption import EnergyConsumptionCreate


class EnergyConsumptionService:
    """EnergyConsumption CRUD + zaman-serisi filtreleme."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _check_facility_ownership(
        self, facility_id: UUID, user_id: UUID
    ) -> None:
        """Tesisin kullanıcıya ait olduğunu doğrular."""
        q = select(Facility.id).where(
            Facility.id == facility_id, Facility.user_id == user_id
        )
        result = await self.db.execute(q)
        if result.scalar_one_or_none() is None:
            raise ValueError("Tesis bulunamadı veya size ait değil.")

    async def create(
        self, user_id: UUID, data: EnergyConsumptionCreate
    ) -> EnergyConsumption:
        """Tek tüketim kaydı oluşturur."""
        await self._check_facility_ownership(data.facility_id, user_id)

        record = EnergyConsumption(**data.model_dump())
        self.db.add(record)
        await self.db.flush()
        return record

    async def create_batch(
        self, user_id: UUID, items: list[EnergyConsumptionCreate]
    ) -> list[EnergyConsumption]:
        """Toplu tüketim kaydı oluşturur (5000 adete kadar)."""
        if not items:
            return []

        # Tüm facility_id'lerin kullanıcıya ait olduğunu tek sorguda kontrol et
        facility_ids = {i.facility_id for i in items}
        q = select(Facility.id).where(
            Facility.id.in_(facility_ids), Facility.user_id == user_id
        )
        result = set((await self.db.execute(q)).scalars().all())

        missing = facility_ids - result
        if missing:
            raise ValueError(
                f"Tesis(ler) bulunamadı veya size ait değil: {missing}"
            )

        records = [EnergyConsumption(**i.model_dump()) for i in items]
        self.db.add_all(records)
        await self.db.flush()
        return records

    async def list_by_facility(
        self,
        facility_id: UUID,
        user_id: UUID,
        energy_source_id: UUID | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[EnergyConsumption], int, float | None, float | None]:
        """
        Tesise ait tüketim kayıtlarını filtreleyerek döndürür.
        Dönüş: (items, total_count, total_value, total_cost)
        """
        await self._check_facility_ownership(facility_id, user_id)

        # Dinamik filtre
        base_filters = [EnergyConsumption.facility_id == facility_id]
        if energy_source_id:
            base_filters.append(
                EnergyConsumption.energy_source_id == energy_source_id
            )
        if date_from:
            base_filters.append(EnergyConsumption.recorded_at >= date_from)
        if date_to:
            base_filters.append(EnergyConsumption.recorded_at <= date_to)

        # Count
        count_q = select(func.count(EnergyConsumption.id)).where(*base_filters)
        total = (await self.db.execute(count_q)).scalar_one()

        # Aggregasyon (toplam tüketim ve maliyet)
        agg_q = select(
            func.coalesce(func.sum(EnergyConsumption.consumption_value), 0),
            func.coalesce(func.sum(EnergyConsumption.cost), 0),
        ).where(*base_filters)
        total_value, total_cost = (await self.db.execute(agg_q)).one()
        total_value = float(total_value) if total_value else None
        total_cost = float(total_cost) if total_cost else None

        # Veriler
        query = (
            select(EnergyConsumption)
            .where(*base_filters)
            .order_by(EnergyConsumption.recorded_at.desc())
            .offset(skip)
            .limit(limit)
        )
        items = list((await self.db.execute(query)).scalars().all())

        return items, total, total_value, total_cost

    async def get_by_id(
        self, record_id: UUID, user_id: UUID
    ) -> EnergyConsumption | None:
        """Tek kaydı, ownership kontrolü ile döndürür."""
        q = (
            select(EnergyConsumption)
            .join(Facility, Facility.id == EnergyConsumption.facility_id)
            .where(
                EnergyConsumption.id == record_id,
                Facility.user_id == user_id,
            )
        )
        return (await self.db.execute(q)).scalar_one_or_none()

    async def delete(self, record: EnergyConsumption) -> None:
        """Tüketim kaydını siler."""
        await self.db.delete(record)
        await self.db.flush()
