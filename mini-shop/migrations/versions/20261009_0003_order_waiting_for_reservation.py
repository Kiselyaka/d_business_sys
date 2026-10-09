"""Make reservation processing the initial Mini Shop order state."""

from alembic import op
import sqlalchemy as sa

revision = "20261009_0003"
down_revision = "20261004_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("UPDATE orders SET status = 'WAITING_FOR_RESERVATION' WHERE status = 'CREATED'")
    with op.batch_alter_table("orders") as batch_op:
        batch_op.alter_column(
            "status",
            existing_type=sa.String(length=32),
            server_default="WAITING_FOR_RESERVATION",
            existing_nullable=False,
        )


def downgrade() -> None:
    op.execute("UPDATE orders SET status = 'CREATED' WHERE status = 'WAITING_FOR_RESERVATION'")
    with op.batch_alter_table("orders") as batch_op:
        batch_op.alter_column(
            "status",
            existing_type=sa.String(length=32),
            server_default="CREATED",
            existing_nullable=False,
        )
