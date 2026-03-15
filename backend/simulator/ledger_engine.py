from __future__ import annotations

from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional
import uuid


TWOPLACES = Decimal("0.01")


def q2(value: Decimal) -> Decimal:
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class LedgerConfig:
    tax_reserve_rate: Decimal = Decimal("0.15")
    insurance_reserve_rate: Decimal = Decimal("0.04")
    maintenance_per_mile: Decimal = Decimal("0.10")
    maintenance_min_rate: Decimal = Decimal("0.05")


@dataclass
class OrderPayoutInput:
    driver_id: str
    order_id: str
    delivery_miles: Decimal
    gross_payout: Decimal
    base_pay: Decimal
    tip_amount: Decimal = Decimal("0.00")
    peak_pay: Decimal = Decimal("0.00")
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LedgerEvent:
    event_id: str
    event_type: str
    driver_id: str
    amount: Decimal
    bucket: str
    reference_id: str
    order_id: str
    timestamp: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["amount"] = str(q2(self.amount))
        return payload


@dataclass
class LedgerAllocation:
    gross_payout: Decimal
    tax_reserve: Decimal
    maintenance_reserve: Decimal
    insurance_reserve: Decimal
    driver_available_now: Decimal

    def to_dict(self) -> Dict[str, str]:
        return {
            "gross_payout": str(q2(self.gross_payout)),
            "tax_reserve": str(q2(self.tax_reserve)),
            "maintenance_reserve": str(q2(self.maintenance_reserve)),
            "insurance_reserve": str(q2(self.insurance_reserve)),
            "driver_available_now": str(q2(self.driver_available_now)),
        }


class LedgerEngine:
    """
    LedgerPay backend engine.

    Responsibilities:
    - split completed order payout into protected reserve buckets
    - create immutable event records
    - expose driver wallet balances
    """

    def __init__(self, config: Optional[LedgerConfig] = None) -> None:
        self.config = config or LedgerConfig()
        self.events: List[LedgerEvent] = []
        self.driver_wallets: Dict[str, Dict[str, Decimal]] = {}

    def _ensure_driver_wallet(self, driver_id: str) -> None:
        if driver_id not in self.driver_wallets:
            self.driver_wallets[driver_id] = {
                "available": Decimal("0.00"),
                "tax_reserve": Decimal("0.00"),
                "maintenance_reserve": Decimal("0.00"),
                "insurance_reserve": Decimal("0.00"),
                "gross_lifetime": Decimal("0.00"),
            }

    def _new_event(
        self,
        *,
        event_type: str,
        driver_id: str,
        amount: Decimal,
        bucket: str,
        reference_id: str,
        order_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> LedgerEvent:
        return LedgerEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            driver_id=driver_id,
            amount=q2(amount),
            bucket=bucket,
            reference_id=reference_id,
            order_id=order_id,
            timestamp=now_iso(),
            metadata=metadata or {},
        )

    def calculate_allocation(self, order_input: OrderPayoutInput) -> LedgerAllocation:
        gross = q2(order_input.gross_payout)

        tax_reserve = q2(gross * self.config.tax_reserve_rate)
        insurance_reserve = q2(gross * self.config.insurance_reserve_rate)

        maintenance_by_mile = q2(order_input.delivery_miles * self.config.maintenance_per_mile)
        maintenance_by_rate = q2(gross * self.config.maintenance_min_rate)
        maintenance_reserve = max(maintenance_by_mile, maintenance_by_rate)

        protected_total = q2(tax_reserve + insurance_reserve + maintenance_reserve)
        driver_available_now = q2(gross - protected_total)

        if driver_available_now < Decimal("0.00"):
            driver_available_now = Decimal("0.00")

        return LedgerAllocation(
            gross_payout=gross,
            tax_reserve=tax_reserve,
            maintenance_reserve=maintenance_reserve,
            insurance_reserve=insurance_reserve,
            driver_available_now=driver_available_now,
        )

    def process_completed_order(self, order_input: OrderPayoutInput) -> Dict[str, Any]:
        self._ensure_driver_wallet(order_input.driver_id)

        allocation = self.calculate_allocation(order_input)
        common_meta = {
            "merchant": order_input.metadata.get("merchant"),
            "zone": order_input.metadata.get("zone"),
            "delivery_miles": str(q2(order_input.delivery_miles)),
            "base_pay": str(q2(order_input.base_pay)),
            "tip_amount": str(q2(order_input.tip_amount)),
            "peak_pay": str(q2(order_input.peak_pay)),
            "gross_payout": str(q2(order_input.gross_payout)),
        }

        gross_event = self._new_event(
            event_type="ORDER_COMPLETED",
            driver_id=order_input.driver_id,
            amount=allocation.gross_payout,
            bucket="gross",
            reference_id=order_input.order_id,
            order_id=order_input.order_id,
            metadata=common_meta,
        )
        tax_event = self._new_event(
            event_type="TAX_RESERVE_HOLD",
            driver_id=order_input.driver_id,
            amount=allocation.tax_reserve,
            bucket="tax_reserve",
            reference_id=order_input.order_id,
            order_id=order_input.order_id,
            metadata=common_meta,
        )
        maintenance_event = self._new_event(
            event_type="MAINTENANCE_RESERVE_HOLD",
            driver_id=order_input.driver_id,
            amount=allocation.maintenance_reserve,
            bucket="maintenance_reserve",
            reference_id=order_input.order_id,
            order_id=order_input.order_id,
            metadata=common_meta,
        )
        insurance_event = self._new_event(
            event_type="INSURANCE_RESERVE_HOLD",
            driver_id=order_input.driver_id,
            amount=allocation.insurance_reserve,
            bucket="insurance_reserve",
            reference_id=order_input.order_id,
            order_id=order_input.order_id,
            metadata=common_meta,
        )
        available_event = self._new_event(
            event_type="DRIVER_AVAILABLE_CREDIT",
            driver_id=order_input.driver_id,
            amount=allocation.driver_available_now,
            bucket="available",
            reference_id=order_input.order_id,
            order_id=order_input.order_id,
            metadata=common_meta,
        )

        for event in [gross_event, tax_event, maintenance_event, insurance_event, available_event]:
            self.events.append(event)

        wallet = self.driver_wallets[order_input.driver_id]
        wallet["gross_lifetime"] = q2(wallet["gross_lifetime"] + allocation.gross_payout)
        wallet["tax_reserve"] = q2(wallet["tax_reserve"] + allocation.tax_reserve)
        wallet["maintenance_reserve"] = q2(wallet["maintenance_reserve"] + allocation.maintenance_reserve)
        wallet["insurance_reserve"] = q2(wallet["insurance_reserve"] + allocation.insurance_reserve)
        wallet["available"] = q2(wallet["available"] + allocation.driver_available_now)

        return {
            "driver_id": order_input.driver_id,
            "order_id": order_input.order_id,
            "allocation": allocation.to_dict(),
            "wallet_snapshot": self.get_driver_wallet(order_input.driver_id),
            "events": [
                gross_event.to_dict(),
                tax_event.to_dict(),
                maintenance_event.to_dict(),
                insurance_event.to_dict(),
                available_event.to_dict(),
            ],
        }

    def get_driver_wallet(self, driver_id: str) -> Dict[str, str]:
        self._ensure_driver_wallet(driver_id)
        wallet = self.driver_wallets[driver_id]
        return {key: str(q2(value)) for key, value in wallet.items()}

    def get_events_for_driver(self, driver_id: str) -> List[Dict[str, Any]]:
        return [event.to_dict() for event in self.events if event.driver_id == driver_id]