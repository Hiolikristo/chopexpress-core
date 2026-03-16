from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, Optional

from ledger_engine import LedgerEngine, LedgerConfig, OrderPayoutInput
from backend.driver_ms_engine import DriverMSEngine, DriverMSConfig
from backend.insurance_support_engine import InsuranceSupportEngine, InsuranceSupportConfig


class SprintAOrchestrator:
    """
    Sprint A orchestration layer.

    Flow:
    1. process maintenance support
    2. process insurance support
    3. process final ledger split
    """

    def __init__(
        self,
        *,
        ledger_engine: Optional[LedgerEngine] = None,
        driver_ms_engine: Optional[DriverMSEngine] = None,
        insurance_support_engine: Optional[InsuranceSupportEngine] = None,
    ) -> None:
        self.ledger = ledger_engine or LedgerEngine(LedgerConfig())
        self.driver_ms = driver_ms_engine or DriverMSEngine(DriverMSConfig())
        self.insurance_support = insurance_support_engine or InsuranceSupportEngine(
            InsuranceSupportConfig()
        )

    def process_completed_order(
        self,
        *,
        driver_id: str,
        order_id: str,
        delivery_miles: Decimal,
        gross_payout: Decimal,
        base_pay: Decimal,
        tip_amount: Decimal,
        peak_pay: Decimal = Decimal("0.00"),
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        metadata = metadata or {}

        driver_ms_result = self.driver_ms.process_completed_order(
            driver_id=driver_id,
            order_id=order_id,
            delivery_miles=delivery_miles,
            gross_payout=gross_payout,
        )

        insurance_result = self.insurance_support.process_completed_order(
            driver_id=driver_id,
            order_id=order_id,
            gross_payout=gross_payout,
        )

        ledger_result = self.ledger.process_completed_order(
            OrderPayoutInput(
                driver_id=driver_id,
                order_id=order_id,
                delivery_miles=delivery_miles,
                gross_payout=gross_payout,
                base_pay=base_pay,
                tip_amount=tip_amount,
                peak_pay=peak_pay,
                metadata=metadata,
            )
        )

        return {
            "order_id": order_id,
            "driver_id": driver_id,
            "maintenance": driver_ms_result,
            "insurance_support": insurance_result,
            "ledger": ledger_result,
        }


if __name__ == "__main__":
    orchestrator = SprintAOrchestrator()

    result = orchestrator.process_completed_order(
        driver_id="driver_001",
        order_id="order_1001",
        delivery_miles=Decimal("6.6"),
        gross_payout=Decimal("8.75"),
        base_pay=Decimal("5.75"),
        tip_amount=Decimal("3.00"),
        peak_pay=Decimal("0.00"),
        metadata={"merchant": "Chick-fil-A", "zone": "clintonville"},
    )

    from pprint import pprint
    pprint(result)