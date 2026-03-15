from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class MarketPressureSnapshot:
    timestamp_minute: int
    hour_float: float
    mode: str
    weather: str
    zone: str
    merchant: str
    demand_index: float
    supply_index: float
    pressure_score: float
    traffic_multiplier: float
    merchant_delay_multiplier: float
    pay_boost_multiplier: float
    batch_probability_boost: float
    notes: str


class MarketPressureEngine:
    """
    Models city pressure conditions for dispatch and market simulation.

    Core concepts:
    - demand_index: how much order demand pressure is present
    - supply_index: how much driver supply is available
    - pressure_score: demand / supply adjusted signal
    - traffic_multiplier: raises travel time under heavier conditions
    - merchant_delay_multiplier: raises prep/wait time at busy merchants
    - pay_boost_multiplier: simulates fairness-aware incentive uplift
    - batch_probability_boost: chance of stacked/batched orders increasing
    """

    def __init__(self) -> None:
        self.zone_base_pressure: Dict[str, float] = {
            "worthington": 0.96,
            "clintonville": 1.04,
            "beechwold": 0.95,
            "northland": 0.98,
            "osu": 1.18,
            "short_north": 1.22,
            "ua_edge": 1.01,
            "dublin_edge": 0.97,
        }

        self.zone_supply_bias: Dict[str, float] = {
            "worthington": 1.02,
            "clintonville": 1.00,
            "beechwold": 0.98,
            "northland": 0.96,
            "osu": 0.92,
            "short_north": 0.90,
            "ua_edge": 1.01,
            "dublin_edge": 1.03,
        }

        self.merchant_pressure: Dict[str, float] = {
            "kroger": 1.18,
            "starbucks": 1.12,
            "chipotle": 1.16,
            "iron grill bbq & breakfast": 1.10,
            "awadh india restaurant": 1.06,
            "mcdonald's": 1.20,
            "pizza hut": 1.08,
            "ritzy's": 1.03,
            "taco bell": 1.11,
            "wendy's": 1.10,
        }

    @staticmethod
    def _hour_from_minute(timestamp_minute: int) -> float:
        return (timestamp_minute % 1440) / 60.0

    @staticmethod
    def _normalize_label(value: Optional[str], fallback: str) -> str:
        if not value:
            return fallback
        return str(value).strip().lower()

    def _time_of_day_demand_multiplier(self, hour_float: float, mode: str) -> float:
        if 6.0 <= hour_float < 9.0:
            breakfast = 1.05
        else:
            breakfast = 0.90

        if 11.0 <= hour_float < 14.0:
            lunch = 1.28
        else:
            lunch = 0.92

        if 17.0 <= hour_float < 21.0:
            dinner = 1.36
        else:
            dinner = 0.94

        if 21.0 <= hour_float < 24.0:
            late_night = 1.08
        else:
            late_night = 0.96

        mode = self._normalize_label(mode, "dinner")

        if mode == "breakfast":
            return breakfast
        if mode == "lunch":
            return lunch
        if mode == "late_night":
            return late_night
        if mode == "all_day":
            return max(breakfast, lunch, dinner, late_night)

        return dinner

    def _time_of_day_supply_multiplier(self, hour_float: float) -> float:
        if 6.0 <= hour_float < 9.0:
            return 0.92
        if 11.0 <= hour_float < 14.0:
            return 0.95
        if 17.0 <= hour_float < 21.0:
            return 0.90
        if 21.0 <= hour_float < 24.0:
            return 0.88
        return 1.00

    def _weather_demand_multiplier(self, weather: str) -> float:
        weather = self._normalize_label(weather, "clear")
        mapping = {
            "clear": 1.00,
            "cloudy": 1.01,
            "windy": 1.02,
            "light_rain": 1.10,
            "rain": 1.18,
            "heavy_rain": 1.28,
            "snow": 1.34,
            "storm": 1.40,
        }
        return mapping.get(weather, 1.00)

    def _weather_supply_multiplier(self, weather: str) -> float:
        weather = self._normalize_label(weather, "clear")
        mapping = {
            "clear": 1.00,
            "cloudy": 1.00,
            "windy": 0.99,
            "light_rain": 0.95,
            "rain": 0.90,
            "heavy_rain": 0.84,
            "snow": 0.78,
            "storm": 0.70,
        }
        return mapping.get(weather, 1.00)

    def _weather_traffic_multiplier(self, weather: str) -> float:
        weather = self._normalize_label(weather, "clear")
        mapping = {
            "clear": 1.00,
            "cloudy": 1.01,
            "windy": 1.02,
            "light_rain": 1.08,
            "rain": 1.15,
            "heavy_rain": 1.24,
            "snow": 1.30,
            "storm": 1.36,
        }
        return mapping.get(weather, 1.00)

    def _weather_delay_multiplier(self, weather: str) -> float:
        weather = self._normalize_label(weather, "clear")
        mapping = {
            "clear": 1.00,
            "cloudy": 1.01,
            "windy": 1.02,
            "light_rain": 1.05,
            "rain": 1.10,
            "heavy_rain": 1.16,
            "snow": 1.22,
            "storm": 1.28,
        }
        return mapping.get(weather, 1.00)

    def _daypart_note(self, hour_float: float) -> str:
        if 6.0 <= hour_float < 9.0:
            return "breakfast_window"
        if 11.0 <= hour_float < 14.0:
            return "lunch_rush"
        if 17.0 <= hour_float < 21.0:
            return "dinner_rush"
        if 21.0 <= hour_float < 24.0:
            return "late_night_window"
        return "off_peak"

    def get_pressure_snapshot(
        self,
        *,
        timestamp_minute: int,
        zone: str,
        merchant: str,
        weather: str = "clear",
        mode: str = "dinner",
        active_driver_count: Optional[int] = None,
        active_order_count: Optional[int] = None,
    ) -> MarketPressureSnapshot:
        zone_key = self._normalize_label(zone, "worthington")
        merchant_key = self._normalize_label(merchant, "unknown")
        weather_key = self._normalize_label(weather, "clear")
        mode_key = self._normalize_label(mode, "dinner")

        hour_float = self._hour_from_minute(timestamp_minute)

        zone_pressure = self.zone_base_pressure.get(zone_key, 1.00)
        zone_supply = self.zone_supply_bias.get(zone_key, 1.00)
        merchant_pressure = self.merchant_pressure.get(merchant_key, 1.00)

        demand_index = (
            zone_pressure
            * merchant_pressure
            * self._time_of_day_demand_multiplier(hour_float, mode_key)
            * self._weather_demand_multiplier(weather_key)
        )

        supply_index = (
            zone_supply
            * self._time_of_day_supply_multiplier(hour_float)
            * self._weather_supply_multiplier(weather_key)
        )

        if active_driver_count is not None and active_driver_count > 0:
            # higher driver count eases pressure
            driver_supply_factor = min(1.25, max(0.75, active_driver_count / 100.0))
            supply_index *= driver_supply_factor

        if active_order_count is not None and active_order_count > 0:
            # higher active orders raise pressure
            order_pressure_factor = min(1.30, max(0.85, active_order_count / 100.0))
            demand_index *= order_pressure_factor

        pressure_score = demand_index / max(supply_index, 0.50)

        traffic_multiplier = (
            1.00
            + max(0.0, (pressure_score - 1.0)) * 0.10
        ) * self._weather_traffic_multiplier(weather_key)

        merchant_delay_multiplier = (
            1.00
            + max(0.0, (pressure_score - 1.0)) * 0.12
        ) * self._weather_delay_multiplier(weather_key)

        pay_boost_multiplier = 1.00 + max(0.0, pressure_score - 1.0) * 0.18
        batch_probability_boost = max(0.0, pressure_score - 1.0) * 0.20

        notes = ",".join(
            [
                self._daypart_note(hour_float),
                f"zone={zone_key}",
                f"merchant={merchant_key}",
                f"weather={weather_key}",
                f"mode={mode_key}",
            ]
        )

        return MarketPressureSnapshot(
            timestamp_minute=timestamp_minute,
            hour_float=round(hour_float, 2),
            mode=mode_key,
            weather=weather_key,
            zone=zone_key,
            merchant=merchant_key,
            demand_index=round(demand_index, 4),
            supply_index=round(supply_index, 4),
            pressure_score=round(pressure_score, 4),
            traffic_multiplier=round(traffic_multiplier, 4),
            merchant_delay_multiplier=round(merchant_delay_multiplier, 4),
            pay_boost_multiplier=round(pay_boost_multiplier, 4),
            batch_probability_boost=round(batch_probability_boost, 4),
            notes=notes,
        )

    def to_dict(self, snapshot: MarketPressureSnapshot) -> Dict[str, Any]:
        return {
            "timestamp_minute": snapshot.timestamp_minute,
            "hour_float": snapshot.hour_float,
            "mode": snapshot.mode,
            "weather": snapshot.weather,
            "zone": snapshot.zone,
            "merchant": snapshot.merchant,
            "demand_index": snapshot.demand_index,
            "supply_index": snapshot.supply_index,
            "pressure_score": snapshot.pressure_score,
            "traffic_multiplier": snapshot.traffic_multiplier,
            "merchant_delay_multiplier": snapshot.merchant_delay_multiplier,
            "pay_boost_multiplier": snapshot.pay_boost_multiplier,
            "batch_probability_boost": snapshot.batch_probability_boost,
            "notes": snapshot.notes,
        }