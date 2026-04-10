from typing import Dict, Any


def insurance_support(payload: Dict[str, Any]):

    value = payload["order_value"]

    coverage = value * 0.02

    return {

        "insurance_buffer": round(coverage, 2)
    }