from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.weekly_comparison import WeeklyAlertResponse, WeeklyComparisonResponse
from app.services.weekly_comparison_service import WeeklyComparisonService

router = APIRouter(prefix="/weekly-comparison", tags=["weekly-comparison"])


@router.get("/", response_model=WeeklyComparisonResponse)
async def compare_weeks(
    facility_id: UUID = Query(..., description="Tesis ID"),
    end_date: date | None = Query(None, description="Referans tarih (opsiyonel)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Bu hafta vs geçen hafta karşılaştırması."""
    service = WeeklyComparisonService(db)
    try:
        result = await service.compare_weeks(facility_id, current_user.id, end_date)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return result


@router.post("/check-alerts", response_model=WeeklyAlertResponse)
async def check_alerts(
    facility_id: UUID = Query(..., description="Tesis ID"),
    threshold_pct: float = Query(20.0, ge=0, le=100, description="Uyarı eşiği (%)"),
    end_date: date | None = Query(None, description="Referans tarih (opsiyonel)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Threshold aşımı varsa alert oluşturur."""
    service = WeeklyComparisonService(db)
    try:
        result = await service.check_alerts(facility_id, current_user.id, threshold_pct)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return result
