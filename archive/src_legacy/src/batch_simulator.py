import random
from fairness import calculate_driver_pay
from logger import log_delivery

RUNS = 1000


def run_batch():

    total_pay = 0
    total_distance = 0
    total_minutes = 0

    for i in range(RUNS):

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

        total_pay += result["final_pay"]
        total_distance += distance
        total_minutes += trip_minutes

    avg_pay = total_pay / RUNS
    avg_distance = total_distance / RUNS
    avg_minutes = total_minutes / RUNS

    hourly_rate = avg_pay / (avg_minutes / 60)

    print("\n=== ChopExpress 1000 Run Simulation ===\n")

    print("runs:", RUNS)
    print("avg_driver_pay:", round(avg_pay, 2))
    print("avg_distance:", round(avg_distance, 2))
    print("avg_minutes:", round(avg_minutes, 2))
    print("driver_hourly_estimate:", round(hourly_rate, 2))


if __name__ == "__main__":
    run_batch()