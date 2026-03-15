from __future__ import annotations

from typing import Dict, Any

from geo_routing_engine import build_route_estimate, route_estimate_to_dict


def estimate_route_time(order: Dict[str, Any], driver: Dict[str, Any]) -> Dict[str, Any]:
    """
    Returns route structure for dispatch + economics.

    Expected order keys:
    - pickup_zone
    - dropoff_zone
    - recovery_zone (optional)
    - market_pressure (optional)
    - merchant_delay_pressure (optional)
    - hotspot_pull (optional)

    Expected driver keys:
    - zone
    """
    driver_zone = driver.get("zone", "Northland")
    pickup_zone = order.get("pickup_zone", driver_zone)
    dropoff_zone = order.get("dropoff_zone", pickup_zone)
    recovery_zone = order.get("recovery_zone", pickup_zone)

    market_pressure = float(order.get("market_pressure", 1.0))
    merchant_delay_pressure = float(order.get("merchant_delay_pressure", 1.0))
    hotspot_pull = float(order.get("hotspot_pull", 1.0))

    route = build_route_estimate(
        driver_zone=driver_zone,
        pickup_zone=pickup_zone,
        dropoff_zone=dropoff_zone,
        recovery_zone=recovery_zone,
        market_pressure=market_pressure,
        merchant_delay_pressure=merchant_delay_pressure,
        hotspot_pull=hotspot_pull,
    )

    return route_estimate_to_dict(route)


def main() -> None:
    sample_order = {
        "pickup_zone": "Easton",
        "dropoff_zone": "Clintonville",
        "recovery_zone": "Easton",
        "market_pressure": 1.2,
        "merchant_delay_pressure": 1.1,
        "hotspot_pull": 1.15,
    }
    sample_driver = {"zone": "Northland"}

    print(estimate_route_time(sample_order, sample_driver))


if __name__ == "__main__":
    main()