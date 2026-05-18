# Architecture

## Overview

HealthShield is a multi-tenant SaaS platform where each insurance company (tenant) operates in full isolation. All data is scoped by `tenant_id` at the database level and enforced by middleware on every request.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Browser (SPA)                           │
│                                                                 │
│  /              Staff Back-Office   (React + Tailwind)          │
│  /buy           Purchase Storefront (public, no auth)           │
│  /portal        Member Self-Service (customer JWT)              │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTPS / Vite proxy (dev)
┌────────────────────────▼────────────────────────────────────────┐
│                    FastAPI (Python 3.9)                         │
│                                                                 │
│  /api/v1/auth/*        Authentication & tenant resolution       │
│  /api/v1/*             Staff API  (JWT required)                │
│  /api/v1/customer/*    Member Portal API  (customer JWT)        │
│  /api/v1/buy/*         Purchase API  (public, X-Tenant-ID only) │
│  /health               Health check                             │
└──────────────┬──────────────────────┬───────────────────────────┘
               │                      │
┌──────────────▼──────────┐  ┌────────▼─────────────────────────┐
│   SQLAlchemy ORM        │  │   Celery Worker (optional)       │
│   SQLite (dev)          │  │   Redis broker                   │
│   PostgreSQL (prod)     │  │   Background tasks               │
└─────────────────────────┘  └──────────────────────────────────┘
```

## Authentication & Multi-Tenancy

### Staff and Member Portal
Every protected request requires:
- `Authorization: Bearer <JWT>` — identifies the user and embeds `tenant_id`
- `X-Tenant-ID: <uuid>` — tenant context header (resolved by `TenantContextMiddleware`)

JWTs are short-lived (access: 30 min, refresh: 7 days). The refresh endpoint rotates tokens with a denylist to prevent reuse.

### Purchase Portal (`/buy/*`)
No authentication required. Endpoints read the tenant from `X-Tenant-ID` only, verified against the `tenants` table.

### Customer vs Staff Tokens
Both use the same `/api/v1/auth/login` endpoint and the same JWT format. The `user_type` claim distinguishes them:
- Staff tokens: `user_type` ∈ `{tenant_admin, agent, broker, underwriter, claims_manager}`
- Customer tokens: `user_type = customer`

The `get_current_customer` dependency (in `customer.py`) enforces this at the route level.

## Data Model

```
Tenant
 ├── User (staff + customers)
 ├── Product
 │    └── Plan
 │         ├── Coverage
 │         └── RateCard
 ├── Quote
 ├── Application
 │    ├── ApplicationItem  (→ Coverage)
 │    └── Member
 ├── Policy  (issued from Application)
 │    ├── Payment
 │    └── Claim
 └── DocumentUpload  (entity_type + entity_id polymorphic)
```

### Key Relationships

| From | To | Via |
|------|----|-----|
| Application | Policy | `PolicyService.issue_policy()` |
| Policy | Member | `Application.members` (through `application_id`) |
| Customer User | Policy | `User.extra_data["policy_id"]` (set at registration) |
| DocumentUpload | any entity | `entity_type` + `entity_id` columns |

## RBAC (Role-Based Access Control)

Permissions are defined as string constants in `app/constants/permissions.py`. Each route uses `Depends(require_permissions(PERMISSION_NAME))`.

Roles are stored in the `roles` and `user_roles` tables and evaluated per-tenant. Super admins bypass all permission checks.

## API Versioning

All routes live under `/api/v1/`. Breaking changes would introduce `/api/v2/`.

## Frontend State

| Store | File | What it holds |
|-------|------|---------------|
| Staff auth | `store/authStore.ts` | JWT, user, tenant — keys: `token`, `user` |
| Customer auth | `store/portalAuthStore.ts` | JWT, user, tenantId — keys: `portal_token`, `portal_user`, `portal_tenantId` |
| React Query cache | `main.tsx` (QueryClient) | All server state — invalidated after mutations |

Staff and customer sessions are independent; both can be active simultaneously (different localStorage keys).

## Error Response Format

All API errors use a consistent envelope:

```json
{
  "success": false,
  "errors": [
    { "code": "HTTP_ERROR", "message": "Plan not found." }
  ],
  "timestamp": "2026-05-18T00:00:00Z"
}
```

Validation errors from Pydantic include a `"loc"` field per error.

## Background Jobs (Celery)

Background tasks (email notifications, PDF generation) run via Celery workers connected to Redis. In development, you can skip Redis — the app starts without it, and background tasks are simply skipped. In production, set `REDIS_URL` in `.env`.
