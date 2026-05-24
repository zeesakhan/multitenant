# Adamjee Insurance UAE — Implementation Plan & Reference

## Overview
Adamjee Insurance is added as a new tenant with a dedicated UAE customer buying journey.
URL: `/buy/adamjee` · Tenant code: `ADAMJEE`

---

## Phases

### Phase 1 — Data Model (Backend)
- Add UAE-specific fields to `Member` model:
  `passport_number`, `emirates_id`, `nationality`, `visa_type`, `document_expiry`, `place_of_birth`
- Drop/recreate `dev.db` to apply new schema in SQLite dev mode

### Phase 2 — Adamjee Tenant Seed (Backend)
- Create tenant `ADAMJEE` in bootstrap (`main.py`)
- Create Product: "Adamjee DHA Family Care"
- Create 7 Plan tiers with full DHA coverage items
- Create admin user `admin@adamjee.ae`

### Phase 3 — UAE Buy API Router (Backend)
Prefix: `/api/v1/uae-buy`

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/info` | Adamjee tenant branding & contact |
| GET | `/plans` | All 7 plans with coverages |
| POST | `/ocr` | Upload passport/EID image → OCR extraction |
| POST | `/quote` | Premium calculation with UAE factors |
| GET | `/regulations` | UAE laws & compliance summary |
| POST | `/apply` | Submit application (UAE fields) |
| POST | `/payment/{app_id}` | Initiate payment |
| GET | `/payment/{app_id}/status` | Poll payment status |

### Phase 4 — Frontend Adamjee Journey
Files:
- `frontend/src/pages/buy/adamjee/AdamjeeLandingPage.tsx`
- `frontend/src/pages/buy/adamjee/AdamjeeBuyPage.tsx`
- `frontend/src/services/adamjeeApi.ts`

7-step wizard:
1. **Personal Details** — UAE-compliant form (name, DOB, nationality, contact, visa type)
2. **Document Upload** — Passport or Emirates ID upload with OCR auto-fill
3. **Plan Selection** — 7 network tier cards with feature comparison
4. **Add Dependents** — Spouse / children / parents with individual premiums
5. **Quote Summary** — Itemised premium breakdown, plan details
6. **Compliance & Agreement** — UAE laws summary + mandatory consent checkboxes
7. **Payment** — Credit card / Apple Pay / Google Pay form + confirmation

### Phase 5 — Testing
- Restart backend, seed Adamjee data
- Walk all 7 wizard steps in browser
- Verify OCR endpoint returns fields (or graceful fallback)
- Verify application stored with UAE fields
- Verify payment flow completes

---

## Adamjee Plans (7 Network Tiers)

All plans: DHA Compliant · TPA: MEDNET · Annual Limit: AED 1,000,000/person

| # | Plan Name | Network | Annual Premium (Individual) |
|---|-----------|---------|---------------------------|
| 1 | GOLD | Gold hospitals (American Hospital, Mediclinic City) | AED 4,500 |
| 2 | SILVER PREMIUM | Silver Premium hospitals | AED 3,400 |
| 3 | SILVER CLASSIC | Silver Classic hospitals | AED 2,600 |
| 4 | EMERALD | Emerald network | AED 2,100 |
| 5 | PEARL | Pearl network | AED 1,800 |
| 6 | GREEN | Green network (government + basic private) | AED 1,500 |
| 7 | SILK ROAD | Silk Road (essential, government hospitals) | AED 1,200 |

**Common Benefits (all tiers):**
- Private room inpatient hospitalization
- ICU / coronary care
- Consultant, surgeon, anaesthetist fees
- Physiotherapy: 15 sessions/year, 0% copay
- Diagnostics & lab: 0% copay
- Pharmaceuticals: 0% copay
- GP consultation: 20% copay (max AED 50)
- Maternity: AED 10,000 (normal & caesarean)
- Dental: AED 3,500/year, 20% copay
- Alternative medicine: AED 1,600/year
- Mental health: emergency covered
- Vaccination: per MOH schedule
- Pre-existing & chronic conditions: AED 150,000 sub-limit
- Newborn coverage: first 30 days under mother's plan
- Repatriation: up to AED 7,500
- Ambulance: emergency with admission

---

## UAE Compliance Data Fields

Per Dubai Health Authority (DHA), Federal Insurance Authority (ISA), and UAE PDPL:

| Field | Required For |
|-------|-------------|
| Full legal name | All members |
| Date of birth | All members |
| Gender | All members |
| Nationality | All members |
| Emirates ID (784-XXXX-XXXXXXX-X) | UAE residents |
| Passport number + expiry | All / expats |
| Visa type | Expats |
| Pre-existing conditions declaration | All |
| Data processing consent | All |

---

## UAE Regulations Referenced in Journey

1. **Dubai Health Insurance Law No. 11 of 2013** — Mandatory health insurance for all Dubai residents
2. **Cabinet Resolution No. 49 of 2019** — Essential Benefits Plan minimum requirements
3. **Federal Law No. 6 of 2007** — UAE Insurance Authority regulations
4. **DHA Minimum Benefits Package** — Mandatory in-patient + out-patient coverage
5. **UAE Personal Data Protection Law (Federal Decree-Law No. 45 of 2021)** — Data privacy rights

---

## Payment Methods Supported

- Visa / Mastercard / American Express credit & debit cards
- Apple Pay
- Google Pay
- Bank Transfer (reference generated)

---

## Change Management

See `CHANGELOG.md` for all changes made under this feature.
