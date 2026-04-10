import random
from fairness import calculate_driver_pay
from logger import log_delivery


def run_simulation():
    distance = random.uniform(1, 9)
    trip_minutes = random.uniform(8, 35)
    pickup_wait = random.uniform(0, 12)
    drop_wait = random.uniform(0, 6)

    result = calculate_driver_pay(
        distance,
        trip_minutes,
        pickup_wait,
        drop_wait
    )

    log_delivery(
        distance,
        trip_minutes,
        pickup_wait,
        drop_wait,
        result["final_pay"]
    )

    print("\n=== ChopExpress Random Simulation ===\n")
    print("distance:", round(distance, 2))
    print("trip_minutes:", round(trip_minutes, 2))
    print("pickup_wait:", round(pickup_wait, 2))
    print("drop_wait:", round(drop_wait, 2))
    print("driver_pay:", round(result["final_pay"], 2))


if __name__ == "__main__":
    run_simulation()