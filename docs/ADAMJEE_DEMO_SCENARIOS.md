# Adamjee Insurance — Demo Scenarios & Use Cases
## Live Demonstration Guide
### For: Adamjee Team Presentation — June 23, 2026

---

## Setup Before Demo

**Start the services** (if not already running):
```bash
# Terminal 1 — Backend
cd backend && venv/bin/uvicorn app.main:app --port 8001 --reload

# Terminal 2 — Frontend  
cd frontend && npm run dev
```

**Login to Staff Portal**: http://localhost:5173
- Email: `admin@adamjee.ae`
- Password: `adamjee123`
- Tenant ID: `84595acc-7561-4684-9aba-7a14795ec81d`

---

## Scenario 1: Dashboard Overview (3 minutes)
**Story**: "This is the command centre for your operations team."

**Steps**:
1. Login and land on **Dashboard**
2. Point to KPI cards:
   - **3 Active Policies** generating AED 16,550/month
   - **2 AML Flagged** (red card — requires Compliance Officer attention)
   - **7 Total Applications** across all lifecycle stages
3. Point to **Applications by Status** bar chart — shows distribution from Draft to Issued
4. Point to **Recent Applications** — shows live app list with statuses including `aml_hold`
5. Point to **Recent Payments** — all in AED: 8,750 / 4,850 / 2,950
6. Notice **notification bell (4 unread)** in bottom-left — real-time alert count

**Talking points**:
- "All amounts are in AED — no currency confusion"
- "The 2 AML alerts are a real-time risk signal from our automated scoring engine"
- "The dashboard refreshes automatically — no need to manually run reports"

---

## Scenario 2: Application Lifecycle (5 minutes)
**Story**: "Let me show you how an application moves from draft to policy issuance."

**Steps**:
1. Click **Applications** in sidebar
2. Show the filter bar — 7 applications with all statuses visible
3. Use the **AML Hold** quick filter chip → shows only APP-2026-0003 (Ibrahim Hassan Al-Nasser)
4. Click **AML Flagged** chip → shows APP-2026-0002 (Rajesh Sharma)
5. Click **Issued** chip → shows 3 issued applications (APP-2026-0001, 0006, 2025-0099)
6. Click **View** on APP-2026-0001 (Mohammed Al-Rashid, issued) to show the full detail

**Talking points**:
- "The filter chips let underwriters focus on their specific queue"
- "Each application shows AML status and Govt Check status side by side"
- "Issued applications link directly to the generated policy"

**Data in system**:
| Application | Customer | Status | AML | Premium |
|-------------|----------|--------|-----|---------|
| APP-2026-0001 | Mohammed Al-Rashid | Issued | Clear | AED 8,750 |
| APP-2026-0002 | Rajesh Sharma | Submitted | MEDIUM Flagged | AED 12,400 |
| APP-2026-0003 | Ibrahim Hassan Al-Nasser | AML Hold | HIGH Hold | AED 45,200 |
| APP-2026-0004 | Sarah Johnson | Approved | Clear | AED 6,200 |
| APP-2026-0005 | Ahmed Khalil | Draft | — | AED 3,200 |
| APP-2026-0006 | Zara Malik | Issued | Clear | AED 4,850 |
| APP-2025-0099 | Ali Hassan Abbasi | Issued | Clear | AED 2,950 |

---

## Scenario 3: AML Compliance Workflow (5 minutes)
**Story**: "The system automatically screens every applicant. Here's a high-risk case."

**Steps**:
1. Click **AML** in sidebar → AML Dashboard
2. Show **2 Open AML Alerts** KPI card
3. Point to the alerts table:
   - **APP-2026-0003 — Ibrahim Hassan Al-Nasser**: Score 67.50 — HIGH (red badge)
   - **APP-2026-0002 — Rajesh Sharma**: Score 38.75 — MEDIUM (amber badge)
4. Explain the risk factors for each:
   - Al-Nasser: Diplomatic passport (5pts) + PEP status (25pts) + premium threshold (10pts) + occupation (5pts) + prior flag (12pts) + income inconsistency (10pts) = 67.5
   - Sharma: FATF nationality (15pts) + premium threshold (10pts) + occupation risk (8pts) + income inconsistency (5pts) = 38.75
5. Click **Clear Hold** on APP-2026-0003 → demonstrate the clearance modal with mandatory notes field
6. Point to **+ Create STR** button for cases requiring Suspicious Transaction Report filing

**Talking points**:
- "The AML engine scores 9 risk factors automatically — no manual scoring"
- "HIGH risk applications cannot proceed without Compliance Officer sign-off"
- "We NEVER disclose AML holds to the policyholder — tipping-off protection is built in"
- "MEDIUM risk applications get automatically notified to the CO but still proceed"
- "All clearance actions are timestamped in the immutable audit log"

**Show AML Hold in Applications**:
- Go back to Applications → Ibrahim Hassan Al-Nasser shows as `aml_hold`
- The customer portal shows this as a generic "Under Review" — no mention of AML

---

## Scenario 4: Government Checks (3 minutes)
**Story**: "Every applicant is screened against UAE government databases."

**Steps**:
1. Click **Govt Checks** in sidebar
2. Show the 4 KPI cards: Pending / Failed-Mismatch / Verified / Overridden
3. Show the **1 Pending ICP check** for Rajesh Sharma
4. Explain the check types:
   - ICP: UAE Immigration & Citizenship (Emirates ID validation)
   - OFAC: US Treasury sanctions
   - UN Sanctions: UN Security Council consolidated list
   - UAE Cabinet 74: UAE local blacklist
5. Click **Override** to demonstrate manual override with justification

**Talking points**:
- "All government API calls are framework-ready — credentials go in environment config"
- "Checks run automatically when an application is submitted"
- "Override requires mandatory justification text — creates an audit record"
- "Results are cached for 90 days — no redundant API calls"

---

## Scenario 5: Policy Management (3 minutes)
**Story**: "Three active policies in the system — let's look at the expiring one."

**Steps**:
1. Click **Policies** in sidebar
2. Show all 3 active policies in the table
3. Point to **POL-2025-00099 (Ali Hassan Abbasi)** — expiry date is 25 days away
4. Explain the renewal warning notification (visible in the notification bell)
5. Click **View** on POL-2026-00001 (Mohammed Al-Rashid) to show policy detail:
   - Personal details tab
   - Premium: AED 8,750
   - Policy period: May 2026 – May 2027
   - Plan: linked to Silver Premium plan
6. Show premium breakdown button → AED 8,333.33 gross + AED 416.67 VAT + AED 24.00 PSP

**Talking points**:
- "VAT is calculated at 5% automatically on every policy"
- "PSP fee (AED 24) is configurable in market configuration — not hardcoded"
- "Expiry notifications go to both the broker and the policyholder 60 and 30 days in advance"

---

## Scenario 6: Reports Module (2 minutes)
**Story**: "All the management reports your finance and compliance teams need."

**Steps**:
1. Click **Reports** in sidebar
2. Show the 7 report categories:
   - Premium Collection Report
   - DHA Fine Report  
   - Commission Statement
   - Underwriter Report
   - AML Screening Report
   - Government Verification Report
   - STR Log Report
3. Set a date range
4. Click **Export CSV** or **Export PDF** for one report

**Talking points**:
- "All reports support CSV export for Excel and PDF export for formal documentation"
- "The Commission Statement calculates insurer (5%) and broker (15.5%) commissions automatically"
- "AML Screening Report is the compliance team's audit trail for regulators"

---

## Scenario 7: Notifications Bell (1 minute)
**Story**: "Real-time alerts so nothing falls through the cracks."

**Steps**:
1. Click the **bell icon (4 unread)** in the bottom-left
2. Walk through the 4 unread notifications:
   - AML Alert — APP-2026-0003 (Ibrahim Hassan Al-Nasser — HIGH risk)
   - New Application — APP-2026-0002 (Rajesh Sharma submitted, AML MEDIUM)
   - AML Medium Risk — APP-2026-0002 (EDD initiated)
   - Policy Expiry Warning — POL-2025-00099 (expires in 25 days)
3. Show the 3 older read notifications (approved, issued events)

**Talking points**:
- "Notifications update every 60 seconds automatically"
- "Each notification links directly to the relevant application or policy"
- "Separate notification types for AML, underwriting, payments, and policy events"

---

## Scenario 8: Customer Self-Service Portal (2 minutes)
**Story**: "Policyholders have their own secure portal."

**Steps**:
1. Navigate to http://localhost:5173/portal
2. Show the customer login page (separate from staff portal)
3. Explain the customer portal features:
   - View active policy and coverage details
   - See all members on the policy
   - View claims history and status
   - View payment history in AED
   - Download policy documents

**Talking points**:
- "Completely separate from the staff portal — different authentication"
- "Customers cannot see AML holds or compliance activity"
- "Full mobile-responsive design"

---

## Scenario 9: Public Buying Portal (2 minutes)
**Story**: "New customers can buy directly online."

**Steps**:
1. Navigate to http://localhost:5173/buy
2. Click on **Adamjee Insurance** tile
3. Show the 10 Adamjee plans with AED pricing:
   - Workers Network (AED 1,200/yr)
   - Pearl Plan (AED 2,200/yr)
   - Emerald Plan (AED 3,800/yr)
   - Silver Classic (AED 6,400/yr)
   - Silver Premium (AED 7,980/yr)
   - General Network (AED 9,200/yr)
4. Click **Apply Now** on any plan → show the application form
5. Show the medical questionnaire (14 health questions)
6. Show the UAE-specific fields: Emirates ID, visa type, diplomatic passport toggle

**Talking points**:
- "All plans are seeded directly from the Adamjee Insurance rate schedule"
- "The medical questionnaire captures all 14 UAE DHA-required questions"
- "Network International payment integration is framework-ready"

---

## Scenario 10: Products & Plans Configuration (1 minute)
**Story**: "All products and rates are database-driven — no code changes needed to update premiums."

**Steps**:
1. Click **Products** in staff sidebar
2. Show the 2 products: Group Medical and Individual Health
3. Show the 10 plans with base premiums in AED
4. Explain that rate cards, loadings, and commission configs are all in the database

**Talking points**:
- "To change a premium, you update the database — the system rebuilds quotes immediately"
- "Commission rates (insurer 5%, broker 15.5%) are configurable per plan"
- "VAT rate, PSP fee, and AML thresholds are all in the market_config table"

---

## Common Questions & Answers

**Q: How does the system prevent unauthorised access to AML data?**
A: RBAC permissions — only users with `aml.read` permission can see the AML dashboard. Compliance Officers and Admins only.

**Q: Can we customise the risk scoring weights?**
A: Yes — all 9 factor weights are stored in the `market_config` database table. Change `aml_pep_self_score`, `aml_fatf_score`, etc. No code change required.

**Q: How are government API credentials managed?**
A: Environment variables — `ICP_API_KEY`, `OFAC_API_KEY`, `DHA_API_KEY` etc. Set them and the system switches from mock to live automatically.

**Q: What happens if the payment gateway is down?**
A: The payment service has 3-retry with exponential backoff, then falls back to marking the payment as `pending` for manual follow-up. No data is lost.

**Q: Is the data encrypted?**
A: Yes — Emirates ID, passport numbers, and medical questionnaire answers use AES-256 encryption at rest. JWT tokens use RS256 signing.

**Q: Can we add more users/roles?**
A: Yes — the Users page in the admin panel allows creating users with specific roles: Admin, Underwriter, Broker, Compliance Officer, Finance.

**Q: What's the audit trail coverage?**
A: Every write action — create, update, status change, approval, clearance — is logged in the `audit_logs` table with: who, what table, what action, before/after values, timestamp, IP address.

---

## Technical Q&A

**Q: What database does it use?**
A: PostgreSQL 14+ — battle-tested, ACID compliant, excellent JSON support for the JSONB fields.

**Q: How are multi-tenant boundaries enforced?**
A: Every database table has a `tenant_id` column. Every query is automatically filtered by the tenant from the request context. It's impossible to read another tenant's data.

**Q: Can it integrate with our existing systems?**
A: Yes — REST API with OpenAPI documentation (http://localhost:8001/docs). We can build adapters for any system that supports HTTP.

**Q: What's the deployment model?**
A: Docker containers. The `docker-compose.yml` in the `infra/` directory sets up the entire stack with one command.

---

*End of Demo Guide*
*Adamjee Insurance Policy Sales Portal — Confidential*
