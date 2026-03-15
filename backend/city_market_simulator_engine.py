from __future__ import annotations

import csv
import random
from pathlib import Path
from typing import Any, Dict, List

from backend.simulator.city_market_simulator import main

if __name__ == "__main__":
    main()
from backend.columbus_market_engine import ColumbusMarketEngine


ROOT_DIR = Path(__file__).resolve().parents[2]


def generate_driver_pool(count: int = 150) -> List[Dict[str, Any]]:
    rng = random.Random(99)

    zones = [
        "worthington",
        "clintonville",
        "beechwold",
        "northland",
        "osu",
        "short_north",
        "ua_edge",
        "dublin_edge",
    ]

    tiers = ["casual", "professional", "pro_plus", "elite"]

    drivers: List[Dict[str, Any]] = []

    for idx in range(count):
        tier = rng.choices(
            tiers,
            weights=[35, 38, 19, 8],
            k=1,
        )[0]

        completed_orders = {
            "casual": rng.randint(8, 40),
            "professional": rng.randint(25, 75),
            "pro_plus": rng.randint(40, 110),
            "elite": rng.randint(60, 140),
        }[tier]

        gross_earnings = round(
            completed_orders * rng.uniform(9.5, 15.5),
            2,
        )

        net_estimated_profit = round(
            gross_earnings * rng.uniform(0.46, 0.62),
            2,
        )

        drivers.append(
            {
                "driver_id": f"DRV-{idx:04d}",
                "name": f"Driver {idx}",
                "tier": tier,
                "gross_earnings": gross_earnings,
                "net_estimated_profit": net_estimated_profit,
                "completed_orders": completed_orders,
                "current_zone": rng.choice(zones),
                "acceptance_rate": round(rng.uniform(0.42, 0.94), 3),
                "fatigue_score": round(rng.uniform(0.0, 0.65), 3),
            }
        )

    return drivers


def export_orders_csv(orders: List[Dict[str, Any]], filename: str = "simulated_orders.csv") -> Path:
    output_path = ROOT_DIR / filename
    if not orders:
        raise ValueError("No orders available to export.")

    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=list(orders[0].keys()))
        writer.writeheader()
        for order in orders:
            writer.writerow(order)

    return output_path


def export_drivers_csv(drivers: List[Dict[str, Any]], filename: str = "simulated_drivers.csv") -> Path:
    output_path = ROOT_DIR / filename
    if not drivers:
        raise ValueError("No drivers available to export.")

    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=list(drivers[0].keys()))
        writer.writeheader()
        for driver in drivers:
            writer.writerow(driver)

    return output_path


def summarize_driver_pool(drivers: List[Dict[str, Any]]) -> Dict[str, Any]:
    home_zone_distribution: Dict[str, int] = {}
    tier_distribution: Dict[str, int] = {}

    for driver in drivers:
        zone = driver["current_zone"]
        tier = driver["tier"]
        home_zone_distribution[zone] = home_zone_distribution.get(zone, 0) + 1
        tier_distribution[tier] = tier_distribution.get(tier, 0) + 1

    top_driver = max(drivers, key=lambda d: d["net_estimated_profit"])

    return {
        "driver_count": len(drivers),
        "home_zone_distribution": home_zone_distribution,
        "tier_distribution": tier_distribution,
        "top_driver": top_driver,
    }


def simulate_market(order_count: int = 2000) -> Dict[str, Any]:
    engine = ColumbusMarketEngine(seed=7)

    orders = engine.generate_orders(
        count=order_count,
        duration_minutes=240,
        weather="clear",
        mode="dinner",
    )

    drivers = generate_driver_pool(150)

    order_summary = engine.summarize_orders(orders)
    driver_summary = summarize_driver_pool(drivers)

    return {
        "orders": orders,
        "drivers": drivers,
        "order_summary": order_summary,
        "driver_summary": driver_summary,
    }


def main() -> None:
    result = simulate_market(order_count=2000)

    orders = result["orders"]
    drivers = result["drivers"]

    orders_path = export_orders_csv(orders, "simulated_orders.csv")
    drivers_path = export_drivers_csv(drivers, "simulated_drivers.csv")

    print("home_zone_distribution:", result["driver_summary"]["home_zone_distribution"])
    print("tier_distribution:", result["driver_summary"]["tier_distribution"])
    print("zone_distribution:", result["order_summary"]["zone_distribution"])
    print("top_merchants:", result["order_summary"]["top_merchants"])
    print("top_driver:", result["driver_summary"]["top_driver"])
    print()
    print("Generated files:")
    print(f" - {orders_path}")
    print(f" - {drivers_path}")


if __name__ == "__main__":
    main()