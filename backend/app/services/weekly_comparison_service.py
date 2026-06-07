from datetime import date, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.energy_consumption import EnergyConsumption
from app.models.energy_source import EnergySource
from app.models.facility import Facility


def _get_week_boundaries(ref_date: date | None = None) -> tuple[datetime, datetime, datetime, datetime]:
    """Returns (current_monday, current_sunday, prev_monday, prev_sunday) for the last COMPLETE week."""
    if ref_date is None:
        ref_date = date.today()
    # Go to last Monday
    days_since_monday = ref_date.weekday()  # Monday=0
    last_monday = ref_date - timedelta(days=days_since_monday)
    # The most recent COMPLETE week is the one BEFORE the current partial week
    current_monday = last_monday - timedelta(weeks=1)
    current_sunday = current_monday + timedelta(days=6)
    prev_monday = current_monday - timedelta(weeks=1)
    prev_sunday = current_sunday - timedelta(weeks=1)
    return (
        datetime.combine(current_monday, datetime.min.time()),
        datetime.combine(current_sunday, datetime.max.time()),
        datetime.combine(prev_monday, datetime.min.time()),
        datetime.combine(prev_sunday, datetime.max.time()),
    )


class WeeklyComparisonService:
    """Haftalık enerji tüketim karşılaştırması ve threshold-based alert üretimi."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _check_facility(self, facility_id: UUID, user_id: UUID) -> None:
        q = select(Facility.id).where(
            Facility.id == facility_id, Facility.user_id == user_id
        )
        r = await self.db.execute(q)
        if r.scalar_one_or_none() is None:
            raise ValueError("Tesis bulunamadı veya size ait değil.")

    async def _get_week_total(
        self, facility_id: UUID, start: datetime, end: datetime
    ) -> float:
        """Tek bir haftanın toplam tüketimini döndürür."""
        q = select(
            func.coalesce(func.sum(EnergyConsumption.consumption_value), 0)
        ).where(
            EnergyConsumption.facility_id == facility_id,
            EnergyConsumption.recorded_at >= start,
            EnergyConsumption.recorded_at <= end,
            EnergyConsumption.consumption_type == "consumption",
        )
        r = await self.db.execute(q)
        return float(r.scalar_one())

    async def _get_week_by_source(
        self, facility_id: UUID, start: datetime, end: datetime
    ) -> dict[UUID, float]:
        """Kaynak bazında haftalık tüketim döndürür."""
        q = (
            select(
                EnergyConsumption.energy_source_id,
                func.coalesce(func.sum(EnergyConsumption.consumption_value), 0),
            )
            .where(
                EnergyConsumption.facility_id == facility_id,
                EnergyConsumption.recorded_at >= start,
                EnergyConsumption.recorded_at <= end,
                EnergyConsumption.consumption_type == "consumption",
            )
            .group_by(EnergyConsumption.energy_source_id)
        )
        rows = await self.db.execute(q)
        return {row[0]: float(row[1]) for row in rows}

    async def compare_weeks(
        self,
        facility_id: UUID,
        user_id: UUID,
        end_date: date | None = None,
    ) -> dict:
        """Bu hafta vs geçen hafta karşılaştırması."""
        await self._check_facility(facility_id, user_id)
        cur_start, cur_end, prev_start, prev_end = _get_week_boundaries(end_date)

        current_total = await self._get_week_total(facility_id, cur_start, cur_end)
        previous_total = await self._get_week_total(facility_id, prev_start, prev_end)

        change_pct = 0.0
        if previous_total > 0:
            change_pct = round(((current_total - previous_total) / previous_total) * 100, 2)

        # Kaynak bazında
        cur_sources = await self._get_week_by_source(facility_id, cur_start, cur_end)
        prev_sources = await self._get_week_by_source(facility_id, prev_start, prev_end)

        # EnergySource isimlerini al
        all_source_ids = set(cur_sources.keys()) | set(prev_sources.keys())
        src_names: dict[UUID, str] = {}
        src_units: dict[UUID, str] = {}
        if all_source_ids:
            src_q = select(EnergySource).where(EnergySource.id.in_(all_source_ids))
            src_rows = await self.db.execute(src_q)
            for s in src_rows.scalars().all():
                src_names[s.id] = s.name
                src_units[s.id] = s.unit

        sources = []
        for sid in all_source_ids:
            cur_val = cur_sources.get(sid, 0)
            prev_val = prev_sources.get(sid, 0)
            sc_pct = 0.0
            if prev_val > 0:
                sc_pct = round(((cur_val - prev_val) / prev_val) * 100, 2)
            sources.append({
                "energy_source_id": sid,
                "energy_source_name": src_names.get(sid, ""),
                "current_week_value": round(cur_val, 2),
                "previous_week_value": round(prev_val, 2),
                "change_pct": sc_pct,
                "unit": src_units.get(sid, "kWh"),
            })

        return {
            "facility_id": facility_id,
            "current_week_label": cur_start.strftime("%Y-W%W"),
            "previous_week_label": prev_start.strftime("%Y-W%W"),
            "current_week_total": round(current_total, 2),
            "previous_week_total": round(previous_total, 2),
            "total_change_pct": change_pct,
            "sources": sources,
        }

    async def check_alerts(
        self,
        facility_id: UUID,
        user_id: UUID,
        threshold_pct: float = 20.0,
    ) -> dict:
        """Threshold aşımı varsa Alert oluşturur."""
        from app.schemas.alert import AlertCreate
        from app.services.alert_service import AlertService

        comparison = await self.compare_weeks(facility_id, user_id)
        alert_service = AlertService(self.db)
        alerts_created = 0
        source_details = []

        for src in comparison["sources"]:
            change = src["change_pct"]
            severity = "info"
            if abs(change) > 50:
                severity = "critical"
            elif abs(change) > 30:
                severity = "high"
            elif abs(change) > 20:
                severity = "medium"

            created = 0
            if abs(change) > threshold_pct:
                alert_data = AlertCreate(
                    facility_id=facility_id,
                    title=f"{src['energy_source_name']} tüketimi %{abs(change):.0f} {'arttı' if change > 0 else 'azaldı'}",
                    message=f"Geçen haftaya göre {src['energy_source_name']} tüketimi %{abs(change):.1f} oranında {'artış' if change > 0 else 'azalış'} gösterdi.",
                    severity=severity,
                    category="weekly_comparison",
                    source="system",
                    deviation_percent=change,
                )
                try:
                    await alert_service.create(user_id=user_id, data=alert_data)
                    created = 1
                    alerts_created += 1
                except ValueError:
                    pass

            source_details.append({
                "energy_source_id": src["energy_source_id"],
                "energy_source_name": src["energy_source_name"],
                "current_week_value": src["current_week_value"],
                "previous_week_value": src["previous_week_value"],
                "change_pct": src["change_pct"],
                "unit": src["unit"],
                "created_alerts": created,
            })

        return {
            "compared": comparison,
            "alerts_created": alerts_created,
            "source_details": source_details,
        }
