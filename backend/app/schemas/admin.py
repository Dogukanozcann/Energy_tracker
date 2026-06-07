from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ---- Energy Source ----

class EnergySourceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    name_tr: str | None = None
    category: str = Field(..., max_length=50)
    unit: str = Field(..., max_length=20)
    formula_type: str = "factor"
    co2_factor_scope_1: float | None = None
    co2_factor_scope_2: float | None = None
    co2_factor_source: str | None = None
    factor_year: int | None = None
    unit_alt: str | None = None
    co2_factor_scope_1_alt: float | None = None
    co2_factor_scope_2_alt: float | None = None
    fuel_density: float | None = None
    fuel_carbon_ratio: float | None = None
    fuel_co2_per_liter: float | None = None
    is_renewable: bool = False
    is_active: bool = True


class EnergySourceUpdate(BaseModel):
    name: str | None = None
    name_tr: str | None = None
    category: str | None = None
    unit: str | None = None
    formula_type: str | None = None
    co2_factor_scope_1: float | None = None
    co2_factor_scope_2: float | None = None
    co2_factor_source: str | None = None
    factor_year: int | None = None
    unit_alt: str | None = None
    co2_factor_scope_1_alt: float | None = None
    co2_factor_scope_2_alt: float | None = None
    fuel_density: float | None = None
    fuel_carbon_ratio: float | None = None
    fuel_co2_per_liter: float | None = None
    is_renewable: bool | None = None
    is_active: bool | None = None


class EnergySourceResponse(BaseModel):
    id: UUID
    name: str
    name_tr: str | None
    category: str
    unit: str
    formula_type: str
    co2_factor_scope_1: float | None
    co2_factor_scope_2: float | None
    co2_factor_source: str | None
    factor_year: int | None
    unit_alt: str | None
    co2_factor_scope_1_alt: float | None
    co2_factor_scope_2_alt: float | None
    fuel_density: float | None
    fuel_carbon_ratio: float | None
    fuel_co2_per_liter: float | None
    is_renewable: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---- User Management ----

class UserListItem(BaseModel):
    id: UUID
    email: str
    full_name: str
    company_name: str | None
    user_type: str
    role: str
    is_active: bool
    email_verified_at: datetime | None
    last_login_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    full_name: str | None = None
    role: str | None = None
    is_active: bool | None = None
    company_name: str | None = None


class UserListResponse(BaseModel):
    items: list[UserListItem]
    total: int


# ---- System Settings ----

class SystemSettingCreate(BaseModel):
    key: str = Field(..., min_length=1, max_length=100)
    value: str
    description: str | None = None
    category: str = "general"


class SystemSettingUpdate(BaseModel):
    value: str | None = None
    description: str | None = None
    category: str | None = None


class SystemSettingResponse(BaseModel):
    id: UUID
    key: str
    value: str
    description: str | None
    category: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SystemSettingListResponse(BaseModel):
    items: list[SystemSettingResponse]
    total: int


# ---- Audit Log ----

class AuditLogResponse(BaseModel):
    id: UUID
    user_email: str | None
    action: str
    resource: str
    resource_id: str | None
    details: str | None
    ip_address: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogListResponse(BaseModel):
    items: list[AuditLogResponse]
    total: int
