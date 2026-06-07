from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.energy_source import EnergySource
from app.models.user import User
from pydantic import BaseModel
from uuid import UUID


class EnergySourceResponse(BaseModel):
    id: UUID
    name: str
    name_tr: str | None
    category: str
    unit: str
    formula_type: str
    is_renewable: bool
    co2_factor_scope_1: float | None
    co2_factor_scope_2: float | None

    model_config = {"from_attributes": True}


router = APIRouter(prefix="/energy-sources", tags=["energy-sources"])


@router.get("/", response_model=list[EnergySourceResponse])
async def list_sources(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Tüm aktif enerji kaynaklarını listeler."""
    result = await db.execute(
        select(EnergySource).where(EnergySource.is_active == True)
    )
    sources = result.scalars().all()
    return [EnergySourceResponse.model_validate(s) for s in sources]
