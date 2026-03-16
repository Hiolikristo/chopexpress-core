from typing import Any, Dict


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


def evaluate(payload: Dict[str, Any]) -> Dict[str, Any]:
    order_id = _to_text(payload.get("order_id"), "UNKNOWN")
    merchant_id = _to_text(payload.get("merchant_id"), payload.get("merchant", "UNKNOWN_MERCHANT"))
    merchant_name = _to_text(payload.get("merchant"), "Unknown Merchant")

    order_value = _to_float(payload.get("order_value"))
    sales_tax_rate = _to_float(payload.get("sales_tax_rate"), 0.075)

    taxable_sales = round(order_value, 2)
    sales_tax_due = round(taxable_sales * sales_tax_rate, 2)
    gross_receipts = round(taxable_sales + sales_tax_due, 2)

    return {
        "order_id": order_id,
        "merchant_id": merchant_id,
        "merchant_name": merchant_name,
        "taxable_sales": taxable_sales,
        "sales_tax_rate": round(sales_tax_rate, 4),
        "sales_tax_due": sales_tax_due,
        "gross_receipts": gross_receipts,
        "filing_note": "This is an operational estimate for bookkeeping and dashboard use.",
    }


def merchant_tax(payload: Dict[str, Any]) -> Dict[str, Any]:
    return evaluate(payload)


def merchant_tax_engine(payload: Dict[str, Any]) -> Dict[str, Any]:
    return evaluate(payload)