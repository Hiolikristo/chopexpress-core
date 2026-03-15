import random
from dataclasses import dataclass, asdict
from typing import Dict, List


@dataclass
class CityZone:
    name: str
    demand_weight: float
    avg_trip_miles: float
    avg_offer_pay: float
    peak_multiplier: float
    restaurant_density: float


class CityMarketModel:
    """
    Synthetic city demand model for ChopExpress / DoorDash-style simulation.

    Generates orders with:
    - zone-based demand
    - trip distance variation
    - pay variation
    - hour-based peak effects
    """

    def __init__(self, seed: int = 42) -> None:
        self.random = random.Random(seed)
        self.zones: List[CityZone] = [
            CityZone(
                name="Northland",
                demand_weight=1.20,
                avg_trip_miles=4.2,
                avg_offer_pay=8.75,
                peak_multiplier=1.15,
                restaurant_density=1.10,
            ),
            CityZone(
                name="Morse",
                demand_weight=1.10,
                avg_trip_miles=4.8,
                avg_offer_pay=9.10,
                peak_multiplier=1.10,
                restaurant_density=1.00,
            ),
            CityZone(
                name="Dublin-Granville",
                demand_weight=1.35,
                avg_trip_miles=3.9,
                avg_offer_pay=8.40,
                peak_multiplier=1.20,
                restaurant_density=1.25,
            ),
            CityZone(
                name="Westerville",
                demand_weight=0.95,
                avg_trip_miles=5.6,
                avg_offer_pay=9.80,
                peak_multiplier=1.05,
                restaurant_density=0.90,
            ),
            CityZone(
                name="Worthington",
                demand_weight=1.00,
                avg_trip_miles=4.5,
                avg_offer_pay=8.95,
                peak_multiplier=1.08,
                restaurant_density=0.95,
            ),
            CityZone(
                name="Easton",
                demand_weight=1.15,
                avg_trip_miles=5.2,
                avg_offer_pay=10.25,
                peak_multiplier=1.18,
                restaurant_density=1.05,
            ),
        ]

        self.restaurant_types = [
            "Fast Food",
            "Pizza",
            "Chicken",
            "Coffee",
            "Casual Dining",
            "Sandwiches",
            "Wings",
            "International",
            "Breakfast",
            "Burgers",
        ]

    def _weighted_zone_choice(self) -> CityZone:
        weights = [z.demand_weight for z in self.zones]
        return self.random.choices(self.zones, weights=weights, k=1)[0]

    def _hour_multiplier(self, hour: int) -> float:
        if 6 <= hour <= 9:
            return 1.10   # breakfast
        if 11 <= hour <= 14:
            return 1.25   # lunch
        if 17 <= hour <= 20:
            return 1.35   # dinner
        if 21 <= hour <= 23:
            return 1.05
        return 0.85

    def _merchant_delay_minutes(self, restaurant_type: str, hour: int) -> int:
        base = {
            "Fast Food": 4,
            "Pizza": 10,
            "Chicken": 8,
            "Coffee": 3,
            "Casual Dining": 11,
            "Sandwiches": 5,
            "Wings": 9,
            "International": 12,
            "Breakfast": 6,
            "Burgers": 7,
        }.get(restaurant_type, 6)

        if 11 <= hour <= 14 or 17 <= hour <= 20:
            base += 2

        return max(2, int(round(base + self.random.uniform(-2, 3))))

    def _tip_amount(self, base_offer_pay: float) -> float:
        # Approximate tip behavior
        tip = round(max(0.0, self.random.gauss(mu=base_offer_pay * 0.35, sigma=1.75)), 2)
        return tip

    def _base_pay_amount(self, trip_miles: float) -> float:
        # Simple platform-style base pay approximation
        base_pay = 2.25 + (trip_miles * 0.45)
        return round(base_pay, 2)

    def generate_orders(self, count: int = 500, start_hour: int = 6) -> List[Dict]:
        orders: List[Dict] = []

        for i in range(count):
            zone = self._weighted_zone_choice()
            hour = (start_hour + (i % 18)) % 24
            hour_mult = self._hour_multiplier(hour)

            restaurant_type = self.random.choice(self.restaurant_types)

            trip_miles = max(
                0.8,
                round(
                    self.random.gauss(
                        mu=zone.avg_trip_miles * hour_mult * 0.95,
                        sigma=1.2,
                    ),
                    2,
                ),
            )

            base_pay = self._base_pay_amount(trip_miles)
            tip = self._tip_amount(zone.avg_offer_pay * hour_mult / 2)
            offer_pay = round(base_pay + tip, 2)

            merchant_delay_min = self._merchant_delay_minutes(restaurant_type, hour)

            order = {
                "order_id": f"ORD-{i+1:05d}",
                "zone": zone.name,
                "hour": hour,
                "restaurant_type": restaurant_type,
                "trip_miles": trip_miles,
                "offer_pay": offer_pay,
                "base_pay": base_pay,
                "tip": tip,
                "merchant_delay_min": merchant_delay_min,
                "restaurant_density": zone.restaurant_density,
                "peak_multiplier": zone.peak_multiplier,
                "demand_weight": zone.demand_weight,
                "estimated_minutes": round((trip_miles / 0.45) + merchant_delay_min, 2),
            }
            orders.append(order)

        return orders

    def zone_snapshot(self) -> List[Dict]:
        return [asdict(z) for z in self.zones]