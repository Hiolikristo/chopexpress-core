from typing import Any, Callable, Dict

from .customer_loyalty_engine import customer_loyalty_engine
from .delivery_verification_engine import delivery_verification_engine
from .dispatch_engine import dispatch_engine
from .driver_ms_engine import driver_ms_engine
from .driver_tax_engine import driver_tax_engine
from .fair_offer_engine import fair_offer_engine
from .insurance_support_engine import insurance_support_engine
from .merchant_finance_engine import merchant_finance_engine
from .merchant_tax_engine import merchant_tax_engine
from .settlement_engine import settlement_engine


class EngineContractError(Exception):
    pass


def _validate_result(module_name: str, result: Any, fn_name: str) -> Dict[str, Any]:
    if not isinstance(result, dict):
        raise EngineContractError(
            f"{module_name} returned non-dict result from '{fn_name}'"
        )
    return result


def _run_callable(
    module_name: str,
    payload: Dict[str, Any],
    fn: Callable[[Dict[str, Any]], Dict[str, Any]],
    fn_name: str,
) -> Dict[str, Any]:
    if not callable(fn):
        raise EngineContractError(
            f"{module_name} must expose callable '{fn_name}'"
        )
    result = fn(payload)
    return _validate_result(module_name, result, fn_name)


def evaluate_order_pipeline(payload: Dict[str, Any]) -> Dict[str, Any]:
    breakdown = _run_callable(
        "fair_offer_engine",
        payload,
        fair_offer_engine,
        "fair_offer_engine",
    )

    dispatch = _run_callable(
        "dispatch_engine",
        payload,
        dispatch_engine,
        "dispatch_engine",
    )

    driver_ms = _run_callable(
        "driver_ms_engine",
        payload,
        driver_ms_engine,
        "driver_ms_engine",
    )

    insurance = _run_callable(
        "insurance_support_engine",
        payload,
        insurance_support_engine,
        "insurance_support_engine",
    )

    verification = _run_callable(
        "delivery_verification_engine",
        payload,
        delivery_verification_engine,
        "delivery_verification_engine",
    )

    merchant_finance = _run_callable(
        "merchant_finance_engine",
        payload,
        merchant_finance_engine,
        "merchant_finance_engine",
    )

    merchant_tax = _run_callable(
        "merchant_tax_engine",
        payload,
        merchant_tax_engine,
        "merchant_tax_engine",
    )

    settlement = _run_callable(
        "settlement_engine",
        payload,
        settlement_engine,
        "settlement_engine",
    )

    driver_tax = _run_callable(
        "driver_tax_engine",
        payload,
        driver_tax_engine,
        "driver_tax_engine",
    )

    customer_loyalty = _run_callable(
        "customer_loyalty_engine",
        payload,
        customer_loyalty_engine,
        "customer_loyalty_engine",
    )

    return {
        "breakdown": breakdown,
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