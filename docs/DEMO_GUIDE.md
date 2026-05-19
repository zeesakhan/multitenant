# Client Demo Guide

This guide walks through every portal area with exact credentials and inputs.  
All data is pre-loaded in `dev.db` by running `python scripts/seed_demo.py`.

---

## Quick-Start Checklist

```bash
# 1. Start backend
cd backend && source ../venv/bin/activate
uvicorn main:app --reload          # → http://localhost:8000

# 2. Start frontend (new terminal)
cd frontend && npm run dev         # → http://localhost:5173
```

---

## Credentials Reference Card

### Staff Portal — `http://localhost:5173`

| Role | Email | Password |
|------|-------|----------|
| Tenant Admin | `admin@testco.com` | `admin123` |
| Agent | `agent@testco.com` | `password123` |
| Underwriter | `underwriter@testco.com` | `underwriter123` |
| Claims Manager | `claims@testco.com` | `claims123` |

### Member Portal — `http://localhost:5173/portal`

| Customer | Email | Password | Policy |
|----------|-------|----------|--------|
| James Wilson (family) | `james.wilson@email.com` | `Customer123` | `POL-DEMO-5F824F` |
| Michael Chen (individual) | `michael.chen@email.com` | `Customer123` | `POL-DEMO-29C0AE` |

### Purchase Portal — `http://localhost:5173/buy`

| Field | Value |
|-------|-------|
| Company Code | `TESTCO` |

### New Member Registration Demo

| Field | Value |
|-------|-------|
| Company code | `TESTCO` |
| Policy number | `POL-DEMO-D87696` (Emily Rodriguez) |
| Date of birth | `1995-07-04` |
| Name | Any (e.g. Emily Rodriguez) |
| Email | Any new email (e.g. `emily@demo.com`) |
| Password | Any 8+ characters |

---

## Demo Scenario 1 — Staff Back-Office

**URL:** `http://localhost:5173`  
**Login:** `admin@testco.com` / `admin123`

### 1.1 Dashboard
- Shows KPI cards: active policies count, recent applications, payment totals
- Click **Dashboard** in the sidebar

### 1.2 Products & Plans
1. Click **Products** in the sidebar
2. Show **Health Shield Plus** — click in to reveal Gold and Silver plans with 6 and 4 coverages respectively
3. Show **Basic Care** with the Essential Plan

### 1.3 Application Queue (Underwriter flow)
1. Click **Applications** in the sidebar
2. Show the queue — 4 incoming applications:
   - **Robert Kim** — Gold Family, 4 members — status: `Under Review`
   - **Linda Park** — Silver Individual — status: `Submitted` (came via self-service portal)
   - **David Brown** — Essential — status: `Submitted` (came via self-service portal)
   - **Priya Sharma** — Gold Family, 2 members — status: `Approved`
3. Open **Robert Kim's application** → click **Approve** to move it forward
4. Open **Priya Sharma's application** (already Approved) → click **Issue Policy** to demonstrate policy creation

### 1.4 Policies
1. Click **Policies** in the sidebar
2. Show the 3 active policies: Wilson (family), Chen (individual), Rodriguez (individual)
3. Open **James Wilson's policy** — shows coverage, premium, member count, dates

### 1.5 Claims Adjudication
1. Click **Claims** in the sidebar
2. Show the 4 claims across statuses:
   - James Wilson — Hospitalization — **Approved** ($3,420 of $3,800)
   - James Wilson — Pharmacy — **Paid** ($280)
   - Emma Wilson — Outpatient — **Submitted** (pending review)
   - Michael Chen — Dental — **Under Review**
3. Open Emma Wilson's claim → approve it (enter approved amount: **$315**)
4. Open Michael Chen's claim → demonstrate rejection with a reason

### 1.6 Payments
1. Click **Payments** — shows 4 payments across the 3 policies
2. Shows payment methods: Bank Transfer, Card, UPI

### 1.7 Reports
1. Click **Reports** — shows KPI summary: active policies, expiring soon, premium collected

### 1.8 Users
1. Click **Users** — shows all 7 users including the 2 customer accounts
2. Shows the 4 staff roles: admin, agent, underwriter, claims manager

---

## Demo Scenario 2 — Purchase Portal (New Customer Buys a Policy)

**URL:** `http://localhost:5173/buy`  
**No login required**

### Step 1 — Landing Page
- Enter company code: **`TESTCO`** → click **Browse**

### Step 2 — Plan Catalog
- Shows 2 products with 3 plans:
  - **Gold Family Plan** — $1,800/yr — 6 coverages (expand to show all)
  - **Silver Individual Plan** — $900/yr — 4 coverages
  - **Essential Plan** — $480/yr — 3 coverages
- Click **Apply Now** on the **Gold Family Plan**

### Step 3 — Application Wizard

**Personal Info (Step 1):**
| Field | Value |
|-------|-------|
| First name | `Sophie` |
| Last name | `Turner` |
| Email | `sophie.turner@demo.com` |
| Phone | `+1 555 987 6543` |
| Date of birth | `1990-05-22` |
| Gender | Female |

**Dependents (Step 2):**
- Click **Add a Dependent**

| Field | Value |
|-------|-------|
| First name | `Oliver` |
| Last name | `Turner` |
| Relationship | `Spouse` |
| Gender | Male |
| Date of birth | `1988-09-14` |

- Watch the live premium preview update: **$1,800 + $1,350 = $3,150/yr**
- Click **Review Quote**

**Review & Quote (Step 3):**
- Server confirms total: **$3,150.00/yr**
- Shows member breakdown and full coverage table
- Shows applicant summary
- Click **Submit Application**

**Confirmation (Step 4):**
- Application reference number displayed (e.g. `APP-20260519-XXXX`)
- "What happens next" guide shown
- Link to **Register on Portal** (for after staff approves)

### Back in Staff Portal
- Go to **Applications** → new application from Sophie Turner is visible with status `Submitted` and source `self_service`

---

## Demo Scenario 3 — Member Portal (Existing Policyholder)

**URL:** `http://localhost:5173/portal`  
**Login:** `james.wilson@email.com` / `Customer123`

### 3.1 Login Flow
1. Enter company code: **`TESTCO`** → Continue
2. Enter email and password → Sign in
3. Lands on the **Dashboard**

### 3.2 Dashboard
- Policy status banner: **Active** — Gold Family Plan
- KPI cards:
  - Policy Status: Active
  - Total Paid: **$1,890.00** (2 quarterly payments)
  - Active Claims: **1** (Emma's outpatient — submitted)
  - Members Covered: **3**
- Recent payments and recent claims panels
- Quick action grid

### 3.3 My Policy
- Click **My Policy** in the sidebar
- Shows policy number `POL-DEMO-5F824F`, plan, premium, dates
- Coverage breakdown table: 6 coverages with limits (Hospitalization $150k, Maternity $20k, etc.)

### 3.4 Covered Members
- Click **Members** in the sidebar
- Primary insured: **James Wilson** (age 43)
- Dependents: **Sarah Wilson** (spouse, age 41), **Emma Wilson** (child, age 10)

### 3.5 Claims
- Click **Claims** in the sidebar
- 3 claims for this family:
  - `CLM-DEMO-...` Hospitalization — **Approved** $3,420
  - `CLM-DEMO-...` Pharmacy — **Paid** $280
  - `CLM-DEMO-...` Outpatient (Emma) — **Submitted** $350
- Click **File a Claim** button
  - Select type: **Vision**
  - Select member: **Emma Wilson**
  - Date: `2026-05-01`
  - Amount: `$180`
  - Description: `Annual eye exam and prescription lenses`
  - Submit → appears in list as `Submitted`

### 3.6 Payments
- Click **Payments** — shows 2 quarterly bank transfer payments
- Total paid: **$1,890.00**

### 3.7 Documents
- Click **Documents** — shows 2 documents:
  - `policy-document-wilson.pdf` — Policy Document (valid)
  - `invoice-Q1-2026.pdf` — Invoice (valid)

### 3.8 Profile
- Click **My Profile**
- Update phone number → Save Changes (shows success banner)
- Change password → enter current (`Customer123`), new password → Update Password

---

## Demo Scenario 4 — Member Portal (Under-Review Claim)

**URL:** `http://localhost:5173/portal`  
**Login:** `michael.chen@email.com` / `Customer123`

### What to show
- Dashboard: **1 active claim** (Dental under review)
- Claims page: shows `CLM-DEMO-...` Dental — `Under Review` — $1,200 claimed
- Policy: Silver Individual Plan, $900/yr, 4 coverages
- Payments: 1 card payment, total paid $900

---

## Demo Scenario 5 — New Customer Self-Registration

**URL:** `http://localhost:5173/portal/register`

Emily Rodriguez has an active policy but no portal account yet. This demonstrates the identity-verification registration flow.

| Step | Field | Value |
|------|-------|-------|
| 1. Company | Code | `TESTCO` |
| 2. Verify | Policy number | `POL-DEMO-D87696` |
| 2. Verify | Date of birth | `1995-07-04` |
| 3. Account | First name | `Emily` |
| 3. Account | Last name | `Rodriguez` |
| 3. Account | Email | `emily@demo.com` (or any new email) |
| 3. Account | Password | `Demo2026!` |

On success → redirected to **Dashboard** showing:
- Essential Plan, 1 member, $480 total paid, 0 claims
- 2 documents available

---

## Demo Data Summary

| Entity | Count | Details |
|--------|-------|---------|
| Products | 2 | Health Shield Plus, Basic Care |
| Plans | 3 | Gold ($1,800), Silver ($900), Essential ($480) |
| Coverages | 13 | Across all 3 plans |
| Active Policies | 3 | Wilson, Chen, Rodriguez |
| Total Members | 13 | Across all applications |
| Payments | 4 | Bank transfer, card, UPI |
| Claims | 4 | Approved, paid, submitted, under review |
| Documents | 5 | Policy docs, invoice, application form |
| Staff Users | 4 | Admin, agent, underwriter, claims manager |
| Customer Accounts | 2 | Wilson, Chen (Rodriguez registers live in demo) |
| Pending Applications | 4 | Under review, submitted ×2, approved |

---

## Resetting Demo Data

```bash
# Remove the database and re-seed from scratch
cd backend
rm dev.db
alembic upgrade head
python scripts/seed_demo.py
```
