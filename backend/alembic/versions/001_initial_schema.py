"""energy_tracker initial schema

Revision ID: 001
Revises:
Create Date: 2026-06-01
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- ENUM types ---
    sa.Enum("individual", "business", name="user_type_enum").create(op.get_bind())
    sa.Enum("admin", "viewer", "operator", name="user_role_enum").create(op.get_bind())
    sa.Enum(
        "electricity", "natural_gas", "fuel_oil", "coal", "lpg",
        "diesel", "gasoline", "biomass", "solar", "wind", "geothermal",
        name="energy_category_enum",
    ).create(op.get_bind())
    sa.Enum(
        "manual", "iot_sensor", "api_integration", "bulk_import",
        name="consumption_source_enum",
    ).create(op.get_bind())
    sa.Enum("scope_1", "scope_2", "scope_3", name="carbon_scope_enum").create(op.get_bind())
    sa.Enum("draft", "confirmed", "audited", name="carbon_status_enum").create(op.get_bind())
    sa.Enum(
        "low", "medium", "high", "critical",
        name="alert_severity_enum",
    ).create(op.get_bind())
    sa.Enum(
        "new", "acknowledged", "resolved", "dismissed",
        name="alert_status_enum",
    ).create(op.get_bind())
    sa.Enum(
        "anomaly", "threshold_breach", "efficiency_gap", "maintenance",
        name="alert_category_enum",
    ).create(op.get_bind())
    sa.Enum(
        "low", "medium", "high", "critical",
        name="action_priority_enum",
    ).create(op.get_bind())
    sa.Enum(
        "pending", "approved", "in_progress", "implemented", "rejected",
        name="action_status_enum",
    ).create(op.get_bind())
    sa.Enum(
        "equipment_upgrade", "behavioral", "maintenance",
        "process_optimization", "renewable_energy", "insulation_hvac",
        name="action_category_enum",
    ).create(op.get_bind())

    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(150), nullable=False),
        sa.Column("phone", sa.String(20)),
        sa.Column("avatar_url", sa.Text),
        sa.Column("company_name", sa.String(255)),
        sa.Column("tax_id", sa.String(50)),
        sa.Column("sector", sa.String(100)),
        sa.Column("country", sa.String(100), server_default="Türkiye"),
        sa.Column("city", sa.String(100)),
        sa.Column("district", sa.String(100)),
        sa.Column("user_type", sa.String(20), nullable=False, server_default="individual"),
        sa.Column("role", sa.String(20), nullable=False, server_default="viewer"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("email_verified_at", sa.DateTime(timezone=True)),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # --- user_preferences ---
    op.create_table(
        "user_preferences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("language", sa.String(10), server_default="tr"),
        sa.Column("timezone", sa.String(50), server_default="Europe/Istanbul"),
        sa.Column("energy_unit", sa.String(20), server_default="kWh"),
        sa.Column("currency", sa.String(10), server_default="TRY"),
        sa.Column("daily_digest", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("email_alerts", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("push_alerts", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("alert_categories", postgresql.JSONB, server_default=sa.text("'[\"anomaly\",\"threshold_breach\"]'::jsonb")),
        sa.Column("weekly_report", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("monthly_goal_co2", sa.Numeric(12, 2)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # --- facilities ---
    op.create_table(
        "facilities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("facility_type", sa.String(50), server_default="office"),
        sa.Column("address", sa.Text),
        sa.Column("city", sa.String(100)),
        sa.Column("district", sa.String(100)),
        sa.Column("postal_code", sa.String(20)),
        sa.Column("country", sa.String(100), server_default="Türkiye"),
        sa.Column("area_sqm", sa.Numeric(12, 2)),
        sa.Column("heated_area_sqm", sa.Numeric(12, 2)),
        sa.Column("num_floors", sa.Integer()),
        sa.Column("num_occupants", sa.Integer()),
        sa.Column("operating_hours", sa.Numeric(4, 2)),
        sa.Column("latitude", sa.Numeric(10, 7)),
        sa.Column("longitude", sa.Numeric(10, 7)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("logo_url", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # --- energy_sources ---
    op.create_table(
        "energy_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(150), unique=True, nullable=False),
        sa.Column("name_tr", sa.String(150)),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("unit", sa.String(20), nullable=False),
        sa.Column("co2_factor_scope_1", sa.Numeric(12, 6)),
        sa.Column("co2_factor_scope_2", sa.Numeric(12, 6)),
        sa.Column("co2_factor_source", sa.String(255)),
        sa.Column("factor_year", sa.Integer()),
        sa.Column("is_renewable", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # --- energy_consumption ---
    op.create_table(
        "energy_consumption",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("facility_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("energy_source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("energy_sources.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("period_start", sa.DateTime(timezone=True)),
        sa.Column("period_end", sa.DateTime(timezone=True)),
        sa.Column("consumption_value", sa.Numeric(14, 4), nullable=False),
        sa.Column("unit", sa.String(20), nullable=False),
        sa.Column("cost", sa.Numeric(12, 4)),
        sa.Column("source", sa.String(20), nullable=False, server_default="manual"),
        sa.Column("is_estimated", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("notes", sa.Text),
        sa.Column("external_id", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_consumption_facility_time", "energy_consumption", ["facility_id", sa.text("recorded_at DESC")])
    op.create_index("idx_consumption_recorded_at", "energy_consumption", [sa.text("recorded_at DESC")])
    op.create_index("idx_consumption_source", "energy_consumption", ["energy_source_id"])

    # --- carbon_footprint_items ---
    op.create_table(
        "carbon_footprint_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("energy_consumption_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("energy_consumption.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("energy_source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("energy_sources.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("scope", sa.String(10), nullable=False),
        sa.Column("consumption_amount", sa.Numeric(14, 4), nullable=False),
        sa.Column("consumption_unit", sa.String(20), nullable=False),
        sa.Column("co2_factor_used", sa.Numeric(12, 6), nullable=False),
        sa.Column("calculated_co2_kg", sa.Numeric(14, 4), nullable=False),
        sa.Column("factor_source", sa.String(255)),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_cfi_energy_consumption", "carbon_footprint_items", ["energy_consumption_id"])
    op.create_index("idx_cfi_energy_source", "carbon_footprint_items", ["energy_source_id"])

    # --- carbon_footprints ---
    op.create_table(
        "carbon_footprints",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("facility_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("calculation_start", sa.Date(), nullable=False),
        sa.Column("calculation_end", sa.Date(), nullable=False),
        sa.Column("calculation_year", sa.Integer(), nullable=False),
        sa.Column("calculation_month", sa.Integer()),
        sa.Column("calculation_quarter", sa.Integer()),
        sa.Column("total_co2_kg", sa.Numeric(14, 2), nullable=False),
        sa.Column("scope_1_co2_kg", sa.Numeric(14, 2)),
        sa.Column("scope_2_co2_kg", sa.Numeric(14, 2)),
        sa.Column("scope_3_co2_kg", sa.Numeric(14, 2)),
        sa.Column("intensity_per_area", sa.Numeric(10, 4)),
        sa.Column("intensity_per_revenue", sa.Numeric(10, 4)),
        sa.Column("methodology", sa.String(50), server_default="ghg_protocol"),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("notes", sa.Text),
        sa.Column("calculated_by_user", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("calculated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("confirmed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("calculation_end > calculation_start", name="chk_footprint_dates"),
        sa.UniqueConstraint("facility_id", "calculation_start", "calculation_end", "calculation_year", name="uq_footprint_period"),
    )
    op.create_index("idx_cf_facility_date", "carbon_footprints", ["facility_id", sa.text("calculation_start DESC")])
    op.create_index("idx_cf_year", "carbon_footprints", ["calculation_year"])

    # --- alerts ---
    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("facility_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("energy_consumption_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("energy_consumption.id", ondelete="SET NULL")),
        sa.Column("energy_source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("energy_sources.id", ondelete="SET NULL")),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("severity", sa.String(20), nullable=False, server_default="medium"),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="new"),
        sa.Column("detected_value", sa.Numeric(14, 4)),
        sa.Column("expected_value", sa.Numeric(14, 4)),
        sa.Column("threshold_value", sa.Numeric(14, 4)),
        sa.Column("deviation_percent", sa.Numeric(6, 2)),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("recommendation_text", sa.Text),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("resolved_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("parent_alert_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("alerts.id", ondelete="SET NULL")),
        sa.Column("is_auto_generated", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_alerts_facility_status", "alerts", ["facility_id", "status"])
    op.create_index("idx_alerts_severity", "alerts", ["severity"], postgresql_where=sa.text("status = 'new'"))
    op.create_index("idx_alerts_category_time", "alerts", ["facility_id", "category", sa.text("detected_at DESC")])
    op.create_index("idx_alerts_detected_at", "alerts", [sa.text("detected_at DESC")])

    # --- actions ---
    op.create_table(
        "actions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("facility_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("priority", sa.String(20), nullable=False, server_default="medium"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("estimated_saving_co2_kg", sa.Numeric(12, 2)),
        sa.Column("estimated_saving_cost", sa.Numeric(12, 2)),
        sa.Column("estimated_investment_cost", sa.Numeric(12, 2)),
        sa.Column("roi_estimate", sa.Numeric(6, 2)),
        sa.Column("payback_months", sa.Integer()),
        sa.Column("is_ai_generated", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("ai_confidence_score", sa.Numeric(4, 2)),
        sa.Column("source_data_summary", sa.Text),
        sa.Column("assigned_to", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("implementation_notes", sa.Text),
        sa.Column("implementation_date", sa.Date()),
        sa.Column("implemented_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_actions_facility_status", "actions", ["facility_id", "status"])
    op.create_index("idx_actions_priority", "actions", ["facility_id", "priority"], postgresql_where=sa.text("status = 'pending'"))


def downgrade() -> None:
    op.drop_table("actions")
    op.drop_table("alerts")
    op.drop_table("carbon_footprints")
    op.drop_table("carbon_footprint_items")
    op.drop_table("energy_consumption")
    op.drop_table("energy_sources")
    op.drop_table("facilities")
    op.drop_table("user_preferences")
    op.drop_table("users")

    sa.Enum(name="action_category_enum").drop(op.get_bind(), if_exists=True)
    sa.Enum(name="action_status_enum").drop(op.get_bind(), if_exists=True)
    sa.Enum(name="action_priority_enum").drop(op.get_bind(), if_exists=True)
    sa.Enum(name="alert_category_enum").drop(op.get_bind(), if_exists=True)
    sa.Enum(name="alert_status_enum").drop(op.get_bind(), if_exists=True)
    sa.Enum(name="alert_severity_enum").drop(op.get_bind(), if_exists=True)
    sa.Enum(name="carbon_status_enum").drop(op.get_bind(), if_exists=True)
    sa.Enum(name="carbon_scope_enum").drop(op.get_bind(), if_exists=True)
    sa.Enum(name="consumption_source_enum").drop(op.get_bind(), if_exists=True)
    sa.Enum(name="energy_category_enum").drop(op.get_bind(), if_exists=True)
    sa.Enum(name="user_role_enum").drop(op.get_bind(), if_exists=True)
    sa.Enum(name="user_type_enum").drop(op.get_bind(), if_exists=True)
