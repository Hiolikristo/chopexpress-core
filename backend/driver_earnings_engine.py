from dataclasses import dataclass


@dataclass
class DriverEarningsResult:
    gross_pay: float
    fuel_cost: float
    maintenance_cost: float
    net_pay: float
    pay_per_mile: float
    net_per_mile: float
    hourly_gross: float
    hourly_net: float


def calculate_driver_earnings(
    gross_pay: float,
    total_miles: float,
    active_minutes: float,
    fuel_price_per_gallon: float = 3.45,
    vehicle_mpg: float = 24.0,
    maintenance_cost_per_mile: float = 0.14,
) -> DriverEarningsResult:
    safe_miles = max(0.01, total_miles)
    safe_hours = max(1.0 / 60.0, active_minutes / 60.0)

    fuel_cost = (safe_miles / max(1.0, vehicle_mpg)) * fuel_price_per_gallon
    maintenance_cost = safe_miles * maintenance_cost_per_mile
    net_pay = gross_pay - fuel_cost - maintenance_cost

    pay_per_mile = gross_pay / safe_miles
    net_per_mile = net_pay / safe_miles
    hourly_gross = gross_pay / safe_hours
    hourly_net = net_pay / safe_hours

    return DriverEarningsResult(
        gross_pay=round(gross_pay, 2),
        fuel_cost=round(fuel_cost, 2),
        maintenance_cost=round(maintenance_cost, 2),
        net_pay=round(net_pay, 2),
        pay_per_mile=round(pay_per_mile, 2),
        net_per_mile=round(net_per_mile, 2),
        hourly_gross=round(hourly_gross, 2),
        hourly_net=round(hourly_net, 2),
    )