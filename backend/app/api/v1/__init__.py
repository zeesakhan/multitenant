from fastapi import APIRouter
from app.api.v1 import auth, tenants, users, branding, products, quotations, applications, policies, members, payments, claims, workflows, documents, dashboard, reports
from app.api.v1.users import roles_router

v1_router = APIRouter(prefix="/api/v1")

v1_router.include_router(auth.router)
v1_router.include_router(tenants.router)
v1_router.include_router(users.router)
v1_router.include_router(roles_router)
v1_router.include_router(branding.router)
v1_router.include_router(products.router)
v1_router.include_router(quotations.router)
v1_router.include_router(applications.router)
v1_router.include_router(members.router)
v1_router.include_router(policies.router)
v1_router.include_router(payments.router)
v1_router.include_router(claims.router)
v1_router.include_router(dashboard.router)
v1_router.include_router(reports.router)
v1_router.include_router(workflows.router)
v1_router.include_router(documents.router)
