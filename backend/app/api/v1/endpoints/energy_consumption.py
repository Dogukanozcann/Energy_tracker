from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.energy_consumption import (
    EnergyConsumptionBatchCreate,
    EnergyConsumptionCreate,
    EnergyConsumptionListResponse,
    EnergyConsumptionResponse,
)
from app.services.energy_consumption_service import EnergyConsumptionService

router = APIRouter(prefix="/energy-consumption", tags=["energy-consumption"])


@router.post(
    "/",
    response_model=EnergyConsumptionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_consumption(
    data: EnergyConsumptionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Tek bir enerji tüketim kaydı ekler."""
    service = EnergyConsumptionService(db)
    try:
        record = await service.create(user_id=current_user.id, data=data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return EnergyConsumptionResponse.model_validate(record)


@router.post(
    "/batch",
    response_model=list[EnergyConsumptionResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_consumption_batch(
    data: EnergyConsumptionBatchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Toplu enerji tüketim kaydı ekler.
    Tek seferde en fazla 5000 kayıt.
    """
    service = EnergyConsumptionService(db)
    try:
        records = await service.create_batch(
            user_id=current_user.id, items=data.items
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return [EnergyConsumptionResponse.model_validate(r) for r in records]


@router.get("/", response_model=EnergyConsumptionListResponse)
async def list_consumption(
    facility_id: UUID = Query(..., description="Tesis ID"),
    energy_source_id: UUID | None = Query(None, description="Enerji kaynağı filtresi"),
    consumption_type: str | None = Query(None, description="consumption | production"),
    date_from: datetime | None = Query(None, description="Başlangıç tarihi (ISO8601)"),
    date_to: datetime | None = Query(None, description="Bitiş tarihi (ISO8601)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Tesise ait enerji tüketim kayıtlarını listeler.
    Zaman aralığı, enerji kaynağı ve tüketim tipi ile filtreleme yapılabilir.
    """
    service = EnergyConsumptionService(db)
    try:
        items, total, total_value, total_cost = await service.list_by_facility(
            facility_id=facility_id,
            user_id=current_user.id,
            energy_source_id=energy_source_id,
            consumption_type=consumption_type,
            date_from=date_from,
            date_to=date_to,
            skip=skip,
            limit=limit,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return EnergyConsumptionListResponse(
        items=[EnergyConsumptionResponse.model_validate(r) for r in items],
        total=total,
        total_value=total_value,
        total_cost=total_cost,
    )


@router.get("/{record_id}", response_model=EnergyConsumptionResponse)
async def get_consumption(
    record_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Tek bir tüketim kaydının detayını döndürür."""
    service = EnergyConsumptionService(db)
    record = await service.get_by_id(record_id, user_id=current_user.id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Kayıt bulunamadı."
        )
    return EnergyConsumptionResponse.model_validate(record)


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_consumption(
    record_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Bir tüketim kaydını siler."""
    service = EnergyConsumptionService(db)
    record = await service.get_by_id(record_id, user_id=current_user.id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Kayıt bulunamadı."
        )
    await service.delete(record)
