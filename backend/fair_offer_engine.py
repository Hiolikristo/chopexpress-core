from __future__ import annotations

from typing import Any, Dict, List

from backend.economic_miles_engine import (
    calculate_economic_miles,
    total_burden_minutes,
)
from backend.order_observation_schema import OrderObservation


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
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 2)


def pay_per_offered_mile(obs: OrderObservation) -> float:
    return safe_div(_to_float(obs.offered_pay_total), _to_float(obs.offered_miles))


def pay_per_economic_mile(obs: OrderObservation) -> float:
    economic_miles = calculate_economic_miles(obs)
    return safe_div(_to_float(obs.offered_pay_total), economic_miles)


def estimate_modeled_total_minutes(obs: OrderObservation) -> float:
    drive_minutes = _to_float(getattr(obs, "drive_minutes_estimate", 0.0))
    burden_minutes = total_burden_minutes(obs)

    offered_miles = _to_float(getattr(obs, "offered_miles", 0.0))
    return_miles_estimate = _to_float(getattr(obs, "return_miles_estimate", 0.0))
    zone_exit_miles = _to_float(getattr(obs, "zone_exit_miles", 0.0))
    deadhead_miles = _to_float(getattr(obs, "deadhead_miles", 0.0))

    extra_miles = return_miles_estimate + zone_exit_miles + deadhead_miles

    # Fallback if drive time is missing or too low
    if drive_minutes <= 0:
        drive_minutes = offered_miles * 3.0

    # Reposition / return burden translated into time
    extra_miles_minutes = extra_miles * 2.8

    modeled_total = drive_minutes + burden_minutes + extra_miles_minutes
    return round(modeled_total, 2)


def estimate_effective_hourly(obs: OrderObservation) -> float:
    modeled_total_minutes = estimate_modeled_total_minutes(obs)
    offered_pay_total = _to_float(getattr(obs, "offered_pay_total", 0.0))

    if modeled_total_minutes <= 0:
        return 0.0

    hourly = offered_pay_total / (modeled_total_minutes / 60.0)
    return round(hourly, 2)


def minimum_driver_pay(obs: OrderObservation) -> float:
    economic_miles = calculate_economic_miles(obs)
    modeled_total_minutes = estimate_modeled_total_minutes(obs)
    burden_minutes = total_burden_minutes(obs)

    short_trip_floor = 0.0
    if economic_miles <= 2.5:
        short_trip_floor = 7.50
    elif economic_miles <= 3.5:
        short_trip_floor = 8.50
    elif economic_miles <= 5.0:
        short_trip_floor = 10.00

    mileage_component = economic_miles * 1.55
    time_component = modeled_total_minutes * 0.10
    burden_component = burden_minutes * 0.15

    minimum_pay = max(short_trip_floor, mileage_component + time_component + burden_component)
    return round(minimum_pay, 2)


def classify_offer(obs: OrderObservation) -> Dict[str, Any]:
    reasons: List[str] = []

    offered_pay_total = _to_float(getattr(obs, "offered_pay_total", 0.0))
    offered_ppm = pay_per_offered_mile(obs)
    economic_ppm = pay_per_economic_mile(obs)
    economic_miles = calculate_economic_miles(obs)
    burden_minutes = total_burden_minutes(obs)
    modeled_total_minutes = estimate_modeled_total_minutes(obs)
    effective_hourly = estimate_effective_hourly(obs)
    minimum_pay_needed = minimum_driver_pay(obs)
    pay_gap = round(offered_pay_total - minimum_pay_needed, 2)

    score = 100.0

    # Minimum pay floor
    if offered_pay_total < minimum_pay_needed - 2.0:
        score -= 38
        reasons.append("hard_under_minimum_pay_decline")
    elif offered_pay_total < minimum_pay_needed:
        score -= 22
        reasons.append("below_minimum_driver_pay")
    elif offered_pay_total < minimum_pay_needed + 0.75:
        score -= 8
        reasons.append("near_minimum_driver_pay")

    # Economic mile logic
    if economic_ppm < 1.10:
        score -= 26
        reasons.append("weak_economic_mile")
    elif economic_ppm < 1.35:
        score -= 12
        reasons.append("borderline_economic_mile")

    # Offered mile logic
    if offered_ppm < 1.00:
        score -= 14
        reasons.append("weak_offered_mile")
    elif offered_ppm < 1.25:
        score -= 7
        reasons.append("borderline_offered_mile")

    # Effective hourly logic
    if effective_hourly < 18.0:
        score -= 22
        reasons.append("weak_effective_hourly")
    elif effective_hourly < 23.0:
        score -= 8
        reasons.append("borderline_effective_hourly")

    # Burden logic
    if burden_minutes >= 15:
        score -= 16
        reasons.append("high_burden_minutes")
    elif burden_minutes >= 8:
        score -= 8
        reasons.append("moderate_burden_minutes")

    # Stack logic
    if _to_float(getattr(obs, "stack_count", 1)) >= 2 and economic_ppm < 1.50:
        score -= 10
        reasons.append("stack_without_enough_density")

    # Hotspot drag
    if bool(getattr(obs, "was_hotspot_wait", False)) and _to_float(
        getattr(obs, "hotspot_wait_minutes", 0.0)
    ) >= 10:
        score -= 8
        reasons.append("hotspot_wait_drag")

    # Zone / return burden evidence
    if _to_float(getattr(obs, "return_miles_estimate", 0.0)) >= 3:
        reasons.append("proof_return_burden")

    if _to_float(getattr(obs, "zone_exit_miles", 0.0)) >= 2:
        score -= 6
        reasons.append("zone_exit_penalty")

    if bool(getattr(obs, "acceptance_rate_pressure_seen", False)):
        reasons.append("acceptance_rate_pressure_seen")

    score = max(0.0, round(score, 1))

    if score >= 85:
        action = "accept"
    elif score >= 60:
        action = "borderline"
    else:
        action = "decline"

    return {
        "score": score,
        "action": action,
        "pay_per_offered_mile": round(offered_ppm, 2),
        "pay_per_economic_mile": round(economic_ppm, 2),
        "economic_miles": round(economic_miles, 2),
        "burden_minutes": round(burden_minutes, 2),
        "modeled_total_minutes": round(modeled_total_minutes, 2),
        "effective_hourly": round(effective_hourly, 2),
        "minimum_driver_pay": round(minimum_pay_needed, 2),
        "pay_gap": round(pay_gap, 2),
        "reasons": reasons,
    }


if __name__ == "__main__":
    class DemoObservation:
        offered_pay_total = 7.10
        offered_miles = 5.8
        actual_trip_miles = 5.8
        return_miles_estimate = 1.5
        zone_exit_miles = 0.8
        deadhead_miles = 0.0
        merchant_wait_minutes = 0.0
        forced_return_minutes_estimate = 0.0
        extra_delay_minutes = 2.0
        drive_minutes_estimate = 16.0
        stack_count = 1
        acceptance_rate_pressure_seen = True
        was_hotspot_wait = False
        hotspot_wait_minutes = 0.0

    demo = DemoObservation()
    print(classify_offer(demo))