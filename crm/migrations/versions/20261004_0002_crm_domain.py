"""Create CRM customer, deal and deal position tables for M1."""

from alembic import op
import sqlalchemy as sa

revision = "20261004_0002"
down_revision = "20260920_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "customers",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("external_customer_id", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("phone", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("external_customer_id", name="uq_customers_external_customer_id"),
    )
    op.create_index("ix_customers_external_customer_id", "customers", ["external_customer_id"])
    op.create_table(
        "deals",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("external_order_id", sa.String(length=255), nullable=False),
        sa.Column("customer_id", sa.String(length=36), sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("amount", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("external_order_id", name="uq_deals_external_order_id"),
    )
    op.create_index("ix_deals_external_order_id", "deals", ["external_order_id"])
    op.create_index("ix_deals_customer_id", "deals", ["customer_id"])
    op.create_table(
        "deal_positions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("deal_id", sa.String(length=36), sa.ForeignKey("deals.id"), nullable=False),
        sa.Column("external_product_code", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("price", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.UniqueConstraint("deal_id", "external_product_code", name="uq_deal_positions_deal_product"),
    )
    op.create_index("ix_deal_positions_deal_id", "deal_positions", ["deal_id"])


def downgrade() -> None:
    op.drop_index("ix_deal_positions_deal_id", table_name="deal_positions")
    op.drop_table("deal_positions")
    op.drop_index("ix_deals_customer_id", table_name="deals")
    op.drop_index("ix_deals_external_order_id", table_name="deals")
    op.drop_table("deals")
    op.drop_index("ix_customers_external_customer_id", table_name="customers")
    op.drop_table("customers")
