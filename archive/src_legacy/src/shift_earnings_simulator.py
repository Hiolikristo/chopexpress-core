import random

ORDERS_PER_SHIFT = 15


def generate_order():

    miles = random.uniform(1.5, 6.5)
    minutes = random.uniform(12, 28)

    base = 2.50
    distance_pay = miles * 1.75
    time_pay = minutes * 0.12

    pay = base + distance_pay + time_pay

    return miles, minutes, pay


def simulate_shift():

    total_pay = 0
    total_miles = 0
    total_minutes = 0

    print("\n=== SHIFT SIMULATION ===\n")

    for i in range(ORDERS_PER_SHIFT):

        miles, minutes, pay = generate_order()

        total_pay += pay
        total_miles += miles
        total_minutes += minutes

        print(
            f"Order {i+1}: "
            f"{miles:.2f} miles | "
            f"{minutes:.1f} min | "
            f"${pay:.2f}"
        )

    hours = total_minutes / 60

    hourly = total_pay / hours
    pay_per_mile = total_pay / total_miles

    print("\n===== SHIFT SUMMARY =====")
    print(f"Orders completed: {ORDERS_PER_SHIFT}")
    print(f"Total pay: ${total_pay:.2f}")
    print(f"Total miles: {total_miles:.2f}")
    print(f"Total hours: {hours:.2f}")
    print(f"Hourly earnings: ${hourly:.2f}")
    print(f"Pay per mile: ${pay_per_mile:.2f}")


def main():

    simulate_shift()


if __name__ == "__main__":
    main()