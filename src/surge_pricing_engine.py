"""
ChopExpress Surge Pricing Engine
V1 Marketplace Dynamics

Calculates surge multiplier based on:

- orders waiting
- active drivers
- zone demand pressure

Surge ensures marketplace balance without excessive price spikes.
"""

MAX_SURGE = 2.0
BASE_SURGE = 1.0


class SurgePricingEngine:

    def __init__(self):
        self.zone_surge = {}

    # --------------------------------
    # Calculate surge multiplier
    # --------------------------------

    def calculate_surge(self, pending_orders, available_drivers):

        if available_drivers == 0:
            return MAX_SURGE

        demand_ratio = pending_orders / available_drivers

        if demand_ratio <= 1:
            surge = BASE_SURGE

        elif demand_ratio <= 1.5:
            surge = 1.1

        elif demand_ratio <= 2:
            surge = 1.25

        elif demand_ratio <= 3:
            surge = 1.5

        else:
            surge = MAX_SURGE

        return min(surge, MAX_SURGE)

    # --------------------------------