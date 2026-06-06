"""
CSV/Excel ile toplu enerji tüketim verisi import endpoint'i.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.energy_consumption import BatchImportResponse
from app.services.import_service import ImportService

router = APIRouter(prefix="/imports", tags=["imports"])


@router.post(
    "/consumption",
    response_model=BatchImportResponse,
    summary="CSV/Excel ile toplu tüketim importu",
)
async def import_consumption(
    facility_id: str,
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """CSV dosyasından toplu enerji tüketim verisi yükler.
    
    CSV formatı: recorded_at, consumption_value, unit, source, cost
    Tarih ISO formatında (2025-01-15T14:30:00), ondalık ayracı nokta veya virgül.
    """
    if not file.filename or not (file.filename.endswith(".csv") or file.filename.endswith(".txt")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sadece CSV dosyaları destekleniyor.",
        )

    content = (await file.read()).decode("utf-8-sig")
    service = ImportService(db)

    try:
        result = await service.import_consumption_csv(
            facility_id=UUID(facility_id),
            content=content,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return BatchImportResponse(
        created=result.created,
        skipped=result.skipped,
        errors=result.errors[:50],  # İlk 50 hata
        message=f"{result.created} kayıt eklendi, {result.skipped} atlandı.",
    )
