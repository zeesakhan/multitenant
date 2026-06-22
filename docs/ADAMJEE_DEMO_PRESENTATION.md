# Adamjee Insurance — Policy Sales Portal
## Product Demonstration Presentation
### Prepared for: Adamjee Insurance Technical & Business Review
### Date: June 23, 2026

---

## 1. Executive Summary

The **Adamjee Insurance Policy Sales Portal** is a purpose-built, UAE-compliant health insurance enrollment and management platform designed specifically for the Adamjee Insurance brand. The system provides an end-to-end digital workflow from customer quotation through policy issuance, with full compliance coverage including AML screening, government verification, and CBUAE regulatory reporting.

**Key Highlights**
- Full end-to-end policy lifecycle management (Draft → Issued)
- UAE regulatory compliance: AML/CFT scoring, ICP verification, sanctions screening
- Real-time VAT calculation (5%), PSP fee management, commission tracking
- Premium in AED — no currency ambiguity
- Role-based access for Admins, Underwriters, Brokers, and Compliance Officers
- Customer self-service portal with policy view, claims, and payment history

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    CLIENT LAYER                          │
│  Staff Portal (React 18 + TypeScript)                   │
│  Customer Portal  ·  Public Buy Portal                  │
└────────────────────────┬────────────────────────────────┘
                         │ HTTPS / JSON API
┌────────────────────────▼────────────────────────────────┐
│                   API LAYER (FastAPI)                    │
│  JWT Auth  ·  RBAC  ·  Multi-Tenant Middleware          │
│  Audit Logger  ·  Rate Limiting                         │
└────────────────────────┬────────────────────────────────┘
                         │ SQLAlchemy 2.0
┌────────────────────────▼────────────────────────────────┐
│                  DATA LAYER (PostgreSQL)                  │
│  Applications  ·  Members  ·  Policies  ·  Payments     │
│  AML Records  ·  Govt Checks  ·  STR Records            │
│  Notifications  ·  Audit Logs  ·  Premium Loadings      │
└─────────────────────────────────────────────────────────┘
```

**Technology Stack**
| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS |
| Backend | Python 3.11, FastAPI, SQLAlchemy 2.0, Pydantic v2 |
| Database | PostgreSQL 14+ |
| PDF Generation | WeasyPrint (Jinja2 HTML → PDF) |
| Auth | JWT (RS256), RBAC with fine-grained permissions |
| Deployment | Docker-ready, environment-config driven |

---

## 3. Key Features Demonstration

### 3.1 Staff Dashboard
- **Live KPIs**: Active policies count, AED premium collected, total applications, AML alerts
- **Applications by Status**: Visual pipeline (Draft → Submitted → Approved → Issued)
- **Recent Activity**: Last 5 applications and payments with one-click access
- **Compliance Alerts**: Red card for AML flagged, amber for pending govt checks

### 3.2 Application Management
- Filter bar: search by name/ref, status, AML status, Govt Check status
- Quick filter chips: Pending Review · AML Hold · AML Flagged · Govt Check Pending · Issued
- All 7 demo applications visible with real-time AML and Govt Check badges
- Two-action buttons per row: View (detail) · Act (approve/reject)

### 3.3 Policy Management
- 3 active policies displayed: POL-2026-00001, POL-2026-00002, POL-2025-00099
- Policy POL-2025-00099 expires in 25 days — renewal alert visible
- Premiums in AED: 8,750 / 4,850 / 2,950
- Full premium breakdown on detail: gross premium, VAT (5%), PSP fee, total payable

### 3.4 AML Compliance Dashboard
- **2 Open AML Alerts** (realistic demo scenarios):
  - APP-2026-0003: Ibrahim Hassan Al-Nasser — **67.50 HIGH** (Diplomatic passport + PEP status)
  - APP-2026-0002: Rajesh Sharma — **38.75 MEDIUM** (FATF nationality + import/export occupation)
- Risk Score Bands: LOW (0–25) · MEDIUM (26–50) · HIGH (51–75) · CRITICAL (76–100)
- "Clear Hold" workflow for Compliance Officer to resolve after EDD
- STR Pipeline for filing Suspicious Transaction Reports with dual authorisation
- **Tipping-off Protection**: Policyholders are NEVER informed of AML holds

### 3.5 Government Checks Dashboard
- ICP Emirates ID verification (UAE Federal Authority)
- OFAC, UN Sanctions, UAE Cabinet Resolution 74 screening
- 1 pending ICP check for demonstration (Rajesh Sharma)
- Manual override workflow with mandatory justification (audit-trailed)
- Bulk retry for failed checks

### 3.6 Reports Module
- 7 report categories available
- CSV and PDF export for all reports
- Date range filtering
- Reports include: DHA Fines, Commission Statement, Underwriter Report, AML Screening, Policy Issued, Government Verification, STR Log

### 3.7 Customer Self-Service Portal
- Customers access via `/portal` with their own login
- View active policy, member list, claims, and payment history
- All figures in AED

### 3.8 Public Buying Portal (`/buy/adamjee`)
- Branded Adamjee landing page
- Product and plan listing with premium pricing in AED
- Online application form with medical questionnaire
- Integration-ready for Network International payment gateway

---

## 4. Compliance Framework

### AML Risk Scoring Engine

The system automatically calculates an AML risk score on every application based on 9 weighted factors:

| Factor | Max Points | Triggered When |
|--------|-----------|----------------|
| PEP Status (self/family) | 25 | Politically Exposed Person declared |
| Sanctions Match | 40 (auto-block) | Name appears on OFAC/UN/HMT lists |
| FATF High-Risk Nationality | 15 | Nationality on FATF watchlist |
| Premium > AED 50,000 | 10 | Single policy premium exceeds threshold |
| Cash Payment | 10 | Payment method is cash |
| High-Risk Occupation | 5 | Import/export, money services, etc. |
| Income vs Premium inconsistency | 10 | Declared income inconsistent with premium |
| Prior AML Flag | 20 | Previous AML record on file |
| Diplomatic Passport | 5 | Member holds diplomatic passport |

**Automated Actions by Risk Band**:
- **LOW (0–25)**: Auto-proceed to underwriting
- **MEDIUM (26–50)**: Proceed + notify Compliance Officer
- **HIGH (51–75)**: Application placed on AML Hold
- **CRITICAL (76–100)**: Auto-hold + auto-generate STR draft

### UAE Regulatory Compliance
- CBUAE AML/CFT Guidelines 2021 aligned
- ICP (Immigration and Citizenship Authority) ID verification
- Dubai Health Authority (DHA) network compliance
- OFAC, UN Security Council, EU sanctions screening
- STR filing workflow with dual-authorisation (CO + Senior Management)
- Full immutable audit trail on all compliance actions

---

## 5. Premium Calculation (AED)

### Sample Breakdown — APP-2026-0001
| Component | Amount (AED) |
|-----------|-------------|
| Base Premium (1 adult, Silver Premium plan) | 7,980.00 |
| Underwriter Loading | 353.33 |
| BMI Loading | — |
| Gross Premium (excl. tax) | 8,333.33 |
| VAT @ 5% | 416.67 |
| PSP Processing Fee | 24.00 |
| **Total Amount Payable** | **8,750.00** |
| Insurer Commission (5%) | 416.67 |
| Broker Commission (15.5%) | 1,291.67 |

All rates and thresholds are database-driven — no hardcoded values in code.

---

## 6. Multi-Tenant Architecture

The platform is designed as a multi-tenant SaaS solution. While this demonstration uses the Adamjee tenant, the platform can support additional insurers with:
- Separate branding (logo, colours, brand name)
- Independent product catalogs and rate structures
- Isolated data with tenant-level encryption
- Per-tenant compliance configuration (different market_config settings)
- Separate admin teams with no cross-tenant data access

---

## 7. Security & Data Protection

- **JWT Authentication**: Stateless tokens with 1-hour expiry, refresh token rotation
- **RBAC**: 6 permission scopes (AML, Govt Checks, Reports, Underwriting, etc.) on every endpoint
- **PII Encryption**: Emirates ID, passport numbers, medical questionnaire answers — AES-256 at rest
- **Audit Log**: Every write action (who, what, when, before/after state) — immutable
- **Tenant Isolation**: Row-level security via tenant_id on every table — cross-tenant queries impossible
- **Rate Limiting**: API rate limits prevent credential stuffing and enumeration
- **HTTPS Only**: TLS 1.3 enforced in production

---

## 8. Integration Points

| System | Status | Notes |
|--------|--------|-------|
| Network International (Payment Gateway) | Stub / Ready | Real integration via `PAYMENT_GATEWAY_API_KEY` env var |
| ICP UAE (Emirates ID Verification) | Stub / Ready | Real integration via `ICP_API_KEY` env var |
| OFAC Sanctions | Stub / Ready | Real integration via `OFAC_API_KEY` env var |
| Dubai Health Authority (DHA) | Stub / Ready | Real integration via `DHA_API_KEY` env var |
| World-Check PEP Database | Stub / Ready | Real integration via `PEP_API_KEY` env var |
| Email (Notifications) | Console / Ready | Production SMTP via `SMTP_*` env vars |
| Munich Re (Reinsurance) | Future | Planned Phase 5 |

---

## 9. Demo Credentials

| Role | Email | Password |
|------|-------|---------|
| Admin (Adamjee) | admin@adamjee.ae | adamjee123 |

**System URLs (Local Demo)**:
- Staff Portal: http://localhost:5173
- API Documentation: http://localhost:8001/docs

---

## 10. Next Steps / Roadmap

| Phase | Feature | Timeline |
|-------|---------|---------|
| Phase 3 (Now) | Current demo — full AML, compliance, reporting | Complete |
| Phase 4 | Network International live payment integration | 2 weeks |
| Phase 5 | Real ICP / OFAC / DHA API integration | 4 weeks |
| Phase 6 | Mobile app for agents (React Native) | 8 weeks |
| Phase 7 | Reinsurance data feeds (Munich Re) | TBD |
| Phase 8 | Business Intelligence dashboard (advanced analytics) | TBD |

---

*Prepared by the Development Team — All amounts in AED*
*Adamjee Insurance Policy Sales Portal — Confidential*
