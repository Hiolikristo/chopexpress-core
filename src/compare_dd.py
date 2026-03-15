from fairness import calculate_driver_pay


def compare_order(dd_pay, distance, minutes, pickup_wait, drop_wait):

    result = calculate_driver_pay(
        distance,
        minutes,
        pickup_wait,
        drop_wait
    )

    ce_pay = result["final_pay"]

    dd_hourly = dd_pay / (minutes / 60)
    ce_hourly = ce_pay / (minutes / 60)

    print("\n===== Order Comparison =====\n")

    print(f"DoorDash Pay: ${dd_pay:.2f}")
    print(f"ChopExpress Pay: ${ce_pay:.2f}")
    print(f"Difference: ${ce_pay - dd_pay:.2f}")

    print("\nHourly Comparison")

    print(f"DoorDash Hourly: ${dd_hourly:.2f}/hr")
    print(f"ChopExpress Hourly: ${ce_hourly:.2f}/hr")

    print("\nPay Breakdown")

    for k, v in result.items():
        print(f"{k}: {round(v,2)}")


def main():

    print("\n=== ChopExpress Comparison Tool ===\n")

    dd_pay = float(input("DoorDash Pay: "))
    distance = float(input("Distance Miles: "))
    minutes = float(input("Trip Minutes: "))
    pickup_wait = float(input("Pickup Wait Minutes: "))
    drop_wait = float(input("Drop Wait Minutes: "))

    compare_order(
        dd_pay,
        distance,
        minutes,
        pickup_wait,
        drop_wait
    )


if __name__ == "__main__":
    main()