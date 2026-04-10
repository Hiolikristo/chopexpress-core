import csv
import os
from datetime import datetime

LOG_FILE = "sim/data/delivery_log.csv"


def log_delivery(distance, trip_minutes, pickup_wait, drop_wait, driver_pay):

    os.makedirs("sim/data", exist_ok=True)

    file_exists = os.path.isfile(LOG_FILE)

    with open(LOG_FILE, "a", newline="") as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow([
                "timestamp",
                "distance_miles",
                "trip_minutes",
                "pickup_wait",
                "drop_wait",
                "driver_pay"
            ])

        writer.writerow([
            datetime.now().isoformat(),
            round(distance, 2),
            round(trip_minutes, 2),
            round(pickup_wait, 2),
            round(drop_wait, 2),
            round(driver_pay, 2)
        ])

    print("Delivery logged.")