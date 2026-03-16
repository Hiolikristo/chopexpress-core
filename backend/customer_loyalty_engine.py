from typing import Any, Dict


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def evaluate(payload: Dict[str, Any]) -> Dict[str, Any]:
    order_value = _to_float(payload.get("order_value"), 0.0)
    customer_month_orders = _to_int(payload.get("customer_month_orders"), 0)
    customer_points = _to_int(payload.get("customer_points"), 0)

    earned_points = int(order_value)
    projected_points = customer_points + earned_points

    if customer_month_orders >= 20:
        tier = "platinum"
        discount_rate = 0.12
        free_delivery_eligible = True
    elif customer_month_orders >= 10:
        tier = "gold"
        discount_rate = 0.08
        free_delivery_eligible = True
    elif customer_month_orders >= 5:
        tier = "silver"
        discount_rate = 0.04
        free_delivery_eligible = False
    else:
        tier = "bronze"
        discount_rate = 0.00
        free_delivery_eligible = False

    reward_value = round(order_value * discount_rate, 2)

    reasons = [
        f"Customer monthly orders: {customer_month_orders}.",
        f"Current loyalty points: {customer_points}.",
        f"Points earned this order: {earned_points}.",
    ]

    if free_delivery_eligible:
        reasons.append("Customer qualifies for free-delivery benefits.")
    if reward_value > 0:
        reasons.append(f"Estimated loyalty value available: {reward_value}.")

    return {
        "customer_month_orders": customer_month_orders,
        "current_points": customer_points,
        "points_earned": earned_points,
        "projected_points": projected_points,
        "tier": tier,
        "discount_rate": discount_rate,
        "reward_value": reward_value,
        "free_delivery_eligible": free_delivery_eligible,
        "retention_score": round(min(1.0, 0.2 + (customer_month_orders * 0.03)), 2),
        "reasons": reasons,
    }


def customer_loyalty(payload: Dict[str, Any]) -> Dict[str, Any]:
    return evaluate(payload)


def customer_loyalty_engine(payload: Dict[str, Any]) -> Dict[str, Any]:
    return evaluate(payload)