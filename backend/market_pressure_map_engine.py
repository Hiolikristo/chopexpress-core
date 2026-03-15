from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, Any


@dataclass
class ZonePressureResult:
    zone: str
    open_orders: int
    online_drivers: int
    backlog: int
    demand_supply_ratio: float
    pressure_score: float
    severity: str


class MarketPressureMapEngine:
    """
    Computes zone-level marketplace pressure.

    pressure_score baseline:
    - 1.00 = balanced
    - > 1.00 = driver shortage / order pressure
    - < 1.00 = driver surplus
    """

    def __init__(
        self,
        min_pressure: float = 0.85,
        max_pressure: float = 1.80,
        backlog_weight: float = 0.35,
        order_weight: float = 1.00,
    ) -> None:
        self.min_pressure = min_pressure
        self.max_pressure = max_pressure
        self.backlog_weight = backlog_weight
        self.order_weight = order_weight

    @staticmethod
    def _safe_ratio(numerator: float, denominator: float) -> float:
        if denominator <= 0:
            return float(numerator) if numerator > 0 else 1.0
        return numerator / denominator

    def calculate_zone_pressure(
        self,
        zone: str,
        open_orders: int,
        online_drivers: int,
        backlog: int,
    ) -> Dict[str, Any]:
        weighted_demand = (open_orders * self.order_weight) + (backlog * self.backlog_weight)
        ratio = self._safe_ratio(weighted_demand, max(online_drivers, 1))

        # Convert raw ratio into a bounded marketplace multiplier.
        # Ratio near 1.0 => pressure near 1.0
        # Lower demand than supply => slight discount, but bounded
        # Higher demand than supply => surge pressure, but bounded
        raw_pressure = 0.90 + (ratio * 0.45)
        pressure_score = max(self.min_pressure, min(self.max_pressure, round(raw_pressure, 2)))

        if pressure_score >= 1.45:
            severity = "extreme"
        elif pressure_score >= 1.20:
            severity = "high"
        elif pressure_score >= 1.05:
            severity = "moderate"
        elif pressure_score <= 0.95:
            severity = "low"
        else:
            severity = "balanced"

        result = ZonePressureResult(
            zone=zone,
            open_orders=open_orders,
            online_drivers=online_drivers,
            backlog=backlog,
            demand_supply_ratio=round(ratio, 2),
            pressure_score=pressure_score,
            severity=severity,
        )
        return asdict(result)

    def calculate_market_pressure(
        self,
        zone_order_counts: Dict[str, int],
        zone_driver_counts: Dict[str, int],
        zone_backlog_counts: Dict[str, int],
    ) -> Dict[str, Dict[str, Any]]:
        all_zones = sorted(
            set(zone_order_counts.keys())
            | set(zone_driver_counts.keys())
            | set(zone_backlog_counts.keys())
        )

        results: Dict[str, Dict[str, Any]] = {}
        for zone in all_zones:
            results[zone] = self.calculate_zone_pressure(
                zone=zone,
                open_orders=zone_order_counts.get(zone, 0),
                online_drivers=zone_driver_counts.get(zone, 0),
                backlog=zone_backlog_counts.get(zone, 0),
            )
        return results


def calculate_market_pressure(
    zone_order_counts: Dict[str, int],
    zone_driver_counts: Dict[str, int],
    zone_backlog_counts: Dict[str, int],
) -> Dict[str, Dict[str, Any]]:
    engine = MarketPressureMapEngine()
    return engine.calculate_market_pressure(
        zone_order_counts=zone_order_counts,
        zone_driver_counts=zone_driver_counts,
        zone_backlog_counts=zone_backlog_counts,
    )