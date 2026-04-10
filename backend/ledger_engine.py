from __future__ import annotations

from typing import Any, Dict, List

from backend.settlement_engine import evaluate as evaluate_settlement


LEDGER: List[Dict[str, Any]] = []


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def record_transaction(entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Canonical ledger entry. If the incoming entry does not already contain
    reserve-aware settlement fields, they are computed first.
    """
    settlement = evaluate_settlement(entry)

    clean_entry = {
        "order_id": _to_text(settlement.get("order_id"), "UNKNOWN"),
        "driver_id": _to_text(settlement.get("driver_id"), "UNASSIGNED"),
        "merchant_id": _to_text(settlement.get("merchant_id"), "UNKNOWN_MERCHANT"),
        "order_value": _to_float(settlement.get("order_value")),
        "customer_total": _to_float(settlement.get("gross_customer_charge")),
        "driver_gross_total": _to_float(settlement.get("driver_gross_total")),
        "driver_available_balance": _to_float(settlement.get("driver_available_balance")),
        "maintenance_reserve": _to_float(settlement.get("maintenance_reserve")),
        "insurance_reserve": _to_float(settlement.get("insurance_reserve")),
        "reserve_total": _to_float(settlement.get("reserve_total")),
        "estimated_tax": _to_float(settlement.get("estimated_tax")),
        "net_after_tax_estimate": _to_float(settlement.get("net_after_tax_estimate")),
        "driver_tier": _to_text(settlement.get("driver_tier"), "Casual"),
        "platform_fee": _to_float(settlement.get("platform_commission"))
        + _to_float(settlement.get("payment_processing_fee")),
        "merchant_tax_collected": _to_float(settlement.get("merchant_tax_collected")),
        "merchant_net": _to_float(settlement.get("merchant_net")),
        "platform_net": _to_float(settlement.get("platform_net")),
        "status": _to_text(settlement.get("settlement_status"), "recorded"),
    }

    LEDGER.append(clean_entry)
    return clean_entry


def get_ledger() -> List[Dict[str, Any]]:
    return LEDGER


def merchant_ledger_view(merchant_id: str) -> Dict[str, Any]:
    rows = [row for row in LEDGER if row.get("merchant_id") == merchant_id]

    gross_sales = round(sum(_to_float(r.get("order_value")) for r in rows), 2)
    tax_collected = round(sum(_to_float(r.get("merchant_tax_collected")) for r in rows), 2)
    driver_gross_total = round(sum(_to_float(r.get("driver_gross_total")) for r in rows), 2)
    available_balance = round(sum(_to_float(r.get("driver_available_balance")) for r in rows), 2)
    maintenance_reserve = round(sum(_to_float(r.get("maintenance_reserve")) for r in rows), 2)
    insurance_reserve = round(sum(_to_float(r.get("insurance_reserve")) for r in rows), 2)
    platform_fees = round(sum(_to_float(r.get("platform_fee")) for r in rows), 2)
    merchant_net = round(sum(_to_float(r.get("merchant_net")) for r in rows), 2)

    return {
        "merchant_id": merchant_id,
        "order_count": len(rows),
        "gross_sales": gross_sales,
        "tax_collected": tax_collected,
        "driver_gross_total": driver_gross_total,
        "driver_available_balance": available_balance,
        "maintenance_reserve": maintenance_reserve,
        "insurance_reserve": insurance_reserve,
        "platform_fees": platform_fees,
        "merchant_net": merchant_net,
        "entries": rows,
    }


def driver_ledger_view(driver_id: str) -> Dict[str, Any]:
    rows = [row for row in LEDGER if row.get("driver_id") == driver_id]

    gross_total = round(sum(_to_float(r.get("driver_gross_total")) for r in rows), 2)
    available_balance = round(sum(_to_float(r.get("driver_available_balance")) for r in rows), 2)
    maintenance_reserve = round(sum(_to_float(r.get("maintenance_reserve")) for r in rows), 2)
    insurance_reserve = round(sum(_to_float(r.get("insurance_reserve")) for r in rows), 2)
    estimated_tax = round(sum(_to_float(r.get("estimated_tax")) for r in rows), 2)

    return {
        "driver_id": driver_id,
        "order_count": len(rows),
        "driver_gross_total": gross_total,
        "driver_available_balance": available_balance,
        "maintenance_reserve": maintenance_reserve,
        "insurance_reserve": insurance_reserve,
        "estimated_tax": estimated_tax,
        "entries": rows,
    }