from __future__ import annotations

from typing import Any, Dict

from backend.driver_tax_engine import evaluate as evaluate_tax
from backend.tier_engine import get_tier_policy


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


def evaluate(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Settlement and reserve view for a single order.
    """

    order_id = _to_text(payload.get("order_id"), "UNKNOWN")
    driver_id = _to_text(payload.get("driver_id"), "UNASSIGNED")
    merchant_id = _to_text(
        payload.get("merchant_id"),
        _to_text(payload.get("merchant"), "UNKNOWN_MERCHANT"),
    )

    order_value = _to_float(payload.get("order_value"), 0.0)
    tip = _to_float(payload.get("tip"), 0.0)
    offered_payout = _to_float(payload.get("offered_payout"), 0.0)
    rolling_30_day_miles = _to_float(payload.get("rolling_30_day_miles"), 0.0)

    sales_tax_rate = _to_float(payload.get("sales_tax_rate"), 0.075)
    commission_rate = _to_float(payload.get("commission_rate"), 0.18)
    processing_rate = _to_float(payload.get("processing_rate"), 0.03)
    fixed_processing_fee = _to_float(payload.get("fixed_processing_fee"), 0.30)
    driver_tax_rate = _to_float(payload.get("driver_tax_rate"), 0.15)

    merchant_tax_collected = round(order_value * sales_tax_rate, 2)
    gross_customer_charge = round(order_value + merchant_tax_collected + tip, 2)

    platform_commission = round(order_value * commission_rate, 2)
    payment_processing_fee = round(
        (gross_customer_charge * processing_rate) + fixed_processing_fee,
        2,
    )

    merchant_net = round(
        order_value - platform_commission - payment_processing_fee,
        2,
    )

    driver_gross_total = round(offered_payout + tip, 2)

    policy = get_tier_policy(rolling_30_day_miles)
    maintenance_reserve = round(
        driver_gross_total * policy.maintenance_reserve_rate,
        2,
    )
    insurance_reserve = round(
        driver_gross_total * policy.insurance_reserve_rate,
        2,
    )

    reserve_total = round(maintenance_reserve + insurance_reserve, 2)
    driver_available_balance = round(driver_gross_total - reserve_total, 2)

    tax_view = evaluate_tax(
        {
            "driver_id": driver_id,
            "gross_pay": driver_gross_total,
            "driver_tax_rate": driver_tax_rate,
        }
    )

    platform_net = round(
        gross_customer_charge - merchant_net - driver_gross_total - merchant_tax_collected,
        2,
    )

    settlement_status = "balanced"
    if platform_net < 0:
        settlement_status = "platform_negative"
    if merchant_net < 0:
        settlement_status = "merchant_negative"

    return {
        "order_id": order_id,
        "driver_id": driver_id,
        "merchant_id": merchant_id,
        "order_value": round(order_value, 2),
        "tip": round(tip, 2),
        "offered_payout": round(offered_payout, 2),
        "gross_customer_charge": gross_customer_charge,
        "merchant_tax_collected": merchant_tax_collected,
        "platform_commission": platform_commission,
        "payment_processing_fee": payment_processing_fee,
        "merchant_net": merchant_net,
        "driver_gross_total": driver_gross_total,
        "rolling_30_day_miles": round(rolling_30_day_miles, 2),
        "driver_tier": policy.name,
        "maintenance_reserve_rate": policy.maintenance_reserve_rate,
        "insurance_reserve_rate": policy.insurance_reserve_rate,
        "maintenance_reserve": maintenance_reserve,
        "insurance_reserve": insurance_reserve,
        "reserve_total": reserve_total,
        "driver_available_balance": driver_available_balance,
        "estimated_tax": tax_view["estimated_tax"],
        "net_after_tax_estimate": tax_view["net_after_tax"],
        "platform_net": platform_net,
        "settlement_status": settlement_status,
    }


def settlement(payload: Dict[str, Any]) -> Dict[str, Any]:
    return evaluate(payload)


def settlement_engine(payload: Dict[str, Any]) -> Dict[str, Any]:
    return evaluate(payload)


if __name__ == "__main__":
    demo_payload = {
        "order_id": "ORD-SETTLE-001",
        "driver_id": "DRV-001",
        "merchant_id": "MERCHANT-KFC-MORSE",
        "order_value": 28.50,
        "tip": 4.50,
        "offered_payout": 7.25,
        "rolling_30_day_miles": 2675,
        "sales_tax_rate": 0.075,
        "commission_rate": 0.18,
        "processing_rate": 0.03,
        "fixed_processing_fee": 0.30,
        "driver_tax_rate": 0.15,
    }

    print(evaluate(demo_payload))