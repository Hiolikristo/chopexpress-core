from __future__ import annotations

import csv
import json
import os
from typing import Any, Dict, List


INPUT_REAL_RUNS = os.path.join("sim", "input", "evidence", "real_driving_log.csv")
OUTPUT_GAS_REPORT = os.path.join("sim", "output", "gas_intelligence_report.json")


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


def _safe_div(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _ensure_parent_dir(path: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def load_real_runs(path: str = INPUT_REAL_RUNS) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing real driving log: {path}")

    rows: List[Dict[str, Any]] = []

    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []

        required = ["date", "platform", "zone", "miles", "hours", "fuel_cost", "other_cost"]
        missing = [col for col in required if col not in fieldnames]
        if missing:
            raise ValueError(f"real_driving_log.csv missing columns: {missing}")

        for raw in reader:
            if not raw:
                continue

            rows.append(
                {
                    "date": str(raw.get("date", "")).strip(),
                    "platform": str(raw.get("platform", "")).strip(),
                    "zone": str(raw.get("zone", "")).strip(),
                    "miles": _to_float(raw.get("miles")),
                    "hours": _to_float(raw.get("hours")),
                    "fuel_cost": _to_float(raw.get("fuel_cost")),
                    "other_cost": _to_float(raw.get("other_cost")),
                }
            )

    if not rows:
        raise ValueError("No real driving rows found")

    return rows


def build_gas_report(real_runs: List[Dict[str, Any]]) -> Dict[str, Any]:
    total_runs = len(real_runs)
    total_miles = sum(_to_float(r["miles"]) for r in real_runs)
    total_hours = sum(_to_float(r["hours"]) for r in real_runs)
    total_fuel_cost = sum(_to_float(r["fuel_cost"]) for r in real_runs)
    total_other_cost = sum(_to_float(r["other_cost"]) for r in real_runs)

    avg_fuel_cost_per_run = _safe_div(total_fuel_cost, total_runs)
    fuel_cost_per_mile = _safe_div(total_fuel_cost, total_miles)
    fuel_cost_per_hour = _safe_div(total_fuel_cost, total_hours)

    zone_breakdown: Dict[str, Dict[str, float]] = {}

    for row in real_runs:
        zone = row["zone"] or "unknown"
        if zone not in zone_breakdown:
            zone_breakdown[zone] = {
                "runs": 0,
                "miles": 0.0,
                "hours": 0.0,
                "fuel_cost": 0.0,
                "other_cost": 0.0,
            }

        zone_breakdown[zone]["runs"] += 1
        zone_breakdown[zone]["miles"] += _to_float(row["miles"])
        zone_breakdown[zone]["hours"] += _to_float(row["hours"])
        zone_breakdown[zone]["fuel_cost"] += _to_float(row["fuel_cost"])
        zone_breakdown[zone]["other_cost"] += _to_float(row["other_cost"])

    normalized_zone_breakdown: Dict[str, Dict[str, float]] = {}
    for zone, values in zone_breakdown.items():
        miles = values["miles"]
        hours = values["hours"]
        fuel_cost = values["fuel_cost"]

        normalized_zone_breakdown[zone] = {
            "runs": values["runs"],
            "miles": round(miles, 2),
            "hours": round(hours, 2),
            "fuel_cost": round(fuel_cost, 2),
            "other_cost": round(values["other_cost"], 2),
            "fuel_cost_per_mile": round(_safe_div(fuel_cost, miles), 4),
            "fuel_cost_per_hour": round(_safe_div(fuel_cost, hours), 4),
        }

    cheapest_zone = None
    cheapest_value = None
    most_expensive_zone = None
    most_expensive_value = None

    for zone, values in normalized_zone_breakdown.items():
        cost_per_mile = values["fuel_cost_per_mile"]
        if cheapest_value is None or cost_per_mile < cheapest_value:
            cheapest_zone = zone
            cheapest_value = cost_per_mile
        if most_expensive_value is None or cost_per_mile > most_expensive_value:
            most_expensive_zone = zone
            most_expensive_value = cost_per_mile

    return {
        "runs_loaded": total_runs,
        "total_miles": round(total_miles, 2),
        "total_hours": round(total_hours, 2),
        "total_fuel_cost": round(total_fuel_cost, 2),
        "total_other_cost": round(total_other_cost, 2),
        "avg_fuel_cost_per_run": round(avg_fuel_cost_per_run, 4),
        "fuel_cost_per_mile": round(fuel_cost_per_mile, 4),
        "fuel_cost_per_hour": round(fuel_cost_per_hour, 4),
        "cheapest_zone_by_fuel_per_mile": cheapest_zone,
        "most_expensive_zone_by_fuel_per_mile": most_expensive_zone,
        "zone_breakdown": normalized_zone_breakdown,
    }


def save_report(report: Dict[str, Any], path: str = OUTPUT_GAS_REPORT) -> None:
    _ensure_parent_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)


def main() -> Dict[str, Any]:
    print("Running gas intelligence analysis...")

    real_runs = load_real_runs(INPUT_REAL_RUNS)
    report = build_gas_report(real_runs)
    save_report(report, OUTPUT_GAS_REPORT)

    print(f"Gas intelligence report written: {OUTPUT_GAS_REPORT}")
    return report


if __name__ == "__main__":
    main()