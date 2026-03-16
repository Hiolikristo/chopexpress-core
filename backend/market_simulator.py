import random
from typing import Dict, List

from order_pipeline import evaluate_order_pipeline


MERCHANTS = [
    "Chipotle",
    "Subway",
    "Local Pizza",
    "Test Kitchen",
    "Campus Cafe",
]

ZONES = [
    "clintonville",
    "osu",
    "downtown",
    "worthington",
]

TIERS = [
    "casual",
    "professional",
    "elite",
]


def generate_order(order_id: int) -> Dict:
    return {
        "order_id": f"SIM{order_id}",
        "merchant": random.choice(MERCHANTS),
        "zone": random.choice(ZONES),
        "tier": random.choice(TIERS),
        "delivery_distance": round(random.uniform(1.0, 6.0), 2),
        "pickup_distance": round(random.uniform(0.5, 3.0), 2),
        "return_distance": round(random.uniform(0.5, 3.5), 2),
        "order_value": round(random.uniform(12, 60), 2),
        "offered_payout": round(random.uniform(6, 18), 2),
        "tip": round(random.uniform(0, 8), 2),
    }


def run_simulation(n_orders: int = 100) -> List[Dict]:
    results = []

    accepted = 0
    rejected = 0

    for i in range(n_orders):
        order = generate_order(i)

        result = evaluate_order_pipeline(order)

        dispatch = result["dispatch"]

        if dispatch["recommended_action"] == "accept":
            accepted += 1
        else:
            rejected += 1

        results.append(result)

    print("Simulation results")
    print("------------------")
    print(f"Orders simulated: {n_orders}")
    print(f"Accepted: {accepted}")
    print(f"Rejected: {rejected}")

    return results


if __name__ == "__main__":
    run_simulation(200)