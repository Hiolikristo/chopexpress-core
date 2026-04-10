import random

ORDERS_PER_SHIFT = 12


def simulate_shift():

    total_pay = 0
    total_miles = 0
    total_minutes = 0

    for i in range(ORDERS_PER_SHIFT):

        miles = random.uniform(1.5, 6.0)
        minutes = random.uniform(12, 25)

        pay = 2.5 + (miles * 1.75) + (minutes * 0.12)

        total_pay += pay
        total_miles += miles
        total_minutes += minutes

        print(
            f"Order {i+1}: "
            f"{miles:.2f} miles, "
            f"{minutes:.1f} min, "
            f"pay ${pay:.2f}"
        )

    hours = total_minutes / 60

    hourly = total_pay / hours
    pay_per_mile = total_pay / total_miles

    print("\n==== SHIFT SUMMARY ====")
    print(f"Orders: {ORDERS_PER_SHIFT}")
    print(f"Total Pay: ${total_pay:.2f}")
    print(f"Total Miles: {total_miles:.2f}")
    print(f"Total Hours: {hours:.2f}")
    print(f"Hourly Earnings: ${hourly:.2f}")
    print(f"Pay per Mile: ${pay_per_mile:.2f}")


def main():

    simulate_shift()


if __name__ == "__main__":
    main()