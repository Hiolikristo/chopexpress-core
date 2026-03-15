import csv
import json
import os
from typing import Dict, List


def load_market_log(path: str) -> List[Dict]:
    rows: List[Dict] = []

    if not os.path.exists(path):
        return rows

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    return rows


def _to_float(value, default=0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _to_int(value, default=0) -> int:
    try:
        return int(float(value))
    except Exception:
        return default


def build_zone_heatmap(rows: List[Dict]) -> List[Dict]:
    zone_map: Dict[str, Dict] = {}

    for row in rows:
        zone = (row.get("pickup_zone") or row.get("zone") or "").strip()
        if not zone:
            continue

        status = (row.get("status") or "").strip().lower()
        trip_miles = _to_float(row.get("trip_miles", 0))
        earnings = _to_float(row.get("base_pay", 0)) + _to_float(row.get("expected_tip", 0))
        ppm = _to_float(row.get("effective_pay_per_mile", 0))
        hourly = _to_float(row.get("effective_hourly_rate", 0))
        pressure = _to_float(row.get("pressure_score", 0))
        surge = _to_float(row.get("surge_multiplier", 1.0))

        if zone not in zone_map:
            zone_map[zone] = {
                "zone": zone,
                "orders": 0,
                "completed_orders": 0,
                "unclaimed_orders": 0,
                "total_earnings": 0.0,
                "total_miles": 0.0,
                "ppm_values": [],
                "hourly_values": [],
                "pressure_values": [],
                "surge_values": [],
            }

        bucket = zone_map[zone]
        bucket["orders"] += 1
        bucket["total_miles"] += trip_miles
        bucket["pressure_values"].append(pressure)
        bucket["surge_values"].append(surge)

        if status == "completed":
            bucket["completed_orders"] += 1
            bucket["total_earnings"] += earnings
            if ppm > 0:
                bucket["ppm_values"].append(ppm)
            if hourly > 0:
                bucket["hourly_values"].append(hourly)
        else:
            bucket["unclaimed_orders"] += 1

    results: List[Dict] = []

    for zone, data in zone_map.items():
        orders = data["orders"]
        completed = data["completed_orders"]
        total_earnings = data["total_earnings"]
        total_miles = data["total_miles"]

        completion_rate = completed / orders if orders else 0.0
        avg_pay_per_order = total_earnings / completed if completed else 0.0
        avg_pay_per_mile = total_earnings / total_miles if total_miles else 0.0
        avg_effective_ppm = (
            sum(data["ppm_values"]) / len(data["ppm_values"])
            if data["ppm_values"] else 0.0
        )
        avg_effective_hourly = (
            sum(data["hourly_values"]) / len(data["hourly_values"])
            if data["hourly_values"] else 0.0
        )
        avg_pressure = (
            sum(data["pressure_values"]) / len(data["pressure_values"])
            if data["pressure_values"] else 0.0
        )
        avg_surge = (
            sum(data["surge_values"]) / len(data["surge_values"])
            if data["surge_values"] else 0.0
        )

        launch_score = (
            (completion_rate * 40.0)
            + (avg_pay_per_mile * 25.0)
            + (avg_effective_hourly * 0.6)
            - (data["unclaimed_orders"] * 1.5)
        )

        results.append({
            "zone": zone,
            "orders": orders,
            "completed_orders": completed,
            "unclaimed_orders": data["unclaimed_orders"],
            "completion_rate": round(completion_rate, 4),
            "total_earnings": round(total_earnings, 2),
            "total_miles": round(total_miles, 2),
            "avg_pay_per_order": round(avg_pay_per_order, 2),
            "avg_pay_per_mile": round(avg_pay_per_mile, 2),
            "avg_effective_ppm": round(avg_effective_ppm, 2),
            "avg_effective_hourly": round(avg_effective_hourly, 2),
            "avg_pressure_score": round(avg_pressure, 4),
            "avg_surge_multiplier": round(avg_surge, 2),
            "launch_score": round(launch_score, 2),
        })

    results.sort(key=lambda x: x["launch_score"], reverse=True)
    return results


def build_investor_summary(zone_heatmap: List[Dict]) -> Dict:
    if not zone_heatmap:
        return {
            "recommended_launch_order": [],
            "best_zone": None,
            "weakest_zone": None,
            "summary": "No zone data available.",
        }

    best_zone = zone_heatmap[0]
    weakest_zone = zone_heatmap[-1]

    recommended_launch_order = [row["zone"] for row in zone_heatmap]

    return {
        "recommended_launch_order": recommended_launch_order,
        "best_zone": best_zone["zone"],
        "weakest_zone": weakest_zone["zone"],
        "summary": (
            f"Best initial launch zone is {best_zone['zone']} based on launch_score "
            f"{best_zone['launch_score']}, completion_rate {best_zone['completion_rate']}, "
            f"and avg_pay_per_mile {best_zone['avg_pay_per_mile']}."
        ),
    }


def write_zone_heatmap_outputs(
    zone_heatmap: List[Dict],
    investor_summary: Dict,
    json_path: str,
    csv_path: str,
    investor_json_path: str,
) -> None:
    os.makedirs(os.path.dirname(json_path), exist_ok=True)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(zone_heatmap, f, indent=2)

    with open(investor_json_path, "w", encoding="utf-8") as f:
        json.dump(investor_summary, f, indent=2)

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        if not zone_heatmap:
            writer = csv.writer(f)
            writer.writerow(["zone", "orders", "completion_rate", "avg_pay_per_mile", "launch_score"])
            return

        fieldnames = list(zone_heatmap[0].keys())
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(zone_heatmap)