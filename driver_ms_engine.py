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
class DriverMSInput:
    order_id: str
    zone: str = "unknown"
    merchant: str = "unknown"
    tier: str = "casual"

    pickup_miles: Decimal = Decimal("0.00")
    delivery_miles: Decimal = Decimal("0.00")
    return_miles_estimate: Decimal = Decimal("0.00")
    deadhead_miles: Decimal = Decimal("0.00")
    economic_miles: Decimal = Decimal("0.00")

    estimated_total_minutes: Decimal = Decimal("0.00")
    estimated_prep_delay_minutes: Decimal = Decimal("0.00")
    estimated_traffic_delay_minutes: Decimal = Decimal("0.00")

    offered_payout: Decimal = Decimal("0.00")
    base_pay: Decimal = Decimal("0.00")
    tip: Decimal = Decimal("0.00")
    peak_pay: Decimal = Decimal("0.00")
    order_value: Decimal = Decimal("0.00")

    pay_per_economic_mile: Decimal = Decimal("0.00")
    effective_hourly_rate: Decimal = Decimal("0.00")

    is_batched_candidate: bool = False
    is_high_wait_merchant: bool = False
    is_long_deadhead_zone: bool = False

    reasons: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "DriverMSInput":
        pickup_miles = _to_decimal(payload.get("pickup_miles", payload.get("pickup_distance", 0)))
        delivery_miles = _to_decimal(payload.get("delivery_miles", payload.get("delivery_distance", 0)))
        return_miles = _to_decimal(
            payload.get("return_miles_estimate", payload.get("return_distance", 0))
        )
        deadhead_miles = _to_decimal(payload.get("deadhead_miles", return_miles))

        economic_miles = _to_decimal(payload.get("economic_miles", 0))
        if economic_miles == Decimal("0.00"):
            economic_miles = pickup_miles + delivery_miles + return_miles

        offered_payout = _to_decimal(payload.get("offered_payout", 0))
        tip = _to_decimal(payload.get("tip", 0))
        peak_pay = _to_decimal(payload.get("peak_pay", payload.get("peak_bonus", 0)))
        base_pay = _to_decimal(payload.get("base_pay", 0))
        if base_pay == Decimal("0.00") and offered_payout > Decimal("0.00"):
            inferred = offered_payout - tip - peak_pay
            if inferred > Decimal("0.00"):
                base_pay = inferred

        estimated_total_minutes = _to_decimal(payload.get("estimated_total_minutes", 0))
        estimated_prep_delay_minutes = _to_decimal(payload.get("estimated_prep_delay_minutes", 0))
        estimated_traffic_delay_minutes = _to_decimal(payload.get("estimated_traffic_delay_minutes", 0))

        pay_per_economic_mile = _to_decimal(payload.get("pay_per_economic_mile", 0))
        if pay_per_economic_mile == Decimal("0.00") and economic_miles > Decimal("0.00"):
            pay_per_economic_mile = offered_payout / economic_miles

        effective_hourly_rate = _to_decimal(payload.get("effective_hourly_rate", 0))
        if effective_hourly_rate == Decimal("0.00") and estimated_total_minutes > Decimal("0.00"):
            effective_hourly_rate = offered_payout * Decimal("60.00") / estimated_total_minutes

        return cls(
            order_id=str(payload.get("order_id", "UNKNOWN")),
            zone=str(payload.get("zone", "unknown")),
            merchant=str(payload.get("merchant", "unknown")),
            tier=str(payload.get("tier", "casual")),
            pickup_miles=pickup_miles,
            delivery_miles=delivery_miles,
            return_miles_estimate=return_miles,
            deadhead_miles=deadhead_miles,
            economic_miles=economic_miles,
            estimated_total_minutes=estimated_total_minutes,
            estimated_prep_delay_minutes=estimated_prep_delay_minutes,
            estimated_traffic_delay_minutes=estimated_traffic_delay_minutes,
            offered_payout=offered_payout,
            base_pay=base_pay,
            tip=tip,
            peak_pay=peak_pay,
            order_value=_to_decimal(payload.get("order_value", 0)),
            pay_per_economic_mile=pay_per_economic_mile,
            effective_hourly_rate=effective_hourly_rate,
            is_batched_candidate=_to_bool(payload.get("is_batched_candidate", False)),
            is_high_wait_merchant=_to_bool(payload.get("is_high_wait_merchant", False)),
            is_long_deadhead_zone=_to_bool(payload.get("is_long_deadhead_zone", False)),
            reasons=list(payload.get("reasons", [])) if isinstance(payload.get("reasons", []), list) else [],
        )

    @classmethod
    def from_any(cls, payload: Any) -> "DriverMSInput":
        if isinstance(payload, cls):
            return payload
        if isinstance(payload, dict):
            return cls.from_dict(payload)
        if hasattr(payload, "to_dict"):
            return cls.from_dict(payload.to_dict())
        if hasattr(payload, "__dict__"):
            return cls.from_dict(payload.__dict__)
        raise TypeError("DriverMSInput requires dict-like or object input")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order_id": self.order_id,
            "zone": self.zone,
            "merchant": self.merchant,
            "tier": self.tier,
            "pickup_miles": float(self.pickup_miles),
            "delivery_miles": float(self.delivery_miles),
            "return_miles_estimate": float(self.return_miles_estimate),
            "deadhead_miles": float(self.deadhead_miles),
            "economic_miles": float(self.economic_miles),
            "estimated_total_minutes": float(self.estimated_total_minutes),
            "estimated_prep_delay_minutes": float(self.estimated_prep_delay_minutes),
            "estimated_traffic_delay_minutes": float(self.estimated_traffic_delay_minutes),
            "offered_payout": float(self.offered_payout),
            "base_pay": float(self.base_pay),
            "tip": float(self.tip),
            "peak_pay": float(self.peak_pay),
            "order_value": float(self.order_value),
            "pay_per_economic_mile": float(self.pay_per_economic_mile),
            "effective_hourly_rate": float(self.effective_hourly_rate),
            "is_batched_candidate": self.is_batched_candidate,
            "is_high_wait_merchant": self.is_high_wait_merchant,
            "is_long_deadhead_zone": self.is_long_deadhead_zone,
            "reasons": self.reasons,
        }


@dataclass
class DriverMSResult:
    order_id: str
    maintenance_reserve: Decimal
    maintenance_rate_per_mile: Decimal
    insurance_reserve: Decimal
    insurance_rate_per_mile: Decimal
    total_driver_ms_cost: Decimal
    economic_miles: Decimal
    reserve_status: str
    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "order_id": self.order_id,
            "maintenance_reserve": float(self.maintenance_reserve),
            "maintenance_rate_per_mile": float(self.maintenance_rate_per_mile),
            "insurance_reserve": float(self.insurance_reserve),
            "insurance_rate_per_mile": float(self.insurance_rate_per_mile),
            "total_driver_ms_cost": float(self.total_driver_ms_cost),
            "economic_miles": float(self.economic_miles),
            "reserve_status": self.reserve_status,
            "reasons": self.reasons,
        }


class DriverMSEngine:
    def __init__(
        self,
        maintenance_rate_per_mile: Decimal | str = Decimal("0.18"),
        insurance_rate_per_mile: Decimal | str = Decimal("0.12"),
    ) -> None:
        self.maintenance_rate_per_mile = _to_decimal(maintenance_rate_per_mile, "0.18")
        self.insurance_rate_per_mile = _to_decimal(insurance_rate_per_mile, "0.12")

    def evaluate(self, payload: Any) -> DriverMSResult:
        input_data = DriverMSInput.from_any(payload)

        economic_miles = input_data.economic_miles
        reasons = list(input_data.reasons)

        maintenance_reserve = economic_miles * self.maintenance_rate_per_mile
        insurance_reserve = economic_miles * self.insurance_rate_per_mile

        if input_data.is_long_deadhead_zone:
            maintenance_reserve += Decimal("0.50")
            insurance_reserve += Decimal("0.25")
            reasons.append("Long deadhead zone reserve adjustment applied.")

        if input_data.is_high_wait_merchant:
            insurance_reserve += Decimal("0.15")
            reasons.append("High-wait merchant risk adjustment applied.")

        if input_data.is_batched_candidate:
            maintenance_reserve += Decimal("0.25")
            reasons.append("Batched order maintenance adjustment applied.")

        total_driver_ms_cost = maintenance_reserve + insurance_reserve

        reserve_status = "ok"
        if total_driver_ms_cost > input_data.offered_payout:
            reserve_status = "overdrawn"
            reasons.append("Reserve requirement exceeds offered payout.")
        elif total_driver_ms_cost > (input_data.offered_payout * Decimal("0.35")):
            reserve_status = "elevated"
            reasons.append("Reserve requirement is elevated relative to offered payout.")

        return DriverMSResult(
            order_id=input_data.order_id,
            maintenance_reserve=maintenance_reserve.quantize(Decimal("0.01")),
            maintenance_rate_per_mile=self.maintenance_rate_per_mile.quantize(Decimal("0.01")),
            insurance_reserve=insurance_reserve.quantize(Decimal("0.01")),
            insurance_rate_per_mile=self.insurance_rate_per_mile.quantize(Decimal("0.01")),
            total_driver_ms_cost=total_driver_ms_cost.quantize(Decimal("0.01")),
            economic_miles=economic_miles.quantize(Decimal("0.01")),
            reserve_status=reserve_status,
            reasons=reasons,
        )

    def run(self, payload: Any) -> DriverMSResult:
        return self.evaluate(payload)


if __name__ == "__main__":
    engine = DriverMSEngine()

    sample = {
        "order_id": "TEST001",
        "zone": "clintonville",
        "merchant": "Test Kitchen",
        "tier": "professional",
        "pickup_miles": 2.1,
        "delivery_miles": 3.4,
        "return_miles_estimate": 2.5,
        "deadhead_miles": 2.5,
        "economic_miles": 8.0,
        "estimated_total_minutes": 35.0,
        "estimated_prep_delay_minutes": 7.0,
        "estimated_traffic_delay_minutes": 4.0,
        "offered_payout": 8.75,
        "base_pay": 4.75,
        "tip": 4.00,
        "peak_pay": 0.00,
        "order_value": 28.50,
        "pay_per_economic_mile": 1.09,
        "effective_hourly_rate": 15.0,
        "is_batched_candidate": True,
        "is_high_wait_merchant": False,
        "is_long_deadhead_zone": False,
        "reasons": ["Batched order complexity adjustment applied."],
    }

    print(engine.evaluate(sample).to_dict())