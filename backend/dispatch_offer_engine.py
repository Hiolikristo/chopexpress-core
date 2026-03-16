from typing import Dict, Any


def dispatch_offer(payload: Dict[str, Any]):

    score = 50

    payout = payload["offered_payout"]
    minutes = payload["estimated_total_minutes"]

    hourly = payout / (minutes / 60)

    if hourly >= 25:
        score += 15
    elif hourly >= 18:
        score += 5
    else:
        score -= 10

    if payload["zone_pressure_score"] > 1.2:
        score += 5

    if payload["merchant_risk_score"] > 0.7:
        score -= 10

    action = "accept" if score >= 60 else "reject"

    return {

        "dispatch_score": score,
        "recommended_action": action,
        "effective_hourly": round(hourly, 2)
    }