from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class TierPolicy:
    name: str
    min_miles: float
    maintenance_reserve_rate: float
    insurance_reserve_rate: float


TIER_POLICIES = (
    TierPolicy("Casual", 0.0, 0.03, 0.02),
    TierPolicy("Professional", 1000.0, 0.05, 0.03),
    TierPolicy("Pro+", 2500.0, 0.07, 0.04),
    TierPolicy("Elite", 4000.0, 0.09, 0.05),
)


def determine_driver_tier(rolling_30_day_miles: float) -> str:
    miles = float(rolling_30_day_miles or 0.0)

    if miles >= 4000:
        return "Elite"
    if miles >= 2500:
        return "Pro+"
    if miles >= 1000:
        return "Professional"
    return "Casual"


def get_tier_policy(rolling_30_day_miles: float) -> TierPolicy:
    tier_name = determine_driver_tier(rolling_30_day_miles)
    for policy in TIER_POLICIES:
        if policy.name == tier_name:
            return policy
    return TIER_POLICIES[0]


def reserve_policy_view(rolling_30_day_miles: float) -> Dict[str, float | str]:
    policy = get_tier_policy(rolling_30_day_miles)
    return {
        "tier": policy.name,
        "rolling_30_day_miles": round(float(rolling_30_day_miles or 0.0), 2),
        "maintenance_reserve_rate": policy.maintenance_reserve_rate,
        "insurance_reserve_rate": policy.insurance_reserve_rate,
    }