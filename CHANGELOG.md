# Changelog

All notable changes to the Health Insurance Platform are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased] — 2026-06-23 (Phase 3 — Demo Ready, LAN Accessible, Full UAT Pass)

### Added
- **LAN hosting**: Both backend (port 8001) and frontend (port 5173) now bind to `0.0.0.0` — accessible from any device on the local network at `http://192.168.1.175:5173` (staff portal), `http://192.168.1.175:8001/docs` (API docs)
- **WeasyPrint fix**: Upgraded from 62.3 → 63.0 (resolved `AttributeError: 'super' has no attribute 'transform'`); added `DYLD_LIBRARY_PATH=/opt/homebrew/lib` to Makefile dev-backend target for macOS Apple Silicon PDF library resolution
- **Full backend UAT pass**: All 36 endpoints verified HTTP 200 — including all 7 PDF generation endpoints (MAF, KYC, ToB, Policy Schedule, Credit Note, Tax Invoice, Receipt Voucher) and all 9 report endpoints (CSV + PDF export)
- **Full frontend UAT pass**: 10 pages verified via Playwright headless browser — Dashboard, Applications, Policies, AML, Govt Checks, Reports, Claims, Products, Buy Portal, Login

### Fixed
- **AED template literals**: 4 pages had broken `AED AED {fmt(...)}` string literals (from prior sed substitution) — fixed in `ReportsPage`, `ClaimsPage`, `PortalPolicyPage`, `PortalClaimsPage`
- **AML Dashboard display**: `holdAlerts` filter used `a.status` (application status) instead of `a.aml_status` — now correctly shows 2 open alerts with customer names and risk scores (67.50 HIGH / 38.75 MEDIUM)
- **Makefile port**: Changed `dev-backend` target from port 8000 → 8001 to match Vite proxy config

---

## [Unreleased] — 2026-06-23 (Phase 3 — Demo Preparation, UAT, Currency Fix, AED Compliance)

### Added
- **Demo data seed** (`/tmp/seed_demo_sql.py`): 7 realistic applications, 3 active policies, 3 payments (AED 16,550 total), 2 AML records (1 MEDIUM, 1 HIGH), 3 govt verification records, 1 pending ICP check, 7 notifications (4 unread) — full Adamjee showcase dataset
- **Demo presentation** (`docs/ADAMJEE_DEMO_PRESENTATION.md`): Professional 10-section document covering architecture, features, compliance, premium breakdown, integration points, and roadmap
- **Demo scenarios guide** (`docs/ADAMJEE_DEMO_SCENARIOS.md`): 10 step-by-step demonstration scenarios with talking points, data tables, and Q&A

### Fixed
- **AML Dashboard** (`AmlDashboardPage.tsx`): `holdAlerts` filter was checking `a.status` (application status) instead of `a.aml_status` — AML alerts were showing 0 even with 2 flagged applications in DB
- **AML Dashboard** (`AmlDashboardPage.tsx`): Table now shows `application_number` and `customer_name` instead of raw UUIDs; risk score uses `aml_risk_score` field from alerts API response
- **`AmlAlert` TypeScript interface** extended with optional fields `application_number`, `customer_name`, `aml_status`, `aml_risk_score`, `created_at` to match actual API response shape
- **`BuyProductsPage.tsx`**: Last remaining `$` USD symbol replaced with `AED` in plan card base premium display (line 119)
- **Vite proxy** (`vite.config.ts`): Changed target from `http://localhost:8000` to `http://localhost:8001` — root cause of all browser API 404s
- **`app/models/__init__.py`**: Added all domain model imports (`Product`, `Plan`, `Member`, `Application`, `Policy`, `Claim`, `Payment`, etc.) to resolve SQLAlchemy string-based relationship lookups

### Currency (AED) — Complete Sweep
All USD `$` symbols replaced with `AED` across the frontend:
- `DashboardPage.tsx`: Recent payments, monthly premium KPI
- `ReportsPage.tsx`: Premium due, collected amounts (3 instances)
- `ClaimsPage.tsx`: Total claimed and approved amounts
- `ProductsPage.tsx`: Base premium table cell
- `BuyProductsPage.tsx`: Plan card base premium (now complete)
- `BuyApplyPage.tsx`: Premium display lines
- `PortalDashboardPage.tsx`, `PortalPolicyPage.tsx`, `PortalPaymentsPage.tsx`, `PortalClaimsPage.tsx`: All monetary displays

---

## [Unreleased] — 2026-06-23

### Added — Phase 1–2: UAE Compliance, AML, Govt Checks, PDF Generation, Enhanced Staff Portal

#### Backend — Database Migrations (0014–0026)
- **0016 market_config**: Tenant-level configurable key/value store (VAT rate, PSP fee, AML thresholds, etc.)
- **0017 premium_loadings**: Underwriter/BMI/Other/TPA/Broker/Insurer loadings per application/member
- **0018 commission_configs**: Configurable insurer/broker/TPA commission percentages per plan/broker
- **0019 application UAE fields**: `aml_status`, `aml_risk_score`, `govt_check_status`, `marital_status`, `occupation`, `employer_name`, `trn`, `sponsor_type`, `existing_health_insurance`, `is_diplomatic_passport`, `is_eid_under_process`, `remarks` (JSONB), `premium_breakdown` (JSONB)
- **0020 member medical questionnaire**: `medical_questionnaire` (JSONB, 14-question), `pregnancy_questionnaire`, `height_cm`, `weight_kg`
- **0021 aml_records**: AML check results (PEP, sanctions, risk score, transaction monitoring)
- **0022 govt_verification_records**: ICP/DHA/OFAC/UN/UAE Cabinet 74 check results with override support
- **0023 str_records**: Suspicious Transaction Reports with dual-authorisation workflow
- **0024 notification_records**: In-portal staff notifications
- **0025**: Extended `user_type_enum` with `compliance_officer` and `finance` values
- **0026**: Added `updated_at` to compliance tables (AML records, govt checks, notifications, loadings)

#### Backend — Services
- **`aml_service.py`**: 9-factor risk scoring engine (all weights configurable via `market_config`), PEP check stub, sanctions check, transaction monitoring, AML hold/clear workflow, auto-STR creation at CRITICAL risk
- **`govt_verification_service.py`**: ICP Emirates ID verification, DHA health check, OFAC/UN/UAE Cabinet 74 sanctions — all stubbed with `GOVT_API_MOCK=true`, Redis cache (90-day TTL), retry+fallback
- **`payment_gateway_service.py`**: Network International UAE gateway stub (`PAYMENT_GATEWAY_MOCK=true`), real mode with timeout/retry
- **`pdf_service.py`**: WeasyPrint + Jinja2 PDF generation for MAF, KYC, ToB, Policy Schedule, Credit Note, Tax Invoice, Receipt Voucher

#### Backend — API Endpoints
- **`/aml`**: `GET /alerts`, `GET /records/{id}`, `POST /{id}/clear`, `POST /{id}/hold`, `GET /str`, `POST /str`, `POST /str/{id}/approve`, `POST /str/{id}/file`
- **`/govt-checks`**: `POST /applications/{id}/verify-icp`, `POST /applications/{id}/verify-sanctions`, `GET /`, `GET /applications/{id}`, `POST /{record_id}/override`, `POST /bulk-retry`
- **`/notifications`**: `GET /` (with 60s polling), `POST /{id}/read`, `POST /read-all`
- **`/applications`** extended: `GET/POST /loadings`, `DELETE /loadings/{id}`, `GET/POST /remarks`, `POST /recalculate`
- **`/documents`**: 7 PDF generation endpoints (MAF, KYC, ToB, Schedule, Credit Note, Tax Invoice, Receipt)
- **`/reports`** extended: 7 new export endpoints with CSV + PDF format — `policies-issued`, `commission-statement`, `underwriter`, `aml-screening`, `govt-verification`, `str-log`, `dha-fines`

#### Backend — Schemas & Models
- `ApplicationCreate`/`ApplicationRead`: full UAE fields + AML/Govt status + premium breakdown
- `MemberCreate`/`MemberRead`: Emirates ID validation (784-YYYY-NNNNNNN-C), medical questionnaire, UAE identity fields
- Compliance models (`PremiumLoading`, `CommissionConfig`, `AmlRecord`, `GovtVerificationRecord`, `StrRecord`, `NotificationRecord`) all in `app/models/compliance.py`
- `MarketConfig` model for tenant-level configuration

#### Frontend
- **Layout**: Notification bell with unread badge (60s polling), AML and Govt Checks nav items
- **Dashboard**: AML Flagged + Govt Check Pending KPI cards linking to compliance pages
- **ApplicationsPage**: 
  - AML/Govt Check status badges in table
  - Filter bar (status, AML status, Govt check status) + search
  - Quick filter chips (Pending Review, AML Hold, AML Flagged, Govt Check Pending, Issued)
  - 4-tab application detail: Details, Loadings, Remarks, Documents
  - Underwriter loadings panel with add/remove
  - Threaded remarks with role badges (Underwriter/Broker/CO/System)
  - Document downloads (MAF, KYC, ToB PDFs)
  - UAE member fields: Emirates ID (validated), nationality, visa type, height/weight, occupation
  - Premium breakdown panel with recalculate button
- **PoliciesPage**:
  - AML status badge in table
  - Filter bar + quick chips (Active, AML Hold, AML Flagged, Expired)
  - 4-tab policy detail: Personal Details, Signed Docs, Other Documents, Remarks
  - PDF downloads: Policy Schedule, Credit Note, Tax Invoice, Receipt Voucher
- **AmlDashboardPage** (`/aml`): Open alerts table, clear-hold modal with mandatory justification, STR pipeline with dual-authorisation (CO submits → Admin approves → CO files)
- **GovtChecksPage** (`/govt-checks`): Verification records table, override modal, bulk retry with checkbox selection
- **ReportsPage**: 7 downloadable reports with CSV/PDF buttons and date range filter

#### Seed Data
- `scripts/seed_phase1.py`: 10 Adamjee plans (Workers Network, Silk Road, Pearl, Super Restricted, Emerald, Green, Restricted Network, Silver Classic, Silver Premium, General Network), 5 staff users, market_config (VAT 5%, AML thresholds, quote validity), commission configs

### Fixed
- `from app.config import get_settings` → `from config import get_settings` in AML, Govt Verification, Payment Gateway services (module path mismatch)
- Missing `updated_at` columns in `aml_records`, `govt_verification_records`, `notification_records`, `premium_loadings` (migration 0026)
- `error` prop rendering in `ApplicationDetailModal` was passing `Error` object as React node instead of string

---

## [Unreleased] — 2026-05-24

### Added — Adamjee UAE Buying Journey

#### Backend
- **New tenant**: `ADAMJEE` seeded in dev bootstrap with branding, admin user, 7 plans
- **UAE Member fields**: `passport_number`, `emirates_id`, `nationality`, `visa_type`, `document_expiry`, `place_of_birth` added to `Member` model
- **New router** `uae_buy.py` at prefix `/api/v1/uae-buy`:
  - `GET /info` — tenant info & branding
  - `GET /plans` — 7 Adamjee network-tier plans with full DHA coverages
  - `POST /ocr` — passport / Emirates ID image upload with OCR extraction
  - `POST /quote` — UAE premium calculation
  - `GET /regulations` — UAE insurance laws summary
  - `POST /apply` — UAE-compliant application submission
  - `POST /payment/{app_id}` — payment initiation (mock gateway)
  - `GET /payment/{app_id}/status` — payment status check
- **Pytesseract + Pillow** added to `requirements.txt` for OCR (with graceful fallback)

#### Frontend
- **New pages**:
  - `/buy/adamjee` — Adamjee branded landing page
  - `/buy/adamjee/buy` — 7-step UAE buying wizard
- **New service** `adamjeeApi.ts` with typed API calls
- **Routes** added to `App.tsx`
- **7-step wizard**:
  1. Personal Details (UAE-compliant form)
  2. Document Upload with OCR auto-fill
  3. Plan Selection (7 network tiers with comparison)
  4. Add Dependents (spouse, children, parents)
  5. Quote Summary
  6. UAE Regulations & Compliance Agreement
  7. Payment (credit card / Apple Pay / Google Pay)

#### Compliance
- All mandatory DHA fields collected
- UAE laws referenced and agreed to before payment
- Pre-existing conditions declaration mandatory

---

## Previous releases

See git log for earlier history.
