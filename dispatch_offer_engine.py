from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Dict, List, Optional


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
class DispatchOfferInput:
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

    estimated_prep_delay_minutes: Decimal = Decimal("0.00")
    estimated_traffic_delay_minutes: Decimal = Decimal("0.00")

    merchant_risk_score: Decimal = Decimal("0.00")
    zone_pressure_score: Decimal = Decimal("1.00")

    is_batched_candidate: bool = False
    is_high_wait_merchant: bool = False
    is_long_deadhead_zone: bool = False

    @classmethod
    def from_any(cls, payload: Any) -> "DispatchOfferInput":
        if isinstance(payload, cls):
            return payload

        if hasattr(payload, "to_dict"):
            payload = payload.to_dict()
        elif hasattr(payload, "__dict__"):
            payload = payload.__dict__

        if not isinstance(payload, dict):
            raise TypeError(
                "DispatchOfferInput.from_any expected dict-like input or object with to_dict/__dict__"
            )

        return cls(
            order_id=str(payload.get("order_id", "UNKNOWN")),
            zone=str(payload.get("zone", "unknown")),
            merchant=str(payload.get("merchant", "unknown")),
            tier=str(payload.get("tier", "casual")),
            pickup_distance=_to_decimal(payload.get("pickup_distance", payload.get("pickup_miles", 0))),
            delivery_distance=_to_decimal(payload.get("delivery_distance", 0)),
            return_distance=_to_decimal(
                payload.get("return_distance", payload.get("return_miles_estimate", 0))
            ),
            offered_payout=_to_decimal(payload.get("offered_payout", 0)),
            base_pay=_to_decimal(payload.get("base_pay", 0)),
            tip=_to_decimal(payload.get("tip", 0)),
            peak_pay=_to_decimal(payload.get("peak_pay", 0)),
            order_value=_to_decimal(payload.get("order_value", 0)),
            estimated_prep_delay_minutes=_to_decimal(payload.get("estimated_prep_delay_minutes", 0)),
            estimated_traffic_delay_minutes=_to_decimal(payload.get("estimated_traffic_delay_minutes", 0)),
            merchant_risk_score=_to_decimal(payload.get("merchant_risk_score", 0)),
            zone_pressure_score=_to_decimal(payload.get("zone_pressure_score", 1)),
            is_batched_candidate=_to_bool(payload.get("is_batched_candidate", False)),
            is_high_wait_merchant=_to_bool(payload.get("is_high_wait_merchant", False)),
            is_long_deadhead_zone=_to_bool(payload.get("is_long_deadhead_zone", False)),
        )

    def total_miles(self) -> Decimal:
        return self.pickup_distance + self.delivery_distance + self.return_distance

    def estimated_total_minutes(self) -> Decimal:
        # Simple deterministic estimate for now
        travel_minutes = self.total_miles() * Decimal("3.0")
        return travel_minutes + self.estimated_prep_delay_minutes + self.estimated_traffic_delay_minutes

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order_id": self.order_id,
            "zone": self.zone,
            "merchant": self.merchant,
            "tier": self.tier,
            "pickup_distance": str(self.pickup_distance),
            "delivery_distance": str(self.delivery_distance),
            "return_distance": str(self.return_distance),
            "offered_payout": str(self.offered_payout),
            "base_pay": str(self.base_pay),
            "tip": str(self.tip),
            "peak_pay": str(self.peak_pay),
            "order_value": str(self.order_value),
            "estimated_prep_delay_minutes": str(self.estimated_prep_delay_minutes),
            "estimated_traffic_delay_minutes": str(self.estimated_traffic_delay_minutes),
            "merchant_risk_score": str(self.merchant_risk_score),
            "zone_pressure_score": str(self.zone_pressure_score),
            "is_batched_candidate": self.is_batched_candidate,
            "is_high_wait_merchant": self.is_high_wait_merchant,
            "is_long_deadhead_zone": self.is_long_deadhead_zone,
        }


@dataclass
class DispatchOfferResult:
    order_id: str
    zone: str
    merchant: str
    tier: str

    recommended_action: str
    dispatch_score: Decimal
    fairness_status: str
    capacity_status: str
    reasons: List[str] = field(default_factory=list)

    total_miles: Decimal = Decimal("0.00")
    estimated_total_minutes: Decimal = Decimal("0.00")
    effective_hourly_rate: Decimal = Decimal("0.00")
    pay_per_economic_mile: Decimal = Decimal("0.00")

    zone_pressure_score: Decimal = Decimal("1.00")
    merchant_risk_score: Decimal = Decimal("0.00")
    batch_bonus_applied: bool = False
    wait_penalty_applied: bool = False
    deadhead_penalty_applied: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order_id": self.order_id,
            "zone": self.zone,
            "merchant": self.merchant,
            "tier": self.tier,
            "recommended_action": self.recommended_action,
            "dispatch_score": float(self.dispatch_score),
            "fairness_status": self.fairness_status,
            "capacity_status": self.capacity_status,
            "reasons": self.reasons,
            "total_miles": float(self.total_miles),
            "estimated_total_minutes": float(self.estimated_total_minutes),
            "effective_hourly_rate": float(self.effective_hourly_rate),
            "pay_per_economic_mile": float(self.pay_per_economic_mile),
            "zone_pressure_score": float(self.zone_pressure_score),
            "merchant_risk_score": float(self.merchant_risk_score),
            "batch_bonus_applied": self.batch_bonus_applied,
            "wait_penalty_applied": self.wait_penalty_applied,
            "deadhead_penalty_applied": self.deadhead_penalty_applied,
        }


class DispatchOfferEngine:
    """
    Dispatch engine for ChopExpress V1.

    Purpose:
    - take an order candidate
    - score whether it should be dispatched
    - preserve fairness logic rather than throughput-only logic
    """

    def __init__(
        self,
        min_pay_per_mile: Decimal | str = Decimal("1.25"),
        min_effective_hourly_rate: Decimal | str = Decimal("18.00"),
    ) -> None:
        self.min_pay_per_mile = _to_decimal(min_pay_per_mile, "1.25")
        self.min_effective_hourly_rate = _to_decimal(min_effective_hourly_rate, "18.00")

    def _score(self, item: DispatchOfferInput) -> DispatchOfferResult:
        total_miles = item.total_miles()
        total_minutes = item.estimated_total_minutes()

        payout = item.offered_payout
        if payout == Decimal("0.00"):
            payout = item.base_pay + item.tip + item.peak_pay

        ppm = payout / total_miles if total_miles > 0 else Decimal("0.00")
        hourly = (payout / total_minutes) * Decimal("60.0") if total_minutes > 0 else Decimal("0.00")

        reasons: List[str] = []
        score = Decimal("100.0")

        batch_bonus_applied = False
        wait_penalty_applied = False
        deadhead_penalty_applied = False

        if item.is_batched_candidate:
            score += Decimal("4.0")
            batch_bonus_applied = True
            reasons.append("Batched order complexity adjustment applied.")

        if item.is_high_wait_merchant:
            score -= Decimal("12.0")
            wait_penalty_applied = True
            reasons.append("High-wait merchant penalty applied.")

        if item.is_long_deadhead_zone:
            score -= Decimal("10.0")
            deadhead_penalty_applied = True
            reasons.append("Long deadhead zone penalty applied.")

        if item.zone_pressure_score > Decimal("1.0"):
            zone_bonus = (item.zone_pressure_score - Decimal("1.0")) * Decimal("10.0")
            score += zone_bonus
            reasons.append("Zone pressure bonus applied.")

        if item.merchant_risk_score > Decimal("0.70"):
            score -= Decimal("6.0")
            reasons.append("Merchant risk penalty applied.")

        fairness_status = "strong"
        recommended_action = "accept"
        capacity_status = "dispatchable"

        if ppm < self.min_pay_per_mile:
            fairness_status = "weak"
            recommended_action = "reject"
            score -= Decimal("25.0")
            reasons.append("Below minimum pay per economic mile.")

        if hourly < self.min_effective_hourly_rate:
            fairness_status = "weak"
            recommended_action = "reject"
            score -= Decimal("20.0")
            reasons.append("Below minimum effective hourly rate.")

        if total_miles > Decimal("12.0"):
            score -= Decimal("8.0")
            reasons.append("High mileage exposure.")

        if total_minutes > Decimal("45.0"):
            score -= Decimal("8.0")
            reasons.append("Long estimated completion time.")

        if score < Decimal("70.0") and recommended_action != "reject":
            recommended_action = "review"
            capacity_status = "manual_review"
            reasons.append("Borderline dispatch score; requires review.")

        score = max(Decimal("0.0"), min(score, Decimal("100.0")))

        return DispatchOfferResult(
            order_id=item.order_id,
            zone=item.zone,
            merchant=item.merchant,
            tier=item.tier,
            recommended_action=recommended_action,
            dispatch_score=score,
            fairness_status=fairness_status,
            capacity_status=capacity_status,
            reasons=reasons,
            total_miles=total_miles,
            estimated_total_minutes=total_minutes,
            effective_hourly_rate=hourly.quantize(Decimal("0.01")),
            pay_per_economic_mile=ppm.quantize(Decimal("0.01")),
            zone_pressure_score=item.zone_pressure_score,
            merchant_risk_score=item.merchant_risk_score,
            batch_bonus_applied=batch_bonus_applied,
            wait_penalty_applied=wait_penalty_applied,
            deadhead_penalty_applied=deadhead_penalty_applied,
        )

    def evaluate(self, payload: Any) -> DispatchOfferResult:
        item = DispatchOfferInput.from_any(payload)
        return self._score(item)


if __name__ == "__main__":
    engine = DispatchOfferEngine()

    sample = {
        "order_id": "TEST001",
        "zone": "clintonville",
        "merchant": "Test Kitchen",
        "tier": "professional",
        "pickup_distance": 2.1,
        "delivery_distance": 3.4,
        "return_distance": 2.5,
        "offered_payout": 8.75,
        "base_pay": 4.75,
        "tip": 4.00,
        "peak_pay": 0.00,
        "order_value": 28.50,
        "estimated_prep_delay_minutes": 7.0,
        "estimated_traffic_delay_minutes": 4.0,
        "merchant_risk_score": 0.80,
        "zone_pressure_score": 1.10,
        "is_batched_candidate": True,
        "is_high_wait_merchant": False,
        "is_long_deadhead_zone": False,
    }

    print(engine.evaluate(sample).to_dict())