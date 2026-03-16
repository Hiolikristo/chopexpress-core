from typing import Any, Callable, Dict, Tuple

import backend.delivery_verification_engine as delivery_verification_engine
import backend.dispatch_offer_engine as dispatch_offer_engine
import backend.driver_ms_engine as driver_ms_engine
import backend.driver_tax_engine as driver_tax_engine
import backend.fair_offer_engine as fair_offer_engine
import backend.insurance_support_engine as insurance_support_engine
import backend.merchant_finance_engine as merchant_finance_engine
import backend.merchant_tax_engine as merchant_tax_engine
import backend.order_value_breakdown_engine as order_value_breakdown_engine
import backend.settlement_engine as settlement_engine
import backend.customer_loyalty_engine as customer_loyalty_engine


class EngineContractError(Exception):
    pass


def _safe_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {"value": value}


def _resolve_engine_callable(
    module: Any,
    candidates: Tuple[str, ...],
    module_name: str,
) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    for name in candidates:
        fn = getattr(module, name, None)
        if callable(fn):
            return fn

    joined = ", ".join(candidates)
    raise EngineContractError(f"{module_name} must expose one of: {joined}")


def _run_breakdown(payload: Dict[str, Any]) -> Dict[str, Any]:
    fn = _resolve_engine_callable(
        order_value_breakdown_engine,
        ("evaluate", "order_value_breakdown", "order_value_breakdown_engine"),
        "order_value_breakdown_engine",
    )
    return _safe_dict(fn(payload))


def _run_fair_offer(payload: Dict[str, Any]) -> Dict[str, Any]:
    fn = _resolve_engine_callable(
        fair_offer_engine,
        ("evaluate", "fair_offer", "fair_offer_engine"),
        "fair_offer_engine",
    )
    return _safe_dict(fn(payload))


def _run_dispatch(payload: Dict[str, Any]) -> Dict[str, Any]:
    fn = _resolve_engine_callable(
        dispatch_offer_engine,
        ("evaluate", "dispatch_offer", "dispatch_offer_engine"),
        "dispatch_offer_engine",
    )
    return _safe_dict(fn(payload))


def _run_driver_ms(payload: Dict[str, Any]) -> Dict[str, Any]:
    fn = _resolve_engine_callable(
        driver_ms_engine,
        ("evaluate", "driver_ms", "driver_ms_engine"),
        "driver_ms_engine",
    )
    return _safe_dict(fn(payload))


def _run_insurance(payload: Dict[str, Any]) -> Dict[str, Any]:
    fn = _resolve_engine_callable(
        insurance_support_engine,
        ("evaluate", "insurance_support", "insurance_support_engine"),
        "insurance_support_engine",
    )
    return _safe_dict(fn(payload))


def _run_verification(payload: Dict[str, Any]) -> Dict[str, Any]:
    fn = _resolve_engine_callable(
        delivery_verification_engine,
        ("evaluate", "delivery_verification", "delivery_verification_engine"),
        "delivery_verification_engine",
    )
    return _safe_dict(fn(payload))


def _run_merchant_finance(payload: Dict[str, Any]) -> Dict[str, Any]:
    fn = _resolve_engine_callable(
        merchant_finance_engine,
        ("evaluate", "merchant_finance", "merchant_finance_engine"),
        "merchant_finance_engine",
    )
    return _safe_dict(fn(payload))


def _run_merchant_tax(payload: Dict[str, Any]) -> Dict[str, Any]:
    fn = _resolve_engine_callable(
        merchant_tax_engine,
        ("evaluate", "merchant_tax", "merchant_tax_engine"),
        "merchant_tax_engine",
    )
    return _safe_dict(fn(payload))


def _run_settlement(payload: Dict[str, Any]) -> Dict[str, Any]:
    fn = _resolve_engine_callable(
        settlement_engine,
        ("evaluate", "settlement", "settlement_engine"),
        "settlement_engine",
    )
    return _safe_dict(fn(payload))


def _run_driver_tax(payload: Dict[str, Any]) -> Dict[str, Any]:
    fn = _resolve_engine_callable(
        driver_tax_engine,
        ("evaluate", "driver_tax", "driver_tax_engine"),
        "driver_tax_engine",
    )
    return _safe_dict(fn(payload))


def _run_customer_loyalty(payload: Dict[str, Any]) -> Dict[str, Any]:
    fn = _resolve_engine_callable(
        customer_loyalty_engine,
        ("evaluate", "customer_loyalty", "customer_loyalty_engine"),
        "customer_loyalty_engine",
    )
    return _safe_dict(fn(payload))


def evaluate_order_pipeline(payload: Dict[str, Any]) -> Dict[str, Any]:
    breakdown = _run_breakdown(payload)
    fair_offer = _run_fair_offer(payload)
    dispatch = _run_dispatch(payload)
    driver_ms = _run_driver_ms(payload)
    insurance = _run_insurance(payload)
    verification = _run_verification(payload)
    merchant_finance = _run_merchant_finance(payload)
    merchant_tax = _run_merchant_tax(payload)
    settlement = _run_settlement(payload)
    driver_tax = _run_driver_tax(payload)
    customer_loyalty = _run_customer_loyalty(payload)

    return {
        "breakdown": breakdown,
        "fair_offer": fair_offer,
        "dispatch": dispatch,
        "driver_ms": driver_ms,
        "insurance": insurance,
        "verification": verification,
        "merchant_finance": merchant_finance,
        "merchant_tax": merchant_tax,
        "settlement": settlement,
        "driver_tax": driver_tax,
        "customer_loyalty": customer_loyalty,
    }