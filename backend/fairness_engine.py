from __future__ import annotations

from typing import Any, Dict, List

from backend.schemas import OrderObservation


class FairnessEngine:
    """
    System-level fairness evaluation.
    This is not the offer scorer itself; it evaluates burden and fairness signals.
    """

    def __init__(
        self,
        min_pay_per_economic_mile: float = 1.15,
        min_effective_hourly: float = 18.0,
        max_burden_minutes: float = 18.0,
    ) -> None:
        self.min_pay_per_economic_mile = min_pay_per_economic_mile
        self.min_effective_hourly = min_effective_hourly
        self.max_burden_minutes = max_burden_minutes

    def evaluate(self, observation: OrderObservation) -> Dict[str, Any]:
        reasons: List[str] = []

        economic_miles = float(observation.economic_miles or 0.0)
        total_pay = float(observation.offered_pay_total or 0.0)
        burden_minutes = (
            float(observation.merchant_wait_minutes or 0.0)
            + float(observation.idle_before_offer_minutes or 0.0)
            + float(observation.delivery_minutes or 0.0)
        )

        pay_per_economic_mile = 0.0
        if economic_miles > 0:
            pay_per_economic_mile = total_pay / economic_miles

        effective_hourly = 0.0
        if burden_minutes > 0:
            effective_hourly = total_pay / (burden_minutes / 60.0)

        score = 1.0

        if economic_miles <= 0:
            reasons.append("missing_economic_miles")
            score -= 0.20

        if pay_per_economic_mile < self.min_pay_per_economic_mile:
            reasons.append("below_min_pay_per_economic_mile")
            score -= 0.30

        if burden_minutes > self.max_burden_minutes:
            reasons.append("high_burden_minutes")
            score -= 0.20

        if effective_hourly < self.min_effective_hourly and burden_minutes > 0:
            reasons.append("below_min_effective_hourly")
            score -= 0.20

        if observation.acceptance_rate_pressure_flag:
            reasons.append("acceptance_rate_pressure_seen")
            score -= 0.05

        if observation.navigate_back_to_zone_flag:
            reasons.append("requires_back_to_zone_navigation")
            score -= 0.05

        if observation.merchant_delay_flag:
            reasons.append("merchant_delay_flag")
            score -= 0.05

        score = max(0.0, round(score, 4))

        return {
            "score": score,
            "reasons": reasons,
            "pay_per_economic_mile": round(pay_per_economic_mile, 4),
            "effective_hourly": round(effective_hourly, 4),
            "burden_minutes": round(burden_minutes, 2),
        }