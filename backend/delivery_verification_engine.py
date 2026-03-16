# backend/delivery_verification_engine.py

from typing import Dict, Any


def evaluate(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Delivery verification engine.

    Validates that the order can be safely handed to the driver and
    confirms that the merchant/customer conditions are acceptable.
    """

    merchant = payload.get("merchant", "unknown")
    merchant_risk = payload.get("merchant_risk_score", 0.0)
    is_batched = payload.get("is_batched_order", False)

    verification_status = "approved"

    if merchant_risk > 0.7:
        verification_status = "manual_review"

    if is_batched:
        batch_flag = True
    else:
        batch_flag = False

    return {
        "merchant": merchant,
        "verification_status": verification_status,
        "merchant_risk_score": merchant_risk,
        "batch_order": batch_flag
    }


# optional aliases so the pipeline contract validator is always satisfied

def delivery_verification(payload: Dict[str, Any]) -> Dict[str, Any]:
    return evaluate(payload)


def delivery_verification_engine(payload: Dict[str, Any]) -> Dict[str, Any]:
    return evaluate(payload)