from typing import Any, Dict, List


def _to_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def evaluate(payload: Dict[str, Any]) -> Dict[str, Any]:
    order_value = _to_float(payload.get("order_value"))
    customer_month_orders = _to_int(payload.get("customer_month_orders"))
    customer_points = _to_int(payload.get("customer_points"))

    if customer_month_orders >= 40:
        tier = "platinum"
    elif customer_month_orders >= 20:
        tier = "gold"
    elif customer_month_orders >= 10:
        tier = "silver"
    else:
        tier = "bronze"

    earned_points = max(int(order_value), 0)
    updated_points = customer_points + earned_points

    benefits: List[str] = []
    if tier == "silver":
        benefits = ["occasional_free_delivery"]
    elif tier == "gold":
        benefits = ["priority_dispatch", "promo_access"]
    elif tier == "platinum":
        benefits = ["priority_dispatch", "reduced_service_fee", "vip_support"]

    points_to_next_reward = 500 - (updated_points % 500)
    if points_to_next_reward == 500:
        points_to_next_reward = 0

    return {
        "customer_tier": tier,
        "orders_this_month": customer_month_orders,
        "earned_points_this_order": earned_points,
        "loyalty_points": updated_points,
        "points_to_next_reward": points_to_next_reward,
        "benefits": benefits,
    }