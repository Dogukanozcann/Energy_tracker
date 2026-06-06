from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.facilities import router as facility_router
from app.api.v1.endpoints.energy_consumption import router as consumption_router
from app.api.v1.endpoints.carbon import router as carbon_router
from app.api.v1.endpoints.alerts import router as alert_router
from app.api.v1.endpoints.imports import router as import_router
from app.api.v1.endpoints.reports import router as report_router

router = APIRouter(prefix="/v1")
router.include_router(auth_router)
router.include_router(facility_router)
router.include_router(consumption_router)
router.include_router(carbon_router)
router.include_router(alert_router)
router.include_router(import_router)
router.include_router(report_router)
