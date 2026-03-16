from typing import Any, Dict, List


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
    return str(value).strip()


def record_transaction(entry: Dict[str, Any]) -> Dict[str, Any]:
    clean_entry = {
        "order_id": _to_text(entry.get("order_id"), "UNKNOWN"),
        "driver_id": _to_text(entry.get("driver_id"), "UNASSIGNED"),
        "merchant_id": _to_text(entry.get("merchant_id"), "UNKNOWN_MERCHANT"),
        "customer_total": _to_float(entry.get("customer_total")),
        "driver_payout": _to_float(entry.get("driver_payout")),
        "platform_fee": _to_float(entry.get("platform_fee")),
        "merchant_subtotal": _to_float(entry.get("merchant_subtotal")),
        "merchant_tax_collected": _to_float(entry.get("merchant_tax_collected")),
        "merchant_net": _to_float(entry.get("merchant_net")),
        "status": _to_text(entry.get("status"), "recorded"),
    }

    LEDGER.append(clean_entry)
    return clean_entry


def get_ledger() -> List[Dict[str, Any]]:
    return LEDGER


def merchant_ledger_view(merchant_id: str) -> Dict[str, Any]:
    rows = [row for row in LEDGER if row.get("merchant_id") == merchant_id]

    gross_sales = round(sum(_to_float(r.get("merchant_subtotal")) for r in rows), 2)
    tax_collected = round(sum(_to_float(r.get("merchant_tax_collected")) for r in rows), 2)
    driver_payouts = round(sum(_to_float(r.get("driver_payout")) for r in rows), 2)
    platform_fees = round(sum(_to_float(r.get("platform_fee")) for r in rows), 2)
    merchant_net = round(sum(_to_float(r.get("merchant_net")) for r in rows), 2)

    return {
        "merchant_id": merchant_id,
        "order_count": len(rows),
        "gross_sales": gross_sales,
        "tax_collected": tax_collected,
        "driver_payouts": driver_payouts,
        "platform_fees": platform_fees,
        "merchant_net": merchant_net,
        "entries": rows,
    }