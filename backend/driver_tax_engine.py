from typing import Any, Dict

IRS_MILEAGE_RATE = 0.67
SELF_EMPLOYMENT_TAX_RATE = 0.153
ESTIMATED_FEDERAL_TAX_RATE = 0.12


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def evaluate(payload: Dict[str, Any]) -> Dict[str, Any]:
    offered_payout = _to_float(payload.get("offered_payout"))
    tip = _to_float(payload.get("tip"))

    delivery_distance = _to_float(payload.get("delivery_distance"))
    pickup_distance = _to_float(payload.get("pickup_distance"))
    return_distance = _to_float(payload.get("return_distance"))

    gross_driver_income = offered_payout + tip
    economic_miles = delivery_distance + pickup_distance + return_distance

    mileage_deduction_value = economic_miles * IRS_MILEAGE_RATE
    taxable_income_estimate = max(gross_driver_income - mileage_deduction_value, 0.0)

    federal_tax_estimate = taxable_income_estimate * ESTIMATED_FEDERAL_TAX_RATE
    self_employment_tax_estimate = taxable_income_estimate * SELF_EMPLOYMENT_TAX_RATE
    estimated_total_tax = federal_tax_estimate + self_employment_tax_estimate

    return {
        "gross_driver_income": round(gross_driver_income, 2),
        "economic_miles": round(economic_miles, 2),
        "mileage_deduction_value": round(mileage_deduction_value, 2),
        "taxable_income_estimate": round(taxable_income_estimate, 2),
        "federal_tax_estimate": round(federal_tax_estimate, 2),
        "self_employment_tax_estimate": round(self_employment_tax_estimate, 2),
        "estimated_tax_reserve": round(estimated_total_tax, 2),
    }