from __future__ import annotations

import random
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

from backend.market_pressure_engine import MarketPressureEngine


@dataclass
class OrderRecord:
    order_id: str
    zone: str
    merchant: str
    pickup_miles: float
    delivery_miles: float
    return_buffer_miles: float
    economic_miles: float
    trip_minutes: float
    merchant_delay_minutes: float
    traffic_multiplier: float
    base_pay: float
    tip: float
    customer_fee: float
    offer_pay: float
    pay_per_economic_mile: float
    batch_size: int
    mode: str
    weather: str
    dropoff_type: str
    is_rush_hour: bool
    is_bad_weather: bool
    timestamp_minute: int
    pressure_score: float
    pressure_demand_index: float
    pressure_supply_index: float
    pay_boost_multiplier: float
    batch_probability_boost: float


class ColumbusMarketEngine:
    def __init__(self, seed: int = 7) -> None:
        self.rng = random.Random(seed)
        self.pressure_engine = MarketPressureEngine()

        self.zone_weights = {
            "worthington": 22,
            "clintonville": 23,
            "beechwold": 11,
            "northland": 11,
            "osu": 10,
            "short_north": 10,
            "ua_edge": 7,
            "dublin_edge": 6,
        }

        self.zone_merchants = {
            "worthington": ["Kroger", "Starbucks", "Chipotle", "Iron Grill BBQ & Breakfast"],
            "clintonville": ["Chipotle", "McDonald's", "Pizza Hut", "Starbucks", "Awadh India Restaurant"],
            "beechwold": ["Kroger", "McDonald's", "Wendy's"],
            "northland": ["Taco Bell", "McDonald's", "Pizza Hut", "Kroger"],
            "osu": ["Chipotle", "Starbucks", "McDonald's", "Taco Bell"],
            "short_north": ["Chipotle", "Starbucks", "Ritzy's", "Pizza Hut"],
            "ua_edge": ["Kroger", "Starbucks", "Chipotle"],
            "dublin_edge": ["Kroger", "Starbucks", "McDonald's"],
        }

        self.mode_windows = {
            "breakfast": (360, 540),
            "lunch": (660, 840),
            "dinner": (1020, 1260),
            "late_night": (1260, 1439),
            "all_day": (360, 1380),
        }

    def _choose_zone(self) -> str:
        zones = list(self.zone_weights.keys())
        weights = list(self.zone_weights.values())
        return self.rng.choices(zones, weights=weights, k=1)[0]

    def _choose_merchant(self, zone: str) -> str:
        merchants = self.zone_merchants.get(zone, ["Chipotle"])
        return self.rng.choice(merchants)

    def _choose_timestamp(self, mode: str) -> int:
        mode_key = mode if mode in self.mode_windows else "dinner"
        start, end = self.mode_windows[mode_key]
        return self.rng.randint(start, end)

    def _pickup_miles(self, zone: str) -> float:
        zone_bias = {
            "osu": (0.2, 1.4),
            "short_north": (0.2, 1.3),
            "clintonville": (0.4, 2.2),
            "worthington": (0.4, 2.4),
            "beechwold": (0.5, 2.6),
            "northland": (0.6, 3.2),
            "ua_edge": (0.5, 2.8),
            "dublin_edge": (0.8, 3.8),
        }
        lo, hi = zone_bias.get(zone, (0.4, 2.5))
        return round(self.rng.uniform(lo, hi), 2)

    def _delivery_miles(self, zone: str) -> float:
        zone_bias = {
            "osu": (0.6, 3.0),
            "short_north": (0.8, 3.6),
            "clintonville": (1.0, 4.2),
            "worthington": (1.0, 4.6),
            "beechwold": (1.0, 4.3),
            "northland": (1.2, 5.4),
            "ua_edge": (1.0, 4.8),
            "dublin_edge": (1.5, 6.2),
        }
        lo, hi = zone_bias.get(zone, (1.0, 4.5))
        return round(self.rng.uniform(lo, hi), 2)

    def _return_buffer(self, delivery_miles: float) -> float:
        return round(max(0.5, delivery_miles * self.rng.uniform(0.15, 0.28)), 2)

    def _customer_fee(self, economic_miles: float, mode: str) -> float:
        base = 4.99 + (economic_miles * 0.55)
        if mode == "dinner":
            base += 1.00
        elif mode == "lunch":
            base += 0.70
        elif mode == "late_night":
            base += 1.20
        return round(base, 2)

    def _tip(self, merchant: str, economic_miles: float, mode: str) -> float:
        baseline = {
            "Starbucks": (1.00, 4.50),
            "McDonald's": (1.00, 5.00),
            "Chipotle": (1.50, 6.50),
            "Kroger": (2.00, 10.00),
            "Iron Grill BBQ & Breakfast": (1.50, 6.50),
            "Awadh India Restaurant": (1.80, 7.50),
            "Pizza Hut": (1.50, 6.00),
            "Ritzy's": (1.00, 5.50),
            "Taco Bell": (1.00, 5.00),
            "Wendy's": (1.00, 4.80),
        }.get(merchant, (1.25, 5.75))

        lo, hi = baseline
        tip = self.rng.uniform(lo, hi) + (economic_miles * self.rng.uniform(0.12, 0.35))

        if mode == "dinner":
            tip *= 1.05
        elif mode == "late_night":
            tip *= 0.98

        return round(tip, 2)

    def _base_pay(self, economic_miles: float, pressure_pay_boost: float) -> float:
        floor = 4.25
        mileage_component = economic_miles * 0.88
        raw = floor + mileage_component
        boosted = raw * pressure_pay_boost
        return round(boosted, 2)

    def _dropoff_type(self) -> str:
        return self.rng.choices(
            ["house", "apartment", "office", "campus"],
            weights=[46, 25, 10, 19],
            k=1,
        )[0]

    def _batch_size(self, batch_probability_boost: float) -> int:
        stacked_weight = min(0.30, 0.08 + batch_probability_boost)
        return 2 if self.rng.random() < stacked_weight else 1

    def generate_orders(
        self,
        count: int = 1000,
        duration_minutes: int = 240,
        weather: str = "clear",
        mode: str = "dinner",
    ) -> List[Dict[str, Any]]:
        orders: List[Dict[str, Any]] = []

        for idx in range(count):
            zone = self._choose_zone()
            merchant = self._choose_merchant(zone)
            timestamp_minute = self._choose_timestamp(mode)

            pressure = self.pressure_engine.get_pressure_snapshot(
                timestamp_minute=timestamp_minute,
                zone=zone,
                merchant=merchant,
                weather=weather,
                mode=mode,
            )

            pickup_miles = self._pickup_miles(zone)
            delivery_miles = self._delivery_miles(zone)
            return_buffer_miles = self._return_buffer(delivery_miles)

            economic_miles = round(pickup_miles + delivery_miles + return_buffer_miles, 2)

            base_trip_minutes = (
                pickup_miles * self.rng.uniform(2.4, 3.2)
                + delivery_miles * self.rng.uniform(3.1, 4.1)
                + return_buffer_miles * self.rng.uniform(1.4, 2.0)
            )

            merchant_delay_minutes = round(
                self.rng.uniform(3.0, 8.5) * pressure.merchant_delay_multiplier,
                2,
            )

            trip_minutes = round(
                (base_trip_minutes * pressure.traffic_multiplier) + merchant_delay_minutes,
                2,
            )

            batch_size = self._batch_size(pressure.batch_probability_boost)
            customer_fee = self._customer_fee(economic_miles, mode)
            tip = self._tip(merchant, economic_miles, mode)
            base_pay = self._base_pay(economic_miles, pressure.pay_boost_multiplier)
            offer_pay = round(base_pay + tip, 2)
            pay_per_economic_mile = round(offer_pay / max(economic_miles, 0.1), 2)

            order = OrderRecord(
                order_id=f"CBUS-{idx:06d}",
                zone=zone,
                merchant=merchant,
                pickup_miles=pickup_miles,
                delivery_miles=delivery_miles,
                return_buffer_miles=return_buffer_miles,
                economic_miles=economic_miles,
                trip_minutes=trip_minutes,
                merchant_delay_minutes=merchant_delay_minutes,
                traffic_multiplier=pressure.traffic_multiplier,
                base_pay=base_pay,
                tip=tip,
                customer_fee=customer_fee,
                offer_pay=offer_pay,
                pay_per_economic_mile=pay_per_economic_mile,
                batch_size=batch_size,
                mode=mode,
                weather=weather,
                dropoff_type=self._dropoff_type(),
                is_rush_hour=pressure.pressure_score >= 1.10,
                is_bad_weather=weather.lower() in {"rain", "heavy_rain", "snow", "storm"},
                timestamp_minute=timestamp_minute,
                pressure_score=pressure.pressure_score,
                pressure_demand_index=pressure.demand_index,
                pressure_supply_index=pressure.supply_index,
                pay_boost_multiplier=pressure.pay_boost_multiplier,
                batch_probability_boost=pressure.batch_probability_boost,
            )

            orders.append(asdict(order))

        return orders

    def summarize_orders(self, orders: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not orders:
            return {
                "total_orders": 0,
                "avg_offer_pay": 0.0,
                "avg_economic_miles": 0.0,
                "avg_trip_minutes": 0.0,
                "avg_customer_fee": 0.0,
                "avg_offer_per_economic_mile": 0.0,
                "avg_pressure_score": 0.0,
                "zone_distribution": {},
                "top_merchants": {},
            }

        total_orders = len(orders)
        avg_offer_pay = round(sum(o["offer_pay"] for o in orders) / total_orders, 2)
        avg_economic_miles = round(sum(o["economic_miles"] for o in orders) / total_orders, 2)
        avg_trip_minutes = round(sum(o["trip_minutes"] for o in orders) / total_orders, 2)
        avg_customer_fee = round(sum(o["customer_fee"] for o in orders) / total_orders, 2)
        avg_offer_per_economic_mile = round(
            sum(o["pay_per_economic_mile"] for o in orders) / total_orders,
            2,
        )
        avg_pressure_score = round(sum(o["pressure_score"] for o in orders) / total_orders, 3)

        zone_distribution: Dict[str, int] = {}
        merchant_distribution: Dict[str, int] = {}

        for order in orders:
            zone_distribution[order["zone"]] = zone_distribution.get(order["zone"], 0) + 1
            merchant_distribution[order["merchant"]] = merchant_distribution.get(order["merchant"], 0) + 1

        top_merchants = dict(
            sorted(merchant_distribution.items(), key=lambda item: item[1], reverse=True)[:10]
        )

        return {
            "total_orders": total_orders,
            "avg_offer_pay": avg_offer_pay,
            "avg_economic_miles": avg_economic_miles,
            "avg_trip_minutes": avg_trip_minutes,
            "avg_customer_fee": avg_customer_fee,
            "avg_offer_per_economic_mile": avg_offer_per_economic_mile,
            "avg_pressure_score": avg_pressure_score,
            "zone_distribution": zone_distribution,
            "top_merchants": top_merchants,
        }


def main() -> None:
    engine = ColumbusMarketEngine(seed=7)

    orders = engine.generate_orders(
        count=10_000,
        duration_minutes=240,
        weather="clear",
        mode="dinner",
    )

    summary = engine.summarize_orders(orders)

    print("Generated orders:", len(orders))
    print("Summary:", summary)
    print("Sample order:", orders[0])


if __name__ == "__main__":
    main()