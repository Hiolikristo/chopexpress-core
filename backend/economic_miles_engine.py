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


def safe_div(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def total_burden_minutes(observation: Any) -> float:
    merchant_wait_minutes = _to_float(getattr(observation, "merchant_wait_minutes", 0.0))
    forced_return_minutes_estimate = _to_float(
        getattr(observation, "forced_return_minutes_estimate", 0.0)
    )
    extra_delay_minutes = _to_float(getattr(observation, "extra_delay_minutes", 0.0))

    return round(
        merchant_wait_minutes + forced_return_minutes_estimate + extra_delay_minutes,
        2,
    )


def calculate_economic_miles(observation: Any) -> float:
    actual_trip_miles = _to_float(getattr(observation, "actual_trip_miles", 0.0))
    offered_miles = _to_float(getattr(observation, "offered_miles", 0.0))
    return_miles_estimate = _to_float(getattr(observation, "return_miles_estimate", 0.0))
    zone_exit_miles = _to_float(getattr(observation, "zone_exit_miles", 0.0))
    deadhead_miles = _to_float(getattr(observation, "deadhead_miles", 0.0))

    base_miles = actual_trip_miles if actual_trip_miles > 0 else offered_miles

    economic_miles = (
        base_miles
        + return_miles_estimate
        + zone_exit_miles
        + deadhead_miles
    )

    return round(economic_miles, 2)


def pay_per_economic_mile(pay: float, economic_miles: float) -> float:
    return round(safe_div(_to_float(pay), _to_float(economic_miles)), 2)


def pay_per_offered_mile(pay: float, offered_miles: float) -> float:
    return round(safe_div(_to_float(pay), _to_float(offered_miles)), 2)


def enrich_observation_with_economic_miles(observation: Any) -> Dict[str, float]:
    economic_miles = calculate_economic_miles(observation)
    burden_minutes = total_burden_minutes(observation)
    offered_pay_total = _to_float(getattr(observation, "offered_pay_total", 0.0))
    offered_miles = _to_float(getattr(observation, "offered_miles", 0.0))

    return {
        "economic_miles": economic_miles,
        "burden_minutes": burden_minutes,
        "pay_per_economic_mile": pay_per_economic_mile(offered_pay_total, economic_miles),
        "pay_per_offered_mile": pay_per_offered_mile(offered_pay_total, offered_miles),
    }


if __name__ == "__main__":
    class DemoObservation:
        offered_pay_total = 7.30
        offered_miles = 5.4
        actual_trip_miles = 5.4
        return_miles_estimate = 1.5
        zone_exit_miles = 0.8
        deadhead_miles = 0.0
        merchant_wait_minutes = 0.0
        forced_return_minutes_estimate = 0.0
        extra_delay_minutes = 0.0

    demo = DemoObservation()
    print(enrich_observation_with_economic_miles(demo))