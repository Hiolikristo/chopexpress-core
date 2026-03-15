import random
from dataclasses import dataclass


@dataclass
class OfferLifecycleResult:
    accepted: bool
    reason: str
    response_seconds: float


def evaluate_offer(
    fair_pay: float,
    total_miles: float,
    pickup_miles: float,
    fatigue_score: float,
    acceptance_rate: float,
) -> OfferLifecycleResult:
    safe_total_miles = max(0.1, total_miles)
    pay_per_mile = fair_pay / safe_total_miles

    accept_probability = acceptance_rate

    if pay_per_mile < 1.80:
        accept_probability -= 0.28
    elif pay_per_mile < 2.20:
        accept_probability -= 0.14
    elif pay_per_mile > 3.20:
        accept_probability += 0.06

    if pickup_miles > 3.0:
        accept_probability -= 0.10
    elif pickup_miles > 2.0:
        accept_probability -= 0.05

    accept_probability -= fatigue_score * 0.35
    accept_probability = max(0.05, min(0.96, accept_probability))

    response_seconds = round(random.uniform(8.0, 42.0), 2)

    if random.random() <= accept_probability:
        return OfferLifecycleResult(
            accepted=True,
            reason="accepted",
            response_seconds=response_seconds,
        )

    decline_reason = "declined_low_value"
    if fatigue_score > 0.55:
        decline_reason = "declined_fatigue"
    elif pickup_miles > 3.0:
        decline_reason = "declined_long_pickup"

    return OfferLifecycleResult(
        accepted=False,
        reason=decline_reason,
        response_seconds=response_seconds,
    )