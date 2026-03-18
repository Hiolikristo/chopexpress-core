from typing import Any, Dict


def evaluate(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fair offer engine.

    Produces a stable compensation breakdown for the pipeline.
    This is a V1 contract-safe implementation that can later be expanded
    into the full fairness/economics engine without breaking imports.
    """

    base_pay = float(payload.get("base_pay", 0.0) or 0.0)
    tip = float(payload.get("tip", 0.0) or 0.0)
    bonus = float(payload.get("bonus", 0.0) or 0.0)

    estimated_miles = float(payload.get("estimated_miles", 0.0) or 0.0)
    return_miles = float(payload.get("return_miles", 0.0) or 0.0)
    estimated_minutes = float(payload.get("estimated_minutes", 0.0) or 0.0)

    tier = str(payload.get("driver_tier", "casual") or "casual").lower()
    is_batched_order = bool(payload.get("is_batched_order", False))

    tier_multiplier_map = {
        "casual": 1.00,
        "professional": 1.03,
        "pro": 1.03,
        "pro_plus": 1.06,
        "elite": 1.10,
    }
    tier_multiplier = tier_multiplier_map.get(tier, 1.00)

    economic_miles = max(0.0, estimated_miles + return_miles)

    gross_offer = base_pay + tip + bonus
    adjusted_offer = round(gross_offer * tier_multiplier, 2)

    effective_pay_per_mile = round(
        adjusted_offer / economic_miles, 2
    ) if economic_miles > 0 else adjusted_offer

    effective_pay_per_minute = round(
        adjusted_offer / estimated_minutes, 4
    ) if estimated_minutes > 0 else adjusted_offer

    fairness_status = "fair"
    if effective_pay_per_mile < 1.00:
        fairness_status = "unfair"
    elif effective_pay_per_mile < 1.35:
        fairness_status = "borderline"

    return {
        "base_pay": round(base_pay, 2),
        "tip": round(tip, 2),
        "bonus": round(bonus, 2),
        "gross_offer": round(gross_offer, 2),
        "adjusted_offer": adjusted_offer,
        "estimated_miles": round(estimated_miles, 2),
        "return_miles": round(return_miles, 2),
        "economic_miles": round(economic_miles, 2),
        "estimated_minutes": round(estimated_minutes, 2),
        "tier": tier,
        "tier_multiplier": tier_multiplier,
        "is_batched_order": is_batched_order,
        "effective_pay_per_mile": effective_pay_per_mile,
        "effective_pay_per_minute": effective_pay_per_minute,
        "fairness_status": fairness_status,
        "status": "ok",
    }


def fair_offer(payload: Dict[str, Any]) -> Dict[str, Any]:
    return evaluate(payload)


def evaluate_fair_offer(payload: Dict[str, Any]) -> Dict[str, Any]:
    return evaluate(payload)


def fair_offer_engine(payload: Dict[str, Any]) -> Dict[str, Any]:
    return evaluate(payload)