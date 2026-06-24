# Policy Sales Portal — Gap Analysis & Enhancement Roadmap

**Prepared:** 2026-06-24  
**Based on:** Analysis of 130 screenshots from reference portal (Green Portal / healthportal.adampeninsurance.ae) + review of current codebase  

---

## 1. Executive Summary

The current system is architecturally complete but **journeys are fragmented** — a broker must navigate 5+ separate pages (Quotations → Applications → Members → Policies → Payments) to complete a single sale. The reference portal achieves the same outcome in **one unified 5-step wizard** with a single master listing page. The current system also has several screens that are internal compliance tools (AML, Govt Checks, Tenants) mixed into the main broker navigation, creating confusion about who the interface is for.

**The target state:** Consolidate into a clean broker-facing portal with:
- A guided, multi-step "New Policy" wizard (the main entry point for all sales)
- A single "Policy Listing" master screen tracking every quote from creation to issuance
- A compact nav that matches what a broker actually does day-to-day

---

## 2. Reference Portal: Full Workflow Map

The reference portal demonstrates this exact journey:

```
[DASHBOARD]
    ↓ "Policy Entry" button
[STEP 1 — Applicant Details]
    Sponsor type · Who to insure · Demographics · Family members · Policy start date · Pre-conditions
    ↓
[STEP 2 — Get Quotes]
    Plan cards with price/network/pharmacy · Co-payment filters · Plan Details PDF · Network hospital list
    ↓
[STEP 3 — Additional Information]
    Full EID/Passport/Visa/Sponsor numbers · Existing policy status · Medical questionnaire per member
    ↓
[STEP 4 — Finalize Application]
    Selected plan summary · Add remarks · Download+Upload signed docs (Med App Form / KYC / ToB)
    ↓
[STEP 5 — Underwriter Approve]
    Activity feed · Remarks history · Approval/rejection with notes · Loading adjustments
    ↓
[PAYMENT]
    Payment gateway → "Thank you" page → Credit Note, Tax Invoice, Receipt Voucher, Policy Schedule PDFs
    ↓
[POLICY ISSUED]
    Visible in Policy Listing under "Policy Issued" status
```

---

## 3. Current System: Navigation vs Reference

| Reference Portal Nav | Our Current Nav | Assessment |
|---|---|---|
| Dashboard | Dashboard | ✅ Exists — needs KPI redesign |
| Policy Entry (wizard) | *(spread across Quotations + Applications + Members)* | ❌ Missing unified wizard |
| Policy Listing | Quotations + Applications + Policies *(3 separate pages)* | ❌ Fragmented — must unify |
| Payments Listing | Payments | ✅ Exists |
| Reports | Reports | ✅ Exists — different reports |
| Manage User | Users | ✅ Exists |
| Notifications (bell) | Notifications (bell in sidebar) | ✅ Exists |
| *(not present)* | Tenants | ⚠️ Keep — admin only, hide from broker role |
| *(not present)* | Products | ⚠️ Keep — admin only, hide from broker role |
| *(not present)* | Members | ⚠️ Fold into Policy Listing detail |
| *(not present)* | Claims | ⚠️ Evaluate — may be needed but out of primary flow |
| *(not present)* | AML | ⚠️ Keep — admin/compliance only, not broker-facing |
| *(not present)* | Govt Checks | ⚠️ Keep — admin/compliance only, not broker-facing |

---

## 4. Feature-by-Feature Gap Analysis

### 4.1 Dashboard

**What the reference portal has:**
- 6 actionable KPI tiles (each links to filtered Policy Listing):
  - Issued Policies
  - Payment Pending
  - Rejected Quotes
  - Underwriting Pending
  - Quotations Generated
  - Issuance Pending
- 2 bar/line charts: Premium Earned (AED) by month, Commission Earned (AED) by month
- "Top 5 Broker Companies by Premium" horizontal bar chart
- "Insurer Discount (last 6 months)" chart
- "Teams Actionable" list: Quote No · Principal · Emirate · Submitted Date · Assigned To · Status · Amount Payable
- Date range filter (Today / Yesterday / This week / Last month / Current year / Custom)

**What we have:**
- 4 KPI tiles (Active Policies, Monthly Premium, Applications, Collected)
- Backend online/offline status banner
- Applications by Status bar chart
- Recent Applications list
- Recent Payments list
- AML Flagged + Govt Check Pending (compliance tiles)
- System Status panel (dev artifact)

**Required changes:**
1. Replace the 4 generic KPI tiles with 6 workflow-action tiles matching the reference (link each to filtered Policy Listing)
2. Add date range filter to Dashboard
3. Replace "Recent Applications" with "Teams Actionable" table (same columns as reference)
4. Add Premium Earned and Commission Earned charts (monthly bar charts)
5. Remove "System Status" panel — it's a dev tool, not for brokers
6. Move AML + Govt Check tiles to an admin-only section or separate compliance dashboard, not main broker dashboard

---

### 4.2 New Policy / Policy Entry Wizard (CRITICAL GAP)

**What the reference portal has:**  
A single 5-step wizard accessible via "Policy Entry" in the nav. All data collection, plan selection, and approval happens within this one flow.

**Step 1 — Applicant Details:**
- Sponsor Type: Individual / Corporate (corporate shows TRN field)
- Who to insure: Self Only / Family Without Self / Both Self and Family
- Pre-qualification: Do you have an existing policy in UAE?
  - Yes, I have an active policy
  - Expired 30+ days ago
  - Expired in the last 30 days
  - No, I don't have any policy
- Principal member: Full Name, Email, Mobile, Gender, Marital Status, DOB, Nationality, Country, Salary (AED/month), Height, Weight
- Family member addition: relationship, same demographic fields
- Policy start date
- Do any members take regular medication? (Yes/No)
- Any female member planning a family? (Yes/No)

**Step 2 — Get Quotes:**
- Medical Cover filter (AED limit selector)
- Co-Payment filters: Physician/GP Consultation %, Prescription/Diagnosis %, Pharmacy %
- Plan comparison cards showing:
  - Plan name, Annual Medical Limit (AED), Pharmacy Level, Network name, Price (AED)
  - "Plan Details >" → opens PDF (Table of Benefits)
  - "See Network >" → opens hospital/clinic list with search
  - "Disclaimer" text
- Clicking a plan price selects it and advances to Step 3

**Step 3 — Additional Information (per member):**
- First Name, Middle Name, Last Name (separate fields)
- DOB, Marital Status, Nationality
- Diplomatic passport holder? Yes/No
- Emirates ID under process? Yes/No
- Emirates ID Number, Emirates ID Expiry Date
- Passport Number
- Visa ID Number
- Sponsor Number
- Existing policy status (4 options as in Step 1 pre-qualification)
- Medical Questionnaire:
  - Suffering from hypertension? Yes/No
  - Suffering from diabetes / insulin dependent? Yes/No
  - Ever tested positive for COVID-19? Yes/No
  - Any ongoing COVID complications under medical monitoring? Yes/No
  - Under any medical observation / undergoing medical/surgical treatment or been advised for one? Yes/No
    - If Yes → text fields: Illness/Condition, Medication details, Diagnosis since (date), Treatment status

**Step 4 — Finalize Application:**
- Summary bar showing selected plan (Annual Medical Limit, Pharmacy Limit, Network, Co-payments)
- "Edit Your Details" link (goes back to Step 1)
- "Add a Remark" text area + "Add Remark" button
- Remarks History (chronological list: who added, when, text)
- "Please upload the signed document to proceed further"
- Documents list with Download (auto-generated pre-filled PDF) + Preview + Upload (signed copy):
  - Medical Application Form
  - KYC Form
  - Table of Benefits

**Step 5 — Approve (Underwriter view):**
- Activity feed showing all status transitions with timestamps
- Underwriter remarks with loading information (e.g., "BMI loading applied", "Annual cover reduced to AED 130,000")
- Signed documents visible
- Action buttons: Approve / Reject / Request More Info

**What we have:**
- `QuotationsPage` — separate page, creates a quote with product/plan/customer name/email
- `ApplicationsPage` — separate page, creates an application referencing a quote
- `MembersPage` — separate page, adds members to an application
- No step-by-step wizard UI
- No plan comparison cards
- No co-payment/network filters on quote selection
- No medical questionnaire in the UI
- No remarks/history system on the application
- No document upload flow tied to the application
- No "Additional Information" step with EID/Passport/Visa/Sponsor fields

**Required changes:**
1. Build a unified 5-step wizard as "New Policy" that replaces the current Quotations + Applications flow
2. Step 1 covers what our Quotations + basic member demographics do
3. Step 2 shows plan cards with real pricing (our pricing engine already calculates this)
4. Step 3 captures the UAE-specific fields we have in migration 0019 (applications_uae_fields) and migration 0020 (medical questionnaire) — but these need a proper UI
5. Step 4 uses our existing document generation (PDF service) — expose Download/Preview/Upload per document
6. Step 5 integrates our existing workflow states — surface them as an activity feed

---

### 4.3 Policy Listing (CRITICAL GAP)

**What the reference portal has:**  
Single master table showing every policy from quote stage to issuance.

**Table columns:**
- Quotation Number (auto-complete search filter)
- Product Plan
- Sponsor Name
- Mobile No.
- Email
- Policy Number
- Broker
- Status
- Created On
- Premium Amount
- Order ID
- Transaction ID
- PS Type (payment system type)

**Quick Filters:**
- Quotation Number (autocomplete dropdown with recent numbers)
- Date range picker
- Status: Pending / Submitted to UW / Rejected / Approved / Payment Approved / Payment Approval Pending / Payment Failed / Policy Issued / Policy Pending
- Company (broker company filter)

**Row expansion — tabs per member:**
- **Personal Details tab**: Full Name, Nationality, Emirates ID, DOB, Gender, Insurance Days, Height/Age, Weight, Policy Start Date, + "Update" button to edit
- **Signed Docs tab**: Signed Medical Application Form, Signed KYC Form, Signed Table of Benefits (Download + Preview per doc)
- **Other Documents tab**: Medical Application Form, KYC Form, Table of Benefits, Emirates ID, Passport, Visa, Certificate of Continuity (Download + Preview)
- **Remarks tab**: Chronological remarks history

**Premium Breakup section (expandable "View Details"):**
- Gross Premium
- Loadings: Underwriter Loading, BMI Loading, Other Loading
- TPA Loading
- Gross Premium excl. VAT/PSP/ICP
- PSP Fee
- VAT
- Amount Payable
- Insurer Commission (x.x%) — editable via modal
- Broker Commission (x.x%) — editable via modal

**Per-Member Breakdown (within Premium Breakup):**
- Each member shown with their own:
  - Base Premium
  - Underwriter Loading, BMI Loading, Other Loading
  - TPA Loading, Broker Loading, Insurer Loading
  - Gross Premium excl. VAT/PSP/ICP
  - PSP Fee, VAT
  - Amount Payable

**Commission Edit Modal:**
- Toggle: Percentage / Amount
- Table: Member Name | Commission value (editable)
- Cancel / Save

**"Download Report" button** top-right of the listing page (exports visible data)

**What we have:**
- `QuotationsPage`: Shows quotes (draft/sent/viewed/expired/converted/declined) — different lifecycle stages
- `ApplicationsPage`: Shows applications — different lifecycle stages  
- `PoliciesPage`: Shows issued policies
- Premium breakup not visible in listing
- No signed docs tracking
- No "Other Documents" with download/preview
- No remarks system on the listing
- No per-member premium breakdown
- No commission editing in the UI
- No "Download Report" export from listing

**Required changes:**
1. Create a unified "Policy Listing" page that replaces Quotations, Applications, and Policies pages
2. Single table with unified status spanning the full lifecycle (maps our current states to reference portal states)
3. Status mapping:
   - Our `draft` → "Pending"
   - Our `submitted` → "Submitted to UW"
   - Our `approved` → "Approved"
   - Our `rejected` → "Rejected"
   - Our `issued` + payment pending → "Payment Approval Pending"
   - Our `issued` + payment success → "Policy Issued"
4. Add row expansion with the 4 tabs (Personal Details, Signed Docs, Other Docs, Remarks)
5. Add Premium Breakup section using our existing pricing engine data
6. Add per-member premium breakdown
7. Add Commission edit modal (we have commission_configs in migration 0018)
8. Add "Download Report" button (CSV/Excel export of visible rows)
9. Add Quick Filters (date, status, company)

---

### 4.4 Post-Payment / Policy Schedule Page

**What the reference portal has:**  
After payment, a dedicated confirmation page with:
- "Thank you [Name]! Your payment for Health Insurance has been successfully received."
- "Click below links to download the policy documents"
- Email button (sends documents to customer)
- 4 downloadable documents:
  1. Credit Note (PDF)
  2. Tax Invoice (PDF)
  3. Receipt Voucher (PDF)
  4. Policy Schedule (PDF — full individual policy schedule document with all member details)
- Plan summary: Annual Medical Limit, Pharmacy Limit, Premium (yearly), Amount Paid

**Policy Schedule PDF includes:**
- Insurance Company Information (Adamjee Insurance, Dubai Branch)
- Policy Number, External Policy Ref, Issuance Date
- Policy Holder details, Broker, Group, Tax Registration No
- Effective Date, Expiry Date, Cover Type, Payment Method, Currency
- Individual member schedule table

**What we have:**
- Our PDF service generates documents but they're not surfaced on a post-payment page
- No "Thank you" confirmation page with document links
- No Credit Note, Tax Invoice, Receipt Voucher generation in the UI

**Required changes:**
1. Create a payment confirmation page accessible at `/policy/:id/issued`
2. Show all 4 documents with Download buttons
3. Add "Email Documents" button that triggers our email service
4. Generate Credit Note and Tax Invoice PDFs (new PDF templates needed)

---

### 4.5 Reports

**What the reference portal has (simple, clean):**
- DHA Flow Report → Download button
- Commission Stat → Download button
- Underwriter Report → Download button
- Commission SOA (Statement of Account) → Download button

**What we have:**
- Summary KPIs (Active Policies, Expiring 30d, Pending Applications, Open Claims)
- Monthly Premium Collected chart
- Monthly Applications chart
- Monthly Claims chart
- 7 downloadable reports: Policy Issued, Commission Statement, Underwriter, AML Screening, Govt Verification, STR Log, DHA Fine

**Assessment:** Our Reports page is more comprehensive, but harder to navigate. The reference keeps it simple. Recommended approach:
1. Keep our charts but improve visual quality (real bar charts vs. simple progress bars)
2. Rename "Commission Statement" → "Commission SOA" to match industry terminology
3. Add "Commission Stat" (summary view, not detailed SOA)
4. Keep AML/Govt/STR reports but move them to a separate "Compliance Reports" section
5. Add date filters to all report downloads (already partially implemented)

---

### 4.6 Manage User / Users Page

**What the reference portal has (implied from nav):**
- User management for the broker company's team

**What we have:**
- Full user management with roles, tenant scoping
- This is adequate — no major gap

**Required changes:**
- Relabel "Users" → "Manage Users" in navigation to match reference terminology
- Ensure broker-role users only see users within their own company

---

### 4.7 Document Generation & Management

**What the reference portal has:**
- Auto-generated pre-filled PDFs available from day of quote onwards:
  - Medical Application Form (Munich RE branded, prefilled with member data + medical questionnaire answers)
  - KYC Form (prefilled)
  - Table of Benefits (plan-specific benefits schedule)
  - Emirates ID scan upload slot
  - Passport scan upload slot
  - Visa scan upload slot
  - Certificate of Continuity upload slot
- After payment:
  - Policy Schedule
  - Credit Note
  - Tax Invoice
  - Receipt Voucher

**What we have:**
- PDF service exists (`pdf_service.py`) and generates documents
- Document model exists with download functionality
- No pre-filled Medical Application Form template
- No KYC Form template
- Certificate of Continuity not tracked as a document type
- Credit Note and Tax Invoice templates not present

**Required changes:**
1. Add Medical Application Form PDF template (Munich RE / Adamjee branded, pre-populated with member data + medical questionnaire)
2. Add KYC Form PDF template
3. Track these document types in the document model: EID, Passport, Visa, Certificate of Continuity (upload slots)
4. Add Credit Note PDF template
5. Add Tax Invoice PDF template
6. Expose all documents with Download + Preview + Upload in the Policy Listing

---

### 4.8 Features in Our System to REMOVE or HIDE

| Feature | Action | Reason |
|---|---|---|
| Separate Quotations page | Remove | Replace with Policy Entry wizard + Policy Listing |
| Separate Applications page | Remove | Folded into Policy Listing |
| Separate Policies page | Remove | Folded into Policy Listing |
| Separate Members page | Remove/hide | Members now visible within Policy Listing row expansion |
| "System Status" panel on Dashboard | Remove | Dev artifact, not for users |
| "Backend API is online/offline" banner | Remove | Dev artifact, not for brokers |
| AML, Govt Checks from broker nav | Move to admin-only nav | Compliance tools, not broker tools |
| Tenants from broker nav | Move to admin-only nav | Super-admin only |
| Products from broker nav | Move to admin-only nav | Admin only |

---

### 4.9 Features to FIX or CLARIFY

| Issue | Fix |
|---|---|
| Quotation statuses (draft/sent/viewed/expired/converted/declined) don't map to the reference portal statuses used by the team | Remap to: Pending → Submitted to UW → Approved/Rejected → Payment Pending → Policy Issued → Policy Pending |
| Premium breakup not visible anywhere in the UI | Expose in Policy Listing expansion |
| Medical questionnaire fields exist in DB (migration 0020) but have no UI | Build the medical questionnaire into Step 3 of the wizard |
| UAE-specific fields (EID, Passport, Visa, Sponsor No.) exist in DB (migration 0019) but have no UI | Build into Step 3 of the wizard |
| Commission configuration (migration 0018) has no UI to edit commissions per deal | Add commission edit modal to Policy Listing |
| Claims page exists but claims are not part of the primary sale workflow | Move Claims to a separate "Post-Sale" section, clearly separate from the quoting flow |
| BMI Loading and other loadings exist in the pricing engine but aren't shown in UI | Show in Premium Breakup section |
| No per-member premium breakdown shown | Add per-member breakdown in Policy Listing |
| The buy flow (/buy/adamjee) is a separate public-facing journey — its relationship to the broker portal is unclear | Either merge into one system or clearly document that the buy flow is customer self-service and the broker portal is separate |

---

## 5. Proposed Target Navigation

### Broker Role (default view)
```
├── Dashboard
├── New Policy          ← replaces "Policy Entry"
├── Policy Listing      ← replaces Quotations + Applications + Policies
├── Payments Listing
├── Reports
├── Manage Users
└── [Notifications bell in header]
```

### Admin / Super-Admin Role (all of the above plus)
```
├── Tenants
├── Products & Plans
├── AML & Compliance     ← merge AML + Govt Checks
└── Compliance Reports
```

---

## 6. Proposed 5-Step Wizard: Field Checklist

### Step 1 — Applicant Details
- [ ] Sponsor Type: Individual / Corporate
- [ ] If Corporate: TRN / Trade License Number
- [ ] Who to insure: Self Only / Family Without Self / Both
- [ ] Existing policy in UAE: Active / Expired 30+ days / Expired last 30 days / None
- [ ] Principal: First Name, Middle Name, Last Name
- [ ] Email, Mobile
- [ ] Gender (Male/Female)
- [ ] Marital Status (Single/Married/Divorced/Widowed)
- [ ] Date of Birth
- [ ] Nationality
- [ ] Country
- [ ] Salary (AED/month)
- [ ] Height (cm), Weight (kg) — used for BMI loading
- [ ] Family members: add rows with relationship + same demographics
- [ ] Policy Start Date
- [ ] Do any members take regular medication? (Yes/No)
- [ ] Any female member planning a family? (Yes/No)

### Step 2 — Get Quotes
- [ ] Medical Cover Amount filter (AED)
- [ ] Co-payment filters: GP Consultation %, Pharmacy %, Lab Tests %, Physiotherapy %
- [ ] Plan cards: Name, Limit, Pharmacy Level, Network, Price, Disclaimer
- [ ] Plan Details button → PDF preview/download
- [ ] Network Hospitals button → searchable hospital list
- [ ] Select plan → advance

### Step 3 — Additional Information (per member)
- [ ] Diplomatic passport holder? Yes/No
- [ ] Emirates ID under process? Yes/No
- [ ] Emirates ID Number
- [ ] Emirates ID Expiry Date
- [ ] Passport Number
- [ ] Visa ID Number
- [ ] Sponsor Number
- [ ] Existing policy status (repeat from Step 1 or pre-fill)
- [ ] Medical Questionnaire:
  - [ ] Hypertension?
  - [ ] Diabetes / insulin dependent?
  - [ ] COVID-19 positive history?
  - [ ] Ongoing COVID complications?
  - [ ] Under medical observation / treatment?
  - [ ] If Yes: Illness/Condition (text), Medication (text), Diagnosis since (date), Treatment status

### Step 4 — Finalize Application
- [ ] Selected plan summary (non-editable, "Edit Details" link)
- [ ] Remarks text area + Add button
- [ ] Remarks history list
- [ ] Documents (each with Download generated PDF + Preview + Upload signed):
  - [ ] Medical Application Form
  - [ ] KYC Form
  - [ ] Table of Benefits
- [ ] "Submit to Underwriter" button

### Step 5 — Underwriter / Approval
- [ ] Activity feed (all status changes with timestamps and actor)
- [ ] Underwriter remarks (loading notes, conditions)
- [ ] Loading edit: Underwriter Loading, BMI Override, Other Loading
- [ ] Annual limit adjustment (underwriter can reduce)
- [ ] Action buttons: Approve / Reject / Request Info
- [ ] On approval → trigger payment link or mark payment pending

---

## 7. Priority Matrix

| Priority | Feature | Effort | Impact |
|---|---|---|---|
| P0 — BLOCKER | Unified Policy Listing with status, filters, row expansion | High | Very High |
| P0 — BLOCKER | 5-Step Policy Entry Wizard | High | Very High |
| P1 — HIGH | Step 3 Additional Info UI (EID/Passport/Medical Q) | Medium | High |
| P1 — HIGH | Step 4 Document download/upload per document | Medium | High |
| P1 — HIGH | Premium Breakup in Policy Listing | Medium | High |
| P1 — HIGH | Dashboard KPI redesign (actionable tiles) | Medium | High |
| P2 — MEDIUM | Commission edit modal in Policy Listing | Medium | Medium |
| P2 — MEDIUM | Per-member premium breakdown | Medium | Medium |
| P2 — MEDIUM | Post-payment confirmation page with 4 docs | Medium | Medium |
| P2 — MEDIUM | Remarks/History system on applications | Low | Medium |
| P2 — MEDIUM | Role-based nav (broker vs admin separation) | Low | High |
| P3 — LOW | Medical Application Form PDF template | High | Medium |
| P3 — LOW | Credit Note + Tax Invoice PDF templates | High | Medium |
| P3 — LOW | Reports: rename + improve charts | Low | Low |
| P3 — LOW | Payments Listing enhancements | Medium | Low |

---

## 8. Things to Remove from Current System

1. **`/quotations` page** — delete after wizard is built (data stays in DB)
2. **`/applications` page** — delete after unified listing is built  
3. **`/policies` page** — merge into Policy Listing
4. **`/members` page** — surface inside Policy Listing row, not standalone
5. **System Status panel** on Dashboard
6. **Backend online/offline banner** on Dashboard
7. **Buy flow (`/buy`, `/buy/products`, `/buy/apply`)** — evaluate if these are still needed or are superseded by the broker wizard; if customer self-service is needed, keep but clearly separate from broker portal
8. **Adamjee buy flow (`/buy/adamjee`)** — evaluate whether this is still the right entry point or if the 5-step wizard replaces it
9. **`/claims` page** from broker nav — move to secondary section; claims processing is post-sale and should not be in the primary quoting nav

---

## 9. Data Model: No New Migrations Needed

The good news: the database already has all the fields needed. The gap is entirely in the **frontend** and **API exposure**:

| Feature | Existing DB support |
|---|---|
| Medical questionnaire | `0020_members_medical_questionnaire.py` |
| UAE ID/Passport/Visa/Sponsor fields | `0019_applications_uae_fields.py` |
| BMI + Underwriter loadings | `0017_premium_loadings.py` |
| Commission configurations | `0018_commission_configs.py` |
| Document model | `0009_create_documents.py` |
| Notifications | `0024_notification_records.py` |
| AML records | `0021_aml_records.py` |
| Govt verification | `0022_govt_verification_records.py` |
| STR records | `0023_str_records.py` |

New PDF templates for Medical Application Form, Credit Note, Tax Invoice, and Policy Schedule are the only additions needed to `pdf_service.py`.

---

## 10. Recommended Developer Handoff

### Phase A — Core Journey (2–3 weeks)
1. Build the 5-step Policy Entry Wizard component (React multi-step form)
2. Wire Steps 1–3 to existing APIs (quotations, applications, members, products/plans)
3. Add Step 3 additional info fields to the application form (EID, Passport, Visa, Sponsor, Medical Questionnaire)
4. Build the unified Policy Listing page with filters + row expansion

### Phase B — Documents & Financials (1–2 weeks)
5. Add document Download/Preview/Upload to Policy Listing (Steps 4 + listing)
6. Implement Premium Breakup display in Policy Listing
7. Implement per-member premium breakdown
8. Add Commission edit modal

### Phase C — Dashboard & Polish (1 week)
9. Redesign Dashboard KPI tiles to be workflow-actionable
10. Add "Teams Actionable" / outstanding quotes table to Dashboard
11. Implement role-based nav (hide admin pages from broker role)
12. Build post-payment confirmation page with document downloads

### Phase D — PDFs & Reports (1–2 weeks)
13. Medical Application Form PDF template (prefilled)
14. KYC Form PDF template
15. Credit Note + Tax Invoice PDF templates
16. Commission SOA report
