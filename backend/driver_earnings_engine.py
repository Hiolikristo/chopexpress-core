from typing import List, Dict


def calculate_hourly_income(orders: List[Dict], hours: float) -> float:
    """
    Calculate total driver earnings per hour from simulated orders.
    """

    total_pay = 0

    for order in orders:
        dispatch = order.get("dispatch", {})
        pay = dispatch.get("pay_per_economic_mile", 0)
        miles = dispatch.get("economic_miles", 0)

        total_pay += pay * miles

    if hours == 0:
        return 0

    return total_pay / hours


def driver_shift_summary(orders: List[Dict], hours: float) -> Dict:

    hourly_income = calculate_hourly_income(orders, hours)

    if hourly_income >= 25:
        satisfaction = 0.9
    elif hourly_income >= 20:
        satisfaction = 0.75
    elif hourly_income >= 15:
        satisfaction = 0.55
    else:
        satisfaction = 0.35

    return {
        "orders_completed": len(orders),
        "hours_worked": hours,
        "hourly_income": round(hourly_income, 2),
        "satisfaction": satisfaction
    }