from __future__ import annotations

from typing import Dict, Any, List


def _safe_div(a: float, b: float) -> float:
    if b == 0:
        return 0.0
    return round(a / b, 2)


def _driver_accepts(order: Dict[str, Any]) -> bool:
    """
    V1 fairness gate:
    - all core orders are acceptable if pay density is good
    - extended/edge must pass stronger thresholds
    """

    miles = float(order.get("miles", 0.0))
    economic_miles = float(order.get("economic_miles", miles))
    offer_pay = float(order.get("offer_pay", order.get("gross_pay", 0.0)))
    radius_band = order.get("radius_band", "core")

    pay_per_mile = _safe_div(offer_pay, economic_miles)

    if radius_band == "core":
        return pay_per_mile >= 1.70
    if radius_band == "extended":
        return pay_per_mile >= 1.85
    if radius_band == "edge":
        return pay_per_mile >= 2.00

    return False


def build_simulation_summary(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    orders: List[Dict[str, Any]] = snapshot.get("orders", [])
    drivers: List[Dict[str, Any]] = snapshot.get("drivers", [])
    merchants: List[Dict[str, Any]] = snapshot.get("merchants", [])

    accepted_orders: List[Dict[str, Any]] = []
    rejected_orders: List[Dict[str, Any]] = []

    for order in orders:
        if _driver_accepts(order):
            accepted_orders.append(order)
        else:
            rejected_orders.append(order)

    total_orders = len(orders)
    accepted_count = len(accepted_orders)
    rejected_count = len(rejected_orders)

    total_offer_pay = round(sum(order.get("offer_pay", 0.0) for order in accepted_orders), 2)
    total_miles = round(sum(order.get("miles", 0.0) for order in accepted_orders), 2)
    total_economic_miles = round(sum(order.get("economic_miles", 0.0) for order in accepted_orders), 2)

    avg_offer_pay = _safe_div(total_offer_pay, accepted_count) if accepted_count else 0.0
    avg_miles = _safe_div(total_miles, accepted_count) if accepted_count else 0.0
    avg_economic_miles = _safe_div(total_economic_miles, accepted_count) if accepted_count else 0.0
    avg_pay_per_order = avg_offer_pay
    avg_pay_per_mile = _safe_div(total_offer_pay, total_miles) if total_miles else 0.0
    avg_pay_per_economic_mile = _safe_div(total_offer_pay, total_economic_miles) if total_economic_miles else 0.0

    approval_rate = _safe_div(accepted_count * 100.0, total_orders) if total_orders else 0.0

    return {
        "status": "ok",
        "driver_count": len(drivers),
        "merchant_count": len(merchants),
        "order_count": total_orders,
        "accepted_orders": accepted_count,
        "rejected_orders": rejected_count,
        "approval_rate": approval_rate,
        "total_offer_pay": total_offer_pay,
        "total_miles": total_miles,
        "total_economic_miles": total_economic_miles,
        "avg_pay_per_order": avg_pay_per_order,
        "avg_miles_per_order": avg_miles,
        "avg_economic_miles_per_order": avg_economic_miles,
        "avg_pay_per_mile": avg_pay_per_mile,
        "avg_pay_per_economic_mile": avg_pay_per_economic_mile,
        "radius_band_counts": snapshot.get("radius_band_counts", {}),
    }


def run_market_simulation() -> Dict[str, Any]:
    from columbus_market_engine import ColumbusMarketEngine

    engine = ColumbusMarketEngine(seed=42)

    snapshot = engine.build_market_snapshot(
        driver_count=25,
        merchant_count=40,
        base_orders_per_hour=60,
        hour=12,
    )

    summary = build_simulation_summary(snapshot)

    return {
        "snapshot": snapshot,
        "summary": summary,
    }


def main() -> Dict[str, Any]:
    return run_market_simulation()