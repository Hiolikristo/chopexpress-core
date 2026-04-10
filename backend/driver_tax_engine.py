from __future__ import annotations

from typing import Any, Dict


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def evaluate(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Advisory-only tax estimate.
    This is not withholding and not formal tax advice.
    """
    driver_id = str(payload.get("driver_id", "unknown")).strip() or "unknown"
    gross_pay = _to_float(payload.get("gross_pay"), 0.0)
    driver_tax_rate = _to_float(payload.get("driver_tax_rate"), 0.15)

    estimated_tax = round(gross_pay * driver_tax_rate, 2)
    net_after_tax = round(gross_pay - estimated_tax, 2)

    return {
        "driver_id": driver_id,
        "gross_pay": round(gross_pay, 2),
        "driver_tax_rate": driver_tax_rate,
        "estimated_tax": estimated_tax,
        "net_after_tax": net_after_tax,
        "status": "ok",
    }


def driver_tax(payload: Dict[str, Any]) -> Dict[str, Any]:
    return evaluate(payload)


def driver_tax_engine(payload: Dict[str, Any]) -> Dict[str, Any]:
    return evaluate(payload)