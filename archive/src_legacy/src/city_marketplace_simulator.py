import random
from dataclasses import dataclass


@dataclass
class Driver:
    driver_id: str
    zone: str
    available: bool = True


@dataclass
class Order:
    order_id: str
    zone: str
    miles: float
    minutes: float
    payout: float
    surge_multiplier: float


ZONES = ["easton", "clintonville", "polaris", "downtown", "westerville", "gahanna"]


BASE_ZONE_WEIGHTS = {
    "easton": 1.3,
    "clintonville": 1.1,
    "polaris": 1.2,
    "downtown": 1.6,
    "westerville": 0.9,
    "gahanna": 0.9,
}


def generate_drivers(driver_count=50):
    drivers = []

    # Weighted driver distribution, but not perfectly balanced
    zone_choices = []
    for zone, weight in BASE_ZONE_WEIGHTS.items():
        zone_choices.extend([zone] * int(weight * 10))

    for i in range(driver_count):
        drivers.append(
            Driver(
                driver_id=f"D{i+1:03}",
                zone=random.choice(zone_choices),
                available=True,
            )
        )

    return drivers


def generate_orders(order_count=80, demand_wave="normal"):
    orders = []

    wave_multiplier = {
        "low": 0.90,
        "normal": 1.00,
        "lunch": 1.15,
        "dinner": 1.30,
        "late_night": 1.10,
    }.get(demand_wave, 1.00)

    zone_weights = BASE_ZONE_WEIGHTS.copy()

    if demand_wave == "lunch":
        zone_weights["downtown"] = 2.1
        zone_weights["easton"] = 1.5
    elif demand_wave == "dinner":
        zone_weights["polaris"] = 1.8
        zone_weights["clintonville"] = 1.5
        zone_weights["downtown"] = 1.8
    elif demand_wave == "late_night":
        zone_weights["downtown"] = 2.2
        zone_weights["polaris"] = 1.4

    weighted_zones = []
    for zone, weight in zone_weights.items():
        weighted_zones.extend([zone] * int(weight * 10))

    for i in range(order_count):
        zone = random.choice(weighted_zones)

        miles = round(random.uniform(1.5, 7.5), 2)
        minutes = round(random.uniform(12, 30), 1)

        base_pay = 2.50 + (miles * 1.55) + (minutes * 0.10)
        payout = round(base_pay * wave_multiplier, 2)

        orders.append(
            Order(
                order_id=f"O{i+1:03}",
                zone=zone,
                miles=miles,
                minutes=minutes,
                payout=payout,
                surge_multiplier=wave_multiplier,
            )
        )

    return orders


def get_zone_supply(drivers):
    supply = {zone: 0 for zone in ZONES}
    for d in drivers:
        if d.available:
            supply[d.zone] += 1
    return supply


def acceptance_probability(order: Order, zone_supply: int):
    pay_per_mile = order.payout / max(order.miles, 0.1)
    hourly = order.payout / (order.minutes / 60)

    # Core attractiveness score
    score = (pay_per_mile * 0.6) + ((hourly / 40) * 0.4)

    # Supply pressure:
    # low supply = higher acceptance pressure
    # high supply = drivers can be pickier
    if zone_supply <= 3:
        supply_adjustment = 0.10
    elif zone_supply <= 6:
        supply_adjustment = 0.03
    elif zone_supply <= 10:
        supply_adjustment = -0.03
    else:
        supply_adjustment = -0.08

    prob = (score / 2.5) + supply_adjustment

    return max(0.15, min(0.75, prob))


def migrate_drivers(drivers, zone_stats):
    """
    Move a small number of drivers toward hot zones with unclaimed pressure.
    """
    hot_zones = sorted(
        zone_stats.items(),
        key=lambda item: item[1]["unclaimed"],
        reverse=True
    )

    if not hot_zones:
        return

    top_hot_zone = hot_zones[0][0]
    top_hot_unclaimed = hot_zones[0][1]["unclaimed"]

    if top_hot_unclaimed == 0:
        return

    candidate_drivers = [d for d in drivers if d.zone != top_hot_zone]
    random.shuffle(candidate_drivers)

    moves = min(5, len(candidate_drivers))

    for d in candidate_drivers[:moves]:
        d.zone = top_hot_zone


def simulate_city_hour(driver_count=50, order_count=80, demand_wave="normal"):
    drivers = generate_drivers(driver_count=driver_count)
    orders = generate_orders(order_count=order_count, demand_wave=demand_wave)

    completed = 0
    unclaimed = 0
    total_payout = 0.0
    total_miles = 0.0
    total_minutes = 0.0

    zone_stats = {
        zone: {
            "orders": 0,
            "completed": 0,
            "unclaimed": 0,
        }
        for zone in ZONES
    }

    for order in orders:
        zone_stats[order.zone]["orders"] += 1

        zone_supply = get_zone_supply(drivers)
        eligible = [d for d in drivers if d.available and d.zone == order.zone]

        if not eligible:
            unclaimed += 1
            zone_stats[order.zone]["unclaimed"] += 1
            continue

        accepted = False
        prob = acceptance_probability(order, zone_supply[order.zone])

        # simulate offer to a few drivers in that zone
        random.shuffle(eligible)
        offer_batch = eligible[: min(4, len(eligible))]

        for driver in offer_batch:
            roll = random.random()
            if roll <= prob:
                completed += 1
                total_payout += order.payout
                total_miles += order.miles
                total_minutes += order.minutes
                zone_stats[order.zone]["completed"] += 1
                accepted = True
                break

        if not accepted:
            # order rejected in-zone
            unclaimed += 1
            zone_stats[order.zone]["unclaimed"] += 1

    # After one pass, simulate migration response to hot zones
    migrate_drivers(drivers, zone_stats)

    completion_rate = completed / len(orders) if orders else 0
    avg_payout = total_payout / completed if completed else 0
    avg_miles = total_miles / completed if completed else 0
    avg_minutes = total_minutes / completed if completed else 0
    hourly_equivalent = avg_payout / (avg_minutes / 60) if avg_minutes else 0

    print("\n=== CITY MARKETPLACE SIMULATION ===\n")
    print(f"Demand wave: {demand_wave}")
    print(f"Drivers: {driver_count}")
    print(f"Orders: {order_count}")
    print(f"Completed: {completed}")
    print(f"Unclaimed: {unclaimed}")
    print(f"Completion rate: {completion_rate:.2%}")
    print(f"Avg payout/order: ${avg_payout:.2f}")
    print(f"Avg miles/order: {avg_miles:.2f}")
    print(f"Avg minutes/order: {avg_minutes:.2f}")
    print(f"Hourly equivalent: ${hourly_equivalent:.2f}/hr")

    print("\n--- Zone Stats ---")
    for zone, stats in zone_stats.items():
        print(
            f"{zone}: "
            f"orders={stats['orders']}, "
            f"completed={stats['completed']}, "
            f"unclaimed={stats['unclaimed']}"
        )


if __name__ == "__main__":
    simulate_city_hour(driver_count=50, order_count=80, demand_wave="dinner")