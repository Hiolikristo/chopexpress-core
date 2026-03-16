from typing import Dict, Any

BASE_RATE_PER_MILE = 1.25
BASE_RATE_PER_MINUTE = 0.22
RETURN_BUFFER_RATE = 0.45

TIER_MULTIPLIERS = {
    "casual": 1.0,
    "professional": 1.08,
    "pro+": 1.15,
    "elite": 1.25
}


def _to_float(v, default=0.0):
    try:
        return float(v)
    except:
        return default


def evaluate(payload: Dict[str, Any]) -> Dict[str, Any]:

    delivery_distance = _to_float(payload.get("delivery_distance"))
    pickup_distance = _to_float(payload.get("pickup_distance"))
    return_distance = _to_float(payload.get("return_distance"))

    minutes = _to_float(payload.get("estimated_total_minutes"))
    tip = _to_float(payload.get("tip"))

    tier = payload.get("tier", "casual").lower()

    tier_multiplier = TIER_MULTIPLIERS.get(tier, 1.0)

    economic_miles = delivery_distance + pickup_distance + return_distance

    mileage_component = economic_miles * BASE_RATE_PER_MILE
    time_component = minutes * BASE_RATE_PER_MINUTE
    return_buffer = return_distance * RETURN_BUFFER_RATE

    fair_base = mileage_component + time_component + return_buffer

    fair_total = fair_base * tier_multiplier

    fair_total += tip

    return {
        "economic_miles": round(economic_miles, 2),
        "mileage_component": round(mileage_component, 2),
        "time_component": round(time_component, 2),
        "return_buffer": round(return_buffer, 2),
        "tier_multiplier": tier_multiplier,
        "fair_driver_total": round(fair_total, 2)
    }