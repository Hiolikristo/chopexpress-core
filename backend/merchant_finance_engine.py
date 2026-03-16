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
    merchant_id = _to_text(payload.get("merchant_id"), payload.get("merchant", "UNKNOWN_MERCHANT"))
    merchant_name = _to_text(payload.get("merchant"), "Unknown Merchant")
    order_id = _to_text(payload.get("order_id"), "UNKNOWN")

    order_value = _to_float(payload.get("order_value"))
    sales_tax_rate = _to_float(payload.get("sales_tax_rate"), 0.075)
    commission_rate = _to_float(payload.get("commission_rate"), 0.18)
    processing_rate = _to_float(payload.get("processing_rate"), 0.03)
    fixed_processing_fee = _to_float(payload.get("fixed_processing_fee"), 0.30)
    promo_support = _to_float(payload.get("promo_support"), 0.0)

    merchant_subtotal = round(order_value, 2)
    merchant_tax_collected = round(merchant_subtotal * sales_tax_rate, 2)
    gross_customer_charge = round(merchant_subtotal + merchant_tax_collected, 2)

    platform_commission = round(merchant_subtotal * commission_rate, 2)
    payment_processing_fee = round((gross_customer_charge * processing_rate) + fixed_processing_fee, 2)

    merchant_net_before_adjustments = round(
        merchant_subtotal - platform_commission - payment_processing_fee,
        2,
    )
    merchant_net = round(merchant_net_before_adjustments - promo_support, 2)

    profitability_band = "healthy"
    if merchant_net < merchant_subtotal * 0.55:
        profitability_band = "tight"
    if merchant_net < merchant_subtotal * 0.40:
        profitability_band = "at_risk"

    return {
        "order_id": order_id,
        "merchant_id": merchant_id,
        "merchant_name": merchant_name,
        "merchant_subtotal": merchant_subtotal,
        "merchant_tax_collected": merchant_tax_collected,
        "gross_customer_charge": gross_customer_charge,
        "platform_commission": platform_commission,
        "payment_processing_fee": payment_processing_fee,
        "promo_support": round(promo_support, 2),
        "merchant_net_before_adjustments": merchant_net_before_adjustments,
        "merchant_net": merchant_net,
        "profitability_band": profitability_band,
    }


def merchant_finance(payload: Dict[str, Any]) -> Dict[str, Any]:
    return evaluate(payload)


def merchant_finance_engine(payload: Dict[str, Any]) -> Dict[str, Any]:
    return evaluate(payload)