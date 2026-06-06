from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.models.facility import Facility
from app.schemas.alert import AlertCreate


class AlertService:
    """Alert CRUD + status lifecycle yönetimi."""

    VALID_TRANSITIONS = {
        "new": {"acknowledged"},
        "acknowledged": {"resolved", "dismissed"},
        "resolved": set(),
        "dismissed": set(),
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _check_facility(self, facility_id: UUID, user_id: UUID) -> None:
        q = select(Facility.id).where(
            Facility.id == facility_id, Facility.user_id == user_id
        )
        if (await self.db.execute(q)).scalar_one_or_none() is None:
            raise ValueError("Tesis bulunamadı veya size ait değil.")

    async def create(
        self, user_id: UUID, data: AlertCreate
    ) -> Alert:
        """Manuel uyarı oluşturur."""
        await self._check_facility(data.facility_id, user_id)

        alert = Alert(
            facility_id=data.facility_id,
            energy_consumption_id=data.energy_consumption_id,
            energy_source_id=data.energy_source_id,
            title=data.title,
            description=data.description,
            severity=data.severity,
            category=data.category,
            detected_value=data.detected_value,
            expected_value=data.expected_value,
            threshold_value=data.threshold_value,
            deviation_percent=data.deviation_percent,
            recommendation_text=data.recommendation_text,
            is_auto_generated=False,
        )
        self.db.add(alert)
        await self.db.flush()
        return alert

    async def list_by_facility(
        self,
        facility_id: UUID,
        user_id: UUID,
        status_filter: str | None = None,
        severity_filter: str | None = None,
        category_filter: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Alert], int, int, int]:
        """
        Uyarıları filtreleyerek listeler.
        Dönüş: (items, total, new_count, critical_count)
        """
        await self._check_facility(facility_id, user_id)

        base = [Alert.facility_id == facility_id]
        if status_filter:
            base.append(Alert.status == status_filter)
        if severity_filter:
            base.append(Alert.severity == severity_filter)
        if category_filter:
            base.append(Alert.category == category_filter)

        # Count
        total = (
            await self.db.execute(select(func.count(Alert.id)).where(*base))
        ).scalar_one()

        # Özet istatistikler
        new_count = (
            await self.db.execute(
                select(func.count(Alert.id)).where(
                    Alert.facility_id == facility_id,
                    Alert.status == "new",
                )
            )
        ).scalar_one()

        critical_count = (
            await self.db.execute(
                select(func.count(Alert.id)).where(
                    Alert.facility_id == facility_id,
                    Alert.severity == "critical",
                    Alert.status.in_(["new", "acknowledged"]),
                )
            )
        ).scalar_one()

        # Items
        q = (
            select(Alert)
            .where(*base)
            .order_by(
                Alert.severity.desc(),  # Önce kritik olanlar
                Alert.detected_at.desc(),
            )
            .offset(skip)
            .limit(limit)
        )
        items = list((await self.db.execute(q)).scalars().all())

        return items, total, new_count, critical_count

    async def get_by_id(self, alert_id: UUID, user_id: UUID) -> Alert | None:
        q = (
            select(Alert)
            .join(Facility, Facility.id == Alert.facility_id)
            .where(Alert.id == alert_id, Facility.user_id == user_id)
        )
        return (await self.db.execute(q)).scalar_one_or_none()

    async def update_status(
        self, alert: Alert, new_status: str, resolved_by: UUID | None = None
    ) -> Alert:
        """Uyarı durumunu geçerli bir transition ile günceller."""
        allowed = self.VALID_TRANSITIONS.get(alert.status, set())
        if new_status not in allowed:
            raise ValueError(
                f"'{alert.status}' → '{new_status}' geçersiz geçiş. "
                f"İzin verilenler: {allowed}"
            )

        alert.status = new_status
        if new_status in ("resolved", "dismissed"):
            alert.resolved_at = datetime.now(timezone.utc)
            alert.resolved_by = resolved_by

        await self.db.flush()
        return alert

    async def delete(self, alert: Alert) -> None:
        await self.db.delete(alert)
        await self.db.flush()
