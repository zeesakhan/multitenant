# Purchase Portal (`/buy`)

The purchase portal is a fully public storefront — no account or login required. Customers browse plans, get an instant quote, and submit an application that feeds directly into the staff back-office.

## URL Structure

| Route | Component | Purpose |
|-------|-----------|---------|
| `/buy` | `BuyLandingPage` | Company code entry + feature overview |
| `/buy/products` | `BuyProductsPage` | Plan catalog for the selected tenant |
| `/buy/apply` | `BuyApplyPage` | 4-step application wizard |

All three pages are public routes in `App.tsx` — no `PrivateRoute` wrapper.

## User Flow

### Step 0 — Landing Page (`/buy`)

Customer enters their **company code** (e.g. `ACME`). The frontend calls `GET /api/v1/auth/tenant/{code}` to resolve the tenant ID and name, then navigates to `/buy/products` passing `{ tenantId, tenantName }` via React Router state.

### Step 1 — Plan Catalog (`/buy/products`)

Calls `GET /api/v1/buy/products` with `X-Tenant-ID` header. Renders a card grid showing:
- Product name and description
- Plan name, type (individual / family / group / senior), and base premium
- Coverage list with limit amounts (first 4 shown; expandable)
- **Apply Now** button

Navigates to `/buy/apply` passing `{ tenantId, tenantName, plan, productName }` in router state.

### Step 2 — Application Wizard (`/buy/apply`)

Four steps managed with local React state:

#### Wizard Step 1 — Personal Information
Captures the primary insured's:
- First name, last name
- Email address (used for correspondence and portal registration)
- Phone number (optional)
- Date of birth
- Gender

#### Wizard Step 2 — Dependents
Optionally add family members with:
- Name, date of birth, relationship, gender
- Live premium preview updates as members are added/removed

Relationships supported: `spouse`, `child`, `parent`, `sibling`, `dependent`

#### Wizard Step 3 — Review & Quote
Calls `POST /api/v1/buy/quote` to get a server-side premium calculation.
Displays:
- Itemised member premium breakdown
- Total annual premium
- Full coverage table
- Applicant summary (name, email, plan)

#### Wizard Step 4 — Confirmation
Calls `POST /api/v1/buy/apply` to create the application.
Shows:
- Application reference number (e.g. `APP-20260518-A3F2`)
- Premium summary
- 4-step "what happens next" guide
- Links to `/portal/register` and back to `/buy`

## Premium Calculation

Premiums are calculated relative to the plan's `base_premium` using per-relationship factors:

| Relationship | Factor | Example (base $1,200) |
|-------------|--------|----------------------|
| `self` | 1.00 | $1,200.00 |
| `spouse` | 0.75 | $900.00 |
| `parent` | 0.70 | $840.00 |
| `sibling` | 0.65 | $780.00 |
| `child` | 0.35 | $420.00 |
| `dependent` | 0.40 | $480.00 |

The same formula is used client-side (for the live preview in Step 2) and server-side (for the authoritative quote in Step 3).

## What the Backend Creates

When `POST /api/v1/buy/apply` succeeds, three things are written in one transaction:

1. **`Application`** — status `submitted`, linked to the selected plan and product, `source: "self_service"` in `additional_info`
2. **`Member`** records — one per person, linked to the application, primary member gets email/phone
3. **`ApplicationItem`** records — one per coverage in the plan, with premium split evenly across coverages

The application is immediately visible in the staff portal's Applications page.

## Frontend Files

```
frontend/src/
├── pages/buy/
│   ├── BuyLandingPage.tsx
│   ├── BuyProductsPage.tsx
│   └── BuyApplyPage.tsx
└── services/
    └── buyApi.ts
```

## Backend Files

```
backend/app/api/v1/
└── buy.py                  # 4 public endpoints
backend/tests/
└── test_buy.py             # 15 tests
```

## Testing

```bash
# All buy endpoint tests
cd backend && python -m pytest tests/test_buy.py -v
```

15 tests cover:
- Product listing (tenant isolation, active-only filter, coverage inclusion)
- Quote calculation (single member, family, empty members, invalid plan)
- Application creation (happy path, family members, missing self, invalid relationship, coverage items)
- Status endpoint (found, not found)
