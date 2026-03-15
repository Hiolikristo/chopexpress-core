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
class InsuranceSupportInput:
    order_id: str
    zone: str = "unknown"
    merchant: str = "unknown"
    tier: str = "casual"

    pickup_distance: Decimal = Decimal("0.00")
    delivery_distance: Decimal = Decimal("0.00")
    return_distance: Decimal = Decimal("0.00")

    offered_payout: Decimal = Decimal("0.00")
    order_value: Decimal = Decimal("0.00")
    tip: Decimal = Decimal("0.00")
    estimated_total_minutes: Decimal = Decimal("0.00")

    is_batched_candidate: bool = False
    is_high_wait_merchant: bool = False
    is_long_deadhead_zone: bool = False

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "InsuranceSupportInput":
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
            order_value=_to_decimal(payload.get("order_value", 0)),
            tip=_to_decimal(payload.get("tip", 0)),
            estimated_total_minutes=_to_decimal(payload.get("estimated_total_minutes", 0)),
            is_batched_candidate=_to_bool(payload.get("is_batched_candidate", False)),
            is_high_wait_merchant=_to_bool(payload.get("is_high_wait_merchant", False)),
            is_long_deadhead_zone=_to_bool(payload.get("is_long_deadhead_zone", False)),
        )

    @classmethod
    def from_any(cls, payload: Any) -> "InsuranceSupportInput":
        if isinstance(payload, cls):
            return payload
        if isinstance(payload, dict):
            return cls.from_dict(payload)
        if hasattr(payload, "to_dict"):
            return cls.from_dict(payload.to_dict())
        if hasattr(payload, "__dict__"):
            return cls.from_dict(payload.__dict__)
        raise TypeError("InsuranceSupportInput requires dict-like or object input")

    def total_miles(self) -> Decimal:
        return self.pickup_distance + self.delivery_distance + self.return_distance

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
            "order_value": float(self.order_value),
            "tip": float(self.tip),
            "estimated_total_minutes": float(self.estimated_total_minutes),
            "is_batched_candidate": self.is_batched_candidate,
            "is_high_wait_merchant": self.is_high_wait_merchant,
            "is_long_deadhead_zone": self.is_long_deadhead_zone,
        }


@dataclass
class InsuranceSupportResult:
    order_id: str
    coverage_recommended: bool
    risk_band: str
    risk_score: Decimal
    reserve_contribution: Decimal
    coverage_note: str
    reasons: List[str] = field(default_factory=list)
    total_miles: Decimal = Decimal("0.00")
    estimated_total_minutes: Decimal = Decimal("0.00")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order_id": self.order_id,
            "coverage_recommended": self.coverage_recommended,
            "risk_band": self.risk_band,
            "risk_score": float(self.risk_score),
            "reserve_contribution": float(self.reserve_contribution),
            "coverage_note": self.coverage_note,
            "reasons": self.reasons,
            "total_miles": float(self.total_miles),
            "estimated_total_minutes": float(self.estimated_total_minutes),
        }


class InsuranceSupportEngine:
    def __init__(
        self,
        base_reserve_rate: Decimal | str = Decimal("0.03"),
        high_risk_reserve_rate: Decimal | str = Decimal("0.06"),
    ) -> None:
        self.base_reserve_rate = _to_decimal(base_reserve_rate, "0.03")
        self.high_risk_reserve_rate = _to_decimal(high_risk_reserve_rate, "0.06")

    def evaluate(self, payload: Any) -> InsuranceSupportResult:
        data = InsuranceSupportInput.from_any(payload)

        total_miles = data.total_miles()
        total_minutes = data.estimated_total_minutes
        risk_score = Decimal("0.00")
        reasons: List[str] = []

        if total_miles >= Decimal("8.0"):
            risk_score += Decimal("0.30")
            reasons.append("Higher mileage exposure.")

        if total_minutes >= Decimal("40.0"):
            risk_score += Decimal("0.20")
            reasons.append("Long active delivery time.")

        if data.is_batched_candidate:
            risk_score += Decimal("0.15")
            reasons.append("Batched order adds complexity.")

        if data.is_high_wait_merchant:
            risk_score += Decimal("0.15")
            reasons.append("High-wait merchant increases exposure time.")

        if data.is_long_deadhead_zone:
            risk_score += Decimal("0.20")
            reasons.append("Long deadhead zone increases uncovered travel.")

        if data.order_value >= Decimal("60.0"):
            risk_score += Decimal("0.10")
            reasons.append("Higher order value increases exposure.")

        if risk_score >= Decimal("0.60"):
            risk_band = "high"
            reserve_rate = self.high_risk_reserve_rate
            coverage_recommended = True
            coverage_note = "High-risk trip profile; elevated reserve coverage recommended."
        elif risk_score >= Decimal("0.30"):
            risk_band = "moderate"
            reserve_rate = self.base_reserve_rate
            coverage_recommended = True
            coverage_note = "Moderate-risk trip profile; standard reserve coverage recommended."
        else:
            risk_band = "low"
            reserve_rate = self.base_reserve_rate / Decimal("2")
            coverage_recommended = False
            coverage_note = "Low-risk trip profile; minimal reserve treatment is sufficient."

        reserve_contribution = (data.offered_payout * reserve_rate).quantize(Decimal("0.01"))

        return InsuranceSupportResult(
            order_id=data.order_id,
            coverage_recommended=coverage_recommended,
            risk_band=risk_band,
            risk_score=risk_score.quantize(Decimal("0.01")),
            reserve_contribution=reserve_contribution,
            coverage_note=coverage_note,
            reasons=reasons,
            total_miles=total_miles.quantize(Decimal("0.01")),
            estimated_total_minutes=total_minutes.quantize(Decimal("0.01")),
        )

    def run(self, payload: Any) -> InsuranceSupportResult:
        return self.evaluate(payload)


if __name__ == "__main__":
    engine = InsuranceSupportEngine()

    sample = {
        "order_id": "TEST001",
        "zone": "clintonville",
        "merchant": "Test Kitchen",
        "tier": "professional",
        "pickup_distance": 2.1,
        "delivery_distance": 3.4,
        "return_distance": 2.5,
        "offered_payout": 8.75,
        "order_value": 28.50,
        "tip": 4.00,
        "estimated_total_minutes": 35.0,
        "is_batched_candidate": True,
        "is_high_wait_merchant": False,
        "is_long_deadhead_zone": False,
    }

    print(engine.evaluate(sample).to_dict())