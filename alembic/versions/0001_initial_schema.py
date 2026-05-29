"""initial schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-05-28 00:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("user_id"),
    )

    op.create_table(
        "blogger_tips",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("product_type", sa.String(length=100), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=255), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "ingredients_library",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("inci_name", sa.String(length=500), nullable=False),
        sa.Column("ru_name", sa.String(length=500), nullable=True),
        sa.Column("description_simple", sa.Text(), nullable=True),
        sa.Column("function", sa.String(length=500), nullable=True),
        sa.Column("comedogenic_score", sa.Integer(), nullable=True),
        sa.Column("irritancy_score", sa.Integer(), nullable=True),
        sa.Column("benefits", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("warnings", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("safe_for", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("avoid_for", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("inci_name"),
    )

    op.create_table(
        "product_parse_queue",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("source", sa.String(length=20), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("raw_html", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_product_parse_queue_status", "product_parse_queue", ["status"])

    op.create_table(
        "products_catalog",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=500), nullable=False),
        sa.Column("brand", sa.String(length=255), nullable=True),
        sa.Column("category", sa.String(length=50), nullable=True),
        sa.Column("ingredients_raw", sa.Text(), nullable=True),
        sa.Column("ingredients_parsed", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("ph", sa.Float(), nullable=True),
        sa.Column("source", sa.String(length=50), nullable=True),
        sa.Column("verified", sa.Boolean(), nullable=True),
        sa.Column("wb_url", sa.Text(), nullable=True),
        sa.Column("za_url", sa.Text(), nullable=True),
        sa.Column("scan_count", sa.Integer(), nullable=True),
        sa.Column("added_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_products_catalog_category", "products_catalog", ["category"])
    op.create_index("ix_products_catalog_name", "products_catalog", ["name"])
    op.create_index("ix_products_catalog_verified", "products_catalog", ["verified"])

    op.create_table(
        "achievements",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("achieved_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "code", name="uq_achievements_user_code"),
    )
    op.create_index("ix_achievements_user", "achievements", ["user_id"])

    op.create_table(
        "ingredient_corrections",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("original_ingredient", sa.Text(), nullable=True),
        sa.Column("corrected_ingredient", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["product_id"], ["products_catalog.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "product_scans",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=True),
        sa.Column("product_name", sa.String(length=500), nullable=True),
        sa.Column("ingredients_raw", sa.Text(), nullable=True),
        sa.Column("ingredients_parsed", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("suitable", sa.Boolean(), nullable=True),
        sa.Column("warnings", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["product_id"], ["products_catalog.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_product_scans_product_id", "product_scans", ["product_id"])
    op.create_index("ix_product_scans_user_created", "product_scans", ["user_id", "created_at"])

    op.create_table(
        "reminders",
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("morning_time", sa.Time(), nullable=True),
        sa.Column("evening_time", sa.Time(), nullable=True),
        sa.Column("timezone", sa.String(length=100), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_index("ix_reminders_active", "reminders", ["active"])

    op.create_table(
        "routine_products",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("period", sa.String(length=10), nullable=False),
        sa.Column("step_index", sa.Integer(), nullable=False),
        sa.Column("product_name", sa.String(length=500), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "period", "step_index", name="uq_routine_products_user_period_step"),
    )
    op.create_index("ix_routine_products_user", "routine_products", ["user_id"])

    op.create_table(
        "routines",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("morning_steps", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("evening_steps", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("reason_for_change", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_routines_user_created", "routines", ["user_id", "created_at"])

    op.create_table(
        "skin_analysis_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("photo_path", sa.Text(), nullable=True),
        sa.Column("ai_raw_response", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("ai_detected_problems", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("user_confirmed_problems", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("user_corrections", sa.Boolean(), nullable=True),
        sa.Column("skin_score", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_skin_analysis_history_user_created", "skin_analysis_history", ["user_id", "created_at"])

    op.create_table(
        "skin_diary",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("photo_path", sa.Text(), nullable=True),
        sa.Column("user_note", sa.Text(), nullable=True),
        sa.Column("ai_comparison", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_skin_diary_user_created", "skin_diary", ["user_id", "created_at"])

    op.create_table(
        "tracking",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("morning_done", sa.Boolean(), nullable=True),
        sa.Column("evening_done", sa.Boolean(), nullable=True),
        sa.Column("streak_days", sa.Integer(), nullable=True),
        sa.Column("products_used", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "date", name="uq_tracking_user_date"),
    )
    op.create_index("ix_tracking_user_date", "tracking", ["user_id", "date"])

    op.create_table(
        "user_leagues",
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("league", sa.String(length=50), nullable=True),
        sa.Column("weekly_days", sa.Integer(), nullable=True),
        sa.Column("week_start", sa.Date(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("user_id"),
    )

    op.create_table(
        "user_products",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("product_name", sa.String(length=500), nullable=True),
        sa.Column("product_type", sa.String(length=50), nullable=True),
        sa.Column("time_of_use", sa.String(length=20), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("added_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("removed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_products_user_status", "user_products", ["user_id", "status"])

    op.create_table(
        "user_profile_versions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("skin_type", sa.String(length=50), nullable=True),
        sa.Column("skin_problems", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("allergies", sa.Text(), nullable=True),
        sa.Column("budget", sa.String(length=20), nullable=True),
        sa.Column("goal", sa.String(length=50), nullable=True),
        sa.Column("age", sa.Integer(), nullable=True),
        sa.Column("changed_by", sa.String(length=10), nullable=True),
        sa.Column("change_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_profile_versions_user_created", "user_profile_versions", ["user_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_user_profile_versions_user_created", table_name="user_profile_versions")
    op.drop_table("user_profile_versions")
    op.drop_index("ix_user_products_user_status", table_name="user_products")
    op.drop_table("user_products")
    op.drop_table("user_leagues")
    op.drop_index("ix_tracking_user_date", table_name="tracking")
    op.drop_table("tracking")
    op.drop_index("ix_skin_diary_user_created", table_name="skin_diary")
    op.drop_table("skin_diary")
    op.drop_index("ix_skin_analysis_history_user_created", table_name="skin_analysis_history")
    op.drop_table("skin_analysis_history")
    op.drop_index("ix_routines_user_created", table_name="routines")
    op.drop_table("routines")
    op.drop_index("ix_routine_products_user", table_name="routine_products")
    op.drop_table("routine_products")
    op.drop_index("ix_reminders_active", table_name="reminders")
    op.drop_table("reminders")
    op.drop_index("ix_product_scans_user_created", table_name="product_scans")
    op.drop_index("ix_product_scans_product_id", table_name="product_scans")
    op.drop_table("product_scans")
    op.drop_table("ingredient_corrections")
    op.drop_index("ix_achievements_user", table_name="achievements")
    op.drop_table("achievements")
    op.drop_index("ix_products_catalog_verified", table_name="products_catalog")
    op.drop_index("ix_products_catalog_name", table_name="products_catalog")
    op.drop_index("ix_products_catalog_category", table_name="products_catalog")
    op.drop_table("products_catalog")
    op.drop_index("ix_product_parse_queue_status", table_name="product_parse_queue")
    op.drop_table("product_parse_queue")
    op.drop_table("ingredients_library")
    op.drop_table("blogger_tips")
    op.drop_table("users")
