from backend.persistence import list_drivers, update_driver_activation
from datetime import datetime

def determine_driver_tier(miles: float) -> str:
    if miles >= 4000:
        return "Elite"
    elif miles >= 2500:
        return "Pro+"
    elif miles >= 1000:
        return "Professional"
    else:
        return "Casual"


def update_driver_metrics(driver, miles, deliveries, base_pay, tips):
    driver.rolling_30_day_miles += miles
    driver.completed_deliveries += deliveries
    driver.total_base_pay += base_pay
    driver.total_tips += tips

    driver.tier = determine_driver_tier(driver.rolling_30_day_miles)

    driver.last_active = datetime.utcnow().isoformat()

    return driver