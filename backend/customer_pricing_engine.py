from __future__ import annotations

from typing import Any, Dict


def _to_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()
    if text == "":
        return default

    try:
        return float(text)
    except (TypeError, ValueError):
        return default


def _to_int(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)

    text = str(value).strip()
    if text == "":
        return default

    try:
        return int(float(text))
    except (TypeError, ValueError):
        return default


def safe_div(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return numerator / denominator


def short_trip_customer_base(economic_miles: float) -> float:
    """
    Customer-facing base floor by economic miles.
    This is NOT final retail price philosophy forever.
    It is V1 fairness pricing floor logic.
    """
    if economic_miles <= 2.5:
        return 8.49
    if economic_miles <= 3.5:
        return 9.29
    if economic_miles <= 5.0:
        return 10.49
    return 0.0


def recommended_customer_base_price(observation: Any) -> Dict[str, float]:
    """
    Produces a customer-visible recommended base charge before optional tip.
    This should be enough to cover fair driver economics plus platform margin.
    """

    offered_pay_total = _to_float(getattr(observation, "offered_pay_total", 0.0))
    economic_miles = _to_float(getattr(observation, "economic_miles", 0.0))
    burden_minutes = _to_float(getattr(observation, "burden_minutes", 0.0))
    modeled_total_minutes = _to_float(getattr(observation, "modeled_total_minutes", 0.0))
    minimum_driver_pay = _to_float(getattr(observation, "minimum_driver_pay", 0.0))
    stack_count = _to_int(getattr(observation, "stack_count", 1), 1)

    zone_exit_miles = _to_float(getattr(observation, "zone_exit_miles", 0.0))
    return_miles_estimate = _to_float(getattr(observation, "return_miles_estimate", 0.0))
    hotspot_wait_minutes = _to_float(getattr(observation, "hotspot_wait_minutes", 0.0))

    short_floor = short_trip_customer_base(economic_miles)

    # Base fairness layer: driver minimum + platform operating margin
    platform_margin = 2.25

    # Mileage-based customer pricing floor
    mileage_component = economic_miles * 1.85

    # Time friction the customer side should partially absorb
    burden_component = burden_minutes * 0.18

    # Longer modeled time creates more drag on driver productivity
    time_component = 0.0
    if modeled_total_minutes > 20:
        time_component = (modeled_total_minutes - 20) * 0.12

    # Zone/reposition penalty if order pushes driver out of useful territory
    reposition_component = 0.0
    reposition_component += zone_exit_miles * 0.35
    reposition_component += return_miles_estimate * 0.20

    # Hotspot idle drag
    hotspot_component = 0.0
    if hotspot_wait_minutes >= 10:
        hotspot_component = (hotspot_wait_minutes - 10) * 0.10

    # Stack complexity fee
    stack_component = 0.0
    if stack_count >= 2:
        stack_component = 0.75 * (stack_count - 1)

    raw_customer_base = max(
        short_floor,
        minimum_driver_pay
        + platform_margin
        + burden_component
        + time_component
        + reposition_component
        + hotspot_component
        + stack_component,
        mileage_component + burden_component + platform_margin,
    )

    recommended_base = round(raw_customer_base, 2)
    gap_vs_current_offer = round(recommended_base - offered_pay_total, 2)

    return {
        "recommended_customer_base": recommended_base,
        "short_trip_floor": round(short_floor, 2),
        "platform_margin": round(platform_margin, 2),
        "mileage_component": round(mileage_component, 2),
        "burden_component": round(burden_component, 2),
        "time_component": round(time_component, 2),
        "reposition_component": round(reposition_component, 2),
        "hotspot_component": round(hotspot_component, 2),
        "stack_component": round(stack_component, 2),
        "gap_vs_current_offer": gap_vs_current_offer,
    }


if __name__ == "__main__":
    class DemoObservation:
        offered_pay_total = 7.10
        economic_miles = 7.10
        burden_minutes = 2.0
        modeled_total_minutes = 28.0
        minimum_driver_pay = 9.99
        stack_count = 1
        zone_exit_miles = 0.8
        return_miles_estimate = 1.5
        hotspot_wait_minutes = 0.0

    demo = DemoObservation()
    print(recommended_customer_base_price(demo))