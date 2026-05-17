"""create members table

Revision ID: 0010
Revises: 0009
Create Date: 2026-05-17

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0010"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "members",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("application_id", sa.String(36), sa.ForeignKey("applications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("date_of_birth", sa.Date, nullable=False),
        sa.Column("relationship", sa.Enum(
            "self", "spouse", "child", "parent", "sibling", "dependent",
            name="member_relationship_enum"
        ), nullable=False),
        sa.Column("gender", sa.Enum(
            "male", "female", "other", "prefer_not_to_say",
            name="gender_enum"
        ), nullable=False),
        sa.Column("status", sa.Enum(
            "active", "inactive", "deceased",
            name="member_status_enum"
        ), nullable=False, server_default="active"),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("national_id", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_members_application", "members", ["application_id"])
    op.create_index("ix_members_tenant", "members", ["tenant_id"])


def downgrade() -> None:
    op.drop_table("members")
    op.execute("DROP TYPE IF EXISTS member_relationship_enum")
    op.execute("DROP TYPE IF EXISTS gender_enum")
    op.execute("DROP TYPE IF EXISTS member_status_enum")
