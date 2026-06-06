from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.alert import (
    AlertCreate,
    AlertListResponse,
    AlertResponse,
    AlertStatusUpdate,
    DetectAnomalyRequest,
    DetectAnomalyResponse,
)
from app.services.alert_service import AlertService
from app.services.anomaly_detector import AnomalyDetectorService

router = APIRouter(prefix="/alerts", tags=["alerts"])


# ========== MANUAL CRUD ==========


@router.post(
    "/",
    response_model=AlertResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_alert(
    data: AlertCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manuel uyarı oluşturur."""
    service = AlertService(db)
    try:
        alert = await service.create(user_id=current_user.id, data=data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return AlertResponse.model_validate(alert)


@router.get("/", response_model=AlertListResponse)
async def list_alerts(
    facility_id: UUID = Query(..., description="Tesis ID"),
    status: str | None = Query(None, description="Filtre: status"),
    severity: str | None = Query(None, description="Filtre: severity"),
    category: str | None = Query(None, description="Filtre: category"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Uyarıları listeler (filtreleme + sıralama + özet istatistikler)."""
    service = AlertService(db)
    try:
        items, total, new_count, critical_count = await service.list_by_facility(
            facility_id=facility_id,
            user_id=current_user.id,
            status_filter=status,
            severity_filter=severity,
            category_filter=category,
            skip=skip,
            limit=limit,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return AlertListResponse(
        items=[AlertResponse.model_validate(a) for a in items],
        total=total,
        new_count=new_count,
        critical_count=critical_count,
    )


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Tek uyarı detayı."""
    service = AlertService(db)
    alert = await service.get_by_id(alert_id, user_id=current_user.id)
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Uyarı bulunamadı.")
    return AlertResponse.model_validate(alert)


@router.patch("/{alert_id}/status", response_model=AlertResponse)
async def update_alert_status(
    alert_id: UUID,
    data: AlertStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Uyarı durumunu günceller (acknowledge → resolve → dismiss)."""
    service = AlertService(db)
    alert = await service.get_by_id(alert_id, user_id=current_user.id)
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Uyarı bulunamadı.")

    try:
        updated = await service.update_status(
            alert, new_status=data.status, resolved_by=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    return AlertResponse.model_validate(updated)


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(
    alert_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Uyarı kaydını siler."""
    service = AlertService(db)
    alert = await service.get_by_id(alert_id, user_id=current_user.id)
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Uyarı bulunamadı.")
    await service.delete(alert)


# ========== ANOMALY DETECTION ==========


@router.post("/detect", response_model=DetectAnomalyResponse)
async def detect_anomalies(
    data: DetectAnomalyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Anomali tespit motorunu çalıştırır.
    Son 24 saatteki tüketim verilerini geçmiş 7 günlük baseline ile
    karşılaştırır ve eşik üstü sapmaları uyarıya çevirir.
    """
    detector = AnomalyDetectorService(db)
    try:
        alerts = await detector.detect(
            facility_id=data.facility_id,
            user_id=current_user.id,
            energy_source_id=data.energy_source_id,
            date_from=data.date_from,
            date_to=data.date_to,
            deviation_threshold=data.deviation_threshold,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    count = len(alerts)
    return DetectAnomalyResponse(
        alerts_created=count,
        message=(
            f"{count} anomali tespit edildi."
            if count > 0
            else "Anomali tespit edilmedi."
        ),
    )
