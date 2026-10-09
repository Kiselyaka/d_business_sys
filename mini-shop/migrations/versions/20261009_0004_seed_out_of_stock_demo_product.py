"""Seed the Mini Shop product used for the M3 rejected-reservation scenario."""

from alembic import op
import sqlalchemy as sa

revision = "20261009_0004"
down_revision = "20261009_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.bulk_insert(
        sa.table(
            "products",
            sa.column("id", sa.String),
            sa.column("product_code", sa.String),
            sa.column("name", sa.String),
            sa.column("price", sa.Numeric),
        ),
        [{"id": "00000000-0000-0000-0000-000000000002", "product_code": "SKU-002", "name": "Second Product", "price": "10.50"}],
    )


def downgrade() -> None:
    op.execute("DELETE FROM products WHERE product_code = 'SKU-002'")
