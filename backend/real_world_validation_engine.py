from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from backend.fair_offer_engine import classify_offer
from backend.sample_observations import load_sample_observations


OUTPUT_DIR = Path("sim/output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def actual_driver_action(observation: Any) -> str:
    if bool(getattr(observation, "accepted", False)):
        return "accepted"
    if bool(getattr(observation, "declined", False)):
        return "declined"
    return "unknown"


def validate_single(scored: Dict[str, Any], observation: Any) -> Dict[str, Any]:
    actual_action = actual_driver_action(observation)
    recommended_action = scored.get("action", "unknown")

    hindsight_label = "unknown"
    validation_score = 50.0
    notes: List[str] = []

    if actual_action == "accepted":
        if recommended_action == "accept":
            hindsight_label = "good_accept"
            validation_score = 100.0
            notes.append("Driver accepted and engine also recommended accept.")
        elif recommended_action == "borderline":
            hindsight_label = "borderline_accept"
            validation_score = 70.0
            notes.append("Driver accepted a borderline offer.")
        else:
            hindsight_label = "bad_accept"
            validation_score = 30.0
            notes.append("Driver accepted an offer engine marked decline.")

    elif actual_action == "declined":
        if recommended_action == "decline":
            hindsight_label = "good_decline"
            validation_score = 100.0
            notes.append("Driver declined and engine also recommended decline.")
        elif recommended_action == "borderline":
            hindsight_label = "borderline_decline"
            validation_score = 70.0
            notes.append("Driver declined a borderline offer.")
        else:
            hindsight_label = "missed_good_offer"
            validation_score = 40.0
            notes.append("Driver may have passed on a viable offer.")

    else:
        notes.append("Actual driver action unknown.")

    if bool(getattr(observation, "merchant_delay_flag", False)):
        notes.append("Merchant delay contributed to realized outcome.")

    if bool(getattr(observation, "navigate_back_to_zone_flag", False)):
        notes.append("Forced zone reposition burden detected.")

    if bool(getattr(observation, "app_error_flag", False)):
        notes.append("App error friction detected.")

    return {
        "observation_id": getattr(observation, "observation_id", "unknown"),
        "session_id": getattr(observation, "session_id", "unknown"),
        "merchant_name": getattr(observation, "merchant_name", "unknown"),
        "zone": getattr(observation, "zone", "unknown"),
        "recommended_action": recommended_action,
        "actual_driver_action": actual_action,
        "hindsight_label": hindsight_label,
        "validation_score": round(validation_score, 2),
        "offered_pay_total": round(float(getattr(observation, "offered_pay_total", 0.0) or 0.0), 2),
        "offered_miles": round(float(getattr(observation, "offered_miles", 0.0) or 0.0), 2),
        "economic_miles": round(float(scored.get("economic_miles", 0.0) or 0.0), 2),
        "burden_minutes": round(float(scored.get("burden_minutes", 0.0) or 0.0), 2),
        "modeled_total_minutes": round(float(scored.get("modeled_total_minutes", 0.0) or 0.0), 2),
        "effective_hourly": round(float(scored.get("effective_hourly", 0.0) or 0.0), 2),
        "minimum_driver_pay": round(float(scored.get("minimum_driver_pay", 0.0) or 0.0), 2),
        "pay_gap": round(float(scored.get("pay_gap", 0.0) or 0.0), 2),
        "score": round(float(scored.get("score", 0.0) or 0.0), 2),
        "reasons": scored.get("reasons", []),
        "notes": notes,
    }


def summarize_validations(validations: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(validations)
    if total == 0:
        return {
            "total_observations": 0,
            "avg_validation_score": 0.0,
            "good_accept_count": 0,
            "good_decline_count": 0,
            "bad_accept_count": 0,
            "missed_good_offer_count": 0,
            "borderline_accept_count": 0,
            "borderline_decline_count": 0,
        }

    def count(label: str) -> int:
        return sum(1 for item in validations if item.get("hindsight_label") == label)

    avg_score = sum(float(item.get("validation_score", 0.0)) for item in validations) / total

    return {
        "total_observations": total,
        "avg_validation_score": round(avg_score, 2),
        "good_accept_count": count("good_accept"),
        "good_decline_count": count("good_decline"),
        "bad_accept_count": count("bad_accept"),
        "missed_good_offer_count": count("missed_good_offer"),
        "borderline_accept_count": count("borderline_accept"),
        "borderline_decline_count": count("borderline_decline"),
    }


def write_validation_report(payload: Dict[str, Any]) -> str:
    report_path = OUTPUT_DIR / "real_world_validation_report.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return str(report_path)


def main() -> None:
    observations = load_sample_observations()
    validations: List[Dict[str, Any]] = []

    for obs in observations:
        scored = classify_offer(obs)
        validation = validate_single(scored, obs)
        validations.append(validation)

    payload = {
        "summary": summarize_validations(validations),
        "results": validations,
    }

    print(json.dumps(payload, indent=2))

    report_path = write_validation_report(payload)
    print(f"\nValidation report written to: {report_path}")


if __name__ == "__main__":
    main()