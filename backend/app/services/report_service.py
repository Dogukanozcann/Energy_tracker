"""
PDF rapor oluşturma servisi.
"""

import io
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.energy_consumption import EnergyConsumption
from app.models.energy_source import EnergySource
from app.models.carbon_footprint import CarbonFootprintItem
from app.models.facility import Facility


class ReportService:
    """PDF ve veri raporları oluşturma."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_carbon_report_html(self, facility_id: UUID) -> str:
        """Karbon ayak izi raporu için HTML içeriği üretir.
        reportlab bağımlılığı olmayan ortamlarda tarayıcıdan yazdırma için.
        """
        # Tesis bilgisi
        result = await self.db.execute(
            select(Facility).where(Facility.id == facility_id)
        )
        facility = result.scalar_one_or_none()
        if facility is None:
            raise ValueError("Tesis bulunamadı.")

        # Tüketim özeti
        cons_result = await self.db.execute(
            select(
                func.count(EnergyConsumption.id).label("total_records"),
                func.coalesce(func.sum(EnergyConsumption.consumption_value), 0).label("total_value"),
                func.coalesce(func.sum(EnergyConsumption.cost), 0).label("total_cost"),
            ).where(EnergyConsumption.facility_id == facility_id)
        )
        cons_summary = cons_result.one()

        # Karbon özeti
        carb_result = await self.db.execute(
            select(
                func.coalesce(func.sum(CarbonFootprintItem.calculated_co2_kg), 0).label("total_co2"),
                CarbonFootprintItem.scope,
            ).where(
                CarbonFootprintItem.energy_consumption_id.in_(
                    select(EnergyConsumption.id).where(
                        EnergyConsumption.facility_id == facility_id
                    )
                )
            ).group_by(CarbonFootprintItem.scope)
        )
        carbon_rows = carb_result.all()
        scope_1 = sum(r.total_co2 for r in carbon_rows if r.scope == "scope_1")
        scope_2 = sum(r.total_co2 for r in carbon_rows if r.scope == "scope_2")
        scope_3 = sum(r.total_co2 for r in carbon_rows if r.scope == "scope_3")
        total_co2 = scope_1 + scope_2 + scope_3

        # Energy sources
        src_result = await self.db.execute(
            select(EnergySource.name, EnergySource.unit, EnergySource.co2_factor_kg_per_unit)
        )
        sources = src_result.all()

        now = datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M")

        html = f"""<!DOCTYPE html>
<html lang="tr">
<head><meta charset="UTF-8"><title>Karbon Ayak İzi Raporu</title>
<style>
  body {{ font-family: 'Helvetica', Arial, sans-serif; margin: 40px; color: #333; }}
  h1 {{ color: #059669; border-bottom: 2px solid #059669; padding-bottom: 10px; }}
  h2 {{ color: #065f46; margin-top: 30px; }}
  .header {{ text-align: center; margin-bottom: 40px; }}
  .meta {{ font-size: 14px; color: #666; }}
  table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
  th, td {{ padding: 10px 12px; text-align: left; border-bottom: 1px solid #e5e7eb; }}
  th {{ background: #f0fdf4; color: #065f46; font-weight: 600; }}
  .stat-box {{ display: inline-block; background: #f0fdf4; border: 1px solid #059669;
                border-radius: 8px; padding: 15px 25px; margin: 10px; text-align: center; }}
  .stat-value {{ font-size: 24px; font-weight: bold; color: #059669; }}
  .stat-label {{ font-size: 12px; color: #666; }}
  .footer {{ margin-top: 50px; text-align: center; font-size: 12px; color: #999; }}
</style></head>
<body>
<div class="header">
  <h1>🌱 Karbon Ayak İzi Raporu</h1>
  <p class="meta">Oluşturulma: {now}</p>
</div>

<h2>Tesis Bilgileri</h2>
<table>
  <tr><th>Ad</th><td>{facility.name}</td></tr>
  <tr><th>Tür</th><td>{facility.facility_type}</td></tr>
  <tr><th>Konum</th><td>{facility.city or '-'} / {facility.district or '-'}</td></tr>
  <tr><th>Alan</th><td>{facility.area_sqm or '-'} m²</td></tr>
</table>

<h2>碳排放 Özeti</h2>
<div>
  <div class="stat-box"><div class="stat-value">{total_co2:,.1f}</div><div class="stat-label">Toplam CO₂ (kg)</div></div>
  <div class="stat-box"><div class="stat-value">{scope_1:,.1f}</div><div class="stat-label">Scope 1 (kg)</div></div>
  <div class="stat-box"><div class="stat-value">{scope_2:,.1f}</div><div class="stat-label">Scope 2 (kg)</div></div>
  <div class="stat-box"><div class="stat-value">{scope_3:,.1f}</div><div class="stat-label">Scope 3 (kg)</div></div>
</div>

<h2>Enerji Tüketimi</h2>
<table>
  <tr><th>Toplam Kayıt</th><td>{cons_summary.total_records}</td></tr>
  <tr><th>Toplam Tüketim</th><td>{cons_summary.total_value:,.1f} kWh</td></tr>
  <tr><th>Toplam Maliyet</th><td>{cons_summary.total_cost:,.2f} ₺</td></tr>
</table>

<h2>Enerji Kaynakları ve Emisyon Faktörleri</h2>
<table>
  <tr><th>Kaynak</th><th>Birim</th><th>CO₂ Faktörü (kg/birim)</th></tr>
"""
        for s in sources:
            factor = f"{s.co2_factor_kg_per_unit:.4f}" if s.co2_factor_kg_per_unit else "-"
            html += f"  <tr><td>{s.name}</td><td>{s.unit}</td><td>{factor}</td></tr>\n"

        if facility.area_sqm and total_co2 > 0:
            intensity = total_co2 / facility.area_sqm
            html += f"""
<h2>Yoğunluk Metrikleri</h2>
<table>
  <tr><th>CO₂ Yoğunluğu</th><td>{intensity:,.2f} kg CO₂/m²</td></tr>
</table>
"""

        html += f"""
<div class="footer">
  <p>EnergyTracker — Enerji Verimliliği ve Sürdürülebilirlik Platformu</p>
  <p>Bu rapor otomatik oluşturulmuştur.</p>
</div>
</body></html>"""
        return html
