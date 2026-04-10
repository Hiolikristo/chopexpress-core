import csv
import os
from datetime import datetime

ORDERS_FILE = "sim/data/orders.csv"


def ingest_order(
    source: str,
    order_id: str,
    doordash_pay: float,
    distance_miles: float,
    trip_minutes: float,
    pickup_wait: float,
    drop_wait: float,
    tip: float = 0.0,
    notes: str = ""
):
    os.makedirs("sim/data", exist_ok=True)
    file_exists = os.path.isfile(ORDERS_FILE)

    with open(ORDERS_FILE, "a", newline="") as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow([
                "timestamp",
                "source",
                "order_id",
                "doordash_pay",
                "distance_miles",
                "trip_minutes",
                "pickup_wait",
                "drop_wait",
                "tip",
                "notes",
            ])

        writer.writerow([
            datetime.now().isoformat(),
            source,
            order_id,
            round(doordash_pay, 2),
            round(distance_miles, 2),
            round(trip_minutes, 2),
            round(pickup_wait, 2),
            round(drop_wait, 2),
            round(tip, 2),
            notes,
        ])

    print("Order ingested successfully.")


def prompt_float(label: str) -> float:
    return float(input(f"{label}: ").strip())


def main():
    print("\n=== ChopExpress Order Ingestion Tool ===\n")

    source = input("Source (e.g. doordash): ").strip() or "doordash"
    order_id = input("Order ID / label: ").strip() or datetime.now().strftime("DD_%Y%m%d_%H%M%S")
    doordash_pay = prompt_float("DoorDash Pay")
    distance_miles = prompt_float("Distance Miles")
    trip_minutes = prompt_float("Trip Minutes")
    pickup_wait = prompt_float("Pickup Wait Minutes")
    drop_wait = prompt_float("Drop Wait Minutes")
    tip_raw = input("Tip (optional, default 0): ").strip()
    tip = float(tip_raw) if tip_raw else 0.0
    notes = input("Notes (optional): ").strip()

    ingest_order(
        source=source,
        order_id=order_id,
        doordash_pay=doordash_pay,
        distance_miles=distance_miles,
        trip_minutes=trip_minutes,
        pickup_wait=pickup_wait,
        drop_wait=drop_wait,
        tip=tip,
        notes=notes,
    )


if __name__ == "__main__":
    main()