from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from statistics import mean
from typing import Any, Dict, List

from backend.fair_offer_engine import classify_offer
from backend.sample_observations import load_sample_observations


@dataclass
class SessionMetrics:
    total_observations: int
    accepted_count: int
    declined_count: int
    borderline_count: int
    avg_offered_pay: float
    avg_offered_miles: float
    avg_economic_miles: float
    avg_pay_per_offered_mile: float
    avg_pay_per_economic_mile: float
    avg_modeled_total_minutes: float
    avg_effective_hourly: float
    avg_minimum_driver_pay: float
    weak_economic_mile_count: int
    pressure_seen_count: int
    below_minimum_driver_pay_count: int
    hard_under_minimum_pay_decline_count: int
    weak_effective_hourly_count: int
    borderline_effective_hourly_count: int


def calculate_session_metrics() -> Dict[str, Any]:
    observations = load_sample_observations()
    results: List[Dict[str, Any]] = [classify_offer(obs) for obs in observations]

    accepted_count = sum(1 for r in results if r["action"] == "accept")
    declined_count = sum(1 for r in results if r["action"] == "decline")
    borderline_count = sum(1 for r in results if r["action"] == "borderline")

    weak_economic_mile_count = sum(
        1 for r in results if "weak_economic_mile" in r.get("reasons", [])
    )
    pressure_seen_count = sum(
        1 for r in results if "acceptance_rate_pressure_seen" in r.get("reasons", [])
    )
    below_minimum_driver_pay_count = sum(
        1 for r in results if "below_minimum_driver_pay" in r.get("reasons", [])
    )
    hard_under_minimum_pay_decline_count = sum(
        1 for r in results if "hard_under_minimum_pay_decline" in r.get("reasons", [])
    )
    weak_effective_hourly_count = sum(
        1 for r in results if "weak_effective_hourly" in r.get("reasons", [])
    )
    borderline_effective_hourly_count = sum(
        1 for r in results if "borderline_effective_hourly" in r.get("reasons", [])
    )

    metrics = SessionMetrics(
        total_observations=len(observations),
        accepted_count=accepted_count,
        declined_count=declined_count,
        borderline_count=borderline_count,
        avg_offered_pay=round(mean(float(o.offered_pay_total) for o in observations), 2),
        avg_offered_miles=round(mean(float(o.offered_miles) for o in observations), 2),
        avg_economic_miles=round(mean(float(r["economic_miles"]) for r in results), 2),
        avg_pay_per_offered_mile=round(
            mean(float(r["pay_per_offered_mile"]) for r in results), 2
        ),
        avg_pay_per_economic_mile=round(
            mean(float(r["pay_per_economic_mile"]) for r in results), 2
        ),
        avg_modeled_total_minutes=round(
            mean(float(r["modeled_total_minutes"]) for r in results), 2
        ),
        avg_effective_hourly=round(
            mean(float(r["effective_hourly"]) for r in results), 2
        ),
        avg_minimum_driver_pay=round(
            mean(float(r["minimum_driver_pay"]) for r in results), 2
        ),
        weak_economic_mile_count=weak_economic_mile_count,
        pressure_seen_count=pressure_seen_count,
        below_minimum_driver_pay_count=below_minimum_driver_pay_count,
        hard_under_minimum_pay_decline_count=hard_under_minimum_pay_decline_count,
        weak_effective_hourly_count=weak_effective_hourly_count,
        borderline_effective_hourly_count=borderline_effective_hourly_count,
    )

    return {
        "metrics": asdict(metrics),
        "results": results,
    }


if __name__ == "__main__":
    payload = calculate_session_metrics()
    print(json.dumps(payload, indent=2))