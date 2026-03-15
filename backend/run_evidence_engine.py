from typing import Dict, Any

def calculate_economic_miles(route: Dict[str, Any]) -> float:
    return (
        route["miles_to_pickup"] +
        route["miles_to_dropoff"] +
        route.get("return_miles", 0)
    )

def effective_pay_per_mile(pay: float, miles: float) -> float:
    if miles == 0:
        return 0
    return pay / miles

def effective_hourly(pay: float, minutes: float) -> float:
    if minutes == 0:
        return 0
    return pay / (minutes / 60)