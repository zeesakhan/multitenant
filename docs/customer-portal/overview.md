# Customer Portal — Overview

The platform exposes two separate experiences for end customers:

| Portal | URL | Purpose | Auth required |
|--------|-----|---------|--------------|
| **Purchase Portal** | `/buy` | Browse plans, get a quote, submit an application | No |
| **Member Portal** | `/portal` | Manage an existing policy — claims, payments, documents, profile | Yes (customer JWT) |

## End-to-End Customer Journey

```
1. Customer visits /buy
        │
        ▼
2. Enters company code  →  sees plans & pricing
        │
        ▼
3. 4-step apply wizard  →  application submitted (status: submitted)
        │
        ▼
4. Staff reviews in back-office  →  approves  →  issues policy
        │
        ▼
5. Customer receives policy number (via email / from agent)
        │
        ▼
6. Customer visits /portal/register
   Enters: policy number + date of birth  →  identity verified
   Creates: email + password  →  account linked to policy
        │
        ▼
7. Customer logs in at /portal/login
        │
        ▼
8. Uses member portal:
   ├── View policy & coverage details
   ├── See all covered members
   ├── File and track claims
   ├── View payment history
   ├── Download documents
   └── Update profile & password
```

## Session Architecture

Staff and customer sessions are completely separate:

| | Staff | Customer |
|-|-------|---------|
| Login URL | `/login` | `/portal/login` |
| localStorage key | `token` | `portal_token` |
| Auth store | `authStore.ts` | `portalAuthStore.ts` |
| API client | `services/api.ts` | `services/portalApi.ts` |
| 401 redirect | `/login` | `/portal/login` |

Both sessions can be active simultaneously in the same browser (different keys).

## Backend Routers

| Router | Prefix | Auth | Description |
|--------|--------|------|-------------|
| `buy.py` | `/api/v1/buy` | None (X-Tenant-ID header only) | Purchase flow |
| `customer.py` | `/api/v1/customer` | Customer JWT | Member portal data |

## Related Documents

- [Purchase Portal](purchase-portal.md) — detailed `/buy` flow
- [Member Portal](member-portal.md) — detailed `/portal` flow
- [API Reference](api-reference.md) — all customer-facing endpoints
