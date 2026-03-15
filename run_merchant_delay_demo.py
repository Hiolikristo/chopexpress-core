from pprint import pprint

from backend.merchant_delay_engine import (
    get_merchant_for_zone,
    simulate_merchant_delay,
)


def main() -> None:
    zones = [
        "Polaris",
        "Westerville",
        "Easton",
        "Clintonville",
        "Gahanna",
        "Downtown",
    ]

    hour_local = 12

    results = []
    for zone in zones:
        merchant = get_merchant_for_zone(zone)
        delay = simulate_merchant_delay(merchant=merchant, hour_local=hour_local)
        results.append(delay.__dict__)

    print("=== MERCHANT DELAY DEMO ===")
    pprint(results)


if __name__ == "__main__":
    main()