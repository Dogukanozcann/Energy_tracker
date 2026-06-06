from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.facility import Facility
from app.schemas.facility import FacilityCreate, FacilityUpdate


class FacilityService:
    """Facility CRUD iş mantığı."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user_id: UUID, data: FacilityCreate) -> Facility:
        facility = Facility(
            user_id=user_id,
            **data.model_dump(),
        )
        self.db.add(facility)
        await self.db.flush()
        return facility

    async def list_by_user(
        self, user_id: UUID, skip: int = 0, limit: int = 20
    ) -> tuple[list[Facility], int]:
        count_q = select(func.count(Facility.id)).where(Facility.user_id == user_id)
        total = (await self.db.execute(count_q)).scalar_one()

        query = (
            select(Facility)
            .where(Facility.user_id == user_id)
            .order_by(Facility.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        items = list((await self.db.execute(query)).scalars().all())
        return items, total

    async def get_by_id(self, facility_id: UUID, user_id: UUID) -> Facility | None:
        query = select(Facility).where(
            Facility.id == facility_id, Facility.user_id == user_id
        )
        return (await self.db.execute(query)).scalar_one_or_none()

    async def update(
        self, facility: Facility, data: FacilityUpdate
    ) -> Facility:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(facility, field, value)
        await self.db.flush()
        return facility

    async def delete(self, facility: Facility) -> None:
        await self.db.delete(facility)
        await self.db.flush()
