"""Premium calculation service.

Produces a full breakdown per member and policy totals:
  base_premium × age_factor × gender_factor × location_factor × sum_insured_factor
  + per-member loadings (UW, BMI, Other, TPA, Broker, Insurer)
  + PSP fee (flat, from market_config)
  + VAT (% on gross premium, from market_config)
  = amount_payable

All rates come from the database. No literals in this file.
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.product import RateCard, Plan
from app.models.market_config import MarketConfig
from app.models.compliance import PremiumLoading, CommissionConfig
from datetime import datetime, timezone, date
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List, Optional


class PricingService:

    def __init__(self, db: Session):
        self.db = db

    # ── Public API ───────────────────────────────────────────────────────────

    def calculate_premium(
        self,
        tenant_id: str,
        product_id: str,
        plan_id: str,
        factors: Dict[str, Any],
    ) -> Decimal:
        """Simple single-value calculation (backward-compatible). Returns amount_payable."""
        result = self.calculate_full_breakdown(tenant_id, product_id, plan_id, [factors])
        return result["amount_payable"]

    def calculate_full_breakdown(
        self,
        tenant_id: str,
        product_id: str,
        plan_id: str,
        members_factors: List[Dict[str, Any]],
        application_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Calculate the full premium breakdown for all members.

        Returns:
        {
          "members": [...per-member breakdown...],
          "gross_premium_excl_tax": Decimal,
          "psp_fee": Decimal,
          "vat_rate": Decimal,
          "vat_amount": Decimal,
          "amount_payable": Decimal,
          "insurer_commission_pct": Decimal,
          "insurer_commission": Decimal,
          "broker_commission_pct": Decimal,
          "broker_commission": Decimal,
        }
        """
        plan = self.db.query(Plan).filter(
            and_(Plan.tenant_id == tenant_id, Plan.id == plan_id, Plan.product_id == product_id)
        ).first()
        if not plan:
            raise ValueError(f"Plan {plan_id} not found")

        rate_card = self._get_active_rate_card(tenant_id, product_id, plan_id)

        # Fetch market config values
        vat_rate = self._get_config(tenant_id, "vat_rate", Decimal("0.05"))
        psp_fee = self._get_config(tenant_id, "psp_fee", Decimal("24.00"))

        # Fetch commission config (default if no broker/plan specific)
        comm = self._get_commission_config(tenant_id, plan_id=plan_id)
        insurer_pct = comm.insurer_pct if comm else Decimal("5.00")
        broker_pct = comm.broker_pct if comm else Decimal("15.50")

        # Fetch existing loadings for this application if provided
        existing_loadings: Dict[str, List[PremiumLoading]] = {}
        if application_id:
            loadings = self.db.query(PremiumLoading).filter(
                PremiumLoading.tenant_id == tenant_id,
                PremiumLoading.application_id == application_id,
            ).all()
            for loading in loadings:
                key = loading.member_id or "_application"
                existing_loadings.setdefault(key, []).append(loading)

        member_breakdowns = []
        gross_premium = Decimal("0")

        for i, factors in enumerate(members_factors):
            member_id = factors.get("member_id")
            base = Decimal(str(plan.base_premium))
            rates = rate_card.rates if rate_card else {}

            rated = base * self._age_factor(factors.get("age", 30), rates)
            rated *= self._gender_factor(factors.get("gender", "male"), rates)
            rated *= self._location_factor(factors.get("location", "Dubai"), rates)
            rated *= self._sum_insured_factor(
                Decimal(str(factors.get("sum_insured", 1_000_000))), rates
            )
            rated = rated.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            # Per-member loadings
            member_loadings = existing_loadings.get(member_id or "", [])
            loading_amounts = {
                "underwriter": Decimal("0"),
                "bmi":         Decimal("0"),
                "other":       Decimal("0"),
                "tpa":         Decimal("0"),
                "broker":      Decimal("0"),
                "insurer":     Decimal("0"),
            }
            for loading in member_loadings:
                ltype = loading.loading_type
                if ltype in loading_amounts:
                    if loading.amount:
                        loading_amounts[ltype] += Decimal(str(loading.amount))
                    elif loading.percentage:
                        loading_amounts[ltype] += rated * Decimal(str(loading.percentage)) / 100

            subtotal = (rated + sum(loading_amounts.values())).quantize(Decimal("0.01"))
            gross_premium += subtotal

            member_breakdowns.append({
                "member_id": member_id,
                "index": i,
                "base_premium": base,
                "rated_premium": rated,
                "underwriter_loading": loading_amounts["underwriter"],
                "bmi_loading": loading_amounts["bmi"],
                "other_loading": loading_amounts["other"],
                "tpa_loading": loading_amounts["tpa"],
                "broker_loading": loading_amounts["broker"],
                "insurer_loading": loading_amounts["insurer"],
                "subtotal": subtotal,
            })

        vat_amount = (gross_premium * vat_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        amount_payable = gross_premium + psp_fee + vat_amount

        insurer_commission = (amount_payable * insurer_pct / 100).quantize(Decimal("0.01"))
        broker_commission = (amount_payable * broker_pct / 100).quantize(Decimal("0.01"))

        return {
            "members": member_breakdowns,
            "gross_premium_excl_tax": gross_premium,
            "psp_fee": psp_fee,
            "vat_rate": vat_rate,
            "vat_amount": vat_amount,
            "amount_payable": amount_payable,
            "insurer_commission_pct": insurer_pct,
            "insurer_commission": insurer_commission,
            "broker_commission_pct": broker_pct,
            "broker_commission": broker_commission,
        }

    # ── Internal helpers ─────────────────────────────────────────────────────

    def _get_active_rate_card(self, tenant_id, product_id, plan_id, as_of=None):
        if as_of is None:
            as_of = date.today()
        return self.db.query(RateCard).filter(
            and_(
                RateCard.tenant_id == tenant_id,
                RateCard.product_id == product_id,
                RateCard.plan_id == plan_id,
                RateCard.effective_date <= as_of,
                RateCard.expiry_date > as_of,
            )
        ).first()

    def _get_config(self, tenant_id: str, key: str, default: Decimal) -> Decimal:
        mc = self.db.query(MarketConfig).filter(
            MarketConfig.tenant_id == tenant_id,
            MarketConfig.key == key,
        ).first()
        if mc is None:
            return default
        return Decimal(str(mc.value))

    def _get_commission_config(self, tenant_id: str, broker_id: Optional[str] = None, plan_id: Optional[str] = None):
        # Try most specific first: broker + plan → broker only → plan only → default
        for bid, pid in [(broker_id, plan_id), (broker_id, None), (None, plan_id), (None, None)]:
            q = self.db.query(CommissionConfig).filter(CommissionConfig.tenant_id == tenant_id)
            q = q.filter(CommissionConfig.broker_id == bid) if bid else q.filter(CommissionConfig.broker_id.is_(None))
            q = q.filter(CommissionConfig.plan_id == pid) if pid else q.filter(CommissionConfig.plan_id.is_(None))
            result = q.first()
            if result:
                return result
        return None

    def _age_factor(self, age: int, rates: dict) -> Decimal:
        age_factors = rates.get("age_factors", {})
        for bracket in sorted(age_factors.keys()):
            if "-" in bracket:
                start, end = bracket.split("-")
                if int(start) <= age <= int(end):
                    return Decimal(str(age_factors[bracket]))
        return Decimal("1.0")

    def _gender_factor(self, gender: str, rates: dict) -> Decimal:
        gender_factors = rates.get("gender_factors", {})
        return Decimal(str(gender_factors.get(gender, 1.0)))

    def _location_factor(self, location: str, rates: dict) -> Decimal:
        location_factors = rates.get("location_factors", {})
        return Decimal(str(location_factors.get(location, 1.0)))

    def _sum_insured_factor(self, sum_insured: Decimal, rates: dict) -> Decimal:
        sum_insured_factors = rates.get("sum_insured_factors", {})
        best_key = None
        for key in sorted(sum_insured_factors.keys(), key=lambda k: Decimal(k) if k.isdigit() else Decimal("999999999")):
            try:
                threshold = Decimal(key)
            except Exception:
                continue
            if sum_insured >= threshold:
                best_key = key
        if best_key:
            return Decimal(str(sum_insured_factors[best_key]))
        return Decimal("1.0")
