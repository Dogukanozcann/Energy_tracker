from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.facilities import router as facility_router
from app.api.v1.endpoints.energy_consumption import router as consumption_router
from app.api.v1.endpoints.energy_sources import router as sources_router
from app.api.v1.endpoints.carbon import router as carbon_router
from app.api.v1.endpoints.alerts import router as alert_router
from app.api.v1.endpoints.imports import router as import_router
from app.api.v1.endpoints.reports import router as report_router
from app.api.v1.endpoints.cost_savings import router as cost_savings_router
from app.api.v1.endpoints.weekly_comparison import router as weekly_comparison_router
from app.api.v1.endpoints.admin import router as admin_router

router = APIRouter(prefix="/v1")
router.include_router(auth_router)
router.include_router(facility_router)
router.include_router(consumption_router)
router.include_router(sources_router)
router.include_router(carbon_router)
router.include_router(alert_router)
router.include_router(import_router)
router.include_router(report_router)
router.include_router(cost_savings_router)
router.include_router(weekly_comparison_router)
router.include_router(admin_router)
