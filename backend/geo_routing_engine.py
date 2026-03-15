from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Dict, Tuple, Optional


Coordinate = Tuple[float, float]


@dataclass(frozen=True)
class ZoneAnchor:
    zone: str
    lat: float
    lon: float


@dataclass
class RouteEstimate:
    origin_zone: str
    destination_zone: str
    pickup_zone: str
    trip_miles: float
    deadhead_miles: float
    return_miles_estimate: float
    economic_miles: float
    traffic_multiplier: float
    estimated_minutes: float


# Columbus starter anchors for V1 calibration.
# These are not exact merchant/customer coordinates.
# They are zone anchors used to simulate structured market geography.
DEFAULT_ZONE_ANCHORS: Dict[str, ZoneAnchor] = {
    "Northland": ZoneAnchor("Northland", 40.0995, -82.9850),
    "Easton": ZoneAnchor("Easton", 40.0522, -82.9150),
    "Clintonville": ZoneAnchor("Clintonville", 40.0389, -83.0018),
    "Worthington": ZoneAnchor("Worthington", 40.0931, -83.0170),
    "Westerville": ZoneAnchor("Westerville", 40.1262, -82.9291),
    "Gahanna": ZoneAnchor("Gahanna", 40.0192, -82.8790),
    "Downtown": ZoneAnchor("Downtown", 39.9612, -82.9988),
    "ShortNorth": ZoneAnchor("ShortNorth", 39.9839, -83.0040),
    "Polaris": ZoneAnchor("Polaris", 40.1434, -82.9810),
    "Reynoldsburg": ZoneAnchor("Reynoldsburg", 39.9548, -82.8121),
}

# Used when a zone is missing or unknown.
FALLBACK_ZONE = "Northland"


def _get_anchor(zone: str, anchors: Optional[Dict[str, ZoneAnchor]] = None) -> ZoneAnchor:
    zone_map = anchors or DEFAULT_ZONE_ANCHORS
    if zone in zone_map:
        return zone_map[zone]
    return zone_map[FALLBACK_ZONE]


def _euclidean_distance_miles(a: Coordinate, b: Coordinate) -> float:
    """
    Fast approximation.
    1 degree lat/lon is not constant, but for city-scale simulation this is enough
    before we plug in full routing APIs.
    """
    lat_scale = 69.0
    lon_scale = 53.0  # rough Columbus-area adjustment
    dlat = (a[0] - b[0]) * lat_scale
    dlon = (a[1] - b[1]) * lon_scale
    return sqrt(dlat * dlat + dlon * dlon)


def estimate_zone_to_zone_miles(
    origin_zone: str,
    destination_zone: str,
    anchors: Optional[Dict[str, ZoneAnchor]] = None,
    road_factor: float = 1.22,
) -> float:
    zone_map = anchors or DEFAULT_ZONE_ANCHORS
    a = _get_anchor(origin_zone, zone_map)
    b = _get_anchor(destination_zone, zone_map)
    direct = _euclidean_distance_miles((a.lat, a.lon), (b.lat, b.lon))
    return round(max(0.6, direct * road_factor), 2)


def estimate_deadhead_miles(
    driver_zone: str,
    pickup_zone: str,
    anchors: Optional[Dict[str, ZoneAnchor]] = None,
) -> float:
    if driver_zone == pickup_zone:
        return 0.0
    return estimate_zone_to_zone_miles(driver_zone, pickup_zone, anchors)


def estimate_return_miles(
    dropoff_zone: str,
    recovery_zone: str,
    anchors: Optional[Dict[str, ZoneAnchor]] = None,
    recovery_factor: float = 0.65,
) -> float:
    """
    Return burden is deliberately discounted from full zone-to-zone mileage
    because not every post-drop reposition is fully incurred.
    """
    if dropoff_zone == recovery_zone:
        return 0.0

    full_back = estimate_zone_to_zone_miles(dropoff_zone, recovery_zone, anchors)
    return round(full_back * recovery_factor, 2)


def estimate_traffic_multiplier(
    market_pressure: float = 1.0,
    merchant_delay_pressure: float = 1.0,
    hotspot_pull: float = 1.0,
) -> float:
    """
    Base traffic pressure model.
    Can later be replaced by clock-based and corridor-specific congestion curves.
    """
    raw = 1.0 + ((market_pressure - 1.0) * 0.35) + ((merchant_delay_pressure - 1.0) * 0.20) + (
        (hotspot_pull - 1.0) * 0.10
    )
    return round(max(0.85, min(raw, 1.85)), 3)


def estimate_minutes_from_miles(
    miles: float,
    traffic_multiplier: float = 1.0,
    avg_city_speed_mph: float = 24.0,
) -> float:
    if avg_city_speed_mph <= 0:
        avg_city_speed_mph = 24.0

    hours = miles / avg_city_speed_mph
    minutes = hours * 60.0 * traffic_multiplier
    return round(max(2.0, minutes), 2)


def build_route_estimate(
    driver_zone: str,
    pickup_zone: str,
    dropoff_zone: str,
    recovery_zone: Optional[str] = None,
    anchors: Optional[Dict[str, ZoneAnchor]] = None,
    market_pressure: float = 1.0,
    merchant_delay_pressure: float = 1.0,
    hotspot_pull: float = 1.0,
) -> RouteEstimate:
    zone_map = anchors or DEFAULT_ZONE_ANCHORS
    recovery_zone = recovery_zone or pickup_zone

    deadhead_miles = estimate_deadhead_miles(driver_zone, pickup_zone, zone_map)
    trip_miles = estimate_zone_to_zone_miles(pickup_zone, dropoff_zone, zone_map)
    return_miles = estimate_return_miles(dropoff_zone, recovery_zone, zone_map)

    economic_miles = round(deadhead_miles + trip_miles + return_miles, 2)

    traffic_multiplier = estimate_traffic_multiplier(
        market_pressure=market_pressure,
        merchant_delay_pressure=merchant_delay_pressure,
        hotspot_pull=hotspot_pull,
    )

    estimated_minutes = estimate_minutes_from_miles(
        economic_miles,
        traffic_multiplier=traffic_multiplier,
    )

    return RouteEstimate(
        origin_zone=driver_zone,
        destination_zone=dropoff_zone,
        pickup_zone=pickup_zone,
        trip_miles=trip_miles,
        deadhead_miles=deadhead_miles,
        return_miles_estimate=return_miles,
        economic_miles=economic_miles,
        traffic_multiplier=traffic_multiplier,
        estimated_minutes=estimated_minutes,
    )


def route_estimate_to_dict(route: RouteEstimate) -> Dict[str, float | str]:
    return {
        "origin_zone": route.origin_zone,
        "pickup_zone": route.pickup_zone,
        "destination_zone": route.destination_zone,
        "trip_miles": route.trip_miles,
        "deadhead_miles": route.deadhead_miles,
        "return_miles_estimate": route.return_miles_estimate,
        "economic_miles": route.economic_miles,
        "traffic_multiplier": route.traffic_multiplier,
        "estimated_minutes": route.estimated_minutes,
    }


def main() -> None:
    sample = build_route_estimate(
        driver_zone="Northland",
        pickup_zone="Easton",
        dropoff_zone="Clintonville",
        recovery_zone="Easton",
        market_pressure=1.20,
        merchant_delay_pressure=1.10,
        hotspot_pull=1.15,
    )
    print(route_estimate_to_dict(sample))


if __name__ == "__main__":
    main()