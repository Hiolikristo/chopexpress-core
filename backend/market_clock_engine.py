from dataclasses import dataclass
from typing import Dict, List


@dataclass
class HourProfile:
    hour_local: int
    demand_multiplier: float
    speed_multiplier: float
    merchant_rush_bias: float
    zone_weights: Dict[str, float]


def build_24h_market_clock(zones: List[str]) -> Dict[int, HourProfile]:
    default_weights = {zone: 1.0 for zone in zones}

    profiles: Dict[int, HourProfile] = {}

    for hour in range(24):
        demand_multiplier = 0.45
        speed_multiplier = 1.0
        merchant_rush_bias = 0.0
        zone_weights = dict(default_weights)

        # Overnight
        if 0 <= hour <= 5:
            demand_multiplier = 0.22
            speed_multiplier = 1.12
            zone_weights["Downtown"] = 1.20
            zone_weights["Polaris"] = 0.85
            zone_weights["Easton"] = 0.80

        # Early morning
        elif 6 <= hour <= 8:
            demand_multiplier = 0.55
            speed_multiplier = 0.82
            zone_weights["Clintonville"] = 1.15
            zone_weights["Gahanna"] = 1.10
            zone_weights["Downtown"] = 1.18

        # Late morning
        elif 9 <= hour <= 10:
            demand_multiplier = 0.78
            speed_multiplier = 0.92
            zone_weights["Easton"] = 1.10
            zone_weights["Polaris"] = 1.08

        # Lunch rush
        elif 11 <= hour <= 13:
            demand_multiplier = 1.45
            speed_multiplier = 0.76
            merchant_rush_bias = 1.0
            zone_weights["Downtown"] = 1.30
            zone_weights["Easton"] = 1.24
            zone_weights["Polaris"] = 1.18
            zone_weights["Clintonville"] = 1.10

        # Mid afternoon
        elif 14 <= hour <= 16:
            demand_multiplier = 0.92
            speed_multiplier = 0.95
            zone_weights["Westerville"] = 1.08
            zone_weights["Gahanna"] = 1.06

        # Dinner rush
        elif 17 <= hour <= 20:
            demand_multiplier = 1.62
            speed_multiplier = 0.72
            merchant_rush_bias = 1.0
            zone_weights["Polaris"] = 1.22
            zone_weights["Westerville"] = 1.14
            zone_weights["Easton"] = 1.18
            zone_weights["Downtown"] = 1.16

        # Late evening
        elif 21 <= hour <= 23:
            demand_multiplier = 0.72
            speed_multiplier = 0.96
            zone_weights["Downtown"] = 1.18
            zone_weights["Clintonville"] = 1.08

        profiles[hour] = HourProfile(
            hour_local=hour,
            demand_multiplier=round(demand_multiplier, 2),
            speed_multiplier=round(speed_multiplier, 2),
            merchant_rush_bias=merchant_rush_bias,
            zone_weights=zone_weights,
        )

    return profiles