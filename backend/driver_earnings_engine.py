from __future__ import annotations

from typing import Any, Dict, List

from backend.settlement_engine import evaluate as evaluate_settlement


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def calculate_hourly_income(orders: List[Dict[str, Any]], hours: float) -> float:
    """
    Legacy-compatible hourly income calculation.

    Prefers reserve-aware settlement output if present.
    Falls back to dispatch pay_per_economic_mile * economic_miles.
    """
    total_available_balance = 0.0

    for order in orders:
        if "driver_available_balance" in order:
            total_available_balance += _to_float(order.get("driver_available_balance"))
            continue

        if "driver_gross_total" in order and "reserve_total" in order:
            gross_total = _to_float(order.get("driver_gross_total"))
            reserve_total = _to_float(order.get("reserve_total"))
            total_available_balance += gross_total - reserve_total
            continue

        dispatch = order.get("dispatch", {}) or {}
        pay_per_economic_mile = _to_float(dispatch.get("pay_per_economic_mile"))
        economic_miles = _to_float(dispatch.get("economic_miles"))
        total_available_balance += pay_per_economic_mile * economic_miles

    hours_value = _to_float(hours, 0.0)
    if hours_value <= 0:
        return 0.0

    return total_available_balance / hours_value


def summarize_driver_order(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Produce a reserve-aware driver earnings view for a single order.

    Expected payload keys:
    - order_id
    - driver_id
    - merchant_id
    - order_value
    - tip
    - offered_payout
    - rolling_30_day_miles

    Optional:
    - driver_tax_rate
    - sales_tax_rate
    - commission_rate
    - processing_rate
    - fixed_processing_fee
    """
    settlement = evaluate_settlement(payload)

    return {
        "order_id": settlement["order_id"],
        "driver_id": settlement["driver_id"],
        "merchant_id": settlement["merchant_id"],
        "driver_tier": settlement["driver_tier"],
        "rolling_30_day_miles": settlement["rolling_30_day_miles"],
        "driver_gross_total": settlement["driver_gross_total"],
        "maintenance_reserve": settlement["maintenance_reserve"],
        "insurance_reserve": settlement["insurance_reserve"],
        "reserve_total": settlement["reserve_total"],
        "driver_available_balance": settlement["driver_available_balance"],
        "estimated_tax": settlement["estimated_tax"],
        "net_after_tax_estimate": settlement["net_after_tax_estimate"],
        "settlement_status": settlement["settlement_status"],
    }


def driver_shift_summary(
    orders: List[Dict[str, Any]],
    hours: float,
) -> Dict[str, Any]:
    """
    Shift-level reserve-aware summary.

    Accepts either:
    - already processed reserve-aware order rows, or
    - raw order payloads that can be passed into settlement_engine.evaluate()
    """
    processed_orders: List[Dict[str, Any]] = []

    for order in orders:
        if "driver_available_balance" in order and "driver_gross_total" in order:
            processed_orders.append(order)
        else:
            processed_orders.append(summarize_driver_order(order))

    total_gross = round(
        sum(_to_float(order.get("driver_gross_total")) for order in processed_orders),
        2,
    )
    total_maintenance_reserve = round(
        sum(_to_float(order.get("maintenance_reserve")) for order in processed_orders),
        2,
    )
    total_insurance_reserve = round(
        sum(_to_float(order.get("insurance_reserve")) for order in processed_orders),
        2,
    )
    total_reserve = round(
        sum(_to_float(order.get("reserve_total")) for order in processed_orders),
        2,
    )
    total_available_balance = round(
        sum(_to_float(order.get("driver_available_balance")) for order in processed_orders),
        2,
    )
    total_estimated_tax = round(
        sum(_to_float(order.get("estimated_tax")) for order in processed_orders),
        2,
    )
    total_net_after_tax_estimate = round(
        sum(_to_float(order.get("net_after_tax_estimate")) for order in processed_orders),
        2,
    )

    hourly_income = round(calculate_hourly_income(processed_orders, hours), 2)

    if hourly_income >= 25:
        satisfaction = 0.90
    elif hourly_income >= 20:
        satisfaction = 0.75
    elif hourly_income >= 15:
        satisfaction = 0.55
    else:
        satisfaction = 0.35

    tier_distribution: Dict[str, int] = {}
    for order in processed_orders:
        tier = str(order.get("driver_tier", "Casual"))
        tier_distribution[tier] = tier_distribution.get(tier, 0) + 1

    return {
        "orders_completed": len(processed_orders),
        "hours_worked": round(_to_float(hours), 2),
        "driver_gross_total": total_gross,
        "maintenance_reserve": total_maintenance_reserve,
        "insurance_reserve": total_insurance_reserve,
        "reserve_total": total_reserve,
        "driver_available_balance": total_available_balance,
        "estimated_tax": total_estimated_tax,
        "net_after_tax_estimate": total_net_after_tax_estimate,
        "hourly_income": hourly_income,
        "satisfaction": satisfaction,
        "tier_distribution": tier_distribution,
        "orders": processed_orders,
    }


def earnings_engine(
    orders: List[Dict[str, Any]],
    hours: float,
) -> Dict[str, Any]:
    return driver_shift_summary(orders, hours)


if __name__ == "__main__":
    demo_orders = [
        {
            "order_id": "ORD-1",
            "driver_id": "DRV-1",
            "merchant_id": "M-1",
            "order_value": 30,
            "tip": 5,
            "offered_payout": 8,
            "rolling_30_day_miles": 2600,
        },
        {
            "order_id": "ORD-2",
            "driver_id": "DRV-1",
            "merchant_id": "M-2",
            "order_value": 22,
            "tip": 3,
            "offered_payout": 7,
            "rolling_30_day_miles": 2600,
        },
    ]

    print(driver_shift_summary(demo_orders, 2.5))