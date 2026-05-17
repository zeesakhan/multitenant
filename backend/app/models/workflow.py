from sqlalchemy import Column, String, Enum, JSON, Boolean, DateTime, Index, UniqueConstraint, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.models.base import TenantModel
from app.constants.enums import WorkflowStatus, WorkflowInstanceStatus
from datetime import datetime
from typing import Optional


class WorkflowDefinition(TenantModel):
    __tablename__ = "workflow_definitions"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    workflow_type: Mapped[str] = mapped_column(String(100), nullable=False)
    states: Mapped[dict] = mapped_column(JSON, nullable=False)
    transitions: Mapped[dict] = mapped_column(JSON, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(WorkflowStatus, name="workflow_status_enum"),
        default=WorkflowStatus.ACTIVE,
        nullable=False,
    )

    instances = relationship("WorkflowInstance", back_populates="definition", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("tenant_id", "name", "workflow_type", name="uq_workflow_definitions_tenant_type"),
        Index("ix_workflow_definitions_tenant_active", "tenant_id", "is_active"),
        Index("ix_workflow_definitions_type", "workflow_type"),
    )


class WorkflowInstance(TenantModel):
    __tablename__ = "workflow_instances"

    workflow_definition_id: Mapped[str] = mapped_column(
        ForeignKey("workflow_definitions.id", ondelete="RESTRICT"), nullable=False
    )
    reference_type: Mapped[str] = mapped_column(String(100), nullable=False)
    reference_id: Mapped[str] = mapped_column(String(36), nullable=False)
    current_state: Mapped[str] = mapped_column(String(100), nullable=False)
    context: Mapped[dict] = mapped_column(JSON, nullable=True, default=dict)
    status: Mapped[str] = mapped_column(
        Enum(WorkflowInstanceStatus, name="workflow_instance_status_enum"),
        default=WorkflowInstanceStatus.IN_PROGRESS,
        nullable=False,
    )

    definition = relationship("WorkflowDefinition", back_populates="instances")

    __table_args__ = (
        Index("ix_workflow_instances_tenant_reference", "tenant_id", "reference_type", "reference_id"),
        Index("ix_workflow_instances_definition", "workflow_definition_id"),
        Index("ix_workflow_instances_status", "status"),
    )
