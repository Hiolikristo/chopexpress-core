import random
from dataclasses import dataclass
from typing import Dict


@dataclass
class MerchantProfile:
    merchant_id: str
    merchant_name: str
    zone: str
    avg_prep_minutes: float
    prep_variance_minutes: float
    reliability_score: float
    rush_hour_multiplier: float
    batching_probability: float


@dataclass
class MerchantDelayResult:
    merchant_id: str
    merchant_name: str
    zone: str
    prep_minutes: float
    batching_delay_minutes: float
    reliability_delay_minutes: float
    total_ready_minutes: float
    is_batched: bool
    rush_applied: bool


DEFAULT_MERCHANTS: Dict[str, MerchantProfile] = {
    "M001": MerchantProfile(
        merchant_id="M001",
        merchant_name="Polaris Grill",
        zone="Polaris",
        avg_prep_minutes=14.0,
        prep_variance_minutes=4.0,
        reliability_score=0.90,
        rush_hour_multiplier=1.20,
        batching_probability=0.18,
    ),
    "M002": MerchantProfile(
        merchant_id="M002",
        merchant_name="Easton Kitchen",
        zone="Easton",
        avg_prep_minutes=16.0,
        prep_variance_minutes=5.0,
        reliability_score=0.86,
        rush_hour_multiplier=1.28,
        batching_probability=0.22,
    ),
    "M003": MerchantProfile(
        merchant_id="M003",
        merchant_name="Downtown Express",
        zone="Downtown",
        avg_prep_minutes=18.0,
        prep_variance_minutes=6.0,
        reliability_score=0.80,
        rush_hour_multiplier=1.35,
        batching_probability=0.27,
    ),
    "M004": MerchantProfile(
        merchant_id="M004",
        merchant_name="Gahanna Bites",
        zone="Gahanna",
        avg_prep_minutes=13.0,
        prep_variance_minutes=3.0,
        reliability_score=0.92,
        rush_hour_multiplier=1.15,
        batching_probability=0.14,
    ),
    "M005": MerchantProfile(
        merchant_id="M005",
        merchant_name="Clintonville Cafe",
        zone="Clintonville",
        avg_prep_minutes=12.0,
        prep_variance_minutes=3.0,
        reliability_score=0.94,
        rush_hour_multiplier=1.12,
        batching_probability=0.12,
    ),
    "M006": MerchantProfile(
        merchant_id="M006",
        merchant_name="Westerville Eats",
        zone="Westerville",
        avg_prep_minutes=15.0,
        prep_variance_minutes=4.0,
        reliability_score=0.88,
        rush_hour_multiplier=1.18,
        batching_probability=0.16,
    ),
}


def is_rush_hour(hour_local: int) -> bool:
    hour = hour_local % 24
    return (11 <= hour <= 13) or (17 <= hour <= 20)


def simulate_merchant_delay(
    merchant: MerchantProfile,
    hour_local: int,
) -> MerchantDelayResult:
    rush = is_rush_hour(hour_local)

    prep_minutes = max(
        4.0,
        random.gauss(merchant.avg_prep_minutes, merchant.prep_variance_minutes),
    )

    if rush:
        prep_minutes *= merchant.rush_hour_multiplier

    reliability_delay_minutes = 0.0
    reliability_gap = max(0.0, 1.0 - merchant.reliability_score)

    if random.random() < reliability_gap:
        reliability_delay_minutes = round(random.uniform(2.0, 9.0), 2)

    is_batched = random.random() < merchant.batching_probability
    batching_delay_minutes = round(random.uniform(2.0, 7.0), 2) if is_batched else 0.0

    total_ready = prep_minutes + reliability_delay_minutes + batching_delay_minutes

    return MerchantDelayResult(
        merchant_id=merchant.merchant_id,
        merchant_name=merchant.merchant_name,
        zone=merchant.zone,
        prep_minutes=round(prep_minutes, 2),
        batching_delay_minutes=round(batching_delay_minutes, 2),
        reliability_delay_minutes=round(reliability_delay_minutes, 2),
        total_ready_minutes=round(total_ready, 2),
        is_batched=is_batched,
        rush_applied=rush,
    )


def get_merchant_for_zone(zone: str) -> MerchantProfile:
    for merchant in DEFAULT_MERCHANTS.values():
        if merchant.zone == zone:
            return merchant

    return MerchantProfile(
        merchant_id="M999",
        merchant_name=f"{zone} Standard Merchant",
        zone=zone,
        avg_prep_minutes=14.0,
        prep_variance_minutes=4.0,
        reliability_score=0.88,
        rush_hour_multiplier=1.20,
        batching_probability=0.15,
    )