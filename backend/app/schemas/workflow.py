from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.constants.enums import WorkflowStatus, WorkflowInstanceStatus


class WorkflowTransition(BaseModel):
    from_state: str = Field(..., min_length=1)
    to_state: str = Field(..., min_length=1)
    action: str = Field(..., min_length=1)
    conditions: Optional[Dict[str, Any]] = None


class WorkflowDefinitionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    workflow_type: str = Field(..., min_length=1, max_length=100)
    states: List[str] = Field(..., min_length=1)
    transitions: List[WorkflowTransition]
    is_active: bool = True


class WorkflowDefinitionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: Optional[str] = None
    workflow_type: str
    states: List[str]
    transitions: List[WorkflowTransition]
    is_active: bool
    status: WorkflowStatus
    created_at: datetime
    updated_at: datetime


class WorkflowDefinitionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = None


class WorkflowInstanceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    workflow_definition_id: str
    reference_type: str
    reference_id: str
    current_state: str
    context: Optional[Dict[str, Any]] = None
    status: WorkflowInstanceStatus
    created_at: datetime
    updated_at: datetime


class WorkflowTransitionRequest(BaseModel):
    action: str = Field(..., min_length=1)
    context: Optional[Dict[str, Any]] = None


class WorkflowCreateInstanceRequest(BaseModel):
    workflow_definition_id: str = Field(..., min_length=1)
    reference_type: str = Field(..., min_length=1, max_length=100)
    reference_id: str = Field(..., min_length=1)
    initial_context: Optional[Dict[str, Any]] = None
