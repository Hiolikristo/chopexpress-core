from typing import Any, Dict


def evaluate(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Driver tax engine.

    Produces a simple estimated tax view for driver earnings.
    This is a planning/ledger helper, not formal tax advice.
    """

    driver_id = payload.get("driver_id", "unknown")
    gross_pay = float(payload.get("gross_pay", 0.0) or 0.0)
    driver_tax_rate = float(payload.get("driver_tax_rate", 0.15) or 0.15)

    estimated_tax = round(gross_pay * driver_tax_rate, 2)
    net_after_tax = round(gross_pay - estimated_tax, 2)

    return {
        "driver_id": driver_id,
        "gross_pay": gross_pay,
        "driver_tax_rate": driver_tax_rate,
        "estimated_tax": estimated_tax,
        "net_after_tax": net_after_tax,
        "status": "ok",
    }


def driver_tax(payload: Dict[str, Any]) -> Dict[str, Any]:
    return evaluate(payload)


def driver_tax_engine(payload: Dict[str, Any]) -> Dict[str, Any]:
    return evaluate(payload)