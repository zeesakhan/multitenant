# Contributing

## Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.9+ |
| Node.js | 18+ |
| Docker & Docker Compose | 24+ (optional) |

## Quick Start (local)

```bash
# Clone and enter the repo
git clone <repo-url>
cd python

# Generate secrets for your .env
bash backend/scripts/generate_secrets.sh

# Backend
cd backend
python -m venv ../venv
source ../venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # fill in the values
alembic upgrade head
uvicorn main:app --reload     # http://localhost:8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev                   # http://localhost:5173
```

Or use `make dev` from the repo root (starts both processes).

## Default Dev Accounts

| Email | Password | Role |
|-------|----------|------|
| `admin@testco.com` | `admin123` | Tenant Admin |
| `agent@testco.com` | `password123` | Agent |
| `superadmin@system.com` | `super123` | Super Admin |

Default tenant code: **TESTCO**

## Portals

| Portal | URL | Notes |
|--------|-----|-------|
| Staff back-office | `http://localhost:5173/` | Requires staff login |
| Purchase storefront | `http://localhost:5173/buy` | Public — no login |
| Member portal | `http://localhost:5173/portal` | Requires customer account |
| API docs | `http://localhost:8000/docs` | FastAPI Swagger (dev only) |

## Project Layout

```
python/
├── backend/
│   ├── app/
│   │   ├── api/v1/        # Route handlers
│   │   │   ├── auth.py
│   │   │   ├── buy.py         ← purchase portal (public)
│   │   │   ├── customer.py    ← member portal (customer JWT)
│   │   │   ├── products.py
│   │   │   ├── applications.py
│   │   │   └── …
│   │   ├── models/        # SQLAlchemy models
│   │   ├── services/      # Business logic
│   │   ├── schemas/       # Pydantic schemas
│   │   └── middleware/    # Auth, tenant context, rate limiting
│   ├── tests/             # pytest suite (105 tests)
│   ├── alembic/           # DB migrations
│   └── main.py
├── frontend/
│   ├── src/
│   │   ├── pages/             # Staff pages
│   │   ├── pages/portal/      # Member portal pages
│   │   ├── pages/buy/         # Purchase portal pages
│   │   ├── components/        # Layout, PortalLayout, shared UI
│   │   ├── services/
│   │   │   ├── api.ts             ← staff API client
│   │   │   ├── portalApi.ts       ← member portal API client
│   │   │   └── buyApi.ts          ← purchase portal API client
│   │   └── store/
│   │       ├── authStore.ts       ← staff session
│   │       └── portalAuthStore.ts ← customer session
│   └── tests/             # Vitest suite (79 tests)
├── docs/                  # Project documentation
├── infra/docker/          # docker-compose + nginx
└── Makefile
```

## Running Tests

```bash
# All tests
make test

# Backend only (pytest)
make test-backend

# Frontend only (vitest)
make test-frontend

# Specific backend file
cd backend && python -m pytest tests/test_buy.py -v

# Specific frontend file
cd frontend && npx vitest run tests/DashboardPage.test.tsx
```

Backend tests use an in-memory SQLite database — no external services needed.  
Frontend tests use Vitest + `@testing-library/react` with jsdom.

## Making Backend Changes

- **New model** → add to `app/models/`, import in `app/models/__init__.py`, generate migration:
  ```bash
  alembic revision --autogenerate -m "describe change"
  alembic upgrade head
  ```
- **New route** → add handler in `app/api/v1/`, register router in `app/api/v1/__init__.py`
- **Staff routes** require `Depends(require_permissions(PERMISSION))` + JWT
- **Customer routes** require `Depends(get_current_customer)` in `customer.py`
- **Public routes** (purchase portal) only need `X-Tenant-ID` via `_get_tenant()` in `buy.py`
- Every query must be scoped to `tenant_id` — never query without it

## Making Frontend Changes

- **New staff page** → `src/pages/`, add route in `App.tsx` inside `<PrivateRoute>`
- **New portal page** → `src/pages/portal/`, add route inside `<PortalPrivateRoute>`
- **New buy page** → `src/pages/buy/`, add as a public route in `App.tsx`
- Use React Query (`useQuery` / `useMutation`) for all server state
- Staff API calls → `src/services/api.ts`
- Member portal calls → `src/services/portalApi.ts`
- Purchase portal calls → `src/services/buyApi.ts`
- Toast feedback → `useToast()` hook

## New Feature Checklist

- [ ] Backend route + service (+ migration if schema changes)
- [ ] Backend tests in `backend/tests/`
- [ ] Frontend page or component
- [ ] Frontend tests in `frontend/tests/`
- [ ] Update relevant docs in `docs/`

## Code Style

- **Python**: `ruff` for linting, `black` for formatting (`make lint` / `make format`)
- **TypeScript**: ESLint + Prettier (`npm run lint` in `frontend/`)
- No `print()` debugging in committed code — use the structured logger (`app/utils/logger.py`)

## Environment Variables

Copy `backend/.env.example` to `backend/.env`. Never commit `.env`.  
Use `make secrets` to generate `SECRET_KEY` and `ENCRYPTION_KEY`.

| Variable | Purpose |
|----------|---------|
| `SECRET_KEY` | JWT signing key |
| `ENCRYPTION_KEY` | Field-level encryption |
| `DATABASE_URL` | SQLAlchemy connection string |
| `FRONTEND_URL` | Used in password-reset emails |
| `REDIS_URL` | Celery broker (optional in dev) |

## Docker

```bash
make docker-up    # starts backend, frontend, nginx, worker, redis
make docker-down  # tears everything down
```

The backend runs `alembic upgrade head` automatically on container start.

## Pull Request Guidelines

1. One concern per PR — avoid mixing feature work with refactors
2. All CI checks must pass (`pytest`, `vitest`, `npm run build`)
3. Include a short description of what changed and why
4. For schema changes, include the generated migration file
5. For portal changes, verify the relevant portal still works end-to-end
