## Session Notes
**Last session:** 2026-06-22
**What was done:**
- Phase 1 foundation complete: WeasyPrint installed (requires DYLD_LIBRARY_PATH=/opt/homebrew/lib on macOS), 10 new database migrations (0016–0025), new enums (AmlStatus, GovtCheckStatus, LoadingType, AmlCheckType, GovtCheckType, StrStatus, SponsorType, ExistingHealthInsurance), new permissions (AML, Govt Check, Loading, Notification), new UserType values (compliance_officer, finance)
- New models: MarketConfig, PremiumLoading, CommissionConfig, AmlRecord, GovtVerificationRecord, StrRecord, NotificationRecord
- Application and Member models extended with UAE compliance fields and medical questionnaire fields
- Pricing service rewritten to produce full breakdown (rated premium + all 6 loading types + PSP fee + VAT)
- Adamjee tenant seeded: 10 spec-correct plans (Workers Network → General Network), rate cards, 34 market config values, default commission config (insurer 5%, broker 15.5%), 5 staff users
- config.py extended with payment gateway, govt API, and AML mock flags; extra="ignore" added to Settings

**Key decisions made:**
- ApplicationStatus enum extended with aml_hold; migration 0019 uses server_default strings not enum values
- WeasyPrint needs DYLD_LIBRARY_PATH=/opt/homebrew/lib set at runtime on macOS
- Rating factors: age 26-35 male Dubai = 1.00 reference; AED 1M = 1.00 sum_insured factor
- Commission config: fall-through logic (broker+plan → broker → plan → default)

**Next session must start with:** TASK-004 — Extend application schemas (ApplicationCreate) for UAE fields, then TASK-006 (Wizard Step 1 UI)

---

## In Progress
(none)

## Pending
- [ ] TASK-004: Extend application/member schemas (ApplicationCreate + MemberCreate with UAE fields)
- [ ] TASK-006: Wizard Step 1 — Quotations (cover amount chips, co-pay config, plan cards)
- [ ] TASK-007: Wizard Step 3 — Additional Info (medical questionnaire, UAE identity fields, health insurance declaration)
- [ ] TASK-008: Wizard Step 4 — Finalise (remarks thread, UW loading panel, document upload slots)
- [ ] TASK-009: Wizard Step 5 — Payment (Network International stub, confirmation + doc downloads)
- [ ] TASK-010: Policy Listing — extend with AML/Govt Check columns, filters, quick chips
- [ ] TASK-011: Policy Detail — 4-tab view (Personal, Signed Docs, Other Docs, Remarks)
- [ ] TASK-012: Dashboard — AML KPI cards
- [ ] TASK-013: PDF generation — MAF, KYC, ToB, Policy Schedule, Credit Note, Tax Invoice, Receipt (WeasyPrint)
- [ ] TASK-014: Payment gateway service (Network International stub + real mode toggle)
- [ ] TASK-015: Government Verification Service (ICP, DHA, OFAC, UN, UAE Cabinet 74 — all stubbed)
- [ ] TASK-016: Government Checks Dashboard (frontend page)
- [ ] TASK-017: AML Service — PEP check + sanctions + risk scoring engine + transaction monitoring
- [ ] TASK-018: AML Hold workflow + AML alerts endpoint
- [ ] TASK-019: AML Dashboard (frontend page)
- [ ] TASK-020: STR Filing workflow (backend + frontend)
- [ ] TASK-021: Reports — all 7 reports (PDF + CSV export)
- [ ] TASK-022: In-portal notification bell (backend records + frontend polling)

## Completed
- [x] Planning session — 2026-06-22
- [x] TASK-001: WeasyPrint added + verified working — 2026-06-22
- [x] TASK-002: Migrations 0016–0025 all run successfully — 2026-06-22
- [x] TASK-003: New enums (AmlStatus, GovtCheckStatus, LoadingType, etc.) + permission codes + compliance_officer/finance UserType — 2026-06-22
- [x] TASK-004 (partial): Pricing service rewritten with full breakdown (base + loadings + VAT + PSP fee) — 2026-06-22
- [x] TASK-005: Adamjee tenant seeded — 10 plans, rate cards, 34 market_configs, commission_config, 5 users — 2026-06-22
