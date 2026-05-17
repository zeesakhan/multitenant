"""create workflow_definitions and workflow_instances tables

Revision ID: 0008
Revises: 0007
Create Date: 2026-05-16

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "workflow_definitions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.String(1000), nullable=True),
        sa.Column("workflow_type", sa.String(100), nullable=False),
        sa.Column("states", sa.JSON, nullable=False),
        sa.Column("transitions", sa.JSON, nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("status", sa.Enum("draft", "active", "archived", name="workflow_status_enum"), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_workflow_definitions_tenant_active", "workflow_definitions", ["tenant_id", "is_active"])
    op.create_index("ix_workflow_definitions_type", "workflow_definitions", ["workflow_type"])
    op.create_unique_constraint("uq_workflow_definitions_tenant_type", "workflow_definitions", ["tenant_id", "name", "workflow_type"])

    op.create_table(
        "workflow_instances",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workflow_definition_id", sa.String(36), sa.ForeignKey("workflow_definitions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("reference_type", sa.String(100), nullable=False),
        sa.Column("reference_id", sa.String(36), nullable=False),
        sa.Column("current_state", sa.String(100), nullable=False),
        sa.Column("context", sa.JSON, nullable=True, server_default="{}"),
        sa.Column("status", sa.Enum("in_progress", "completed", "failed", "cancelled", name="workflow_instance_status_enum"), nullable=False, server_default="in_progress"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_workflow_instances_tenant_reference", "workflow_instances", ["tenant_id", "reference_type", "reference_id"])
    op.create_index("ix_workflow_instances_definition", "workflow_instances", ["workflow_definition_id"])
    op.create_index("ix_workflow_instances_status", "workflow_instances", ["status"])


def downgrade() -> None:
    op.drop_table("workflow_instances")
    op.drop_table("workflow_definitions")
    op.execute("DROP TYPE IF EXISTS workflow_status_enum")
    op.execute("DROP TYPE IF EXISTS workflow_instance_status_enum")
