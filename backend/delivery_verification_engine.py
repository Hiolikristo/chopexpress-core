from typing import Any, Dict


def evaluate(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Delivery verification engine.

    Validates that the order can be safely handed to the driver and
    confirms that the merchant/customer conditions are acceptable.
    """

    merchant = payload.get("merchant", "unknown")
    merchant_risk = float(payload.get("merchant_risk_score", 0.0) or 0.0)
    is_batched = bool(payload.get("is_batched_order", False))

    verification_status = "approved"

    if merchant_risk > 0.7:
        verification_status = "manual_review"

    return {
        "merchant": merchant,
        "verification_status": verification_status,
        "merchant_risk_score": merchant_risk,
        "batch_order": is_batched,
        "status": "ok",
    }


def delivery_verification(payload: Dict[str, Any]) -> Dict[str, Any]:
    return evaluate(payload)


def delivery_verification_engine(payload: Dict[str, Any]) -> Dict[str, Any]:
    return evaluate(payload)