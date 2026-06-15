from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.cost_savings import (
    DailyComparisonResponse,
    ProductionSavingsListResponse,
    SavingsSummaryResponse,
)
from app.services.cost_savings_service import CostSavingsService

router = APIRouter(prefix="/cost-savings", tags=["cost-savings"])


def _build_list_response(items, total, total_savings, total_co2, total_tree):
    return ProductionSavingsListResponse(
        items=[
            {
                "id": i["id"],
                "facility_id": i["facility_id"],
                "energy_source_id": i["energy_source_id"],
                "energy_source_name": i["energy_source_name"],
                "recorded_at": i["recorded_at"],
                "consumption_value": i["consumption_value"],
                "unit": i["unit"],
                "savings_amount": i["savings_amount"],
                "co2_avoided_kg": i["co2_avoided_kg"],
                "tree_equivalent": i["tree_equivalent"],
            }
            for i in items
        ],
        total=total,
        total_savings=total_savings,
        total_co2_avoided=total_co2,
        total_tree_equivalent=total_tree,
    )


@router.get("/", response_model=ProductionSavingsListResponse)
async def list_savings(
    facility_id: UUID = Query(..., description="Tesis ID"),
    date_from: date | None = Query(None, description="Başlangıç tarihi"),
    date_to: date | None = Query(None, description="Bitiş tarihi"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Üretim kayıtlarını tasarruf hesaplarıyla listeler."""
    service = CostSavingsService(db)
    try:
        items, total, total_savings, total_co2, total_tree = await service.list_by_facility(
            facility_id, current_user.id, date_from, date_to, skip, limit
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return _build_list_response(items, total, total_savings, total_co2, total_tree)


@router.get("/summary", response_model=SavingsSummaryResponse)
async def savings_summary(
    facility_id: UUID = Query(..., description="Tesis ID"),
    date_from: date | None = Query(None, description="Başlangıç tarihi"),
    date_to: date | None = Query(None, description="Bitiş tarihi"),
    energy_source_id: UUID | None = Query(None, description="Enerji kaynağı filtresi"),
    consumption_type: str | None = Query(None, description="Tüketim tipi (consumption/production)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Özet istatistikler: toplam üretim, tasarruf, CO2, ağaç eşdeğeri."""
    service = CostSavingsService(db)
    try:
        summary = await service.get_summary(facility_id, current_user.id, date_from, date_to, energy_source_id, consumption_type)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return summary


@router.get("/daily", response_model=DailyComparisonResponse)
async def daily_comparison(
    facility_id: UUID = Query(..., description="Tesis ID"),
    date_from: date | None = Query(None, description="Başlangıç tarihi"),
    date_to: date | None = Query(None, description="Bitiş tarihi"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Günlük üretim/tasarruf kırılımı."""
    service = CostSavingsService(db)
    try:
        items = await service.get_daily_comparison(facility_id, current_user.id, date_from, date_to)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return DailyComparisonResponse(items=items)
