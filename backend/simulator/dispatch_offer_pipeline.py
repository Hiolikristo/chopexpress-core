from __future__ import annotations

import os
import sys
from decimal import Decimal
from typing import Any, Dict


# Support both:
# 1) python -m backend.simulator.dispatch_offer_pipeline
# 2) python backend/simulator/dispatch_offer_pipeline.py
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# Import engines directly from project root
from backend.order_value_breakdown_engine import (
    OrderValueBreakdownEngine,
    OrderValueBreakdownInput,
)
from backend.fair_offer_engine import (
    FairOfferEngine,
    FairOfferInput,
)


class DispatchOfferPipeline:
    """
    Connects:
    1. OrderValueBreakdownEngine
    2. FairOfferEngine

    This is the recommended evaluation sequence for a candidate order
    before final dispatch assignment.
    """

    def __init__(self) -> None:
        self.value_engine = OrderValueBreakdownEngine()
        self.fair_engine = FairOfferEngine()

    def evaluate_candidate_order(self) -> Dict[str, Any]:
        value_result = self.value_engine.evaluate(
            OrderValueBreakdownInput(
                order_id="order_1001",
                zone="clintonville",
                merchant="Chick-fil-A",
                pickup_miles=Decimal("1.70"),
                delivery_miles=Decimal("3.20"),
                return_miles_estimate=Decimal("1.70"),
                base_pay=Decimal("5.75"),
                tip_amount=Decimal("3.00"),
                peak_pay=Decimal("0.00"),
                estimated_prep_delay_minutes=Decimal("7"),
                estimated_traffic_delay_minutes=Decimal("4"),
                merchant_risk_score=Decimal("0.80"),
                zone_pressure_score=Decimal("1.10"),
                is_batched_candidate=True,
                is_high_wait_merchant=False,
                is_long_deadhead_zone=False,
            )
        )

        fair_result = self.fair_engine.evaluate(
            FairOfferInput(
                order_id="order_1001",
                zone="clintonville",
                merchant="Chick-fil-A",
                offered_payout=Decimal("8.75"),
                delivery_miles=Decimal("6.60"),
                economic_miles=Decimal("6.60"),
                estimated_total_minutes=Decimal("24"),
                tier="professional",
                zone_pressure_score=Decimal("1.10"),
                merchant_risk_score=Decimal("0.80"),
                is_batched_candidate=True,
                is_high_wait_merchant=False,
                is_long_deadhead_zone=False,
            )
        )

        return {
            "value_result": (
                value_result.to_dict()
                if hasattr(value_result, "to_dict")
                else value_result
            ),
            "fair_result": (
                fair_result.to_dict()
                if hasattr(fair_result, "to_dict")
                else fair_result
            ),
        }


if __name__ == "__main__":
    pipeline = DispatchOfferPipeline()
    result = pipeline.evaluate_candidate_order()
    print(result)