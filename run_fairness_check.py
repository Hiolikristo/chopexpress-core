from __future__ import annotations

import csv
import json
import os

from backend.fairness_engine import FairnessEngine
from backend.driver_profitability_engine import DriverProfitabilityEngine


INPUT_PATH = os.path.join("sim", "input", "real_world_offers.csv")
OUTPUT_PATH = os.path.join("sim", "output", "real_world_fairness_check.json")


def main() -> None:
    fairness_engine = FairnessEngine(min_ppem=1.15)
    profit_engine = DriverProfitabilityEngine(vehicle_cost_per_mile=0.42, fixed_cost_per_order=0.35)

    results = []

    with open(INPUT_PATH, "r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)

        for row in reader:
            order_id = row["order_id"]
            pay = float(row["pay"])
            trip_miles = float(row["trip_miles"])
            return_estimate = float(row["return_estimate"])

            fairness = fairness_engine.evaluate(
                offer_pay=pay,
                trip_miles=trip_miles,
                return_miles=return_estimate,
            )

            assumed_trip_minutes = max(8.0, (trip_miles + return_estimate) * 3.1)
            profitability = profit_engine.calculate_driver_profit(
                offer_pay=pay,
                economic_miles=fairness.economic_miles,
                trip_time_minutes=assumed_trip_minutes,
            )

            results.append(
                {
                    "order_id": order_id,
                    "offer_pay": round(pay, 2),
                    "trip_miles": round(trip_miles, 2),
                    "return_estimate": round(return_estimate, 2),
                    "economic_miles": fairness.economic_miles,
                    "ppem": fairness.pay_per_economic_mile,
                    "fairness_threshold": fairness.minimum_required_ppem,
                    "fairness_approved": fairness.approved,
                    "fairness_reason": fairness.reason,
                    "driver_cost": profitability["driver_cost"],
                    "net_profit": profitability["net_profit"],
                    "hourly_rate": profitability["hourly_rate"],
                }
            )

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2)

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()