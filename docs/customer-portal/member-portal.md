# Member Portal (`/portal`)

The member portal gives existing policyholders self-service access to their insurance. Customers must register using their policy number and date of birth to create an account, then log in to access all features.

## URL Structure

| Route | Component | Auth | Purpose |
|-------|-----------|------|---------|
| `/portal/login` | `PortalLoginPage` | None | 2-step login (company code → credentials) |
| `/portal/register` | `PortalRegisterPage` | None | 3-step self-registration |
| `/portal/dashboard` | `PortalDashboardPage` | Required | Overview — KPIs, recent activity |
| `/portal/policy` | `PortalPolicyPage` | Required | Policy details + coverage breakdown |
| `/portal/members` | `PortalMembersPage` | Required | Covered members list |
| `/portal/claims` | `PortalClaimsPage` | Required | Claims history + file new claim |
| `/portal/payments` | `PortalPaymentsPage` | Required | Premium payment history |
| `/portal/documents` | `PortalDocumentsPage` | Required | Policy documents |
| `/portal/profile` | `PortalProfilePage` | Required | Update profile + change password |

Routes under `/portal/*` are wrapped in `PortalPrivateRoute` which checks `portalAuthStore.isAuthenticated`.

## Registration (`/portal/register`)

Three-step wizard:

1. **Company** — enter company code to resolve tenant
2. **Verify** — enter policy number + date of birth
   - Looks up the policy by number
   - Finds the primary (`self`) member on the linked application
   - Compares their `date_of_birth` — must match exactly
3. **Account** — enter name, email, password (min 8 chars)

On success:
- Creates a `User` record with `user_type = customer`
- Stores `policy_id` in `user.extra_data` — this links the account to their policy
- Returns a JWT and redirects to `/portal/dashboard`

**Constraints:**
- Each email address can only have one account per tenant
- Each policy can only have one customer portal account

## Login (`/portal/login`)

Two-step form:

1. Enter company code (resolves `tenantId`)
2. Enter email + password

After successful login, verifies `user.user_type === "customer"`. Non-customer users (staff) see an error and are directed to the staff portal.

The token is written to `localStorage` **before** calling `GET /customer/me` so the axios interceptor can attach the `Authorization` header.

## Dashboard (`/portal/dashboard`)

Loads data from four endpoints in parallel:
- Policy details (status, product, plan, expiry)
- Payments (total paid, recent 3)
- Claims (active count, recent 3)
- Members (count)

Shows:
- Policy status banner with expiry warning (≤ 60 days)
- 4 KPI cards: policy status, total paid, active claims, members covered
- Recent payments + recent claims panels
- Quick action grid (File Claim, View Coverage, Download Docs, View Members)

## Policy Page (`/portal/policy`)

Shows full policy details and a coverage breakdown table sourced from `ApplicationItem` records linked to the policy's application.

## Members Page (`/portal/members`)

Separates primary insured (`relationship = self`) from dependents. Each member card shows name, DOB, age (calculated), gender, relationship badge, and contact info.

## Claims Page (`/portal/claims`)

- Status filter tabs (All / Submitted / Under Review / Approved / Paid / Rejected)
- Claims table with claim number, type, incident date, claimed amount, approved amount, status
- **File a Claim** modal:
  - Claim type (hospitalization, outpatient, pharmacy, dental, vision, maternity, emergency, other)
  - Optional member selection (from covered members list)
  - Incident date, claimed amount, description

## Payments Page (`/portal/payments`)

Summary cards (total paid, payment count) + full history table. Payments are read-only — customers cannot initiate payments from the portal.

## Documents Page (`/portal/documents`)

Lists all `DocumentUpload` records where `entity_type = "policy"` and `entity_id = policy.id`. Grouped by document type. Customers cannot upload or download — downloads require staff assistance (shown as a notice).

## Profile Page (`/portal/profile`)

Two independent forms:
1. **Personal information** — update first name, last name, phone. Email is read-only.
2. **Change password** — current password verification + new password (min 8 chars, confirm match).

On profile save, `portalAuthStore` is updated in memory with the new user data.

## Auth Implementation

### Token storage
```
localStorage.portal_token      → Bearer token for API calls
localStorage.portal_tenantId   → Sent as X-Tenant-ID on every request
localStorage.portal_user       → Cached user object (JSON)
```

### Axios interceptor (`portalApi.ts`)
Reads `portal_token` and `portal_tenantId` from localStorage on every request. On 401, clears all portal keys and redirects to `/portal/login`.

### Store (`portalAuthStore.ts`)
Manual subscription store (same pattern as `authStore.ts`). `setPortalAuth`, `clearPortalAuth`, and `usePortalAuth` hook. No Zustand dependency — uses `useState` + `useEffect` with a module-level listeners set.

## Frontend Files

```
frontend/src/
├── pages/portal/
│   ├── PortalLoginPage.tsx
│   ├── PortalRegisterPage.tsx
│   ├── PortalDashboardPage.tsx
│   ├── PortalPolicyPage.tsx
│   ├── PortalMembersPage.tsx
│   ├── PortalClaimsPage.tsx
│   ├── PortalPaymentsPage.tsx
│   ├── PortalDocumentsPage.tsx
│   └── PortalProfilePage.tsx
├── components/
│   └── PortalLayout.tsx         # Emerald sidebar + logout
├── services/
│   └── portalApi.ts             # Axios instance + auth/customer API functions
└── store/
    └── portalAuthStore.ts       # Customer session state
```

## Backend Files

```
backend/app/api/v1/
└── customer.py                  # 10 endpoints
```
