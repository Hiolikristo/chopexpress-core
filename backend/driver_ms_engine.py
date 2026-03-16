from typing import Dict, Any


ZONE_PRESSURE_MULTIPLIERS = {
    "low": 0.9,
    "normal": 1.0,
    "busy": 1.1,
    "surge": 1.25
}


def _to_float(v, default=0.0):
    try:
        return float(v)
    except:
        return default


def evaluate(payload: Dict[str, Any]) -> Dict[str, Any]:

    zone_pressure_score = _to_float(payload.get("zone_pressure_score", 1.0))
    merchant_risk_score = _to_float(payload.get("merchant_risk_score", 0.3))

    base_multiplier = 1.0

    if zone_pressure_score < 0.9:
        zone_state = "low"
    elif zone_pressure_score < 1.1:
        zone_state = "normal"
    elif zone_pressure_score < 1.3:
        zone_state = "busy"
    else:
        zone_state = "surge"

    pressure_multiplier = ZONE_PRESSURE_MULTIPLIERS.get(zone_state, 1.0)

    merchant_delay_risk = merchant_risk_score * 0.15

    final_driver_market_multiplier = base_multiplier * pressure_multiplier + merchant_delay_risk

    return {
        "zone_state": zone_state,
        "zone_pressure_score": round(zone_pressure_score, 2),
        "pressure_multiplier": round(pressure_multiplier, 3),
        "merchant_delay_risk": round(merchant_delay_risk, 3),
        "driver_market_multiplier": round(final_driver_market_multiplier, 3)
    }