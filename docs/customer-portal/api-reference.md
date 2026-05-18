# Customer-Facing API Reference

Base URL: `/api/v1`

All endpoints require `X-Tenant-ID: <tenant-uuid>` header.  
Endpoints marked **Auth** additionally require `Authorization: Bearer <customer-jwt>`.

---

## Purchase API (`/buy/*`)

These endpoints are fully public — no authentication required.

### `GET /buy/products`

Returns active products and their active plans with coverage details for the tenant.

**Response**
```json
{
  "success": true,
  "data": [
    {
      "id": "prod-uuid",
      "name": "Health Plus",
      "code": "HLTH001",
      "description": "Comprehensive health coverage",
      "plans": [
        {
          "id": "plan-uuid",
          "name": "Gold Plan",
          "code": "GOLD",
          "plan_type": "family",
          "base_premium": "1200.00",
          "description": "Premium family coverage",
          "coverages": [
            {
              "id": "cov-uuid",
              "name": "Hospitalization",
              "coverage_type": "hospitalization",
              "limit_amount": "50000.00",
              "copay": "20.00"
            }
          ]
        }
      ]
    }
  ]
}
```

---

### `POST /buy/quote`

Calculates an annual premium for a plan and member list.

**Request**
```json
{
  "plan_id": "plan-uuid",
  "members": [
    {
      "first_name": "Alice",
      "last_name": "Smith",
      "date_of_birth": "1985-03-15",
      "relationship": "self",
      "gender": "F"
    },
    {
      "first_name": "Bob",
      "last_name": "Smith",
      "date_of_birth": "2012-07-20",
      "relationship": "child",
      "gender": "M"
    }
  ]
}
```

**Relationship values:** `self` · `spouse` · `child` · `parent` · `sibling` · `dependent`  
**Gender values:** `M` · `F` · `O` · `U`

**Response**
```json
{
  "success": true,
  "data": {
    "plan_id": "plan-uuid",
    "plan_name": "Gold Plan",
    "product_name": "Health Plus",
    "total_premium": 1620.0,
    "breakdown": [
      { "relationship": "self",  "first_name": "Alice", "last_name": "Smith", "premium": 1200.0 },
      { "relationship": "child", "first_name": "Bob",   "last_name": "Smith", "premium": 420.0 }
    ],
    "coverages": [
      { "name": "Hospitalization", "coverage_type": "hospitalization", "limit_amount": "50000.00" }
    ]
  }
}
```

**Premium factors:** self=1.0 · spouse=0.75 · parent=0.70 · sibling=0.65 · child=0.35 · dependent=0.40

---

### `POST /buy/apply`

Submits a purchase application. Creates `Application`, `Member`, and `ApplicationItem` records in one transaction.

**Request**
```json
{
  "plan_id": "plan-uuid",
  "email": "alice@example.com",
  "phone": "+1 555 123 4567",
  "members": [
    {
      "first_name": "Alice", "last_name": "Smith",
      "date_of_birth": "1985-03-15",
      "relationship": "self", "gender": "F"
    }
  ]
}
```

At least one member with `relationship: "self"` is required.

**Response — 201 Created**
```json
{
  "success": true,
  "data": {
    "application_id": "app-uuid",
    "application_number": "APP-20260518-A3F2",
    "total_premium": 1200.0,
    "status": "submitted",
    "plan_name": "Gold Plan",
    "product_name": "Health Plus",
    "member_count": 1
  },
  "message": "Application submitted! Our team will review it and contact you within 1–2 business days."
}
```

---

### `GET /buy/apply/{application_id}`

Retrieves the current status of a submitted application.

**Response**
```json
{
  "success": true,
  "data": {
    "application_id": "app-uuid",
    "application_number": "APP-20260518-A3F2",
    "status": "submitted",
    "total_premium": 1200.0,
    "member_count": 1,
    "customer_name": "Alice Smith",
    "customer_email": "alice@example.com"
  }
}
```

---

## Customer Registration & Auth

### `GET /auth/tenant/{code}` — Public

Resolves a tenant code to ID and name (used by login and registration forms).

**Response**
```json
{ "success": true, "data": { "id": "tenant-uuid", "name": "ACME Insurance", "code": "ACME" } }
```

---

### `POST /auth/login` (with `X-Tenant-ID`) — Public

Standard login. Returns `access_token` and `refresh_token`. Customer accounts have `user_type: "customer"` in the JWT.

---

### `POST /customer/register` — Public (with `X-Tenant-ID`)

Creates a customer portal account verified against an existing policy.

**Request**
```json
{
  "email": "alice@example.com",
  "password": "secret123",
  "first_name": "Alice",
  "last_name": "Smith",
  "policy_number": "POL-20260001",
  "date_of_birth": "1985-03-15"
}
```

Verification: matches `policy_number` → finds the `Member` with `relationship=self` on the linked application → compares `date_of_birth`. Returns 400 if verification fails.

**Response — 201 Created**
```json
{
  "success": true,
  "data": { "access_token": "...", "refresh_token": "...", "token_type": "bearer" },
  "message": "Account created. Welcome to your policy portal!"
}
```

---

## Member Portal API (`/customer/*`)

All endpoints require `Authorization: Bearer <customer-jwt>` and `X-Tenant-ID`.

### `GET /customer/me` — Auth

Returns the authenticated customer's profile.

```json
{
  "data": {
    "id": "user-uuid", "email": "alice@example.com",
    "first_name": "Alice", "last_name": "Smith",
    "phone": "+1 555 000 0000", "user_type": "customer",
    "policy_id": "policy-uuid"
  }
}
```

---

### `PUT /customer/me` — Auth

Updates first name, last name, and/or phone. Email cannot be changed.

**Request**
```json
{ "first_name": "Alice", "last_name": "Jones", "phone": "+1 555 999 9999" }
```

---

### `PUT /customer/me/password` — Auth

Changes the account password.

**Request**
```json
{ "current_password": "old_secret", "new_password": "new_secret_min8" }
```

Returns 400 if `current_password` is incorrect.

---

### `GET /customer/policy` — Auth

Full policy details including product and plan names.

```json
{
  "data": {
    "id": "policy-uuid", "policy_number": "POL-20260001",
    "status": "active", "customer_name": "Alice Smith",
    "product_name": "Health Plus", "plan_name": "Gold Plan",
    "plan_type": "family", "base_premium": "1200.00",
    "total_premium": "1200.00", "member_count": 1,
    "effective_date": "2026-01-01", "expiry_date": "2027-01-01"
  }
}
```

---

### `GET /customer/coverage` — Auth

Application items with coverage details for the policy.

```json
{
  "data": [
    {
      "id": "item-uuid", "coverage_name": "Hospitalization",
      "coverage_type": "hospitalization",
      "limit_amount": "50000.00", "copay": "20.00",
      "coinsurance_percent": null, "premium": "600.00",
      "status": "approved"
    }
  ]
}
```

---

### `GET /customer/members` — Auth

All members covered under the policy (via the linked application).

---

### `GET /customer/payments` — Auth

Payment history for the policy.

```json
{
  "data": {
    "total_paid": 1200.0,
    "payments": [
      {
        "id": "pay-uuid", "payment_number": "PAY-...",
        "amount": "1200.00", "method": "bank_transfer",
        "status": "success", "reference": "REF123",
        "paid_at": "2026-01-15T10:30:00Z"
      }
    ]
  }
}
```

---

### `GET /customer/claims` — Auth

All claims for the policy, ordered newest first.

---

### `POST /customer/claims` — Auth

Files a new claim.

**Request**
```json
{
  "claim_type": "hospitalization",
  "incident_date": "2026-03-10",
  "description": "Emergency appendix surgery",
  "claimed_amount": 8500.00,
  "member_id": "member-uuid"
}
```

**Claim types:** `hospitalization` · `outpatient` · `pharmacy` · `dental` · `vision` · `maternity` · `emergency` · `other`

**Response — 201 Created**
```json
{
  "data": {
    "id": "claim-uuid",
    "claim_number": "CLM-20260518-X9K2",
    "status": "submitted"
  },
  "message": "Claim submitted successfully."
}
```

---

### `GET /customer/documents` — Auth

All documents uploaded against the policy (`entity_type = "policy"`), ordered newest first.

---

## Error Responses

All errors follow the same envelope:

```json
{
  "success": false,
  "errors": [
    { "code": "HTTP_ERROR", "message": "Policy not found." }
  ],
  "timestamp": "2026-05-18T00:00:00Z"
}
```

Common HTTP status codes:

| Code | Meaning |
|------|---------|
| 400 | Bad request — validation or business rule failure |
| 401 | Unauthenticated — missing or expired token |
| 403 | Forbidden — not a customer account |
| 404 | Resource not found |
| 409 | Conflict — duplicate email or policy account |
| 422 | Unprocessable — invalid enum value or field constraint |
| 429 | Rate limited |
