from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.carbon_footprint import CarbonFootprintItem
from app.models.energy_consumption import EnergyConsumption
from app.models.facility import Facility
from app.models.user import User
from app.schemas.carbon import (
    BatchCalculateResponse,
    CarbonBatchCalculateRequest,
    CarbonCalculateRequest,
    CarbonFootprintItemListResponse,
    CarbonFootprintItemResponse,
    CarbonFootprintListResponse,
    CarbonFootprintResponse,
    FootprintGenerateRequest,
)
from app.services.carbon_calculator import CarbonCalculatorService
from app.services.carbon_footprint_service import CarbonFootprintService

router = APIRouter(prefix="/carbon", tags=["carbon"])


# ========== ITEM-LEVEL (Carbon Calculator) ==========


@router.post(
    "/calculate",
    response_model=CarbonFootprintItemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def calculate_single(
    data: CarbonCalculateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Tek bir tüketim kaydı için karbon ayak izi hesaplar."""
    service = CarbonCalculatorService(db)
    try:
        item = await service.calculate(
            consumption_id=data.consumption_id,
            user_id=current_user.id,
            force=data.force_recalculate,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return CarbonFootprintItemResponse.model_validate(item)


@router.post(
    "/calculate-batch",
    response_model=BatchCalculateResponse,
)
async def calculate_batch(
    data: CarbonBatchCalculateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Bir tesisteki hesaplanmamış tüm tüketimler için toplu karbon hesaplaması yapar."""
    service = CarbonCalculatorService(db)
    try:
        count, total_co2, source_breakdown = await service.calculate_batch(
            facility_id=data.facility_id,
            user_id=current_user.id,
            date_from=data.date_from,
            date_to=data.date_to,
            energy_source_id=data.energy_source_id,
            consumption_type=data.consumption_type,
            force=data.force_recalculate,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    breakdown_list = [
        {"source_name": name, "co2_kg": round(val, 4)}
        for name, val in sorted(source_breakdown.items(), key=lambda x: -x[1])
    ]

    return BatchCalculateResponse(
        processed=count,
        total_co2_kg=round(total_co2, 4),
        source_breakdown=breakdown_list,
        message=f"{count} kayıt işlendi, toplam {total_co2:.2f} kg CO2e hesaplandı."
        if count > 0
        else "Hesaplanacak yeni kayıt bulunamadı.",
    )


# ========== ITEM LIST ==========


@router.get("/items", response_model=CarbonFootprintItemListResponse)
async def list_items(
    facility_id: UUID = Query(..., description="Tesis ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Bir tesise ait tüm karbon ayak izi kalemlerini listeler."""
    # Ownership
    q_owner = select(Facility.id).where(
        Facility.id == facility_id, Facility.user_id == current_user.id
    )
    if (await db.execute(q_owner)).scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tesis bulunamadı.")

    # Count
    count_q = (
        select(func.count(CarbonFootprintItem.id))
        .join(EnergyConsumption)
        .where(EnergyConsumption.facility_id == facility_id)
    )
    total = (await db.execute(count_q)).scalar_one()

    # Sum
    sum_q = (
        select(func.coalesce(func.sum(CarbonFootprintItem.calculated_co2_kg), 0))
        .join(EnergyConsumption)
        .where(EnergyConsumption.facility_id == facility_id)
    )
    total_co2 = float((await db.execute(sum_q)).scalar_one())

    # Items
    q = (
        select(CarbonFootprintItem)
        .join(EnergyConsumption)
        .where(EnergyConsumption.facility_id == facility_id)
        .order_by(CarbonFootprintItem.calculated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    items = list((await db.execute(q)).scalars().all())

    return CarbonFootprintItemListResponse(
        items=[CarbonFootprintItemResponse.model_validate(i) for i in items],
        total=total,
        total_co2_kg=total_co2,
    )


# ========== AGGREGATION (Footprints) ==========


@router.post(
    "/footprints/generate",
    response_model=CarbonFootprintResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_footprint(
    data: FootprintGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Belirli bir dönem (ay/yıl) için karbon özeti oluşturur."""
    service = CarbonFootprintService(db)
    try:
        if data.month:
            footprint = await service.generate_monthly(
                facility_id=data.facility_id,
                user_id=current_user.id,
                year=data.year,
                month=data.month,
            )
        else:
            footprint = await service.generate_yearly(
                facility_id=data.facility_id,
                user_id=current_user.id,
                year=data.year,
            )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return CarbonFootprintResponse.model_validate(footprint)


@router.get("/footprints", response_model=CarbonFootprintListResponse)
async def list_footprints(
    facility_id: UUID = Query(..., description="Tesis ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Tesise ait periyodik karbon özetlerini listeler."""
    service = CarbonFootprintService(db)
    try:
        items, total = await service.list_footprints(
            facility_id=facility_id,
            user_id=current_user.id,
            skip=skip,
            limit=limit,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return CarbonFootprintListResponse(
        items=[CarbonFootprintResponse.model_validate(f) for f in items],
        total=total,
    )
