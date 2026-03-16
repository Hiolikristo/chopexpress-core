from typing import Any, Dict, List


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "y"}:
            return True
        if lowered in {"false", "0", "no", "n"}:
            return False
    return bool(value)


def _to_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip()


def evaluate(payload: Dict[str, Any]) -> Dict[str, Any]:
    order_id = _to_text(payload.get("order_id"), "UNKNOWN")
    merchant = _to_text(payload.get("merchant"), "Unknown Merchant")
    zone = _to_text(payload.get("zone"), "unknown").lower()
    tier = _to_text(payload.get("tier"), "casual").lower()

    delivery_distance = _to_float(payload.get("delivery_distance"))
    pickup_distance = _to_float(payload.get("pickup_distance"))
    return_distance = _to_float(payload.get("return_distance"))
    estimated_total_minutes = _to_float(payload.get("estimated_total_minutes"), 0.0)
    merchant_risk_score = _to_float(payload.get("merchant_risk_score"), 0.0)
    is_batched_order = _to_bool(payload.get("is_batched_order"), False)

    total_miles = delivery_distance + pickup_distance + return_distance
    reasons: List[str] = []

    mileage_exposure_score = min(total_miles / 10.0, 1.0)
    time_exposure_score = min(estimated_total_minutes / 60.0, 1.0) if estimated_total_minutes > 0 else 0.0
    batch_exposure_score = 0.15 if is_batched_order else 0.0

    risk_score = (
        mileage_exposure_score * 0.45
        + time_exposure_score * 0.20
        + merchant_risk_score * 0.20
        + batch_exposure_score
    )

    risk_score = round(min(risk_score, 1.0), 2)

    if total_miles >= 8:
        reasons.append("Higher mileage exposure.")
    elif total_miles >= 5:
        reasons.append("Moderate mileage exposure.")
    else:
        reasons.append("Low mileage exposure.")

    if estimated_total_minutes >= 35:
        reasons.append("Longer trip time exposure.")
    elif estimated_total_minutes > 0:
        reasons.append("Standard trip time exposure.")

    if merchant_risk_score >= 0.5:
        reasons.append("Merchant friction raises support risk.")

    if is_batched_order:
        reasons.append("Batched order adds complexity.")

    if risk_score >= 0.70:
        risk_band = "high"
        reserve_contribution = round(total_miles * 0.08, 2)
        coverage_recommended = True
        coverage_note = "High-risk trip profile; elevated reserve coverage recommended."
    elif risk_score >= 0.35:
        risk_band = "moderate"
        reserve_contribution = round(total_miles * 0.0325, 2)
        coverage_recommended = True
        coverage_note = "Moderate-risk trip profile; standard reserve coverage recommended."
    else:
        risk_band = "low"
        reserve_contribution = round(total_miles * 0.015, 2)
        coverage_recommended = False
        coverage_note = "Low-risk trip profile; minimal reserve coverage is sufficient."

    return {
        "order_id": order_id,
        "merchant": merchant,
        "zone": zone,
        "tier": tier,
        "total_miles": round(total_miles, 2),
        "estimated_total_minutes": round(estimated_total_minutes, 2),
        "merchant_risk_score": round(merchant_risk_score, 2),
        "risk_score": risk_score,
        "risk_band": risk_band,
        "coverage_recommended": coverage_recommended,
        "coverage_note": coverage_note,
        "reserve_contribution": reserve_contribution,
        "reasons": reasons,
    }


def insurance_support(payload: Dict[str, Any]) -> Dict[str, Any]:
    return evaluate(payload)


def insurance_support_engine(payload: Dict[str, Any]) -> Dict[str, Any]:
    return evaluate(payload)