from __future__ import annotations

from typing import Any, Dict


def _norm(text: str) -> str:
    return text.strip().lower()


MERCHANT_RULES = {
    "wingstop": {
        "pickup_wait_risk": 8.0,
        "parking_friction": 2.0,
        "handoff_complexity": 1.0,
    },
    "kfc": {
        "pickup_wait_risk": 4.0,
        "parking_friction": 1.0,
        "handoff_complexity": 0.5,
    },
    "jimmy john's": {
        "pickup_wait_risk": 2.0,
        "parking_friction": 0.5,
        "handoff_complexity": 0.5,
    },
    "tim hortons": {
        "pickup_wait_risk": 2.0,
        "parking_friction": 0.5,
        "handoff_complexity": 0.5,
    },
    "main ground coffee": {
        "pickup_wait_risk": 3.0,
        "parking_friction": 0.5,
        "handoff_complexity": 0.5,
    },
}


DROP_TYPE_RULES = {
    "apartment": {
        "vertical_delay": 4.0,
        "access_friction": 2.0,
    },
    "hotel": {
        "vertical_delay": 5.0,
        "access_friction": 2.5,
    },
    "hospital": {
        "vertical_delay": 6.0,
        "access_friction": 3.0,
    },
    "house": {
        "vertical_delay": 0.5,
        "access_friction": 0.5,
    },
    "office": {
        "vertical_delay": 3.0,
        "access_friction": 2.0,
    },
}


def get_merchant_friction(observation: Any) -> Dict[str, float]:
    merchant_name = str(getattr(observation, "merchant_name", "") or "")
    dropoff_type = str(getattr(observation, "dropoff_type", "") or "")

    merchant_key = _norm(merchant_name)
    dropoff_key = _norm(dropoff_type)

    merchant = MERCHANT_RULES.get(
        merchant_key,
        {
            "pickup_wait_risk": 1.5,
            "parking_friction": 0.5,
            "handoff_complexity": 0.5,
        },
    )

    dropoff = DROP_TYPE_RULES.get(
        dropoff_key,
        {
            "vertical_delay": 1.0,
            "access_friction": 1.0,
        },
    )

    total_friction_minutes = round(
        merchant["pickup_wait_risk"]
        + merchant["parking_friction"]
        + merchant["handoff_complexity"]
        + dropoff["vertical_delay"]
        + dropoff["access_friction"],
        2,
    )

    return {
        "pickup_wait_risk": round(merchant["pickup_wait_risk"], 2),
        "parking_friction": round(merchant["parking_friction"], 2),
        "handoff_complexity": round(merchant["handoff_complexity"], 2),
        "vertical_delay": round(dropoff["vertical_delay"], 2),
        "access_friction": round(dropoff["access_friction"], 2),
        "merchant_total_friction_minutes": total_friction_minutes,
    }


if __name__ == "__main__":
    class DemoObservation:
        merchant_name = "KFC"
        dropoff_type = "apartment"

    demo = DemoObservation()
    print(get_merchant_friction(demo))