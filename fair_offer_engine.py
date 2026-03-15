from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict


TWOPLACES = Decimal("0.01")


def q2(value: Decimal) -> Decimal:
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


@dataclass
class FairOfferInput:
    order_id: str
    zone: str
    merchant: str
    offered_payout: Decimal
    delivery_miles: Decimal
    economic_miles: Decimal
    estimated_total_minutes: Decimal
    tier: str
    zone_pressure_score: Decimal
    merchant_risk_score: Decimal
    is_batched_candidate: bool
    is_high_wait_merchant: bool
    is_long_deadhead_zone: bool


@dataclass
class FairOfferResult:
    order_id: str
    zone: str
    merchant: str
    tier: str
    offered_payout: Decimal
    delivery_miles: Decimal
    economic_miles: Decimal
    estimated_total_minutes: Decimal
    effective_pay_per_delivery_mile: Decimal
    effective_pay_per_economic_mile: Decimal
    effective_hourly_rate: Decimal
    zone_pressure_score: Decimal
    merchant_risk_score: Decimal
    fairness_score: Decimal
    fairness_status: str
    recommended_action: str
    reasons: list[str]

    def to_dict(self) -> Dict[str, object]:
        data = asdict(self)
        for key, value in data.items():
            if isinstance(value, Decimal):
                data[key] = str(q2(value))
        return data


class FairOfferEngine:
    """
    Evaluates whether a proposed order is fair enough to dispatch.

    Core idea:
    - economic_miles matters more than raw delivery miles
    - time matters
    - merchant risk and pressure matter
    - long deadhead / high wait should reduce attractiveness
    """

    def __init__(
        self,
        min_pay_per_economic_mile: Decimal = Decimal("1.35"),
        min_hourly_floor: Decimal = Decimal("18.00"),
        strong_hourly_target: Decimal = Decimal("24.00"),
        strong_mile_target: Decimal = Decimal("2.00"),
    ) -> None:
        self.min_pay_per_economic_mile = min_pay_per_economic_mile
        self.min_hourly_floor = min_hourly_floor
        self.strong_hourly_target = strong_hourly_target
        self.strong_mile_target = strong_mile_target

    def evaluate(self, input_data: FairOfferInput) -> FairOfferResult:
        offered_payout = Decimal(input_data.offered_payout)
        delivery_miles = max(Decimal(input_data.delivery_miles), Decimal("0.01"))
        economic_miles = max(Decimal(input_data.economic_miles), Decimal("0.01"))
        total_minutes = max(Decimal(input_data.estimated_total_minutes), Decimal("1"))

        pay_per_delivery_mile = offered_payout / delivery_miles
        pay_per_economic_mile = offered_payout / economic_miles
        hourly_rate = offered_payout / (total_minutes / Decimal("60"))

        reasons: list[str] = []
        score = Decimal("100")

        if pay_per_economic_mile < self.min_pay_per_economic_mile:
            shortfall = self.min_pay_per_economic_mile - pay_per_economic_mile
            penalty = shortfall * Decimal("25")
            score -= penalty
            reasons.append("Below minimum pay per economic mile.")

        if hourly_rate < self.min_hourly_floor:
            shortfall = self.min_hourly_floor - hourly_rate
            penalty = shortfall * Decimal("2")
            score -= penalty
            reasons.append("Below hourly floor.")

        if input_data.is_high_wait_merchant:
            score -= Decimal("10")
            reasons.append("High-wait merchant penalty applied.")

        if input_data.is_long_deadhead_zone:
            score -= Decimal("12")
            reasons.append("Long deadhead zone penalty applied.")

        if input_data.is_batched_candidate:
            score -= Decimal("4")
            reasons.append("Batched order complexity adjustment applied.")

        if Decimal(input_data.merchant_risk_score) > Decimal("1.00"):
            risk_penalty = (Decimal(input_data.merchant_risk_score) - Decimal("1.00")) * Decimal("10")
            score -= risk_penalty
            reasons.append("Merchant risk penalty applied.")

        if Decimal(input_data.zone_pressure_score) > Decimal("1.00"):
            pressure_bonus = (Decimal(input_data.zone_pressure_score) - Decimal("1.00")) * Decimal("8")
            score += pressure_bonus
            reasons.append("Zone pressure bonus applied.")

        if pay_per_economic_mile >= self.strong_mile_target:
            score += Decimal("6")
            reasons.append("Strong pay per economic mile.")

        if hourly_rate >= self.strong_hourly_target:
            score += Decimal("6")
            reasons.append("Strong hourly earnings profile.")

        if score < Decimal("0"):
            score = Decimal("0")
        if score > Decimal("100"):
            score = Decimal("100")

        if score >= Decimal("80"):
            fairness_status = "strong"
            recommended_action = "accept"
        elif score >= Decimal("65"):
            fairness_status = "acceptable"
            recommended_action = "accept"
        elif score >= Decimal("50"):
            fairness_status = "borderline"
            recommended_action = "review"
        else:
            fairness_status = "weak"
            recommended_action = "decline"

        if not reasons:
            reasons.append("Offer meets baseline fairness thresholds.")

        return FairOfferResult(
            order_id=input_data.order_id,
            zone=input_data.zone,
            merchant=input_data.merchant,
            tier=input_data.tier,
            offered_payout=q2(offered_payout),
            delivery_miles=q2(delivery_miles),
            economic_miles=q2(economic_miles),
            estimated_total_minutes=q2(total_minutes),
            effective_pay_per_delivery_mile=q2(pay_per_delivery_mile),
            effective_pay_per_economic_mile=q2(pay_per_economic_mile),
            effective_hourly_rate=q2(hourly_rate),
            zone_pressure_score=q2(Decimal(input_data.zone_pressure_score)),
            merchant_risk_score=q2(Decimal(input_data.merchant_risk_score)),
            fairness_score=q2(score),
            fairness_status=fairness_status,
            recommended_action=recommended_action,
            reasons=reasons,
        )


if __name__ == "__main__":
    engine = FairOfferEngine()

    sample = FairOfferInput(
        order_id="order_1001",
        zone="clintonville",
        merchant="Chick-fil-A",
        offered_payout=Decimal("8.75"),
        delivery_miles=Decimal("6.60"),
        economic_miles=Decimal("6.60"),
        estimated_total_minutes=Decimal("24"),
        tier="professional",
        zone_pressure_score=Decimal("1.10"),
        merchant_risk_score=Decimal("0.80"),
        is_batched_candidate=True,
        is_high_wait_merchant=False,
        is_long_deadhead_zone=False,
    )

    print(engine.evaluate(sample).to_dict())