"""Add notification_records table

Revision ID: 0024
Revises: 0023
Create Date: 2026-06-22
"""
from typing import Union
import sqlalchemy as sa
from alembic import op

revision: str = "0024"
down_revision: Union[str, None] = "0023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notification_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("recipient_user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("notification_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("related_entity_type", sa.String(50), nullable=True),
        sa.Column("related_entity_id", sa.String(36), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_notification_records_tenant_id", "notification_records", ["tenant_id"])
    op.create_index("ix_notification_records_recipient_user_id", "notification_records", ["recipient_user_id"])
    op.create_index("ix_notification_records_is_read", "notification_records", ["is_read"])
    op.create_index("ix_notification_records_created_at", "notification_records", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_notification_records_created_at", "notification_records")
    op.drop_index("ix_notification_records_is_read", "notification_records")
    op.drop_index("ix_notification_records_recipient_user_id", "notification_records")
    op.drop_index("ix_notification_records_tenant_id", "notification_records")
    op.drop_table("notification_records")
