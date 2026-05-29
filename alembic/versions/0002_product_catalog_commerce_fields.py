"""product catalog commerce fields

Revision ID: 0002_product_catalog_commerce_fields
Revises: 0001_initial_schema
Create Date: 2026-05-29 00:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002_product_catalog_commerce_fields"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("products_catalog", sa.Column("price", sa.Integer(), nullable=True))
    op.add_column("products_catalog", sa.Column("rating", sa.Float(), nullable=True))
    op.add_column("products_catalog", sa.Column("reviews_count", sa.Integer(), nullable=True))
    op.add_column("products_catalog", sa.Column("review_summary", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("products_catalog", "review_summary")
    op.drop_column("products_catalog", "reviews_count")
    op.drop_column("products_catalog", "rating")
    op.drop_column("products_catalog", "price")
