# Contributing

## Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.9+ |
| Node.js | 18+ |
| Docker & Docker Compose | 24+ (optional, for full-stack dev) |

## Quick start (local)

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
uvicorn main:app --reload

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Or use `make dev` from the repo root (starts both processes).

Default dev accounts (SQLite seed):

| Email | Password | Role |
|-------|----------|------|
| admin@testco.com | admin123 | tenant_admin |
| agent@testco.com | password123 | agent |
| superadmin@system.com | super123 | super_admin |

## Project layout

```
python/
├── backend/          # FastAPI application
│   ├── app/
│   │   ├── api/v1/   # Route handlers
│   │   ├── models/   # SQLAlchemy models
│   │   ├── services/ # Business logic
│   │   └── middleware/
│   ├── tests/        # pytest suite
│   ├── alembic/      # DB migrations
│   └── main.py
├── frontend/         # React + Vite SPA
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   ├── services/api.ts
│   │   └── store/
│   └── tests/        # Vitest suite
├── infra/docker/     # docker-compose + nginx
└── Makefile
```

## Running tests

```bash
# All tests
make test

# Backend only
make test-backend

# Frontend only
make test-frontend
```

Backend: `pytest` with an in-memory SQLite database — no external services needed.  
Frontend: `vitest` with `@testing-library/react` — components rendered in jsdom.

## Making changes

### Backend

- Models live in `app/models/`. After changing a model, generate a migration:
  ```bash
  alembic revision --autogenerate -m "describe change"
  alembic upgrade head
  ```
- All API routes require a valid JWT (`Authorization: Bearer <token>`) and a tenant header (`X-Tenant-ID: <uuid>`), except `/api/v1/auth/*` and `/health`.
- Multi-tenancy: every query must be scoped to `tenant_id`. The `TenantContextMiddleware` resolves the tenant from the header and stores it in `request.state`.

### Frontend

- Pages are in `src/pages/`. Each page uses React Query for data fetching and the `useToast()` hook for feedback.
- API calls go through `src/services/api.ts`. Add new endpoints there.
- Auth state is in `src/store/authStore.ts` (Zustand).

### Adding a new feature (checklist)

- [ ] Backend route + service + model (+ migration if schema changes)
- [ ] Backend tests in `backend/tests/`
- [ ] Frontend page or component
- [ ] Frontend tests in `frontend/tests/`
- [ ] Update `TASKS.md` if it tracks this area

## Code style

- **Python**: `ruff` for linting, `black` for formatting (`make lint` / `make format`).
- **TypeScript**: ESLint + Prettier (`npm run lint` in `frontend/`).
- No `print()` debugging in committed code — use the structured logger (`app/utils/logger.py`).

## Environment variables

Copy `backend/.env.example` to `backend/.env`. Never commit `.env`.  
Use `make secrets` to generate `SECRET_KEY` and `ENCRYPTION_KEY` values.

Key variables:

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

## Pull request guidelines

1. One concern per PR — avoid mixing feature work with refactors.
2. All CI checks must pass (`pytest`, `vitest`, `npm run build`).
3. Include a short description of what changed and why.
4. For schema changes, include the generated migration file.
