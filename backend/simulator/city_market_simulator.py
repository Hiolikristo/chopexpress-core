from __future__ import annotations

import csv
import random
from pathlib import Path
from typing import Any, Dict, List

from backend.dispatch_engine import DispatchEngine
from backend.market_pressure_map_engine import calculate_market_pressure


ROOT_DIR = Path(__file__).resolve().parents[2]


ZONES = [
    "worthington",
    "clintonville",
    "beechwold",
    "northland",
    "osu",
    "short_north",
    "ua_edge",
    "dublin_edge",
]

MERCHANTS = [
    "Kroger",
    "Starbucks",
    "Chipotle",
    "Iron Grill BBQ & Breakfast",
    "Awadh India Restaurant",
    "McDonald's",
    "Wendy's",
    "Pizza Hut",
    "Taco Bell",
    "Ritzy's",
]


def generate_driver_pool(count: int = 150) -> List[Dict[str, Any]]:
    tiers = ["casual", "professional", "pro", "elite"]
    drivers: List[Dict[str, Any]] = []

    for idx in range(count):
        zone = random.choice(ZONES)
        tier = random.choices(
            population=tiers,
            weights=[46, 34, 14, 6],
            k=1,
        )[0]

        drivers.append(
            {
                "driver_id": f"DRV-{idx+1:04d}",
                "name": f"Driver {idx+1}",
                "zone": zone,
                "tier": tier,
                "online": random.random() > 0.28,
                "active_order_id": None,
                "acceptance_rate": round(random.uniform(0.62, 0.98), 2),
                "fatigue_score": round(random.uniform(0.0, 1.8), 2),
                "recent_declines": random.randint(0, 4),
                "reposition_miles": round(random.uniform(1.0, 6.5), 2),
                "preferred_zones": [zone],
            }
        )
    return drivers


def generate_orders(count: int = 2000) -> List[Dict[str, Any]]:
    orders: List[Dict[str, Any]] = []

    for idx in range(count):
        zone = random.choices(
            population=ZONES,
            weights=[18, 18, 10, 11, 12, 17, 7, 7],
            k=1,
        )[0]
        merchant = random.choice(MERCHANTS)

        pickup_miles = round(random.uniform(0.2, 2.8), 2)
        dropoff_miles = round(random.uniform(1.0, 6.4), 2)
        return_buffer_miles = round(random.uniform(0.6, 2.4), 2)
        pickup_minutes = round(random.uniform(3.0, 10.0), 2)
        delivery_minutes = round(random.uniform(8.0, 24.0), 2)
        merchant_delay_minutes = round(random.uniform(0.0, 14.0), 2)
        traffic_multiplier = round(random.uniform(1.0, 1.65), 2)
        tip = round(random.uniform(0.0, 8.5), 2)
        customer_fee = round(random.uniform(4.0, 12.0), 2)

        orders.append(
            {
                "order_id": f"ORD-{idx+1:06d}",
                "zone": zone,
                "merchant_name": merchant,
                "merchant_type": "restaurant",
                "pickup_miles": pickup_miles,
                "dropoff_miles": dropoff_miles,
                "return_buffer_miles": return_buffer_miles,
                "pickup_minutes": pickup_minutes,
                "delivery_minutes": delivery_minutes,
                "merchant_delay_minutes": merchant_delay_minutes,
                "traffic_multiplier": traffic_multiplier,
                "tip": tip,
                "customer_fee": customer_fee,
                "batch_size": random.choice([1, 1, 1, 2, 2, 3]),
                "is_rush_hour": random.random() > 0.55,
                "is_bad_weather": random.random() > 0.86,
                "is_apartment_dropoff": random.random() > 0.62,
                "is_gated_dropoff": random.random() > 0.80,
            }
        )

    return orders


def export_csv(rows: List[Dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        output_path.write_text("", encoding="utf-8")
        return

    fieldnames = list(rows[0].keys())
    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def summarize_zone_orders(orders: List[Dict[str, Any]]) -> Dict[str, int]:
    counts = {zone: 0 for zone in ZONES}
    for order in orders:
        counts[order["zone"]] = counts.get(order["zone"], 0) + 1
    return counts


def summarize_zone_drivers(drivers: List[Dict[str, Any]]) -> Dict[str, int]:
    counts = {zone: 0 for zone in ZONES}
    for driver in drivers:
        if driver.get("online", False):
            counts[driver["zone"]] = counts.get(driver["zone"], 0) + 1
    return counts


def estimate_zone_backlog(zone_orders: Dict[str, int], zone_drivers: Dict[str, int]) -> Dict[str, int]:
    backlog: Dict[str, int] = {}
    for zone in ZONES:
        demand = zone_orders.get(zone, 0)
        supply = zone_drivers.get(zone, 0)
        backlog[zone] = max(0, demand - (supply * 6))
    return backlog


def main() -> None:
    random.seed(7)

    engine = DispatchEngine()

    orders = generate_orders(2000)
    drivers = generate_driver_pool(150)

    zone_order_counts = summarize_zone_orders(orders)
    zone_driver_counts = summarize_zone_drivers(drivers)
    zone_backlog_counts = estimate_zone_backlog(zone_order_counts, zone_driver_counts)
    pressure_map = calculate_market_pressure(
        zone_order_counts=zone_order_counts,
        zone_driver_counts=zone_driver_counts,
        zone_backlog_counts=zone_backlog_counts,
    )

    assigned_orders = 0
    unassigned_orders = 0
    total_offer_pay = 0.0
    total_net_profit_proxy = 0.0
    driver_completed_counts: Dict[str, int] = {}
    driver_gross_earnings: Dict[str, float] = {}

    simulated_orders: List[Dict[str, Any]] = []

    for order in orders:
        decision = engine.dispatch_order(
            order=order,
            drivers=drivers,
            zone_order_counts=zone_order_counts,
            zone_driver_counts=zone_driver_counts,
            zone_backlog_counts=zone_backlog_counts,
        )

        order_row = {
            "order_id": decision.order_id,
            "zone": order["zone"],
            "merchant_name": order["merchant_name"],
            "assigned": decision.accepted,
            "assigned_driver_id": decision.assigned_driver_id,
            "assigned_driver_name": decision.assigned_driver_name,
            "offer_amount": decision.offer_amount,
            "effective_pay_per_mile": decision.effective_pay_per_mile,
            "total_economic_miles": decision.total_economic_miles,
            "total_minutes": decision.total_minutes,
            "status": decision.status,
            "reason": decision.reason,
            "zone_pressure_multiplier": decision.breakdown["zone_pressure_multiplier"],
        }
        simulated_orders.append(order_row)

        if decision.accepted and decision.assigned_driver_id:
            assigned_orders += 1
            total_offer_pay += decision.offer_amount

            proxy_cost = decision.total_economic_miles * 0.42
            proxy_net = decision.offer_amount - proxy_cost
            total_net_profit_proxy += proxy_net

            driver_completed_counts[decision.assigned_driver_id] = (
                driver_completed_counts.get(decision.assigned_driver_id, 0) + 1
            )
            driver_gross_earnings[decision.assigned_driver_id] = (
                driver_gross_earnings.get(decision.assigned_driver_id, 0.0) + decision.offer_amount
            )
        else:
            unassigned_orders += 1

    simulated_drivers: List[Dict[str, Any]] = []
    for driver in drivers:
        driver_id = driver["driver_id"]
        completed = driver_completed_counts.get(driver_id, 0)
        gross = round(driver_gross_earnings.get(driver_id, 0.0), 2)
        net_estimated = round(gross - (completed * 2.35), 2)

        row = {
            "driver_id": driver_id,
            "name": driver["name"],
            "zone": driver["zone"],
            "tier": driver["tier"],
            "online": driver["online"],
            "completed_orders": completed,
            "gross_earnings": gross,
            "net_estimated_profit": net_estimated,
        }
        simulated_drivers.append(row)

    orders_path = ROOT_DIR / "simulated_orders.csv"
    drivers_path = ROOT_DIR / "simulated_drivers.csv"
    export_csv(simulated_orders, orders_path)
    export_csv(simulated_drivers, drivers_path)

    avg_offer = round(total_offer_pay / max(assigned_orders, 1), 2)
    avg_driver_net_profit = round(total_net_profit_proxy / max(len(drivers), 1), 2)

    online_count = sum(1 for d in drivers if d["online"])
    offline_count = len(drivers) - online_count

    zone_distribution = {zone: zone_order_counts.get(zone, 0) for zone in ZONES}
    home_zone_distribution = {}
    for d in drivers:
        home_zone_distribution[d["zone"]] = home_zone_distribution.get(d["zone"], 0) + 1

    top_merchants: Dict[str, int] = {}
    for order in orders:
        m = order["merchant_name"]
        top_merchants[m] = top_merchants.get(m, 0) + 1
    top_merchants = dict(sorted(top_merchants.items(), key=lambda kv: kv[1], reverse=True)[:10])

    top_driver = None
    if simulated_drivers:
        top_driver = max(simulated_drivers, key=lambda d: d["net_estimated_profit"])

    print("=== CITY MARKET SIMULATION SUMMARY ===")
    print(f"total_orders: {len(orders)}")
    print(f"assigned_orders: {assigned_orders}")
    print(f"unassigned_orders: {unassigned_orders}")
    print(f"assignment_rate: {round((assigned_orders / max(len(orders), 1)) * 100, 2)}")
    print(f"avg_offer_pay: {avg_offer}")
    print(f"total_driver_gross_earnings: {round(total_offer_pay, 2)}")
    print(f"total_driver_net_profit: {round(total_net_profit_proxy, 2)}")
    print(f"avg_driver_net_profit: {avg_driver_net_profit}")
    print(f"online_drivers_end: {online_count}")
    print(f"offline_drivers_end: {offline_count}")
    print(f"tier_distribution: { {t: sum(1 for d in drivers if d['tier'] == t) for t in ['casual','professional','pro','elite']} }")
    print(f"home_zone_distribution: {home_zone_distribution}")
    print(f"zone_distribution: {zone_distribution}")
    print(f"top_merchants: {top_merchants}")
    print(f"top_driver: {top_driver}")
    print()
    print("market_pressure_map:")
    for zone, pressure in pressure_map.items():
        print(f"  {zone}: {pressure}")
    print()
    print("Generated files:")
    print(f"- {orders_path}")
    print(f"- {drivers_path}")


if __name__ == "__main__":
    main()