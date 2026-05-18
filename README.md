# HealthShield — Multi-Tenant Health Insurance Platform

A full-stack insurance management platform with three distinct portals: a staff back-office, a customer self-service portal, and a public policy purchase storefront.

## Portals at a Glance

| Portal | URL | Who uses it |
|--------|-----|-------------|
| **Staff** | `/` | Admins, agents, underwriters, claims managers |
| **Purchase** | `/buy` | Anyone — no login required |
| **Member** | `/portal` | Existing policyholders |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.9 · FastAPI · SQLAlchemy · SQLite (dev) / PostgreSQL (prod) |
| Frontend | React 18 · TypeScript · Vite · Tailwind CSS · React Query |
| Auth | JWT (access + refresh) · per-tenant isolation |
| Background jobs | Celery + Redis (optional in dev) |
| Tests | pytest (105 backend) · Vitest (79 frontend) |

## Quick Start

```bash
# 1. Backend
cd backend
python -m venv ../venv && source ../venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # fill in SECRET_KEY etc.
alembic upgrade head
uvicorn main:app --reload     # http://localhost:8000

# 2. Frontend (new terminal)
cd frontend
npm install
npm run dev                   # http://localhost:5173
```

Or `make dev` from the repo root to start both at once.

### Default dev accounts

| Email | Password | Role |
|-------|----------|------|
| `admin@testco.com` | `admin123` | Tenant Admin |
| `agent@testco.com` | `password123` | Agent |
| `superadmin@system.com` | `super123` | Super Admin |

Default tenant code: **TESTCO**

## Documentation

| Document | Description |
|----------|-------------|
| [docs/architecture.md](docs/architecture.md) | System design, data model, auth |
| [docs/customer-portal/overview.md](docs/customer-portal/overview.md) | Customer-facing portals overview |
| [docs/customer-portal/purchase-portal.md](docs/customer-portal/purchase-portal.md) | `/buy` — policy purchase flow |
| [docs/customer-portal/member-portal.md](docs/customer-portal/member-portal.md) | `/portal` — policyholder self-service |
| [docs/customer-portal/api-reference.md](docs/customer-portal/api-reference.md) | Public & customer API endpoints |
| [docs/staff-portal/overview.md](docs/staff-portal/overview.md) | Staff back-office portal |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Dev setup, testing, conventions |

## Running Tests

```bash
make test            # both suites
make test-backend    # pytest (105 tests)
make test-frontend   # vitest (79 tests)
```

## Project Layout

```
python/
├── backend/
│   ├── app/
│   │   ├── api/v1/        # Route handlers (auth, products, applications, customer, buy, …)
│   │   ├── models/        # SQLAlchemy ORM models
│   │   ├── services/      # Business logic
│   │   ├── schemas/       # Pydantic request/response schemas
│   │   ├── constants/     # Enums, permissions
│   │   └── middleware/    # Auth, tenant context, rate limiting
│   ├── tests/             # pytest suite (105 tests)
│   ├── alembic/           # DB migrations
│   └── main.py
├── frontend/
│   ├── src/
│   │   ├── pages/         # Staff pages
│   │   ├── pages/portal/  # Member portal pages
│   │   ├── pages/buy/     # Purchase portal pages
│   │   ├── components/    # Shared UI components
│   │   ├── services/      # API clients (api.ts, portalApi.ts, buyApi.ts)
│   │   └── store/         # Auth state (authStore, portalAuthStore)
│   └── tests/             # Vitest suite (79 tests)
├── docs/                  # Project documentation
├── infra/docker/          # docker-compose + nginx
└── Makefile
```
