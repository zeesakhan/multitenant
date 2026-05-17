from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.tenant import Tenant, BrandConfig
from app.schemas.tenant import TenantCreate, TenantUpdate, BrandConfigUpdate
from app.constants.enums import TenantStatus
from app.constants.messages import TENANT_NOT_FOUND, TENANT_ALREADY_EXISTS
from typing import Optional, List
import uuid


class TenantService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: TenantCreate) -> Tenant:
        if self.db.query(Tenant).filter(Tenant.code == data.code).first():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=TENANT_ALREADY_EXISTS)

        tenant = Tenant(
            id=str(uuid.uuid4()),
            code=data.code,
            name=data.name,
            contact_email=data.contact_email,
            contact_phone=data.contact_phone,
            country=data.country,
            currency=data.currency,
            timezone=data.timezone,
            config=data.config or {},
            status=TenantStatus.ACTIVE,
        )
        self.db.add(tenant)

        brand = BrandConfig(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            company_name=data.name,
        )
        self.db.add(brand)
        self.db.commit()
        self.db.refresh(tenant)
        return tenant

    def get_by_id(self, tenant_id: str) -> Tenant:
        t = self.db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not t:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=TENANT_NOT_FOUND)
        return t

    def get_by_code(self, code: str) -> Optional[Tenant]:
        return self.db.query(Tenant).filter(Tenant.code == code).first()

    def list_all(self, skip: int = 0, limit: int = 20) -> tuple[List[Tenant], int]:
        q = self.db.query(Tenant)
        total = q.count()
        return q.offset(skip).limit(limit).all(), total

    def update(self, tenant_id: str, data: TenantUpdate) -> Tenant:
        tenant = self.get_by_id(tenant_id)
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(tenant, field, value)
        self.db.commit()
        self.db.refresh(tenant)
        return tenant

    def get_brand_config(self, tenant_id: str) -> BrandConfig:
        brand = self.db.query(BrandConfig).filter(BrandConfig.tenant_id == tenant_id).first()
        if not brand:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=TENANT_NOT_FOUND)
        return brand

    def update_brand_config(self, tenant_id: str, data: BrandConfigUpdate) -> BrandConfig:
        brand = self.get_brand_config(tenant_id)
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(brand, field, value)
        self.db.commit()
        self.db.refresh(brand)
        return brand

    def get_config(self, tenant_id: str, key: str, default=None):
        tenant = self.get_by_id(tenant_id)
        config = tenant.config or {}
        return config.get(key, default)

    def set_config(self, tenant_id: str, updates: dict) -> Tenant:
        tenant = self.get_by_id(tenant_id)
        config = dict(tenant.config or {})
        config.update(updates)
        tenant.config = config
        self.db.commit()
        self.db.refresh(tenant)
        return tenant
