"""create audit_logs table

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-15

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=True),
        sa.Column("user_email", sa.String(255), nullable=True),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", sa.String(36), nullable=True),
        sa.Column(
            "action",
            sa.Enum(
                "create", "read", "update", "delete", "login", "logout",
                "approve", "reject", "submit", "cancel", "issue", "renew", "export",
                name="audit_action_enum",
            ),
            nullable=False,
        ),
        sa.Column("old_values", sa.JSON, nullable=True),
        sa.Column("new_values", sa.JSON, nullable=True),
        sa.Column("ip_address", sa.String(50), nullable=True),
        sa.Column("user_agent", sa.Text, nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("metadata", sa.JSON, nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_audit_logs_tenant_id", "audit_logs", ["tenant_id"])
    op.create_index("ix_audit_logs_timestamp", "audit_logs", ["timestamp"])
    op.create_index("ix_audit_logs_tenant_timestamp", "audit_logs", ["tenant_id", "timestamp"])
    op.create_index("ix_audit_logs_tenant_entity", "audit_logs", ["tenant_id", "entity_type", "entity_id"])
    op.create_index("ix_audit_logs_user", "audit_logs", ["user_id", "timestamp"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.execute("DROP TYPE IF EXISTS audit_action_enum")
