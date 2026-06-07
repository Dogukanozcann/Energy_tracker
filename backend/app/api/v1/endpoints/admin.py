"""
Admin paneli endpoint'leri — sadece role='admin' kullanıcılar erişebilir.
Enerji kaynakları, kullanıcı yönetimi, sistem ayarları, audit log.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.api.deps import get_admin_user, get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.admin import (
    AuditLogListResponse,
    AuditLogResponse,
    EnergySourceCreate,
    EnergySourceResponse,
    EnergySourceUpdate,
    SystemSettingCreate,
    SystemSettingListResponse,
    SystemSettingResponse,
    SystemSettingUpdate,
    UserListResponse,
    UserListItem,
    UserUpdate,
)
from app.services.admin_service import AdminService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/admin", tags=["admin"])


def _get_admin_service(db: AsyncSession = Depends(get_db)) -> AdminService:
    return AdminService(db)


async def _audit(
    request: Request,
    admin: User,
    service: AdminService,
    action: str,
    resource: str,
    resource_id: str | None = None,
    details: str | None = None,
):
    await service.log(
        user_id=admin.id,
        user_email=admin.email,
        action=action,
        resource=resource,
        resource_id=resource_id,
        details=details,
        ip_address=request.client.host if request.client else None,
    )


# ========================
# ENERGY SOURCES
# ========================


@router.get("/energy-sources", response_model=list[EnergySourceResponse])
async def admin_list_sources(
    service: AdminService = Depends(_get_admin_service),
    admin: User = Depends(get_admin_user),
):
    """Tüm enerji kaynaklarını listeler (aktif/pasif fark etmez)."""
    sources = await service.list_sources()
    return [EnergySourceResponse.model_validate(s) for s in sources]


@router.get("/energy-sources/{source_id}", response_model=EnergySourceResponse)
async def admin_get_source(
    source_id: UUID,
    service: AdminService = Depends(_get_admin_service),
    admin: User = Depends(get_admin_user),
):
    source = await service.get_source(source_id)
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kaynak bulunamadı.")
    return EnergySourceResponse.model_validate(source)


@router.post("/energy-sources", response_model=EnergySourceResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_source(
    data: EnergySourceCreate,
    request: Request,
    service: AdminService = Depends(_get_admin_service),
    admin: User = Depends(get_admin_user),
):
    source = await service.create_source(data)
    await _audit(request, admin, service, "create", "energy_source", str(source.id), f"Kaynak oluşturuldu: {source.name}")
    return EnergySourceResponse.model_validate(source)


@router.put("/energy-sources/{source_id}", response_model=EnergySourceResponse)
async def admin_update_source(
    source_id: UUID,
    data: EnergySourceUpdate,
    request: Request,
    service: AdminService = Depends(_get_admin_service),
    admin: User = Depends(get_admin_user),
):
    source = await service.update_source(source_id, data)
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kaynak bulunamadı.")
    await _audit(request, admin, service, "update", "energy_source", str(source.id), f"Kaynak güncellendi: {source.name}")
    return EnergySourceResponse.model_validate(source)


@router.delete("/energy-sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_source(
    source_id: UUID,
    request: Request,
    service: AdminService = Depends(_get_admin_service),
    admin: User = Depends(get_admin_user),
):
    source = await service.get_source(source_id)
    if source:
        await _audit(request, admin, service, "delete", "energy_source", str(source.id), f"Kaynak silindi: {source.name}")
    deleted = await service.delete_source(source_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kaynak bulunamadı.")


# ========================
# USERS
# ========================


@router.get("/users", response_model=UserListResponse)
async def admin_list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: AdminService = Depends(_get_admin_service),
    admin: User = Depends(get_admin_user),
):
    users, total = await service.list_users(skip, limit)
    return UserListResponse(
        items=[UserListItem.model_validate(u) for u in users],
        total=total,
    )


@router.get("/users/{user_id}", response_model=UserListItem)
async def admin_get_user(
    user_id: UUID,
    service: AdminService = Depends(_get_admin_service),
    admin: User = Depends(get_admin_user),
):
    user = await service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kullanıcı bulunamadı.")
    return UserListItem.model_validate(user)


@router.put("/users/{user_id}", response_model=UserListItem)
async def admin_update_user(
    user_id: UUID,
    data: UserUpdate,
    request: Request,
    service: AdminService = Depends(_get_admin_service),
    admin: User = Depends(get_admin_user),
):
    user = await service.update_user(user_id, data)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kullanıcı bulunamadı.")
    await _audit(request, admin, service, "update", "user", str(user.id), f"Kullanıcı güncellendi: {user.email}")
    return UserListItem.model_validate(user)


# ========================
# SYSTEM SETTINGS
# ========================


@router.get("/settings", response_model=SystemSettingListResponse)
async def admin_list_settings(
    category: str | None = Query(None),
    service: AdminService = Depends(_get_admin_service),
    admin: User = Depends(get_admin_user),
):
    items, total = await service.list_settings(category)
    return SystemSettingListResponse(
        items=[SystemSettingResponse.model_validate(i) for i in items],
        total=total,
    )


@router.get("/settings/{setting_id}", response_model=SystemSettingResponse)
async def admin_get_setting(
    setting_id: UUID,
    service: AdminService = Depends(_get_admin_service),
    admin: User = Depends(get_admin_user),
):
    setting = await service.get_setting(setting_id)
    if not setting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ayar bulunamadı.")
    return SystemSettingResponse.model_validate(setting)


@router.post("/settings", response_model=SystemSettingResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_setting(
    data: SystemSettingCreate,
    request: Request,
    service: AdminService = Depends(_get_admin_service),
    admin: User = Depends(get_admin_user),
):
    setting = await service.create_setting(data)
    await _audit(request, admin, service, "create", "setting", str(setting.id), f"Ayar oluşturuldu: {setting.key}")
    return SystemSettingResponse.model_validate(setting)


@router.put("/settings/{setting_id}", response_model=SystemSettingResponse)
async def admin_update_setting(
    setting_id: UUID,
    data: SystemSettingUpdate,
    request: Request,
    service: AdminService = Depends(_get_admin_service),
    admin: User = Depends(get_admin_user),
):
    setting = await service.update_setting(setting_id, data)
    if not setting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ayar bulunamadı.")
    await _audit(request, admin, service, "update", "setting", str(setting.id), f"Ayar güncellendi: {setting.key}")
    return SystemSettingResponse.model_validate(setting)


@router.delete("/settings/{setting_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_setting(
    setting_id: UUID,
    request: Request,
    service: AdminService = Depends(_get_admin_service),
    admin: User = Depends(get_admin_user),
):
    deleted = await service.delete_setting(setting_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ayar bulunamadı.")


# ========================
# AUDIT LOGS
# ========================


@router.get("/logs", response_model=AuditLogListResponse)
async def admin_list_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: AdminService = Depends(_get_admin_service),
    admin: User = Depends(get_admin_user),
):
    logs, total = await service.list_logs(skip, limit)
    return AuditLogListResponse(
        items=[AuditLogResponse.model_validate(l) for l in logs],
        total=total,
    )
