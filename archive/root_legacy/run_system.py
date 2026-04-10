import os
import sys
from pprint import pprint
from typing import Any

# Make local same-folder imports work when running:
#   python run_system.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.order_value_breakdown_engine import OrderValueBreakdownEngine
from backend.fair_offer_engine import FairOfferEngine
from backend.dispatch_offer_engine import DispatchOfferEngine
from backend.driver_ms_engine import DriverMSEngine
from backend.insurance_support_engine import InsuranceSupportEngine


def _safe_to_dict(value: Any) -> Any:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if hasattr(value, "__dict__"):
        return value.__dict__
    return value


def simulate_order() -> None:
    order = {
        "order_id": "TEST001",
        "zone": "clintonville",
        "merchant": "Test Kitchen",
        "tier": "professional",
        "pickup_distance": 2.1,
        "delivery_distance": 3.4,
        "return_distance": 2.5,
        "order_value": 28.50,
        "tip": 4.00,
        "offered_payout": 8.75,
        "is_batched_candidate": True,
        "is_high_wait_merchant": False,
        "is_long_deadhead_zone": False,
    }

    print("\n--- ORDER INPUT ---")
    pprint(order)

    ov_engine = OrderValueBreakdownEngine()
    fair_engine = FairOfferEngine()
    dispatch_engine = DispatchOfferEngine()
    driver_ms_engine = DriverMSEngine()
    insurance_engine = InsuranceSupportEngine()

    print("\n--- ORDER VALUE BREAKDOWN RESULT ---")
    ov_result = ov_engine.evaluate(order)
    pprint(_safe_to_dict(ov_result))

    print("\n--- FAIR OFFER RESULT ---")
    fair_result = fair_engine.evaluate(order)
    pprint(_safe_to_dict(fair_result))

    print("\n--- DISPATCH OFFER RESULT ---")
    dispatch_result = dispatch_engine.evaluate(order)
    pprint(_safe_to_dict(dispatch_result))

    print("\n--- DRIVER MS RESULT ---")
    driver_ms_result = driver_ms_engine.evaluate(order)
    pprint(_safe_to_dict(driver_ms_result))

    print("\n--- INSURANCE SUPPORT RESULT ---")
    insurance_result = insurance_engine.evaluate(order)
    pprint(_safe_to_dict(insurance_result))


if __name__ == "__main__":
    simulate_order()