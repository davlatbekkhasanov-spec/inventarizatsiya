"""pause workflow and hub day log

Revision ID: 002
Revises: 001
"""

from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "work_sessions",
        sa.Column("paused_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "work_sessions",
        sa.Column("total_pause_sec", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_table(
        "hub_day_push",
        sa.Column("day", sa.String(10), nullable=False),
        sa.Column("tg_id", sa.BigInteger(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("day", "tg_id"),
    )


def downgrade() -> None:
    op.drop_table("hub_day_push")
    op.drop_column("work_sessions", "total_pause_sec")
    op.drop_column("work_sessions", "paused_at")
