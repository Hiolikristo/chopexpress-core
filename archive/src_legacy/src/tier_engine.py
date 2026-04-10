"""
ChopExpress Tier Engine
V1 Locked Policy

Tier progression is based on rolling 30-day mileage exposure.

Tiers:
Casual:        0–999 miles
Professional:  1000–2499 miles
Pro+:          2500–3999 miles
Elite:         4000+ miles
"""

from collections import deque

WINDOW_DAYS = 30


class TierEngine:
    def __init__(self, driver_id: str):
        self.driver_id = driver_id
        self.mileage_log = deque(maxlen=WINDOW_DAYS)
        self.current_tier = "Casual"

    def record_miles(self, miles: float):
        self.mileage_log.append(float(miles))
        self.update_tier()

    def rolling_miles(self) -> float:
        return round(sum(self.mileage_log), 2)

    def update_tier(self):
        miles = self.rolling_miles()

        if miles < 1000:
            self.current_tier = "Casual"
        elif miles < 2500:
            self.current_tier = "Professional"
        elif miles < 4000:
            self.current_tier = "Pro+"
        else:
            self.current_tier = "Elite"

    def dispatch_weight(self) -> float:
        weights = {
            "Casual": 1.00,
            "Professional": 1.05,
            "Pro+": 1.10,
            "Elite": 1.20,
        }
        return weights[self.current_tier]

    def status(self) -> dict:
        return {
            "driver_id": self.driver_id,
            "rolling_miles": self.rolling_miles(),
            "tier": self.current_tier,
            "dispatch_weight": self.dispatch_weight(),
        }


if __name__ == "__main__":
    tier = TierEngine("D001")

    sample_days = [
        120, 110, 130, 95, 140, 125, 118, 132, 105, 111,
        109, 115, 123, 117, 108, 126, 121, 119, 112, 124,
        127, 116, 113, 122, 128, 129, 114, 120, 118, 130,
    ]

    for miles in sample_days:
        tier.record_miles(miles)

    print(tier.status())