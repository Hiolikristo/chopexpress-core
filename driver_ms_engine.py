from __future__ import annotations

from dataclasses import dataclass, asdict
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, Optional


TWOPLACES = Decimal("0.01")


def q2(value: Decimal) -> Decimal:
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


@dataclass
class DriverMSConfig:
    maintenance_per_mile: Decimal = Decimal("0.10")
    maintenance_min_rate: Decimal = Decimal("0.05")
    caution_threshold: Decimal = Decimal("50.00")
    risk_threshold: Decimal = Decimal("20.00")


@dataclass
class DriverMSResult:
    order_id: str
    driver_id: str
    delivery_miles: Decimal
    maintenance_by_mile: Decimal
    maintenance_by_rate: Decimal
    mandatory_hold: Decimal
    reserve_balance_after: Decimal
    reserve_status: str

    def to_dict(self) -> Dict[str, str]:
        payload = asdict(self)
        for key, value in payload.items():
            if isinstance(value, Decimal):
                payload[key] = str(q2(value))
        return payload


class DriverMSEngine:
    """
    Driver Maintenance Support engine.

    Mandatory across the platform.
    Protects the driver from underfunded vehicle wear.
    """

    def __init__(self, config: Optional[DriverMSConfig] = None) -> None:
        self.config = config or DriverMSConfig()
        self.driver_maintenance_balances: Dict[str, Decimal] = {}

    def _ensure_driver(self, driver_id: str) -> None:
        if driver_id not in self.driver_maintenance_balances:
            self.driver_maintenance_balances[driver_id] = Decimal("0.00")

    def calculate_mandatory_hold(self, delivery_miles: Decimal, gross_payout: Decimal) -> Decimal:
        maintenance_by_mile = q2(delivery_miles * self.config.maintenance_per_mile)
        maintenance_by_rate = q2(gross_payout * self.config.maintenance_min_rate)
        return max(maintenance_by_mile, maintenance_by_rate)

    def determine_status(self, reserve_balance: Decimal) -> str:
        if reserve_balance <= self.config.risk_threshold:
            return "risk"
        if reserve_balance <= self.config.caution_threshold:
            return "caution"
        return "healthy"

    def process_completed_order(
        self,
        *,
        driver_id: str,
        order_id: str,
        delivery_miles: Decimal,
        gross_payout: Decimal,
    ) -> Dict[str, Any]:
        self._ensure_driver(driver_id)

        maintenance_by_mile = q2(delivery_miles * self.config.maintenance_per_mile)
        maintenance_by_rate = q2(gross_payout * self.config.maintenance_min_rate)
        mandatory_hold = max(maintenance_by_mile, maintenance_by_rate)

        self.driver_maintenance_balances[driver_id] = q2(
            self.driver_maintenance_balances[driver_id] + mandatory_hold
        )

        reserve_balance_after = self.driver_maintenance_balances[driver_id]
        reserve_status = self.determine_status(reserve_balance_after)

        result = DriverMSResult(
            order_id=order_id,
            driver_id=driver_id,
            delivery_miles=q2(delivery_miles),
            maintenance_by_mile=maintenance_by_mile,
            maintenance_by_rate=maintenance_by_rate,
            mandatory_hold=mandatory_hold,
            reserve_balance_after=reserve_balance_after,
            reserve_status=reserve_status,
        )
        return result.to_dict()

    def get_balance(self, driver_id: str) -> str:
        self._ensure_driver(driver_id)
        return str(q2(self.driver_maintenance_balances[driver_id]))