"""
Admin servisi — enerji kaynakları, kullanıcılar, sistem ayarları, audit log.
"""

from uuid import UUID

from sqlalchemy import func, select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.energy_source import EnergySource
from app.models.system_setting import SystemSetting
from app.models.user import User
from app.schemas.admin import (
    EnergySourceCreate,
    EnergySourceUpdate,
    UserUpdate,
    SystemSettingCreate,
    SystemSettingUpdate,
)


class AdminService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ===================== AUDIT LOG =====================

    async def log(
        self,
        user_id: UUID | None,
        user_email: str | None,
        action: str,
        resource: str,
        resource_id: str | None = None,
        details: str | None = None,
        ip_address: str | None = None,
    ):
        log = AuditLog(
            user_id=user_id,
            user_email=user_email,
            action=action,
            resource=resource,
            resource_id=str(resource_id) if resource_id else None,
            details=details,
            ip_address=ip_address,
        )
        self.db.add(log)
        await self.db.flush()

    # ===================== ENERGY SOURCES =====================

    async def list_sources(self) -> list[EnergySource]:
        result = await self.db.execute(
            select(EnergySource).order_by(EnergySource.name)
        )
        return list(result.scalars().all())

    async def get_source(self, source_id: UUID) -> EnergySource | None:
        result = await self.db.execute(
            select(EnergySource).where(EnergySource.id == source_id)
        )
        return result.scalar_one_or_none()

    async def create_source(self, data: EnergySourceCreate) -> EnergySource:
        source = EnergySource(**data.model_dump())
        self.db.add(source)
        await self.db.flush()
        return source

    async def update_source(self, source_id: UUID, data: EnergySourceUpdate) -> EnergySource | None:
        source = await self.get_source(source_id)
        if source is None:
            return None
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(source, k, v)
        await self.db.flush()
        return source

    async def delete_source(self, source_id: UUID) -> bool:
        source = await self.get_source(source_id)
        if source is None:
            return False
        await self.db.delete(source)
        await self.db.flush()
        return True

    # ===================== USER MANAGEMENT =====================

    async def list_users(self, skip: int = 0, limit: int = 50) -> tuple[list[User], int]:
        count_q = select(func.count(User.id))
        total = (await self.db.execute(count_q)).scalar_one()

        q = select(User).order_by(User.created_at.desc()).offset(skip).limit(limit)
        users = list((await self.db.execute(q)).scalars().all())
        return users, total

    async def get_user(self, user_id: UUID) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def update_user(self, user_id: UUID, data: UserUpdate) -> User | None:
        user = await self.get_user(user_id)
        if user is None:
            return None
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(user, k, v)
        await self.db.flush()
        return user

    # ===================== SYSTEM SETTINGS =====================

    async def list_settings(self, category: str | None = None) -> tuple[list[SystemSetting], int]:
        filters = []
        if category:
            filters.append(SystemSetting.category == category)

        count_q = select(func.count(SystemSetting.id)).where(*filters)
        total = (await self.db.execute(count_q)).scalar_one()

        q = select(SystemSetting).where(*filters).order_by(SystemSetting.key)
        items = list((await self.db.execute(q)).scalars().all())
        return items, total

    async def get_setting(self, setting_id: UUID) -> SystemSetting | None:
        result = await self.db.execute(
            select(SystemSetting).where(SystemSetting.id == setting_id)
        )
        return result.scalar_one_or_none()

    async def create_setting(self, data: SystemSettingCreate) -> SystemSetting:
        setting = SystemSetting(**data.model_dump())
        self.db.add(setting)
        await self.db.flush()
        return setting

    async def update_setting(self, setting_id: UUID, data: SystemSettingUpdate) -> SystemSetting | None:
        setting = await self.get_setting(setting_id)
        if setting is None:
            return None
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(setting, k, v)
        await self.db.flush()
        return setting

    async def delete_setting(self, setting_id: UUID) -> bool:
        setting = await self.get_setting(setting_id)
        if setting is None:
            return False
        await self.db.delete(setting)
        await self.db.flush()
        return True

    # ===================== AUDIT LOGS =====================

    async def list_logs(self, skip: int = 0, limit: int = 50) -> tuple[list[AuditLog], int]:
        count_q = select(func.count(AuditLog.id))
        total = (await self.db.execute(count_q)).scalar_one()

        q = select(AuditLog).order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)
        logs = list((await self.db.execute(q)).scalars().all())
        return logs, total
