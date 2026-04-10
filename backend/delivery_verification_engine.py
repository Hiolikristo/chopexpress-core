from __future__ import annotations

from typing import Any, Dict, List, Optional


class DeliveryVerificationEngine:
    """
    Canonical backend verification helper.

    This module should stay lightweight and deterministic.
    It evaluates whether an order requires extra proof burden
    and returns a normalized verification payload.
    """

    @staticmethod
    def evaluate(payload: Dict[str, Any]) -> Dict[str, Any]:
        merchant_category = str(payload.get("merchant_category", "unknown")).lower()
        proof_required = bool(payload.get("proof_required", False))
        receipt_photo_required = bool(payload.get("receipt_photo_required", False))
        dropoff_photo_required = bool(payload.get("dropoff_photo_required", False))
        drink_risk = bool(payload.get("drink_risk", False))
        merchant_delay_flag = bool(payload.get("merchant_delay_flag", False))
        app_error_flag = bool(payload.get("app_error_flag", False))

        reasons: List[str] = []

        if proof_required:
            reasons.append("proof_required")

        if receipt_photo_required:
            reasons.append("receipt_photo_required")

        if dropoff_photo_required:
            reasons.append("dropoff_photo_required")

        if drink_risk:
            reasons.append("drink_risk")

        if merchant_delay_flag:
            reasons.append("merchant_delay_flag")

        if app_error_flag:
            reasons.append("app_error_flag")

        if merchant_category in {"grocery", "pharmacy", "retail"}:
            reasons.append("high_item_variability")

        risk_score = 0.0
        risk_score += 0.20 if proof_required else 0.0
        risk_score += 0.10 if receipt_photo_required else 0.0
        risk_score += 0.10 if dropoff_photo_required else 0.0
        risk_score += 0.15 if drink_risk else 0.0
        risk_score += 0.15 if merchant_delay_flag else 0.0
        risk_score += 0.20 if app_error_flag else 0.0
        risk_score += 0.10 if merchant_category in {"grocery", "pharmacy", "retail"} else 0.0
        risk_score = min(risk_score, 1.0)

        burden_minutes = 0.0
        burden_minutes += 2.0 if proof_required else 0.0
        burden_minutes += 1.5 if receipt_photo_required else 0.0
        burden_minutes += 1.5 if dropoff_photo_required else 0.0
        burden_minutes += 1.0 if drink_risk else 0.0
        burden_minutes += 3.0 if merchant_delay_flag else 0.0
        burden_minutes += 2.0 if app_error_flag else 0.0

        return {
            "verification_required": len(reasons) > 0,
            "risk_score": round(risk_score, 4),
            "burden_minutes": round(burden_minutes, 2),
            "reasons": reasons,
        }


def delivery_verification_engine(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compatibility function used by existing backend callers.
    """
    return DeliveryVerificationEngine.evaluate(payload)