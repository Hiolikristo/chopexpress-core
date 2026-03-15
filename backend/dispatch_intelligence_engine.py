from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple
import math


# ============================================================
# Safe helpers
# ============================================================

def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _get_xy(obj: Dict[str, Any], prefix: str = "") -> Tuple[float, float]:
    """
    Supports:
      x / y
      lat / lng
      pickup_x / pickup_y
      dropoff_x / dropoff_y
      etc.
    """
    x = obj.get(f"{prefix}x")
    y = obj.get(f"{prefix}y")

    if x is None and y is None:
        x = obj.get(f"{prefix}lat")
        y = obj.get(f"{prefix}lng")

    return _to_float(x), _to_float(y)


def _euclidean_miles(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    ax, ay = a
    bx, by = b
    return math.sqrt((ax - bx) ** 2 + (ay - by) ** 2)


def _zone_of(record: Dict[str, Any], default: str = "UNKNOWN") -> str:
    return (
        record.get("zone")
        or record.get("pickup_zone")
        or record.get("dropoff_zone")
        or default
    )


# ============================================================
# Optional external engine adapters
# ============================================================

class EconomicMilesAdapter:
    """
    Falls back to internal logic if external engine is absent.
    """

    def __init__(self) -> None:
        self.engine = None
        try:
            from economic_miles_engine import EconomicMilesEngine  # type: ignore
            self.engine = EconomicMilesEngine()
        except Exception:
            self.engine = None

    def estimate(
        self,
        driver: Dict[str, Any],
        order: Dict[str, Any],
        return_buffer_miles: float = 1.0,
    ) -> float:
        if self.engine is not None:
            for method_name in (
                "estimate_order_economic_miles",
                "calculate_order_economic_miles",
                "compute_order_economic_miles",
                "estimate",
                "calculate",
            ):
                fn = getattr(self.engine, method_name, None)
                if callable(fn):
                    try:
                        return _to_float(fn(driver, order), 0.0)
                    except TypeError:
                        pass
                    try:
                        return _to_float(fn(order), 0.0)
                    except TypeError:
                        pass

        driver_loc = _get_xy(driver)
        pickup_loc = _get_xy(order, "pickup_")
        if pickup_loc == (0.0, 0.0):
            pickup_loc = _get_xy(order)

        dropoff_loc = _get_xy(order, "dropoff_")
        if dropoff_loc == (0.0, 0.0):
            dropoff_loc = (
                _to_float(order.get("customer_x")),
                _to_float(order.get("customer_y")),
            )

        pickup_miles = _euclidean_miles(driver_loc, pickup_loc)
        trip_miles = _to_float(order.get("miles"), 0.0)
        if trip_miles <= 0:
            trip_miles = _euclidean_miles(pickup_loc, dropoff_loc)

        return pickup_miles + trip_miles + return_buffer_miles


class ProfitabilityAdapter:
    """
    Falls back to simple profit logic if external engine is absent.
    """

    def __init__(self) -> None:
        self.engine = None
        try:
            from driver_profitability_engine import DriverProfitabilityEngine  # type: ignore
            self.engine = DriverProfitabilityEngine()
        except Exception:
            self.engine = None

    def estimate(
        self,
        driver: Dict[str, Any],
        order: Dict[str, Any],
        economic_miles: float,
        fuel_cost_per_mile: float = 0.20,
    ) -> Dict[str, float]:
        if self.engine is not None:
            for method_name in (
                "estimate_offer_profitability",
                "estimate_profitability",
                "calculate_offer_profitability",
                "calculate",
                "estimate",
            ):
                fn = getattr(self.engine, method_name, None)
                if callable(fn):
                    try:
                        result = fn(driver, order, economic_miles)
                        if isinstance(result, dict):
                            return {
                                "gross_pay": _to_float(result.get("gross_pay"), 0.0),
                                "cost": _to_float(result.get("cost"), 0.0),
                                "net_profit": _to_float(result.get("net_profit"), 0.0),
                                "profit_per_mile": _to_float(result.get("profit_per_mile"), 0.0),
                            }
                    except TypeError:
                        pass

        gross_pay = _to_float(order.get("offer_pay"), 0.0)
        if gross_pay <= 0:
            gross_pay = _to_float(order.get("gross_pay"), 0.0)
        if gross_pay <= 0:
            gross_pay = _to_float(order.get("base_pay"), 0.0) + _to_float(order.get("tip"), 0.0)

        cost = economic_miles * fuel_cost_per_mile
        net_profit = gross_pay - cost
        ppm = net_profit / economic_miles if economic_miles > 0 else 0.0

        return {
            "gross_pay": gross_pay,
            "cost": cost,
            "net_profit": net_profit,
            "profit_per_mile": ppm,
        }


class MerchantDelayAdapter:
    def estimate_delay_minutes(self, order: Dict[str, Any]) -> float:
        merchant_delay = _to_float(order.get("merchant_delay_min"), -1.0)
        if merchant_delay >= 0:
            return merchant_delay

        prep_time = _to_float(order.get("prep_time_min"), -1.0)
        if prep_time >= 0:
            return prep_time

        merchant = order.get("merchant", {})
        if isinstance(merchant, dict):
            prep_time = _to_float(merchant.get("prep_time_min"), -1.0)
            if prep_time >= 0:
                return prep_time

        return 8.0


# ============================================================
# Dispatch scoring
# ============================================================

@dataclass
class DispatchDecision:
    driver_id: str
    order_id: str
    accepted: bool
    score: float
    reason: str

    driver_zone: str
    pickup_zone: str
    dropoff_zone: str

    pickup_miles: float
    trip_miles: float
    economic_miles: float

    gross_pay: float
    estimated_cost: float
    estimated_net_profit: float
    profit_per_mile: float

    merchant_delay_min: float
    fatigue_penalty: float
    zone_bonus: float
    tier_bonus: float
    fairness_bonus: float
    idle_bonus: float

    rule_flags: List[str]


class DispatchIntelligenceEngine:
    """
    ChopExpress V1 dispatch brain.

    Locked philosophy:
    - fairness first
    - driver profitability first
    - no coercive dispatch
    - zone-aware
    - delay-aware
    - economic miles aware
    """

    def __init__(
        self,
        max_pickup_miles: float = 2.5,
        min_profit_per_mile: float = 1.25,
        max_merchant_delay_min: float = 18.0,
        same_zone_bonus: float = 0.60,
        dropoff_home_zone_bonus: float = 0.35,
        fairness_recovery_bonus: float = 0.50,
        idle_bonus_weight: float = 0.03,
        fatigue_penalty_weight: float = 0.08,
        tier_bonus_map: Optional[Dict[str, float]] = None,
    ) -> None:
        self.max_pickup_miles = max_pickup_miles
        self.min_profit_per_mile = min_profit_per_mile
        self.max_merchant_delay_min = max_merchant_delay_min
        self.same_zone_bonus = same_zone_bonus
        self.dropoff_home_zone_bonus = dropoff_home_zone_bonus
        self.fairness_recovery_bonus = fairness_recovery_bonus
        self.idle_bonus_weight = idle_bonus_weight
        self.fatigue_penalty_weight = fatigue_penalty_weight
        self.tier_bonus_map = tier_bonus_map or {
            "CASUAL": 0.00,
            "PROFESSIONAL": 0.08,
            "PRO_PLUS": 0.15,
            "ELITE": 0.25,
        }

        self.economic_miles = EconomicMilesAdapter()
        self.profitability = ProfitabilityAdapter()
        self.merchant_delay = MerchantDelayAdapter()

    # --------------------------------------------------------
    # Rule helpers
    # --------------------------------------------------------

    def _pickup_miles(self, driver: Dict[str, Any], order: Dict[str, Any]) -> float:
        driver_loc = _get_xy(driver)
        pickup_loc = _get_xy(order, "pickup_")
        if pickup_loc == (0.0, 0.0):
            pickup_loc = _get_xy(order)
        return _euclidean_miles(driver_loc, pickup_loc)

    def _trip_miles(self, order: Dict[str, Any]) -> float:
        trip = _to_float(order.get("miles"), 0.0)
        if trip > 0:
            return trip

        pickup_loc = _get_xy(order, "pickup_")
        if pickup_loc == (0.0, 0.0):
            pickup_loc = _get_xy(order)

        dropoff_loc = _get_xy(order, "dropoff_")
        if dropoff_loc == (0.0, 0.0):
            dropoff_loc = (
                _to_float(order.get("customer_x")),
                _to_float(order.get("customer_y")),
            )

        return _euclidean_miles(pickup_loc, dropoff_loc)

    def _tier_bonus(self, driver: Dict[str, Any]) -> float:
        tier = str(driver.get("tier", "CASUAL")).upper()
        return self.tier_bonus_map.get(tier, 0.0)

    def _fatigue_penalty(self, driver: Dict[str, Any]) -> float:
        fatigue = _to_float(driver.get("fatigue_score"), 0.0)
        active_hours = _to_float(driver.get("active_hours"), 0.0)
        penalty = fatigue + (active_hours * self.fatigue_penalty_weight)
        return penalty

    def _zone_bonus(self, driver: Dict[str, Any], order: Dict[str, Any]) -> Tuple[float, List[str]]:
        flags: List[str] = []
        bonus = 0.0

        driver_zone = _zone_of(driver)
        pickup_zone = order.get("pickup_zone", "UNKNOWN")
        dropoff_zone = order.get("dropoff_zone", "UNKNOWN")

        home_zone = driver.get("home_zone", driver_zone)

        if driver_zone == pickup_zone:
            bonus += self.same_zone_bonus
            flags.append("same_zone_pickup")

        if dropoff_zone == home_zone:
            bonus += self.dropoff_home_zone_bonus
            flags.append("returns_toward_home_zone")

        return bonus, flags

    def _fairness_bonus(self, driver: Dict[str, Any]) -> Tuple[float, List[str]]:
        flags: List[str] = []
        bonus = 0.0

        recent_rejections = int(_to_float(driver.get("recent_rejections"), 0))
        recent_accepts = int(_to_float(driver.get("recent_accepts"), 0))
        idle_minutes = _to_float(driver.get("idle_minutes"), 0.0)

        if recent_accepts == 0 and recent_rejections >= 2:
            bonus += self.fairness_recovery_bonus
            flags.append("fairness_recovery_bonus")

        if idle_minutes > 0:
            bonus += idle_minutes * self.idle_bonus_weight
            flags.append("idle_priority_bonus")

        return bonus, flags

    # --------------------------------------------------------
    # Core evaluation
    # --------------------------------------------------------

    def evaluate_driver_for_order(
        self,
        driver: Dict[str, Any],
        order: Dict[str, Any],
    ) -> DispatchDecision:
        driver_id = str(driver.get("driver_id", driver.get("id", "unknown_driver")))
        order_id = str(order.get("order_id", order.get("id", "unknown_order")))

        driver_zone = _zone_of(driver)
        pickup_zone = str(order.get("pickup_zone", "UNKNOWN"))
        dropoff_zone = str(order.get("dropoff_zone", "UNKNOWN"))

        pickup_miles = self._pickup_miles(driver, order)
        trip_miles = self._trip_miles(order)
        economic_miles = self.economic_miles.estimate(driver, order)

        profit = self.profitability.estimate(driver, order, economic_miles)
        gross_pay = profit["gross_pay"]
        estimated_cost = profit["cost"]
        estimated_net_profit = profit["net_profit"]
        profit_per_mile = profit["profit_per_mile"]

        merchant_delay_min = self.merchant_delay.estimate_delay_minutes(order)
        fatigue_penalty = self._fatigue_penalty(driver)
        tier_bonus = self._tier_bonus(driver)
        zone_bonus, zone_flags = self._zone_bonus(driver, order)
        fairness_bonus, fairness_flags = self._fairness_bonus(driver)

        idle_bonus = max(0.0, _to_float(driver.get("idle_minutes"), 0.0) * self.idle_bonus_weight)
        flags: List[str] = []

        # --------------------------------------------
        # Hard rejection rules
        # --------------------------------------------
        if pickup_miles > self.max_pickup_miles:
            flags.append("hard_reject_long_pickup")
            return DispatchDecision(
                driver_id=driver_id,
                order_id=order_id,
                accepted=False,
                score=-999.0,
                reason="pickup_miles_exceeded",
                driver_zone=driver_zone,
                pickup_zone=pickup_zone,
                dropoff_zone=dropoff_zone,
                pickup_miles=pickup_miles,
                trip_miles=trip_miles,
                economic_miles=economic_miles,
                gross_pay=gross_pay,
                estimated_cost=estimated_cost,
                estimated_net_profit=estimated_net_profit,
                profit_per_mile=profit_per_mile,
                merchant_delay_min=merchant_delay_min,
                fatigue_penalty=fatigue_penalty,
                zone_bonus=zone_bonus,
                tier_bonus=tier_bonus,
                fairness_bonus=fairness_bonus,
                idle_bonus=idle_bonus,
                rule_flags=flags,
            )

        if profit_per_mile < self.min_profit_per_mile:
            flags.append("hard_reject_low_profit_per_mile")
            return DispatchDecision(
                driver_id=driver_id,
                order_id=order_id,
                accepted=False,
                score=-998.0,
                reason="profit_per_mile_below_floor",
                driver_zone=driver_zone,
                pickup_zone=pickup_zone,
                dropoff_zone=dropoff_zone,
                pickup_miles=pickup_miles,
                trip_miles=trip_miles,
                economic_miles=economic_miles,
                gross_pay=gross_pay,
                estimated_cost=estimated_cost,
                estimated_net_profit=estimated_net_profit,
                profit_per_mile=profit_per_mile,
                merchant_delay_min=merchant_delay_min,
                fatigue_penalty=fatigue_penalty,
                zone_bonus=zone_bonus,
                tier_bonus=tier_bonus,
                fairness_bonus=fairness_bonus,
                idle_bonus=idle_bonus,
                rule_flags=flags,
            )

        if merchant_delay_min > self.max_merchant_delay_min:
            flags.append("delay_risk_penalty")
            # Not a hard reject, just severe penalty

        # --------------------------------------------
        # Score formula
        # --------------------------------------------
        score = 0.0

        # Profitability dominates
        score += estimated_net_profit * 1.25
        score += profit_per_mile * 2.50

        # Penalize economic exposure and long pickup
        score -= economic_miles * 0.70
        score -= pickup_miles * 1.00

        # Delay/fatigue penalties
        score -= merchant_delay_min * 0.10
        score -= fatigue_penalty

        # Bonuses
        score += tier_bonus
        score += zone_bonus
        score += fairness_bonus
        score += idle_bonus

        flags.extend(zone_flags)
        flags.extend(fairness_flags)

        if merchant_delay_min <= 8:
            flags.append("fast_merchant")
        if profit_per_mile >= 1.75:
            flags.append("strong_profitability")
        if estimated_net_profit >= 4.50:
            flags.append("strong_net_profit")
        if pickup_miles <= 1.0:
            flags.append("short_pickup")

        return DispatchDecision(
            driver_id=driver_id,
            order_id=order_id,
            accepted=True,
            score=score,
            reason="dispatch_candidate",
            driver_zone=driver_zone,
            pickup_zone=pickup_zone,
            dropoff_zone=dropoff_zone,
            pickup_miles=pickup_miles,
            trip_miles=trip_miles,
            economic_miles=economic_miles,
            gross_pay=gross_pay,
            estimated_cost=estimated_cost,
            estimated_net_profit=estimated_net_profit,
            profit_per_mile=profit_per_mile,
            merchant_delay_min=merchant_delay_min,
            fatigue_penalty=fatigue_penalty,
            zone_bonus=zone_bonus,
            tier_bonus=tier_bonus,
            fairness_bonus=fairness_bonus,
            idle_bonus=idle_bonus,
            rule_flags=flags,
        )

    def rank_drivers_for_order(
        self,
        drivers: List[Dict[str, Any]],
        order: Dict[str, Any],
    ) -> List[DispatchDecision]:
        decisions = [self.evaluate_driver_for_order(driver, order) for driver in drivers]
        accepted = [d for d in decisions if d.accepted]
        rejected = [d for d in decisions if not d.accepted]

        accepted.sort(key=lambda d: d.score, reverse=True)
        rejected.sort(key=lambda d: d.score, reverse=True)
        return accepted + rejected

    def select_best_driver(
        self,
        drivers: List[Dict[str, Any]],
        order: Dict[str, Any],
    ) -> Optional[DispatchDecision]:
        ranked = self.rank_drivers_for_order(drivers, order)
        for decision in ranked:
            if decision.accepted:
                return decision
        return None

    def assign_orders(
        self,
        drivers: List[Dict[str, Any]],
        orders: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Greedy V1 dispatcher:
        - ranks drivers per order
        - prevents double-assignment in same cycle
        """
        assigned_driver_ids = set()
        assignments: List[Dict[str, Any]] = []
        unassigned_orders: List[Dict[str, Any]] = []

        for order in orders:
            available_drivers = [
                d for d in drivers
                if str(d.get("driver_id", d.get("id", ""))) not in assigned_driver_ids
            ]

            best = self.select_best_driver(available_drivers, order)
            if best is None:
                unassigned_orders.append({
                    "order_id": order.get("order_id", order.get("id", "unknown_order")),
                    "reason": "no_qualified_driver",
                })
                continue

            assigned_driver_ids.add(best.driver_id)
            assignments.append(asdict(best))

        return {
            "total_orders": len(orders),
            "assigned_orders": len(assignments),
            "unassigned_orders": len(unassigned_orders),
            "assignments": assignments,
            "unassigned": unassigned_orders,
        }


# ============================================================
# Demo
# ============================================================

def _demo() -> Dict[str, Any]:
    engine = DispatchIntelligenceEngine()

    drivers = [
        {
            "driver_id": "D1",
            "x": 0.0,
            "y": 0.0,
            "zone": "MORSE",
            "home_zone": "MORSE",
            "tier": "CASUAL",
            "idle_minutes": 22,
            "recent_rejections": 2,
            "recent_accepts": 0,
            "fatigue_score": 0.4,
            "active_hours": 2.0,
        },
        {
            "driver_id": "D2",
            "x": 1.2,
            "y": 0.6,
            "zone": "MORSE",
            "home_zone": "POLARIS",
            "tier": "PROFESSIONAL",
            "idle_minutes": 8,
            "recent_rejections": 0,
            "recent_accepts": 2,
            "fatigue_score": 0.3,
            "active_hours": 3.5,
        },
        {
            "driver_id": "D3",
            "x": 3.8,
            "y": 3.2,
            "zone": "POLARIS",
            "home_zone": "POLARIS",
            "tier": "ELITE",
            "idle_minutes": 3,
            "recent_rejections": 0,
            "recent_accepts": 4,
            "fatigue_score": 0.6,
            "active_hours": 6.0,
        },
    ]

    orders = [
        {
            "order_id": "O1",
            "pickup_x": 0.7,
            "pickup_y": 0.4,
            "dropoff_x": 1.3,
            "dropoff_y": 0.9,
            "pickup_zone": "MORSE",
            "dropoff_zone": "MORSE",
            "miles": 2.4,
            "offer_pay": 8.25,
            "prep_time_min": 7,
        },
        {
            "order_id": "O2",
            "pickup_x": 3.5,
            "pickup_y": 3.3,
            "dropoff_x": 4.2,
            "dropoff_y": 3.8,
            "pickup_zone": "POLARIS",
            "dropoff_zone": "POLARIS",
            "miles": 2.7,
            "offer_pay": 9.75,
            "prep_time_min": 6,
        },
    ]

    return engine.assign_orders(drivers, orders)


def main() -> Dict[str, Any]:
    return _demo()


if __name__ == "__main__":
    import json
    print(json.dumps(main(), indent=2))