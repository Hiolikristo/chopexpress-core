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

    order_value = _to_float(payload.get("order_value"))
    tip = _to_float(payload.get("tip"))
    offered_payout = _to_float(payload.get("offered_payout"))

    sales_tax_rate = _to_float(payload.get("sales_tax_rate"), 0.075)
    commission_rate = _to_float(payload.get("commission_rate"), 0.18)
    processing_rate = _to_float(payload.get("processing_rate"), 0.03)
    fixed_processing_fee = _to_float(payload.get("fixed_processing_fee"), 0.30)

    merchant_tax_collected = round(order_value * sales_tax_rate, 2)
    gross_customer_charge = round(order_value + merchant_tax_collected + tip, 2)

    platform_commission = round(order_value * commission_rate, 2)
    payment_processing_fee = round((gross_customer_charge * processing_rate) + fixed_processing_fee, 2)

    merchant_net = round(order_value - platform_commission - payment_processing_fee, 2)
    driver_total = round(offered_payout + tip, 2)

    platform_net = round(
        gross_customer_charge - merchant_net - driver_total - merchant_tax_collected,
        2,
    )

    settlement_status = "balanced"
    if platform_net < 0:
        settlement_status = "platform_negative"
    if merchant_net < 0:
        settlement_status = "merchant_negative"

    return {
        "order_id": order_id,
        "merchant_id": merchant_id,
        "gross_customer_charge": gross_customer_charge,
        "merchant_tax_collected": merchant_tax_collected,
        "merchant_net": merchant_net,
        "driver_total": driver_total,
        "platform_net": platform_net,
        "settlement_status": settlement_status,
    }


def settlement(payload: Dict[str, Any]) -> Dict[str, Any]:
    return evaluate(payload)


def settlement_engine(payload: Dict[str, Any]) -> Dict[str, Any]:
    return evaluate(payload)