from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.product import Product, Plan, Coverage, RateCard, Quote
from app.schemas.product import ProductCreate, ProductUpdate, PlanCreate, PlanUpdate, CoverageCreate
from app.schemas.quotation import RateCardCreate, RateCardUpdate
from app.constants.enums import ProductStatus, QuoteStatus
from app.utils.formatters import generate_reference_number
from app.services.audit_service import AuditService
from datetime import datetime, timezone
import uuid


class ProductService:
    def __init__(self, db: Session, audit_service: AuditService):
        self.db = db
        self.audit = audit_service

    def create_product(self, tenant_id: str, data: ProductCreate, user_id: str) -> Product:
        product = Product(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            name=data.name,
            code=data.code,
            description=data.description,
            status=data.status,
            config=data.config,
        )
        self.db.add(product)
        self.db.flush()
        self.audit.log(
            tenant_id=tenant_id,
            action="create",
            entity_type="product",
            entity_id=product.id,
            user_id=user_id,
        )
        return product

    def get_by_id(self, tenant_id: str, product_id: str) -> Product:
        return self.db.query(Product).filter(
            and_(Product.tenant_id == tenant_id, Product.id == product_id)
        ).first()

    def list_products(self, tenant_id: str, skip: int = 0, limit: int = 20) -> tuple[list[Product], int]:
        query = self.db.query(Product).filter(Product.tenant_id == tenant_id)
        total = query.count()
        products = query.offset(skip).limit(limit).all()
        return products, total

    def update_product(self, tenant_id: str, product_id: str, data: ProductUpdate, user_id: str) -> Product:
        product = self.get_by_id(tenant_id, product_id)
        if not product:
            return None

        old_values = {
            "name": product.name,
            "status": product.status,
        }

        if data.name is not None:
            product.name = data.name
        if data.description is not None:
            product.description = data.description
        if data.status is not None:
            product.status = data.status
        if data.config is not None:
            product.config = data.config

        self.db.flush()
        self.audit.log(
            tenant_id=tenant_id,
            action="update",
            entity_type="product",
            entity_id=product.id,
            user_id=user_id,
            old_values=old_values,
            new_values={"name": product.name, "status": product.status},
        )
        return product

    def delete_product(self, tenant_id: str, product_id: str, user_id: str) -> bool:
        product = self.get_by_id(tenant_id, product_id)
        if not product:
            return False

        self.db.delete(product)
        self.db.flush()
        self.audit.log(
            tenant_id=tenant_id,
            action="delete",
            entity_type="product",
            entity_id=product_id,
            user_id=user_id,
        )
        return True


class PlanService:
    def __init__(self, db: Session, audit_service: AuditService):
        self.db = db
        self.audit = audit_service

    def create_plan(self, tenant_id: str, product_id: str, data: PlanCreate, user_id: str) -> Plan:
        plan = Plan(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            product_id=product_id,
            name=data.name,
            code=data.code,
            plan_type=data.plan_type,
            base_premium=data.base_premium,
            description=data.description,
            coverage_details=data.coverage_details,
            included_services=data.included_services,
            exclusions=data.exclusions,
            is_active=data.is_active,
        )
        self.db.add(plan)
        self.db.flush()
        self.audit.log(
            tenant_id=tenant_id,
            action="create",
            entity_type="plan",
            entity_id=plan.id,
            user_id=user_id,
        )
        return plan

    def get_by_id(self, tenant_id: str, plan_id: str) -> Plan:
        return self.db.query(Plan).filter(
            and_(Plan.tenant_id == tenant_id, Plan.id == plan_id)
        ).first()

    def list_plans(self, tenant_id: str, product_id: str, skip: int = 0, limit: int = 20) -> tuple[list[Plan], int]:
        query = self.db.query(Plan).filter(
            and_(Plan.tenant_id == tenant_id, Plan.product_id == product_id)
        )
        total = query.count()
        plans = query.offset(skip).limit(limit).all()
        return plans, total

    def update_plan(self, tenant_id: str, plan_id: str, data: PlanUpdate, user_id: str) -> Plan:
        plan = self.get_by_id(tenant_id, plan_id)
        if not plan:
            return None

        if data.name is not None:
            plan.name = data.name
        if data.plan_type is not None:
            plan.plan_type = data.plan_type
        if data.base_premium is not None:
            plan.base_premium = data.base_premium
        if data.description is not None:
            plan.description = data.description
        if data.coverage_details is not None:
            plan.coverage_details = data.coverage_details
        if data.included_services is not None:
            plan.included_services = data.included_services
        if data.exclusions is not None:
            plan.exclusions = data.exclusions
        if data.is_active is not None:
            plan.is_active = data.is_active

        self.db.flush()
        self.audit.log(
            tenant_id=tenant_id,
            action="update",
            entity_type="plan",
            entity_id=plan.id,
            user_id=user_id,
        )
        return plan

    def add_coverage(self, tenant_id: str, plan_id: str, data: CoverageCreate, user_id: str) -> Coverage:
        coverage = Coverage(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            plan_id=plan_id,
            name=data.name,
            coverage_type=data.coverage_type,
            limit_amount=data.limit_amount,
            copay=data.copay,
            coinsurance_percent=data.coinsurance_percent,
            config=data.config,
        )
        self.db.add(coverage)
        self.db.flush()
        self.audit.log(
            tenant_id=tenant_id,
            action="create",
            entity_type="coverage",
            entity_id=coverage.id,
            user_id=user_id,
        )
        return coverage
