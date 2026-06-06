from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.facility import (
    FacilityCreate,
    FacilityListResponse,
    FacilityResponse,
    FacilityUpdate,
)
from app.services.facility_service import FacilityService

router = APIRouter(prefix="/facilities", tags=["facilities"])


@router.post("/", response_model=FacilityResponse, status_code=status.HTTP_201_CREATED)
async def create_facility(
    data: FacilityCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Yeni tesis oluşturur."""
    service = FacilityService(db)
    facility = await service.create(user_id=current_user.id, data=data)
    return FacilityResponse.model_validate(facility)


@router.get("/", response_model=FacilityListResponse)
async def list_facilities(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Kullanıcının tüm tesislerini listeler."""
    service = FacilityService(db)
    items, total = await service.list_by_user(
        user_id=current_user.id, skip=skip, limit=limit
    )
    return FacilityListResponse(
        items=[FacilityResponse.model_validate(f) for f in items],
        total=total,
    )


@router.get("/{facility_id}", response_model=FacilityResponse)
async def get_facility(
    facility_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Tek bir tesisin detayını döner."""
    service = FacilityService(db)
    facility = await service.get_by_id(facility_id, user_id=current_user.id)
    if facility is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tesis bulunamadı.")
    return FacilityResponse.model_validate(facility)


@router.put("/{facility_id}", response_model=FacilityResponse)
async def update_facility(
    facility_id: UUID,
    data: FacilityUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Tesis bilgilerini günceller."""
    service = FacilityService(db)
    facility = await service.get_by_id(facility_id, user_id=current_user.id)
    if facility is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tesis bulunamadı.")
    updated = await service.update(facility, data)
    return FacilityResponse.model_validate(updated)


@router.delete("/{facility_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_facility(
    facility_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Tesisi siler (ilişkili veriler de kademeli olarak silinir)."""
    service = FacilityService(db)
    facility = await service.get_by_id(facility_id, user_id=current_user.id)
    if facility is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tesis bulunamadı.")
    await service.delete(facility)
