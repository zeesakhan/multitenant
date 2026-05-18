.PHONY: help dev dev-backend dev-frontend test test-backend test-frontend \
        migrate seed lint format build docker-up docker-down secrets

help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "  dev             Start backend + frontend in parallel"
	@echo "  dev-backend     Start FastAPI dev server only"
	@echo "  dev-frontend    Start Vite dev server only"
	@echo ""
	@echo "  test            Run all tests (backend + frontend)"
	@echo "  test-backend    Run pytest with coverage"
	@echo "  test-frontend   Run vitest"
	@echo ""
	@echo "  migrate         Run Alembic migrations"
	@echo "  seed            Seed development data"
	@echo "  lint            Ruff + ESLint"
	@echo "  format          Black + Prettier"
	@echo ""
	@echo "  build           Build frontend production bundle"
	@echo "  docker-up       Start all services via docker-compose"
	@echo "  docker-down     Stop all services"
	@echo "  secrets         Generate SECRET_KEY and ENCRYPTION_KEY"

# ── Development ───────────────────────────────────────────────────────────────

dev:
	@$(MAKE) -j2 dev-backend dev-frontend

dev-backend:
	cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && npm run dev

# ── Tests ─────────────────────────────────────────────────────────────────────

test: test-backend test-frontend

test-backend:
	cd backend && python -m pytest tests/ -x -q --cov=app --cov-report=term-missing

test-frontend:
	cd frontend && npm run test:run

# ── Database ──────────────────────────────────────────────────────────────────

migrate:
	cd backend && alembic upgrade head

seed:
	cd backend && python main.py seed 2>/dev/null || python -c "from main import seed_dev_data; seed_dev_data()"

# ── Code quality ──────────────────────────────────────────────────────────────

lint:
	cd backend && ruff check app/ tests/ || true
	cd frontend && npx eslint src/ --ext .ts,.tsx || true

format:
	cd backend && black app/ tests/ || true
	cd frontend && npx prettier --write "src/**/*.{ts,tsx}" || true

# ── Build & deploy ────────────────────────────────────────────────────────────

build:
	cd frontend && npm run build

docker-up:
	docker compose -f infra/docker/docker-compose.yml up --build -d

docker-down:
	docker compose -f infra/docker/docker-compose.yml down

secrets:
	@bash backend/scripts/generate_secrets.sh
