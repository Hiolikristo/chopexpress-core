from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Optional


TWOPLACES = Decimal("0.01")


def q2(value: Decimal) -> Decimal:
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


@dataclass
class OrderValueBreakdownInput:
    order_id: str
    zone: str
    merchant: str

    # Optional total; if not supplied we derive it from components
    offered_payout: Optional[Decimal] = None

    base_pay: Decimal = Decimal("0.00")
    tip_amount: Decimal = Decimal("0.00")
    peak_pay: Decimal = Decimal("0.00")

    pickup_miles: Decimal = Decimal("0.00")
    delivery_miles: Decimal = Decimal("0.00")
    return_miles_estimate: Decimal = Decimal("0.00")
    deadhead_miles: Decimal = Decimal("0.00")

    estimated_total_minutes: Decimal = Decimal("0.00")
    estimated_prep_delay_minutes: Decimal = Decimal("0.00")
    estimated_traffic_delay_minutes: Decimal = Decimal("0.00")

    merchant_risk_score: Decimal = Decimal("0.00")
    zone_pressure_score: Decimal = Decimal("0.00")

    is_batched_candidate: bool = False
    is_high_wait_merchant: bool = False
    is_long_deadhead_zone: bool = False


@dataclass
class OrderValueBreakdownResult:
    order_id: str
    zone: str
    merchant: str

    offered_payout: Decimal
    base_pay: Decimal
    tip_amount: Decimal
    peak_pay: Decimal

    pickup_miles: Decimal
    delivery_miles: Decimal
    return_miles_estimate: Decimal
    deadhead_miles: Decimal
    economic_miles: Decimal

    estimated_total_minutes: Decimal
    estimated_prep_delay_minutes: Decimal
    estimated_traffic_delay_minutes: Decimal

    pay_per_pickup_mile: Decimal
    pay_per_delivery_mile: Decimal
    pay_per_economic_mile: Decimal
    effective_hourly_rate: Decimal

    base_component_ratio: Decimal
    tip_component_ratio: Decimal
    peak_component_ratio: Decimal

    time_cost_score: Decimal
    distance_cost_score: Decimal
    merchant_risk_score: Decimal
    zone_pressure_score: Decimal

    complexity_penalty: Decimal
    recommended_value_band: str

    def to_dict(self) -> Dict[str, object]:
        data = asdict(self)
        for key, value in data.items():
            if isinstance(value, Decimal):
                data[key] = str(q2(value))
        return data


class OrderValueBreakdownEngine:
    """
    V1 economic value model.

    Supports either:
    - explicit offered_payout, or
    - derived offered_payout from base_pay + tip_amount + peak_pay

    Also supports either:
    - return_miles_estimate
    - deadhead_miles

    Effective unpaid return exposure is the max of the two.
    """

    def evaluate(self, input_data: OrderValueBreakdownInput) -> OrderValueBreakdownResult:
        base_pay = Decimal(input_data.base_pay)
        tip_amount = Decimal(input_data.tip_amount)
        peak_pay = Decimal(input_data.peak_pay)

        if input_data.offered_payout is None:
            offered_payout = base_pay + tip_amount + peak_pay
        else:
            offered_payout = Decimal(input_data.offered_payout)

        pickup_miles = Decimal(input_data.pickup_miles)
        delivery_miles = Decimal(input_data.delivery_miles)
        return_miles_estimate = Decimal(input_data.return_miles_estimate)
        deadhead_miles = Decimal(input_data.deadhead_miles)

        estimated_total_minutes = Decimal(input_data.estimated_total_minutes)
        estimated_prep_delay_minutes = Decimal(input_data.estimated_prep_delay_minutes)
        estimated_traffic_delay_minutes = Decimal(input_data.estimated_traffic_delay_minutes)

        merchant_risk_score = Decimal(input_data.merchant_risk_score)
        zone_pressure_score = Decimal(input_data.zone_pressure_score)

        effective_return_exposure = max(return_miles_estimate, deadhead_miles)
        economic_miles = pickup_miles + delivery_miles + effective_return_exposure

        pickup_miles_safe = pickup_miles if pickup_miles > 0 else Decimal("0.01")
        delivery_miles_safe = delivery_miles if delivery_miles > 0 else Decimal("0.01")
        economic_miles_safe = economic_miles if economic_miles > 0 else Decimal("0.01")
        total_minutes_safe = estimated_total_minutes if estimated_total_minutes > 0 else Decimal("1")

        pay_per_pickup_mile = offered_payout / pickup_miles_safe
        pay_per_delivery_mile = offered_payout / delivery_miles_safe
        pay_per_economic_mile = offered_payout / economic_miles_safe
        effective_hourly_rate = offered_payout / (total_minutes_safe / Decimal("60"))

        if offered_payout > 0:
            base_component_ratio = base_pay / offered_payout
            tip_component_ratio = tip_amount / offered_payout
            peak_component_ratio = peak_pay / offered_payout
        else:
            base_component_ratio = Decimal("0.00")
            tip_component_ratio = Decimal("0.00")
            peak_component_ratio = Decimal("0.00")

        time_cost_score = total_minutes_safe / Decimal("30")
        distance_cost_score = economic_miles_safe / Decimal("5")

        complexity_penalty = Decimal("0.00")
        if input_data.is_batched_candidate:
            complexity_penalty += Decimal("0.25")
        if input_data.is_high_wait_merchant:
            complexity_penalty += Decimal("0.35")
        if input_data.is_long_deadhead_zone:
            complexity_penalty += Decimal("0.40")

        if pay_per_economic_mile >= Decimal("2.00") and effective_hourly_rate >= Decimal("24.00"):
            recommended_value_band = "strong"
        elif pay_per_economic_mile >= Decimal("1.50") and effective_hourly_rate >= Decimal("18.00"):
            recommended_value_band = "acceptable"
        elif pay_per_economic_mile >= Decimal("1.15"):
            recommended_value_band = "borderline"
        else:
            recommended_value_band = "weak"

        return OrderValueBreakdownResult(
            order_id=input_data.order_id,
            zone=input_data.zone,
            merchant=input_data.merchant,

            offered_payout=q2(offered_payout),
            base_pay=q2(base_pay),
            tip_amount=q2(tip_amount),
            peak_pay=q2(peak_pay),

            pickup_miles=q2(pickup_miles),
            delivery_miles=q2(delivery_miles),
            return_miles_estimate=q2(return_miles_estimate),
            deadhead_miles=q2(deadhead_miles),
            economic_miles=q2(economic_miles),

            estimated_total_minutes=q2(estimated_total_minutes),
            estimated_prep_delay_minutes=q2(estimated_prep_delay_minutes),
            estimated_traffic_delay_minutes=q2(estimated_traffic_delay_minutes),

            pay_per_pickup_mile=q2(pay_per_pickup_mile),
            pay_per_delivery_mile=q2(pay_per_delivery_mile),
            pay_per_economic_mile=q2(pay_per_economic_mile),
            effective_hourly_rate=q2(effective_hourly_rate),

            base_component_ratio=q2(base_component_ratio),
            tip_component_ratio=q2(tip_component_ratio),
            peak_component_ratio=q2(peak_component_ratio),

            time_cost_score=q2(time_cost_score),
            distance_cost_score=q2(distance_cost_score),
            merchant_risk_score=q2(merchant_risk_score),
            zone_pressure_score=q2(zone_pressure_score),

            complexity_penalty=q2(complexity_penalty),
            recommended_value_band=recommended_value_band,
        )


if __name__ == "__main__":
    engine = OrderValueBreakdownEngine()

    sample = OrderValueBreakdownInput(
        order_id="order_1001",
        zone="clintonville",
        merchant="Chick-fil-A",

        base_pay=Decimal("5.75"),
        tip_amount=Decimal("3.00"),
        peak_pay=Decimal("0.00"),

        pickup_miles=Decimal("1.70"),
        delivery_miles=Decimal("6.60"),
        return_miles_estimate=Decimal("1.20"),
        deadhead_miles=Decimal("1.20"),

        estimated_total_minutes=Decimal("24"),
        estimated_prep_delay_minutes=Decimal("7"),
        estimated_traffic_delay_minutes=Decimal("4"),

        merchant_risk_score=Decimal("0.80"),
        zone_pressure_score=Decimal("1.10"),

        is_batched_candidate=True,
        is_high_wait_merchant=False,
        is_long_deadhead_zone=False,
    )

    print(engine.evaluate(sample).to_dict())