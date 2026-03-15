from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional
import math

from backend.market_pressure_map_engine import calculate_market_pressure


# ============================================================
# ChopExpress V1 Fairness-First Dispatch Engine
# ============================================================

DEFAULT_DISPATCH_CONFIG: Dict[str, Any] = {
    "base_floor": 4.25,
    "mileage_rate": 1.35,
    "merchant_delay_rate_per_min": 0.18,
    "traffic_multiplier_weight": 0.85,
    "batch_bonus_per_extra_order": 1.10,
    "rush_hour_bonus": 0.75,
    "weather_bonus": 1.25,
    "apartment_bonus": 0.50,
    "gated_bonus": 0.35,
    "minimum_fair_offer": 5.60,
    "minimum_effective_pay_per_mile": 1.65,
    "max_pickup_radius_miles": 8.0,
    "driver_reposition_rate_per_mile": 0.55,
    "zone_preference_bonus": 0.60,
    "zone_penalty": 0.50,
    "driver_fatigue_penalty": 0.10,
    "driver_decline_penalty": 0.15,
    "priority_score_weight_offer": 0.45,
    "priority_score_weight_distance": 0.15,
    "priority_score_weight_delay": 0.15,
    "priority_score_weight_zone": 0.10,
    "priority_score_weight_fatigue": 0.10,
    "priority_score_weight_tier": 0.05,
    "tier_multipliers": {
        "casual": 1.00,
        "professional": 1.06,
        "pro": 1.10,
        "elite": 1.15,
    },
}


# ============================================================
# Helpers
# ============================================================

def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        result = float(value)
        if math.isnan(result) or math.isinf(result):
            return default
        return result
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _norm_zone(zone: Any) -> str:
    if zone is None:
        return "unknown"
    return str(zone).strip().lower()


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


# ============================================================
# Data Models
# ============================================================

@dataclass
class DriverState:
    driver_id: str
    name: str
    zone: str
    tier: str = "casual"
    online: bool = True
    active_order_id: Optional[str] = None
    acceptance_rate: float = 1.0
    fatigue_score: float = 0.0
    recent_declines: int = 0
    reposition_miles: float = 0.0
    preferred_zones: Optional[List[str]] = None

    def normalized_tier(self) -> str:
        tier = str(self.tier).strip().lower()
        if tier in ("proplus", "pro plus", "pro_plus"):
            return "pro"
        if tier not in ("casual", "professional", "pro", "elite"):
            return "casual"
        return tier


@dataclass
class OrderInput:
    order_id: str
    zone: str
    merchant_name: str
    merchant_type: str
    pickup_miles: float
    dropoff_miles: float
    return_buffer_miles: float
    pickup_minutes: float
    delivery_minutes: float
    merchant_delay_minutes: float
    traffic_multiplier: float
    tip: float
    customer_fee: float
    batch_size: int = 1
    is_rush_hour: bool = False
    is_bad_weather: bool = False
    is_apartment_dropoff: bool = False
    is_gated_dropoff: bool = False

    @property
    def total_economic_miles(self) -> float:
        return round(self.pickup_miles + self.dropoff_miles + self.return_buffer_miles, 2)

    @property
    def total_minutes(self) -> float:
        return round(self.pickup_minutes + self.delivery_minutes + self.merchant_delay_minutes, 2)


@dataclass
class OfferBreakdown:
    base_floor: float
    mileage_component: float
    merchant_delay_component: float
    traffic_component: float
    batch_component: float
    rush_component: float
    weather_component: float
    apartment_component: float
    gated_component: float
    reposition_component: float
    zone_pressure_multiplier: float
    tier_multiplier: float
    pre_tier_subtotal: float
    final_offer: float
    effective_pay_per_mile: float
    blocked: bool
    block_reason: Optional[str] = None


@dataclass
class DriverEvaluation:
    driver_id: str
    driver_name: str
    zone_match: str
    reposition_miles: float
    tier: str
    fatigue_score: float
    recent_declines: int
    candidate_offer: float
    effective_pay_per_mile: float
    dispatch_score: float
    eligible: bool
    reason: Optional[str] = None


@dataclass
class DispatchDecision:
    accepted: bool
    order_id: str
    assigned_driver_id: Optional[str]
    assigned_driver_name: Optional[str]
    offer_amount: float
    effective_pay_per_mile: float
    total_economic_miles: float
    total_minutes: float
    status: str
    reason: str
    breakdown: Dict[str, Any]
    driver_evaluations: List[Dict[str, Any]]


# ============================================================
# Engine
# ============================================================

class DispatchEngine:
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = dict(DEFAULT_DISPATCH_CONFIG)
        if config:
            self.config.update(config)

    def _normalize_driver(self, driver: Dict[str, Any]) -> DriverState:
        return DriverState(
            driver_id=str(driver.get("driver_id", "unknown")),
            name=str(driver.get("name", "Unknown Driver")),
            zone=_norm_zone(driver.get("zone")),
            tier=str(driver.get("tier", "casual")),
            online=bool(driver.get("online", True)),
            active_order_id=driver.get("active_order_id"),
            acceptance_rate=_safe_float(driver.get("acceptance_rate", 1.0), 1.0),
            fatigue_score=_safe_float(driver.get("fatigue_score", 0.0)),
            recent_declines=_safe_int(driver.get("recent_declines", 0)),
            reposition_miles=_safe_float(driver.get("reposition_miles", 0.0)),
            preferred_zones=driver.get("preferred_zones"),
        )

    def _normalize_order(self, order: Dict[str, Any]) -> OrderInput:
        return OrderInput(
            order_id=str(order.get("order_id", "unknown")),
            zone=_norm_zone(order.get("zone")),
            merchant_name=str(order.get("merchant_name", "Unknown Merchant")),
            merchant_type=str(order.get("merchant_type", "restaurant")),
            pickup_miles=_safe_float(order.get("pickup_miles", 0.0)),
            dropoff_miles=_safe_float(order.get("dropoff_miles", 0.0)),
            return_buffer_miles=_safe_float(order.get("return_buffer_miles", 0.0)),
            pickup_minutes=_safe_float(order.get("pickup_minutes", 0.0)),
            delivery_minutes=_safe_float(order.get("delivery_minutes", 0.0)),
            merchant_delay_minutes=_safe_float(order.get("merchant_delay_minutes", 0.0)),
            traffic_multiplier=_safe_float(order.get("traffic_multiplier", 1.0), 1.0),
            tip=_safe_float(order.get("tip", 0.0)),
            customer_fee=_safe_float(order.get("customer_fee", 0.0)),
            batch_size=max(1, _safe_int(order.get("batch_size", 1), 1)),
            is_rush_hour=bool(order.get("is_rush_hour", False)),
            is_bad_weather=bool(order.get("is_bad_weather", False)),
            is_apartment_dropoff=bool(order.get("is_apartment_dropoff", False)),
            is_gated_dropoff=bool(order.get("is_gated_dropoff", False)),
        )

    def should_block_offer(
        self,
        final_offer: float,
        effective_pay_per_mile: float,
        total_economic_miles: float,
    ) -> tuple[bool, Optional[str]]:
        if final_offer < _safe_float(self.config["minimum_fair_offer"]):
            return True, "below_minimum_fair_offer"

        if effective_pay_per_mile < _safe_float(self.config["minimum_effective_pay_per_mile"]):
            return True, "below_minimum_effective_pay_per_mile"

        if total_economic_miles > _safe_float(self.config["max_pickup_radius_miles"]) + 20:
            return True, "excessive_total_economic_miles"

        return False, None

    def generate_fair_offer(
        self,
        order: Dict[str, Any],
        reposition_miles: float = 0.0,
        driver_tier: str = "casual",
        zone_pressure_multiplier: float = 1.0,
    ) -> OfferBreakdown:
        normalized = self._normalize_order(order)
        tier_key = DriverState(
            driver_id="temp",
            name="temp",
            zone=normalized.zone,
            tier=driver_tier,
        ).normalized_tier()
        tier_multiplier = _safe_float(self.config["tier_multipliers"].get(tier_key, 1.0), 1.0)

        base_floor = _safe_float(self.config["base_floor"])
        mileage_component = normalized.total_economic_miles * _safe_float(self.config["mileage_rate"])
        merchant_delay_component = (
            normalized.merchant_delay_minutes * _safe_float(self.config["merchant_delay_rate_per_min"])
        )

        traffic_pressure = max(normalized.traffic_multiplier - 1.0, 0.0)
        traffic_component = (
            normalized.total_economic_miles
            * traffic_pressure
            * _safe_float(self.config["traffic_multiplier_weight"])
        )

        batch_component = max(normalized.batch_size - 1, 0) * _safe_float(self.config["batch_bonus_per_extra_order"])
        rush_component = _safe_float(self.config["rush_hour_bonus"]) if normalized.is_rush_hour else 0.0
        weather_component = _safe_float(self.config["weather_bonus"]) if normalized.is_bad_weather else 0.0
        apartment_component = _safe_float(self.config["apartment_bonus"]) if normalized.is_apartment_dropoff else 0.0
        gated_component = _safe_float(self.config["gated_bonus"]) if normalized.is_gated_dropoff else 0.0
        reposition_component = reposition_miles * _safe_float(self.config["driver_reposition_rate_per_mile"])

        pre_tier_subtotal = (
            base_floor
            + mileage_component
            + merchant_delay_component
            + traffic_component
            + batch_component
            + rush_component
            + weather_component
            + apartment_component
            + gated_component
            + reposition_component
        )

        zone_pressure_multiplier = _clamp(zone_pressure_multiplier, 0.85, 1.80)

        final_offer = round(pre_tier_subtotal * tier_multiplier * zone_pressure_multiplier, 2)
        effective_pay_per_mile = round(final_offer / max(normalized.total_economic_miles, 0.01), 2)

        blocked, reason = self.should_block_offer(
            final_offer=final_offer,
            effective_pay_per_mile=effective_pay_per_mile,
            total_economic_miles=normalized.total_economic_miles,
        )

        return OfferBreakdown(
            base_floor=round(base_floor, 2),
            mileage_component=round(mileage_component, 2),
            merchant_delay_component=round(merchant_delay_component, 2),
            traffic_component=round(traffic_component, 2),
            batch_component=round(batch_component, 2),
            rush_component=round(rush_component, 2),
            weather_component=round(weather_component, 2),
            apartment_component=round(apartment_component, 2),
            gated_component=round(gated_component, 2),
            reposition_component=round(reposition_component, 2),
            zone_pressure_multiplier=round(zone_pressure_multiplier, 2),
            tier_multiplier=round(tier_multiplier, 4),
            pre_tier_subtotal=round(pre_tier_subtotal, 2),
            final_offer=final_offer,
            effective_pay_per_mile=effective_pay_per_mile,
            blocked=blocked,
            block_reason=reason,
        )

    def evaluate_driver(
        self,
        driver: Dict[str, Any],
        order: Dict[str, Any],
        zone_pressure_multiplier: float = 1.0,
    ) -> DriverEvaluation:
        normalized_driver = self._normalize_driver(driver)
        normalized_order = self._normalize_order(order)

        if not normalized_driver.online:
            return DriverEvaluation(
                driver_id=normalized_driver.driver_id,
                driver_name=normalized_driver.name,
                zone_match="offline",
                reposition_miles=0.0,
                tier=normalized_driver.normalized_tier(),
                fatigue_score=normalized_driver.fatigue_score,
                recent_declines=normalized_driver.recent_declines,
                candidate_offer=0.0,
                effective_pay_per_mile=0.0,
                dispatch_score=-999.0,
                eligible=False,
                reason="driver_offline",
            )

        if normalized_driver.active_order_id:
            return DriverEvaluation(
                driver_id=normalized_driver.driver_id,
                driver_name=normalized_driver.name,
                zone_match="busy",
                reposition_miles=0.0,
                tier=normalized_driver.normalized_tier(),
                fatigue_score=normalized_driver.fatigue_score,
                recent_declines=normalized_driver.recent_declines,
                candidate_offer=0.0,
                effective_pay_per_mile=0.0,
                dispatch_score=-999.0,
                eligible=False,
                reason="driver_busy",
            )

        zone_match = "same_zone" if normalized_driver.zone == normalized_order.zone else "reposition"
        reposition_miles = 0.0 if zone_match == "same_zone" else max(normalized_driver.reposition_miles, 1.5)

        offer = self.generate_fair_offer(
            order=order,
            reposition_miles=reposition_miles,
            driver_tier=normalized_driver.normalized_tier(),
            zone_pressure_multiplier=zone_pressure_multiplier,
        )

        if offer.blocked:
            return DriverEvaluation(
                driver_id=normalized_driver.driver_id,
                driver_name=normalized_driver.name,
                zone_match=zone_match,
                reposition_miles=reposition_miles,
                tier=normalized_driver.normalized_tier(),
                fatigue_score=normalized_driver.fatigue_score,
                recent_declines=normalized_driver.recent_declines,
                candidate_offer=offer.final_offer,
                effective_pay_per_mile=offer.effective_pay_per_mile,
                dispatch_score=-500.0,
                eligible=False,
                reason=offer.block_reason,
            )

        zone_score = 1.0 if zone_match == "same_zone" else max(
            0.0,
            1.0 - (reposition_miles / max(_safe_float(self.config["max_pickup_radius_miles"]), 0.01)),
        )

        tier_score_map = {
            "casual": 0.65,
            "professional": 0.80,
            "pro": 0.90,
            "elite": 1.00,
        }

        tier_score = tier_score_map.get(normalized_driver.normalized_tier(), 0.65)
        offer_score = min(offer.effective_pay_per_mile / max(_safe_float(self.config["minimum_effective_pay_per_mile"]), 0.01), 2.0)
        distance_score = max(0.0, 1.0 - (reposition_miles / 10.0))
        delay_score = min(normalized_order.merchant_delay_minutes / 15.0, 1.0)
        fatigue_penalty = normalized_driver.fatigue_score * _safe_float(self.config["driver_fatigue_penalty"])
        decline_penalty = normalized_driver.recent_declines * _safe_float(self.config["driver_decline_penalty"])

        dispatch_score = (
            offer_score * _safe_float(self.config["priority_score_weight_offer"])
            + distance_score * _safe_float(self.config["priority_score_weight_distance"])
            + delay_score * _safe_float(self.config["priority_score_weight_delay"])
            + zone_score * _safe_float(self.config["priority_score_weight_zone"])
            + tier_score * _safe_float(self.config["priority_score_weight_tier"])
            - fatigue_penalty * _safe_float(self.config["priority_score_weight_fatigue"])
            - decline_penalty
        )

        return DriverEvaluation(
            driver_id=normalized_driver.driver_id,
            driver_name=normalized_driver.name,
            zone_match=zone_match,
            reposition_miles=round(reposition_miles, 2),
            tier=normalized_driver.normalized_tier(),
            fatigue_score=round(normalized_driver.fatigue_score, 2),
            recent_declines=normalized_driver.recent_declines,
            candidate_offer=offer.final_offer,
            effective_pay_per_mile=offer.effective_pay_per_mile,
            dispatch_score=round(dispatch_score, 3),
            eligible=True,
            reason=None,
        )

    def dispatch_order(
        self,
        order: Dict[str, Any],
        drivers: List[Dict[str, Any]],
        zone_order_counts: Optional[Dict[str, int]] = None,
        zone_driver_counts: Optional[Dict[str, int]] = None,
        zone_backlog_counts: Optional[Dict[str, int]] = None,
    ) -> DispatchDecision:
        normalized_order = self._normalize_order(order)

        pressure_map = calculate_market_pressure(
            zone_order_counts=zone_order_counts or {normalized_order.zone: 1},
            zone_driver_counts=zone_driver_counts or {normalized_order.zone: len([d for d in drivers if d.get("online", True)])},
            zone_backlog_counts=zone_backlog_counts or {normalized_order.zone: 0},
        )
        zone_pressure_multiplier = _safe_float(
            pressure_map.get(normalized_order.zone, {}).get("pressure_score", 1.0),
            1.0,
        )

        evaluations = [
            self.evaluate_driver(
                driver=driver,
                order=order,
                zone_pressure_multiplier=zone_pressure_multiplier,
            )
            for driver in drivers
        ]
        eligible = [e for e in evaluations if e.eligible]

        base_breakdown = self.generate_fair_offer(
            order=order,
            reposition_miles=0.0,
            driver_tier="casual",
            zone_pressure_multiplier=zone_pressure_multiplier,
        )

        if not eligible:
            return DispatchDecision(
                accepted=False,
                order_id=normalized_order.order_id,
                assigned_driver_id=None,
                assigned_driver_name=None,
                offer_amount=base_breakdown.final_offer,
                effective_pay_per_mile=base_breakdown.effective_pay_per_mile,
                total_economic_miles=normalized_order.total_economic_miles,
                total_minutes=normalized_order.total_minutes,
                status="unassigned",
                reason="no_eligible_drivers",
                breakdown=asdict(base_breakdown),
                driver_evaluations=[asdict(e) for e in evaluations],
            )

        best = max(eligible, key=lambda x: x.dispatch_score)

        best_breakdown = self.generate_fair_offer(
            order=order,
            reposition_miles=best.reposition_miles,
            driver_tier=best.tier,
            zone_pressure_multiplier=zone_pressure_multiplier,
        )

        return DispatchDecision(
            accepted=True,
            order_id=normalized_order.order_id,
            assigned_driver_id=best.driver_id,
            assigned_driver_name=best.driver_name,
            offer_amount=best_breakdown.final_offer,
            effective_pay_per_mile=best_breakdown.effective_pay_per_mile,
            total_economic_miles=normalized_order.total_economic_miles,
            total_minutes=normalized_order.total_minutes,
            status="assigned",
            reason="best_driver_selected_by_fairness_first_dispatch",
            breakdown=asdict(best_breakdown),
            driver_evaluations=[asdict(e) for e in sorted(evaluations, key=lambda x: x.dispatch_score, reverse=True)],
        )