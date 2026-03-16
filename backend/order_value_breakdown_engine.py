from typing import Dict, Any


def order_value_breakdown(payload: Dict[str, Any]):

    total = payload["order_value"]
    payout = payload["offered_payout"]

    company_margin = total - payout

    return {

        "order_value": total,
        "driver_payout": payout,
        "platform_margin": round(company_margin, 2)
    }