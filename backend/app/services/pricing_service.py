from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.product import RateCard, Plan
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Any, Optional


class PricingService:
    """Calculates premium based on rate cards and rating factors."""

    def __init__(self, db: Session):
        self.db = db

    def get_active_rate_card(
        self, tenant_id: str, product_id: str, plan_id: str, as_of: Optional[datetime] = None
    ) -> RateCard:
        """Get the active rate card for a plan at a given date."""
        if as_of is None:
            as_of = datetime.now(timezone.utc)

        return self.db.query(RateCard).filter(
            and_(
                RateCard.tenant_id == tenant_id,
                RateCard.product_id == product_id,
                RateCard.plan_id == plan_id,
                RateCard.effective_date <= as_of,
                RateCard.expiry_date > as_of,
            )
        ).first()

    def calculate_premium(
        self,
        tenant_id: str,
        product_id: str,
        plan_id: str,
        factors: Dict[str, Any],
    ) -> Decimal:
        """Calculate premium based on base premium and rating factors.

        Factors expected: age, location, health_status, sum_insured, etc.
        """
        plan = self.db.query(Plan).filter(
            and_(Plan.tenant_id == tenant_id, Plan.id == plan_id, Plan.product_id == product_id)
        ).first()

        if not plan:
            raise ValueError(f"Plan {plan_id} not found")

        rate_card = self.get_active_rate_card(tenant_id, product_id, plan_id)
        if not rate_card:
            raise ValueError(f"No active rate card for plan {plan_id}")

        base_premium = Decimal(str(plan.base_premium))
        rates = rate_card.rates or {}

        premium = base_premium
        applied_factors = {}

        # Age rating factor
        if "age" in factors and "age_factors" in rates:
            age = factors["age"]
            age_factors = rates["age_factors"]
            age_factor = self._get_age_factor(age, age_factors)
            premium *= Decimal(str(age_factor))
            applied_factors["age"] = age_factor

        # Location/region rating factor
        if "location" in factors and "location_factors" in rates:
            location = factors["location"]
            location_factors = rates["location_factors"]
            location_factor = location_factors.get(location, 1.0)
            premium *= Decimal(str(location_factor))
            applied_factors["location"] = location_factor

        # Health status rating factor
        if "health_status" in factors and "health_factors" in rates:
            health = factors["health_status"]
            health_factors = rates["health_factors"]
            health_factor = health_factors.get(health, 1.0)
            premium *= Decimal(str(health_factor))
            applied_factors["health"] = health_factor

        # Sum insured rating factor
        if "sum_insured" in factors and "sum_insured_factors" in rates:
            sum_insured = Decimal(str(factors["sum_insured"]))
            sum_insured_factors = rates["sum_insured_factors"]
            sum_insured_factor = self._get_sum_insured_factor(sum_insured, sum_insured_factors)
            premium *= Decimal(str(sum_insured_factor))
            applied_factors["sum_insured"] = sum_insured_factor

        # Additional factors/surcharges
        if "surcharge_percent" in factors:
            surcharge = Decimal(str(factors["surcharge_percent"])) / Decimal("100")
            premium *= Decimal("1") + surcharge
            applied_factors["surcharge_percent"] = factors["surcharge_percent"]

        # Round to 2 decimal places
        premium = premium.quantize(Decimal("0.01"))

        return premium

    def _get_age_factor(self, age: int, age_factors: Dict[str, float]) -> float:
        """Get age factor based on age brackets."""
        for bracket in sorted(age_factors.keys()):
            if "-" in bracket:
                start, end = bracket.split("-")
                if int(start) <= age < int(end):
                    return age_factors[bracket]
            elif age >= int(bracket):
                return age_factors[bracket]
        return 1.0

    def _get_sum_insured_factor(self, sum_insured: Decimal, sum_insured_factors: Dict[str, float]) -> float:
        """Get sum insured factor based on amount brackets."""
        for bracket in sorted(sum_insured_factors.keys()):
            if "-" in bracket:
                start, end = bracket.split("-")
                if Decimal(start) <= sum_insured < Decimal(end):
                    return sum_insured_factors[bracket]
            elif sum_insured >= Decimal(bracket):
                return sum_insured_factors[bracket]
        return 1.0
