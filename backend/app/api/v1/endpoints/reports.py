"""
PDF rapor endpoint'i.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get(
    "/carbon/{facility_id}",
    response_class=HTMLResponse,
    summary="Karbon ayak izi raporu (HTML)",
)
async def carbon_report(
    facility_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Tesis bazlı karbon ayak izi raporu üretir. HTML formatında."""
    service = ReportService(db)
    try:
        html = await service.generate_carbon_report_html(facility_id)
        return HTMLResponse(content=html)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
