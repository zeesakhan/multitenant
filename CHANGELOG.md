# Changelog

All notable changes to the Health Insurance Platform are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

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
