from dataclasses import dataclass
from typing import List
import random


@dataclass
class DriverPoolState:
    driver_id: str
    tier: str
    home_zone: str
    preferred_zones: List[str]
    is_online: bool
    acceptance_rate: float
    current_zone: str
    recent_complaint_flag: bool = False
    on_probation: bool = False


def hour_online_probability(service_hour: int, tier: str) -> float:
    """
    Models realistic online behavior by time of day.
    """
    if 6 <= service_hour <= 9:
        base = 0.42   # breakfast
    elif 10 <= service_hour <= 14:
        base = 0.72   # lunch
    elif 15 <= service_hour <= 16:
        base = 0.48   # afternoon dip
    elif 17 <= service_hour <= 21:
        base = 0.88   # dinner rush
    elif 22 <= service_hour <= 1:
        base = 0.36   # late night
    else:
        base = 0.18   # very low hours

    tier_bonus = {
        "Casual": -0.04,
        "Professional": 0.02,
        "Pro+": 0.05,
        "Elite": 0.07,
    }.get(tier, 0.0)

    return max(0.05, min(0.98, base + tier_bonus))


def refresh_driver_pool_for_hour(
    drivers: List[DriverPoolState],
    service_hour: int,
) -> List[DriverPoolState]:
    refreshed: List[DriverPoolState] = []

    for driver in drivers:
        online_prob = hour_online_probability(service_hour, driver.tier)
        driver.is_online = random.random() < online_prob

        if driver.is_online:
            # Most drivers remain in home/preferred zone, some drift.
            if random.random() < 0.75:
                if driver.preferred_zones:
                    driver.current_zone = random.choice(driver.preferred_zones)
                else:
                    driver.current_zone = driver.home_zone

        refreshed.append(driver)

    return refreshed


def filter_online_drivers(drivers: List[DriverPoolState]) -> List[DriverPoolState]:
    return [driver for driver in drivers if driver.is_online]


def driver_accepts_order(
    driver: DriverPoolState,
    offered_effective_ppm: float,
    offered_effective_hourly: float,
    min_effective_ppm: float = 1.60,
    min_effective_hourly: float = 20.00,
) -> bool:
    """
    Adds realistic post-offer driver acceptance behavior.
    """
    threshold_bonus = 0.0

    if offered_effective_ppm >= min_effective_ppm:
        threshold_bonus += 0.08
    if offered_effective_hourly >= min_effective_hourly:
        threshold_bonus += 0.08

    complaint_penalty = 0.08 if driver.recent_complaint_flag else 0.0
    probation_penalty = 0.12 if driver.on_probation else 0.0

    effective_acceptance = (
        driver.acceptance_rate
        + threshold_bonus
        - complaint_penalty
        - probation_penalty
    )

    effective_acceptance = max(0.05, min(0.97, effective_acceptance))
    return random.random() < effective_acceptance