from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Dict, List


def _to_decimal(value: Any, default: str = "0.00") -> Decimal:
    if value is None:
        return Decimal(default)
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal(default)


def _to_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y"}
    return bool(value)


@dataclass
class OrderValueBreakdownInput:
    order_id: str
    zone: str = "unknown"
    merchant: str = "unknown"
    tier: str = "casual"

    pickup_distance: Decimal = Decimal("0.00")
    delivery_distance: Decimal = Decimal("0.00")
    return_distance: Decimal = Decimal("0.00")

    offered_payout: Decimal = Decimal("0.00")
    base_pay: Decimal = Decimal("0.00")
    tip: Decimal = Decimal("0.00")
    peak_pay: Decimal = Decimal("0.00")
    order_value: Decimal = Decimal("0.00")

    estimated_total_minutes: Decimal = Decimal("0.00")
    estimated_prep_delay_minutes: Decimal = Decimal("0.00")
    estimated_traffic_delay_minutes: Decimal = Decimal("0.00")

    is_batched_candidate: bool = False
    is_high_wait_merchant: bool = False
    is_long_deadhead_zone: bool = False

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "OrderValueBreakdownInput":
        offered_payout = _to_decimal(payload.get("offered_payout", 0))
        tip = _to_decimal(payload.get("tip", 0))
        peak_pay = _to_decimal(payload.get("peak_pay", payload.get("peak_bonus", 0)))
        base_pay = _to_decimal(payload.get("base_pay", 0))

        # If base pay is missing, infer it from offered payout - tip - peak pay
        if base_pay == Decimal("0.00") and offered_payout > Decimal("0.00"):
            inferred = offered_payout - tip - peak_pay
            if inferred > Decimal("0.00"):
                base_pay = inferred

        pickup_distance = _to_decimal(
            payload.get("pickup_distance", payload.get("pickup_miles", 0))
        )
        delivery_distance = _to_decimal(payload.get("delivery_distance", 0))
        return_distance = _to_decimal(
            payload.get("return_distance", payload.get("return_miles_estimate", 0))
        )

        estimated_total_minutes = _to_decimal(payload.get("estimated_total_minutes", 0))
        prep_delay = _to_decimal(payload.get("estimated_prep_delay_minutes", 0))
        traffic_delay = _to_decimal(payload.get("estimated_traffic_delay_minutes", 0))

        return cls(
            order_id=str(payload.get("order_id", "UNKNOWN")),
            zone=str(payload.get("zone", "unknown")),
            merchant=str(payload.get("merchant", "unknown")),
            tier=str(payload.get("tier", "casual")),
            pickup_distance=pickup_distance,
            delivery_distance=delivery_distance,
            return_distance=return_distance,
            offered_payout=offered_payout,
            base_pay=base_pay,
            tip=tip,
            peak_pay=peak_pay,
            order_value=_to_decimal(payload.get("order_value", 0)),
            estimated_total_minutes=estimated_total_minutes,
            estimated_prep_delay_minutes=prep_delay,
            estimated_traffic_delay_minutes=traffic_delay,
            is_batched_candidate=_to_bool(payload.get("is_batched_candidate", False)),
            is_high_wait_merchant=_to_bool(payload.get("is_high_wait_merchant", False)),
            is_long_deadhead_zone=_to_bool(payload.get("is_long_deadhead_zone", False)),
        )

    @classmethod
    def from_any(cls, payload: Any) -> "OrderValueBreakdownInput":
        if isinstance(payload, cls):
            return payload
        if isinstance(payload, dict):
            return cls.from_dict(payload)
        if hasattr(payload, "to_dict"):
            return cls.from_dict(payload.to_dict())
        if hasattr(payload, "__dict__"):
            return cls.from_dict(payload.__dict__)
        raise TypeError("OrderValueBreakdownInput requires dict-like or object input")

    def total_economic_miles(self) -> Decimal:
        return self.pickup_distance + self.delivery_distance + self.return_distance

    def total_active_minutes(self) -> Decimal:
        total = self.estimated_total_minutes
        if total <= Decimal("0.00"):
            total = (
                self.estimated_prep_delay_minutes
                + self.estimated_traffic_delay_minutes
                + Decimal("20.00")
            )
        return total

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order_id": self.order_id,
            "zone": self.zone,
            "merchant": self.merchant,
            "tier": self.tier,
            "pickup_distance": float(self.pickup_distance),
            "delivery_distance": float(self.delivery_distance),
            "return_distance": float(self.return_distance),
            "offered_payout": float(self.offered_payout),
            "base_pay": float(self.base_pay),
            "tip": float(self.tip),
            "peak_pay": float(self.peak_pay),
            "order_value": float(self.order_value),
            "estimated_total_minutes": float(self.estimated_total_minutes),
            "estimated_prep_delay_minutes": float(self.estimated_prep_delay_minutes),
            "estimated_traffic_delay_minutes": float(self.estimated_traffic_delay_minutes),
            "is_batched_candidate": self.is_batched_candidate,
            "is_high_wait_merchant": self.is_high_wait_merchant,
            "is_long_deadhead_zone": self.is_long_deadhead_zone,
        }


@dataclass
class OrderValueBreakdownResult:
    order_id: str
    zone: str
    merchant: str
    tier: str

    base_pay: Decimal
    peak_pay: Decimal
    tip: Decimal
    offered_payout: Decimal
    order_value: Decimal

    pickup_miles: Decimal
    delivery_miles: Decimal
    return_miles_estimate: Decimal
    deadhead_miles: Decimal
    economic_miles: Decimal

    estimated_prep_delay_minutes: Decimal
    estimated_traffic_delay_minutes: Decimal
    estimated_total_minutes: Decimal

    pay_per_pickup_mile: Decimal
    pay_per_delivery_mile: Decimal
    pay_per_economic_mile: Decimal
    effective_hourly_rate: Decimal

    base_component_ratio: Decimal
    tip_component_ratio: Decimal
    peak_component_ratio: Decimal

    complexity_penalty: Decimal
    distance_cost_score: Decimal
    time_cost_score: Decimal
    merchant_risk_score: Decimal
    zone_pressure_score: Decimal

    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order_id": self.order_id,
            "zone": self.zone,
            "merchant": self.merchant,
            "tier": self.tier,
            "base_pay": float(self.base_pay),
            "peak_pay": float(self.peak_pay),
            "tip": float(self.tip),
            "offered_payout": float(self.offered_payout),
            "order_value": float(self.order_value),
            "pickup_miles": float(self.pickup_miles),
            "delivery_miles": float(self.delivery_miles),
            "return_miles_estimate": float(self.return_miles_estimate),
            "deadhead_miles": float(self.deadhead_miles),
            "economic_miles": float(self.economic_miles),
            "estimated_prep_delay_minutes": float(self.estimated_prep_delay_minutes),
            "estimated_traffic_delay_minutes": float(self.estimated_traffic_delay_minutes),
            "estimated_total_minutes": float(self.estimated_total_minutes),
            "pay_per_pickup_mile": float(self.pay_per_pickup_mile),
            "pay_per_delivery_mile": float(self.pay_per_delivery_mile),
            "pay_per_economic_mile": float(self.pay_per_economic_mile),
            "effective_hourly_rate": float(self.effective_hourly_rate),
            "base_component_ratio": float(self.base_component_ratio),
            "tip_component_ratio": float(self.tip_component_ratio),
            "peak_component_ratio": float(self.peak_component_ratio),
            "complexity_penalty": float(self.complexity_penalty),
            "distance_cost_score": float(self.distance_cost_score),
            "time_cost_score": float(self.time_cost_score),
            "merchant_risk_score": float(self.merchant_risk_score),
            "zone_pressure_score": float(self.zone_pressure_score),
            "reasons": self.reasons,
        }


class OrderValueBreakdownEngine:
    def evaluate(self, payload: Any) -> OrderValueBreakdownResult:
        input_data = OrderValueBreakdownInput.from_any(payload)

        pickup_miles = input_data.pickup_distance
        delivery_miles = input_data.delivery_distance
        return_miles = input_data.return_distance
        deadhead_miles = return_miles
        economic_miles = input_data.total_economic_miles()

        total_minutes = input_data.total_active_minutes()
        prep_delay = input_data.estimated_prep_delay_minutes
        traffic_delay = input_data.estimated_traffic_delay_minutes

        offered_payout = input_data.offered_payout
        base_pay = input_data.base_pay
        tip = input_data.tip
        peak_pay = input_data.peak_pay
        order_value = input_data.order_value

        zero = Decimal("0.00")

        pay_per_pickup_mile = (offered_payout / pickup_miles) if pickup_miles > 0 else zero
        pay_per_delivery_mile = (offered_payout / delivery_miles) if delivery_miles > 0 else zero
        pay_per_economic_mile = (offered_payout / economic_miles) if economic_miles > 0 else zero
        effective_hourly_rate = (
            offered_payout * Decimal("60.00") / total_minutes if total_minutes > 0 else zero
        )

        if offered_payout > 0:
            base_component_ratio = base_pay / offered_payout
            tip_component_ratio = tip / offered_payout
            peak_component_ratio = peak_pay / offered_payout
        else:
            base_component_ratio = zero
            tip_component_ratio = zero
            peak_component_ratio = zero

        complexity_penalty = zero
        merchant_risk_score = Decimal("0.20")
        zone_pressure_score = Decimal("1.00")
        reasons: List[str] = []

        if input_data.is_batched_candidate:
            complexity_penalty += Decimal("0.25")
            reasons.append("Batched order complexity adjustment applied.")

        if input_data.is_high_wait_merchant:
            merchant_risk_score += Decimal("0.30")
            complexity_penalty += Decimal("0.15")
            reasons.append("Merchant wait-risk penalty applied.")

        if input_data.is_long_deadhead_zone:
            zone_pressure_score += Decimal("0.20")
            complexity_penalty += Decimal("0.15")
            reasons.append("Long deadhead zone penalty applied.")

        if traffic_delay > Decimal("5.00"):
            reasons.append("Elevated traffic delay detected.")

        if prep_delay > Decimal("8.00"):
            reasons.append("High prep-delay exposure detected.")

        distance_cost_score = economic_miles
        time_cost_score = total_minutes / Decimal("60.00") if total_minutes > 0 else zero

        return OrderValueBreakdownResult(
            order_id=input_data.order_id,
            zone=input_data.zone,
            merchant=input_data.merchant,
            tier=input_data.tier,
            base_pay=base_pay.quantize(Decimal("0.01")),
            peak_pay=peak_pay.quantize(Decimal("0.01")),
            tip=tip.quantize(Decimal("0.01")),
            offered_payout=offered_payout.quantize(Decimal("0.01")),
            order_value=order_value.quantize(Decimal("0.01")),
            pickup_miles=pickup_miles.quantize(Decimal("0.01")),
            delivery_miles=delivery_miles.quantize(Decimal("0.01")),
            return_miles_estimate=return_miles.quantize(Decimal("0.01")),
            deadhead_miles=deadhead_miles.quantize(Decimal("0.01")),
            economic_miles=economic_miles.quantize(Decimal("0.01")),
            estimated_prep_delay_minutes=prep_delay.quantize(Decimal("0.01")),
            estimated_traffic_delay_minutes=traffic_delay.quantize(Decimal("0.01")),
            estimated_total_minutes=total_minutes.quantize(Decimal("0.01")),
            pay_per_pickup_mile=pay_per_pickup_mile.quantize(Decimal("0.01")) if pickup_miles > 0 else zero,
            pay_per_delivery_mile=pay_per_delivery_mile.quantize(Decimal("0.01")) if delivery_miles > 0 else zero,
            pay_per_economic_mile=pay_per_economic_mile.quantize(Decimal("0.01")) if economic_miles > 0 else zero,
            effective_hourly_rate=effective_hourly_rate.quantize(Decimal("0.01")) if total_minutes > 0 else zero,
            base_component_ratio=base_component_ratio.quantize(Decimal("0.01")) if offered_payout > 0 else zero,
            tip_component_ratio=tip_component_ratio.quantize(Decimal("0.01")) if offered_payout > 0 else zero,
            peak_component_ratio=peak_component_ratio.quantize(Decimal("0.01")) if offered_payout > 0 else zero,
            complexity_penalty=complexity_penalty.quantize(Decimal("0.01")),
            distance_cost_score=distance_cost_score.quantize(Decimal("0.01")),
            time_cost_score=time_cost_score.quantize(Decimal("0.01")),
            merchant_risk_score=merchant_risk_score.quantize(Decimal("0.01")),
            zone_pressure_score=zone_pressure_score.quantize(Decimal("0.01")),
            reasons=reasons,
        )

    def run(self, payload: Any) -> OrderValueBreakdownResult:
        return self.evaluate(payload)


if __name__ == "__main__":
    engine = OrderValueBreakdownEngine()

    sample = {
        "order_id": "TEST001",
        "zone": "clintonville",
        "merchant": "Test Kitchen",
        "tier": "professional",
        "pickup_distance": 2.1,
        "delivery_distance": 3.4,
        "return_distance": 2.5,
        "offered_payout": 8.75,
        "tip": 4.00,
        "peak_pay": 0.00,
        "order_value": 28.50,
        "estimated_total_minutes": 35.0,
        "estimated_prep_delay_minutes": 7.0,
        "estimated_traffic_delay_minutes": 4.0,
        "is_batched_candidate": True,
        "is_high_wait_merchant": False,
        "is_long_deadhead_zone": False,
    }

    print(engine.evaluate(sample).to_dict())