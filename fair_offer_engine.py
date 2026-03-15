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
class FairOfferInput:
    order_id: str
    zone: str = "unknown"
    merchant: str = "unknown"
    tier: str = "casual"

    offered_payout: Decimal = Decimal("0.00")
    base_pay: Decimal = Decimal("0.00")
    tip: Decimal = Decimal("0.00")
    peak_pay: Decimal = Decimal("0.00")
    order_value: Decimal = Decimal("0.00")

    pickup_miles: Decimal = Decimal("0.00")
    delivery_miles: Decimal = Decimal("0.00")
    return_miles_estimate: Decimal = Decimal("0.00")
    deadhead_miles: Decimal = Decimal("0.00")
    economic_miles: Decimal = Decimal("0.00")

    estimated_total_minutes: Decimal = Decimal("0.00")
    estimated_prep_delay_minutes: Decimal = Decimal("0.00")
    estimated_traffic_delay_minutes: Decimal = Decimal("0.00")

    pay_per_pickup_mile: Decimal = Decimal("0.00")
    pay_per_delivery_mile: Decimal = Decimal("0.00")
    pay_per_economic_mile: Decimal = Decimal("0.00")
    effective_hourly_rate: Decimal = Decimal("0.00")

    complexity_penalty: Decimal = Decimal("0.00")
    distance_cost_score: Decimal = Decimal("0.00")
    time_cost_score: Decimal = Decimal("0.00")
    merchant_risk_score: Decimal = Decimal("0.00")
    zone_pressure_score: Decimal = Decimal("1.00")

    is_batched_candidate: bool = False
    is_high_wait_merchant: bool = False
    is_long_deadhead_zone: bool = False

    reasons: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "FairOfferInput":
        offered_payout = _to_decimal(payload.get("offered_payout", 0))
        tip = _to_decimal(payload.get("tip", 0))
        peak_pay = _to_decimal(payload.get("peak_pay", payload.get("peak_bonus", 0)))
        base_pay = _to_decimal(payload.get("base_pay", 0))

        if base_pay == Decimal("0.00") and offered_payout > Decimal("0.00"):
            inferred = offered_payout - tip - peak_pay
            if inferred > Decimal("0.00"):
                base_pay = inferred

        pickup_miles = _to_decimal(
            payload.get("pickup_miles", payload.get("pickup_distance", 0))
        )
        delivery_miles = _to_decimal(
            payload.get("delivery_miles", payload.get("delivery_distance", 0))
        )
        return_miles = _to_decimal(
            payload.get("return_miles_estimate", payload.get("return_distance", 0))
        )
        deadhead_miles = _to_decimal(payload.get("deadhead_miles", return_miles))
        economic_miles = _to_decimal(payload.get("economic_miles", 0))
        if economic_miles == Decimal("0.00"):
            economic_miles = pickup_miles + delivery_miles + return_miles

        estimated_total_minutes = _to_decimal(payload.get("estimated_total_minutes", 0))
        prep_delay = _to_decimal(payload.get("estimated_prep_delay_minutes", 0))
        traffic_delay = _to_decimal(payload.get("estimated_traffic_delay_minutes", 0))

        pay_per_pickup_mile = _to_decimal(payload.get("pay_per_pickup_mile", 0))
        pay_per_delivery_mile = _to_decimal(payload.get("pay_per_delivery_mile", 0))
        pay_per_economic_mile = _to_decimal(payload.get("pay_per_economic_mile", 0))
        effective_hourly_rate = _to_decimal(payload.get("effective_hourly_rate", 0))

        complexity_penalty = _to_decimal(payload.get("complexity_penalty", 0))
        distance_cost_score = _to_decimal(payload.get("distance_cost_score", economic_miles))
        time_cost_score = _to_decimal(payload.get("time_cost_score", 0))
        merchant_risk_score = _to_decimal(payload.get("merchant_risk_score", 0))
        zone_pressure_score = _to_decimal(payload.get("zone_pressure_score", 1))

        return cls(
            order_id=str(payload.get("order_id", "UNKNOWN")),
            zone=str(payload.get("zone", "unknown")),
            merchant=str(payload.get("merchant", "unknown")),
            tier=str(payload.get("tier", "casual")),
            offered_payout=offered_payout,
            base_pay=base_pay,
            tip=tip,
            peak_pay=peak_pay,
            order_value=_to_decimal(payload.get("order_value", 0)),
            pickup_miles=pickup_miles,
            delivery_miles=delivery_miles,
            return_miles_estimate=return_miles,
            deadhead_miles=deadhead_miles,
            economic_miles=economic_miles,
            estimated_total_minutes=estimated_total_minutes,
            estimated_prep_delay_minutes=prep_delay,
            estimated_traffic_delay_minutes=traffic_delay,
            pay_per_pickup_mile=pay_per_pickup_mile,
            pay_per_delivery_mile=pay_per_delivery_mile,
            pay_per_economic_mile=pay_per_economic_mile,
            effective_hourly_rate=effective_hourly_rate,
            complexity_penalty=complexity_penalty,
            distance_cost_score=distance_cost_score,
            time_cost_score=time_cost_score,
            merchant_risk_score=merchant_risk_score,
            zone_pressure_score=zone_pressure_score,
            is_batched_candidate=_to_bool(payload.get("is_batched_candidate", False)),
            is_high_wait_merchant=_to_bool(payload.get("is_high_wait_merchant", False)),
            is_long_deadhead_zone=_to_bool(payload.get("is_long_deadhead_zone", False)),
            reasons=list(payload.get("reasons", [])) if isinstance(payload.get("reasons", []), list) else [],
        )

    @classmethod
    def from_any(cls, payload: Any) -> "FairOfferInput":
        if isinstance(payload, cls):
            return payload
        if isinstance(payload, dict):
            return cls.from_dict(payload)
        if hasattr(payload, "to_dict"):
            return cls.from_dict(payload.to_dict())
        if hasattr(payload, "__dict__"):
            return cls.from_dict(payload.__dict__)
        raise TypeError("FairOfferInput requires dict-like or object input")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order_id": self.order_id,
            "zone": self.zone,
            "merchant": self.merchant,
            "tier": self.tier,
            "offered_payout": float(self.offered_payout),
            "base_pay": float(self.base_pay),
            "tip": float(self.tip),
            "peak_pay": float(self.peak_pay),
            "order_value": float(self.order_value),
            "pickup_miles": float(self.pickup_miles),
            "delivery_miles": float(self.delivery_miles),
            "return_miles_estimate": float(self.return_miles_estimate),
            "deadhead_miles": float(self.deadhead_miles),
            "economic_miles": float(self.economic_miles),
            "estimated_total_minutes": float(self.estimated_total_minutes),
            "estimated_prep_delay_minutes": float(self.estimated_prep_delay_minutes),
            "estimated_traffic_delay_minutes": float(self.estimated_traffic_delay_minutes),
            "pay_per_pickup_mile": float(self.pay_per_pickup_mile),
            "pay_per_delivery_mile": float(self.pay_per_delivery_mile),
            "pay_per_economic_mile": float(self.pay_per_economic_mile),
            "effective_hourly_rate": float(self.effective_hourly_rate),
            "complexity_penalty": float(self.complexity_penalty),
            "distance_cost_score": float(self.distance_cost_score),
            "time_cost_score": float(self.time_cost_score),
            "merchant_risk_score": float(self.merchant_risk_score),
            "zone_pressure_score": float(self.zone_pressure_score),
            "is_batched_candidate": self.is_batched_candidate,
            "is_high_wait_merchant": self.is_high_wait_merchant,
            "is_long_deadhead_zone": self.is_long_deadhead_zone,
            "reasons": self.reasons,
        }


@dataclass
class FairOfferResult:
    order_id: str
    zone: str
    merchant: str
    tier: str

    dispatch_score: Decimal
    fairness_status: str
    recommended_action: str
    capacity_status: str

    effective_hourly_rate: Decimal
    pay_per_economic_mile: Decimal
    minimum_hourly_target: Decimal
    minimum_pay_per_economic_mile: Decimal

    merchant_risk_score: Decimal
    zone_pressure_score: Decimal
    complexity_penalty: Decimal

    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order_id": self.order_id,
            "zone": self.zone,
            "merchant": self.merchant,
            "tier": self.tier,
            "dispatch_score": float(self.dispatch_score),
            "fairness_status": self.fairness_status,
            "recommended_action": self.recommended_action,
            "capacity_status": self.capacity_status,
            "effective_hourly_rate": float(self.effective_hourly_rate),
            "pay_per_economic_mile": float(self.pay_per_economic_mile),
            "minimum_hourly_target": float(self.minimum_hourly_target),
            "minimum_pay_per_economic_mile": float(self.minimum_pay_per_economic_mile),
            "merchant_risk_score": float(self.merchant_risk_score),
            "zone_pressure_score": float(self.zone_pressure_score),
            "complexity_penalty": float(self.complexity_penalty),
            "reasons": self.reasons,
        }


class FairOfferEngine:
    def __init__(
        self,
        minimum_hourly_target: Decimal | str = Decimal("20.00"),
        minimum_pay_per_economic_mile: Decimal | str = Decimal("1.25"),
    ) -> None:
        self.minimum_hourly_target = _to_decimal(minimum_hourly_target, "20.00")
        self.minimum_pay_per_economic_mile = _to_decimal(minimum_pay_per_economic_mile, "1.25")

    def evaluate(self, payload: Any) -> FairOfferResult:
        input_data = FairOfferInput.from_any(payload)

        offered = input_data.offered_payout
        effective_hourly = input_data.effective_hourly_rate
        pay_per_economic_mile = input_data.pay_per_economic_mile

        if effective_hourly == Decimal("0.00") and input_data.estimated_total_minutes > Decimal("0.00"):
            effective_hourly = (
                offered * Decimal("60.00") / input_data.estimated_total_minutes
            )

        if pay_per_economic_mile == Decimal("0.00") and input_data.economic_miles > Decimal("0.00"):
            pay_per_economic_mile = offered / input_data.economic_miles

        score = Decimal("100.00")
        reasons = list(input_data.reasons)

        if pay_per_economic_mile < self.minimum_pay_per_economic_mile:
            gap = self.minimum_pay_per_economic_mile - pay_per_economic_mile
            score -= gap * Decimal("40.00")
            reasons.append("Below minimum pay per economic mile.")

        if effective_hourly < self.minimum_hourly_target:
            gap = self.minimum_hourly_target - effective_hourly
            score -= gap * Decimal("2.00")
            reasons.append("Below minimum effective hourly rate.")

        score -= input_data.complexity_penalty * Decimal("10.00")
        score -= input_data.merchant_risk_score * Decimal("5.00")

        if input_data.zone_pressure_score > Decimal("1.00"):
            score += (input_data.zone_pressure_score - Decimal("1.00")) * Decimal("10.00")
            reasons.append("Zone pressure bonus applied.")

        if input_data.is_batched_candidate:
            reasons.append("Batched order complexity adjustment applied.")
        if input_data.is_high_wait_merchant:
            reasons.append("Merchant wait-risk applied.")
        if input_data.is_long_deadhead_zone:
            reasons.append("Long deadhead exposure considered.")

        if score < Decimal("0.00"):
            score = Decimal("0.00")
        if score > Decimal("100.00"):
            score = Decimal("100.00")

        if score >= Decimal("80.00"):
            fairness_status = "strong"
            recommended_action = "accept"
        elif score >= Decimal("60.00"):
            fairness_status = "borderline"
            recommended_action = "review"
        else:
            fairness_status = "weak"
            recommended_action = "reject"

        capacity_status = "dispatchable" if score >= Decimal("60.00") else "hold"

        return FairOfferResult(
            order_id=input_data.order_id,
            zone=input_data.zone,
            merchant=input_data.merchant,
            tier=input_data.tier,
            dispatch_score=score.quantize(Decimal("0.01")),
            fairness_status=fairness_status,
            recommended_action=recommended_action,
            capacity_status=capacity_status,
            effective_hourly_rate=effective_hourly.quantize(Decimal("0.01")),
            pay_per_economic_mile=pay_per_economic_mile.quantize(Decimal("0.01")),
            minimum_hourly_target=self.minimum_hourly_target.quantize(Decimal("0.01")),
            minimum_pay_per_economic_mile=self.minimum_pay_per_economic_mile.quantize(Decimal("0.01")),
            merchant_risk_score=input_data.merchant_risk_score.quantize(Decimal("0.01")),
            zone_pressure_score=input_data.zone_pressure_score.quantize(Decimal("0.01")),
            complexity_penalty=input_data.complexity_penalty.quantize(Decimal("0.01")),
            reasons=reasons,
        )

    def run(self, payload: Any) -> FairOfferResult:
        return self.evaluate(payload)


if __name__ == "__main__":
    engine = FairOfferEngine()

    sample = {
        "order_id": "TEST001",
        "zone": "clintonville",
        "merchant": "Test Kitchen",
        "tier": "professional",
        "offered_payout": 8.75,
        "base_pay": 4.75,
        "tip": 4.00,
        "peak_pay": 0.00,
        "order_value": 28.50,
        "pickup_miles": 2.1,
        "delivery_miles": 3.4,
        "return_miles_estimate": 2.5,
        "deadhead_miles": 2.5,
        "economic_miles": 8.0,
        "estimated_total_minutes": 35.0,
        "estimated_prep_delay_minutes": 7.0,
        "estimated_traffic_delay_minutes": 4.0,
        "pay_per_pickup_mile": 4.17,
        "pay_per_delivery_mile": 2.57,
        "pay_per_economic_mile": 1.09,
        "effective_hourly_rate": 15.0,
        "complexity_penalty": 0.25,
        "distance_cost_score": 8.0,
        "time_cost_score": 0.58,
        "merchant_risk_score": 0.20,
        "zone_pressure_score": 1.00,
        "is_batched_candidate": True,
        "is_high_wait_merchant": False,
        "is_long_deadhead_zone": False,
        "reasons": ["Batched order complexity adjustment applied."],
    }

    print(engine.evaluate(sample).to_dict())