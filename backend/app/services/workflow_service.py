from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.workflow import WorkflowDefinition, WorkflowInstance
from app.schemas.workflow import (
    WorkflowDefinitionCreate,
    WorkflowDefinitionUpdate,
    WorkflowCreateInstanceRequest,
    WorkflowTransitionRequest,
)
from app.services.audit_service import AuditService
from datetime import datetime, timezone
import uuid


class WorkflowService:
    def __init__(self, db: Session, audit_service: AuditService):
        self.db = db
        self.audit = audit_service

    def create_definition(
        self,
        tenant_id: str,
        data: WorkflowDefinitionCreate,
        user_id: str,
    ) -> WorkflowDefinition:
        """Create a new workflow definition."""
        # Validate transitions reference valid states
        valid_states = set(data.states)
        for transition in data.transitions:
            if transition.from_state not in valid_states:
                raise ValueError(f"Invalid from_state: {transition.from_state}")
            if transition.to_state not in valid_states:
                raise ValueError(f"Invalid to_state: {transition.to_state}")

        definition = WorkflowDefinition(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            name=data.name,
            description=data.description,
            workflow_type=data.workflow_type,
            states=data.states,
            transitions=[{
                "from_state": t.from_state,
                "to_state": t.to_state,
                "action": t.action,
                "conditions": t.conditions or {},
            } for t in data.transitions],
            is_active=data.is_active,
        )

        self.db.add(definition)
        self.db.flush()

        self.audit.log(
            tenant_id=tenant_id,
            action="create",
            entity_type="workflow_definition",
            entity_id=definition.id,
            user_id=user_id,
        )

        return definition

    def get_definition(self, tenant_id: str, definition_id: str) -> WorkflowDefinition:
        return self.db.query(WorkflowDefinition).filter(
            and_(WorkflowDefinition.tenant_id == tenant_id, WorkflowDefinition.id == definition_id)
        ).first()

    def list_definitions(
        self,
        tenant_id: str,
        workflow_type: str = None,
        is_active: bool = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[WorkflowDefinition], int]:
        query = self.db.query(WorkflowDefinition).filter(WorkflowDefinition.tenant_id == tenant_id)

        if workflow_type:
            query = query.filter(WorkflowDefinition.workflow_type == workflow_type)
        if is_active is not None:
            query = query.filter(WorkflowDefinition.is_active == is_active)

        total = query.count()
        definitions = query.order_by(WorkflowDefinition.created_at.desc()).offset(skip).limit(limit).all()
        return definitions, total

    def update_definition(
        self,
        tenant_id: str,
        definition_id: str,
        data: WorkflowDefinitionUpdate,
        user_id: str,
    ) -> WorkflowDefinition:
        """Update workflow definition."""
        definition = self.get_definition(tenant_id, definition_id)
        if not definition:
            return None

        # Check if definition is in use
        instance_count = self.db.query(WorkflowInstance).filter(
            WorkflowInstance.workflow_definition_id == definition_id
        ).count()

        if instance_count > 0:
            raise ValueError("Cannot update workflow definition that is in use")

        if data.name is not None:
            definition.name = data.name
        if data.description is not None:
            definition.description = data.description
        if data.is_active is not None:
            definition.is_active = data.is_active

        self.db.flush()

        self.audit.log(
            tenant_id=tenant_id,
            action="update",
            entity_type="workflow_definition",
            entity_id=definition.id,
            user_id=user_id,
        )

        return definition

    def create_instance(
        self,
        tenant_id: str,
        workflow_definition_id: str,
        reference_type: str,
        reference_id: str,
        initial_context: dict = None,
        user_id: str = None,
    ) -> WorkflowInstance:
        """Create a new workflow instance."""
        definition = self.get_definition(tenant_id, workflow_definition_id)
        if not definition:
            raise ValueError(f"Workflow definition {workflow_definition_id} not found")

        # Get first state from definition states
        states = definition.states if isinstance(definition.states, list) else definition.states.get("states", [])
        if not states:
            raise ValueError("Workflow definition has no states")

        first_state = states[0]

        instance = WorkflowInstance(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            workflow_definition_id=workflow_definition_id,
            reference_type=reference_type,
            reference_id=reference_id,
            current_state=first_state,
            context=initial_context or {},
        )

        self.db.add(instance)
        self.db.flush()

        if user_id:
            self.audit.log(
                tenant_id=tenant_id,
                action="create",
                entity_type="workflow_instance",
                entity_id=instance.id,
                user_id=user_id,
            )

        return instance

    def get_instance(self, tenant_id: str, instance_id: str) -> WorkflowInstance:
        return self.db.query(WorkflowInstance).filter(
            and_(WorkflowInstance.tenant_id == tenant_id, WorkflowInstance.id == instance_id)
        ).first()

    def get_by_reference(self, tenant_id: str, reference_type: str, reference_id: str) -> WorkflowInstance:
        return self.db.query(WorkflowInstance).filter(
            and_(
                WorkflowInstance.tenant_id == tenant_id,
                WorkflowInstance.reference_type == reference_type,
                WorkflowInstance.reference_id == reference_id,
            )
        ).first()

    def transition(
        self,
        tenant_id: str,
        instance_id: str,
        action: str,
        context: dict = None,
        user_id: str = None,
    ) -> WorkflowInstance:
        """Perform a state transition in the workflow."""
        instance = self.get_instance(tenant_id, instance_id)
        if not instance:
            raise ValueError(f"Workflow instance {instance_id} not found")

        definition = instance.definition
        if not definition:
            raise ValueError(f"Workflow definition not found")

        # Find valid transition
        transitions = definition.transitions or []
        valid_transition = None

        for transition in transitions:
            if transition.get("from_state") == instance.current_state and transition.get("action") == action:
                valid_transition = transition
                break

        if not valid_transition:
            raise ValueError(
                f"No valid transition from state '{instance.current_state}' with action '{action}'"
            )

        # Update state
        old_state = instance.current_state
        instance.current_state = valid_transition.get("to_state")

        # Merge context
        if context:
            if not instance.context:
                instance.context = {}
            instance.context.update(context)

        # Record transition in context
        if not instance.context:
            instance.context = {}
        instance.context["last_transition"] = {
            "from_state": old_state,
            "to_state": instance.current_state,
            "action": action,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        self.db.flush()

        if user_id:
            self.audit.log(
                tenant_id=tenant_id,
                action="update",
                entity_type="workflow_instance",
                entity_id=instance.id,
                user_id=user_id,
                new_values={
                    "current_state": instance.current_state,
                    "action": action,
                },
            )

        return instance
