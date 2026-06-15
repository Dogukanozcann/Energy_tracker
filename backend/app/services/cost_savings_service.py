from datetime import date, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.config import settings
from app.models.energy_consumption import EnergyConsumption
from app.models.energy_source import EnergySource
from app.models.facility import Facility


class CostSavingsService:
    """Üretilen yenilenebilir enerjinin parasal ve çevresel karşılığını hesaplar."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.grid_rate = getattr(settings, "GRID_ELECTRICITY_UNIT_PRICE", 2.5)

    async def _check_facility(self, facility_id: UUID, user_id: UUID) -> None:
        q = select(Facility.id).where(
            Facility.id == facility_id, Facility.user_id == user_id
        )
        r = await self.db.execute(q)
        if r.scalar_one_or_none() is None:
            raise ValueError("Tesis bulunamadı veya size ait değil.")

    async def list_by_facility(
        self,
        facility_id: UUID,
        user_id: UUID,
        date_from: date | None = None,
        date_to: date | None = None,
        energy_source_id: UUID | None = None,
        consumption_type: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[dict], int, float, float, float]:
        """Üretim kayıtlarını tasarruf hesaplarıyla listeler."""
        await self._check_facility(facility_id, user_id)

        base_q = (
            select(EnergyConsumption)
            .join(EnergySource, EnergyConsumption.energy_source_id == EnergySource.id)
            .where(
                EnergyConsumption.facility_id == facility_id,
                EnergyConsumption.consumption_type == "production",
                EnergySource.is_renewable == True,
            )
            .options(joinedload(EnergyConsumption.energy_source))
        )

        if date_from:
            base_q = base_q.where(EnergyConsumption.recorded_at >= datetime.combine(date_from, datetime.min.time()))
        if date_to:
            base_q = base_q.where(EnergyConsumption.recorded_at <= datetime.combine(date_to, datetime.max.time()))
        if energy_source_id:
            base_q = base_q.where(EnergyConsumption.energy_source_id == energy_source_id)
        if consumption_type:
            base_q = base_q.where(EnergyConsumption.consumption_type == consumption_type)

        count_q = select(func.count()).select_from(base_q.subquery())
        total = (await self.db.execute(count_q)).scalar_one()

        rows_q = base_q.order_by(EnergyConsumption.recorded_at.desc()).offset(skip).limit(limit)
        rows = list((await self.db.execute(rows_q)).scalars().all())

        items = []
        total_savings = 0.0
        total_co2 = 0.0
        for r in rows:
            src = r.energy_source
            cost = float(r.cost) if r.cost else 0.0
            savings = cost  # tasarruf = kullanıcının girdiği üretim maliyeti
            co2_avoided = round(float(r.consumption_value) * 0.45, 4)
            tree_eq = round(co2_avoided / 21, 2)
            total_savings += savings
            total_co2 += co2_avoided
            items.append({
                "id": r.id,
                "facility_id": r.facility_id,
                "energy_source_id": r.energy_source_id,
                "energy_source_name": src.name if src else "",
                "recorded_at": r.recorded_at,
                "consumption_value": float(r.consumption_value),
                "unit": r.unit,
                "savings_amount": savings,
                "co2_avoided_kg": co2_avoided,
                "tree_equivalent": tree_eq,
            })

        return items, total, round(total_savings, 2), round(total_co2, 4), round(total_co2 / 21, 2)

    async def get_summary(
        self,
        facility_id: UUID,
        user_id: UUID,
        date_from: date | None = None,
        date_to: date | None = None,
        energy_source_id: UUID | None = None,
        consumption_type: str | None = None,
    ) -> dict:
        """Özet istatistikler: toplam üretim, tasarruf, CO2, ağaç eşdeğeri, maliyet."""
        items, total, total_savings, total_co2, total_tree = await self.list_by_facility(
            facility_id, user_id, date_from, date_to, energy_source_id, consumption_type, limit=99999
        )

        # Kaynak bazında kırılım
        source_map: dict[str, dict] = {}
        for item in items:
            name = item["energy_source_name"]
            if name not in source_map:
                source_map[name] = {"source_name": name, "production": 0, "savings": 0, "co2_avoided": 0}
            source_map[name]["production"] += item["consumption_value"]
            source_map[name]["savings"] += item["savings_amount"]
            source_map[name]["co2_avoided"] += item["co2_avoided_kg"]

        for v in source_map.values():
            v["production"] = round(v["production"], 2)
            v["savings"] = round(v["savings"], 2)
            v["co2_avoided"] = round(v["co2_avoided"], 4)

        return {
            "total_production": round(sum(i["consumption_value"] for i in items), 2),
            "total_savings": total_savings,
            "total_co2_avoided": total_co2,
            "total_tree_equivalent": total_tree,
            "source_breakdown": list(source_map.values()),
        }

    async def get_daily_comparison(
        self,
        facility_id: UUID,
        user_id: UUID,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[dict]:
        """Günlük üretim/tasarruf kırılımı."""
        items, _, _, _, _ = await self.list_by_facility(
            facility_id, user_id, date_from, date_to, limit=99999
        )

        daily: dict[str, dict] = {}
        for item in items:
            day_key = item["recorded_at"].strftime("%Y-%m-%d")
            if day_key not in daily:
                daily[day_key] = {
                    "date": day_key,
                    "production_value": 0,
                    "savings_amount": 0,
                    "co2_avoided_kg": 0,
                    "tree_equivalent": 0,
                }
            daily[day_key]["production_value"] += item["consumption_value"]
            daily[day_key]["savings_amount"] += item["savings_amount"]
            daily[day_key]["co2_avoided_kg"] += item["co2_avoided_kg"]
            daily[day_key]["tree_equivalent"] += item["tree_equivalent"]

        result = []
        for day_key in sorted(daily.keys()):
            d = daily[day_key]
            d["production_value"] = round(d["production_value"], 2)
            d["savings_amount"] = round(d["savings_amount"], 2)
            d["co2_avoided_kg"] = round(d["co2_avoided_kg"], 4)
            d["tree_equivalent"] = round(d["tree_equivalent"], 2)
            result.append(d)

        return result
