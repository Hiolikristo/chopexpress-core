from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FairnessDecision:
    approved: bool
    reason: str
    offer_pay: float
    trip_miles: float
    return_miles: float
    economic_miles: float
    pay_per_economic_mile: float
    minimum_required_ppem: float
    return_buffer_used: float


class FairnessEngine:
    def __init__(self, min_ppem: float = 1.15) -> None:
        self.min_ppem = float(min_ppem)

    def evaluate(
        self,
        offer_pay: float,
        trip_miles: float,
        return_miles: float = 0.0,
        min_ppem: float | None = None,
    ) -> FairnessDecision:
        offer_pay = float(offer_pay)
        trip_miles = max(0.0, float(trip_miles))
        return_miles = max(0.0, float(return_miles))
        threshold = self.min_ppem if min_ppem is None else float(min_ppem)

        economic_miles = round(trip_miles + return_miles, 2)
        if economic_miles <= 0:
            ppem = 0.0
        else:
            ppem = round(offer_pay / economic_miles, 2)

        approved = ppem >= threshold
        reason = "approved" if approved else "below_fairness_threshold"

        return FairnessDecision(
            approved=approved,
            reason=reason,
            offer_pay=round(offer_pay, 2),
            trip_miles=round(trip_miles, 2),
            return_miles=round(return_miles, 2),
            economic_miles=economic_miles,
            pay_per_economic_mile=ppem,
            minimum_required_ppem=round(threshold, 2),
            return_buffer_used=round(return_miles, 2),
        )