import csv
from fairness import calculate_driver_pay


def analyze():

    total_dd = 0
    total_ce = 0
    total_miles = 0
    total_minutes = 0
    orders = 0

    with open("sim/data/orders.csv") as f:

        reader = csv.DictReader(f)

        for row in reader:

            dd_pay = float(row["doordash_pay"])
            miles = float(row["distance_miles"])
            minutes = float(row["trip_minutes"])
            pickup = float(row["pickup_wait"])
            drop = float(row["drop_wait"])

            ce = calculate_driver_pay(
                miles,
                minutes,
                pickup,
                drop
            )["final_pay"]

            total_dd += dd_pay
            total_ce += ce
            total_miles += miles
            total_minutes += minutes
            orders += 1

    dd_hourly = total_dd / (total_minutes / 60)
    ce_hourly = total_ce / (total_minutes / 60)

    print("\n=== Weekly Economics Report ===\n")

    print("Orders:", orders)

    print("\nTotals")
    print("DoorDash:", round(total_dd,2))
    print("ChopExpress:", round(total_ce,2))

    print("\nHourly")
    print("DoorDash:", round(dd_hourly,2))
    print("ChopExpress:", round(ce_hourly,2))

    print("\nPer Mile")
    print("DoorDash:", round(total_dd / total_miles,2))
    print("ChopExpress:", round(total_ce / total_miles,2))


if __name__ == "__main__":
    analyze()
    