from __future__ import annotations

from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


# ============================================================
# Helpers
# ============================================================

def _utcnow() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _safe_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip()


# ============================================================
# Order States
# ============================================================

class OrderState(str, Enum):
    CREATED = "created"
    DISPATCHING = "dispatching"
    DRIVER_ASSIGNED = "driver_assigned"
    DRIVER_EN_ROUTE = "driver_en_route"
    ARRIVED_PICKUP = "arrived_pickup"
    PICKED_UP = "picked_up"
    EN_ROUTE_DROP = "en_route_drop"
    ARRIVED_DROP = "arrived_drop"
    DELIVERED = "delivered"
    VERIFIED = "verified"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


VALID_TRANSITIONS = {
    OrderState.CREATED: {
        OrderState.DISPATCHING,
        OrderState.CANCELLED,
        OrderState.FAILED,
    },
    OrderState.DISPATCHING: {
        OrderState.DRIVER_ASSIGNED,
        OrderState.CANCELLED,
        OrderState.FAILED,
    },
    OrderState.DRIVER_ASSIGNED: {
        OrderState.DRIVER_EN_ROUTE,
        OrderState.CANCELLED,
        OrderState.FAILED,
    },
    OrderState.DRIVER_EN_ROUTE: {
        OrderState.ARRIVED_PICKUP,
        OrderState.CANCELLED,
        OrderState.FAILED,
    },
    OrderState.ARRIVED_PICKUP: {
        OrderState.PICKED_UP,
        OrderState.CANCELLED,
        OrderState.FAILED,
    },
    OrderState.PICKED_UP: {
        OrderState.EN_ROUTE_DROP,
        OrderState.CANCELLED,
        OrderState.FAILED,
    },
    OrderState.EN_ROUTE_DROP: {
        OrderState.ARRIVED_DROP,
        OrderState.CANCELLED,
        OrderState.FAILED,
    },
    OrderState.ARRIVED_DROP: {
        OrderState.DELIVERED,
        OrderState.CANCELLED,
        OrderState.FAILED,
    },
    OrderState.DELIVERED: {
        OrderState.VERIFIED,
        OrderState.FAILED,
    },
    OrderState.VERIFIED: {
        OrderState.COMPLETED,
        OrderState.FAILED,
    },
    OrderState.COMPLETED: set(),
    OrderState.CANCELLED: set(),
    OrderState.FAILED: set(),
}


# ============================================================
# Data Models
# ============================================================

@dataclass
class OrderEvent:
    event_type: str
    state: str
    timestamp: str
    actor: str = ""
    notes: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OrderRecord:
    order_id: str
    customer_id: str
    merchant_id: str
    current_state: str

    created_at: str
    updated_at: str

    driver_id: Optional[str] = None
    zone_id: str = ""
    pickup_zone: str = ""
    dropoff_zone: str = ""

    offer_pay: float = 0.0
    miles: float = 0.0
    economic_miles: float = 0.0

    verification_status: str = ""
    cancellation_reason: str = ""
    failure_reason: str = ""

    events: List[OrderEvent] = field(default_factory=list)


# ============================================================
# Engine
# ============================================================

class OrderLifecycleEngine:
    """
    ChopExpress V1 order lifecycle state machine.

    Responsibilities:
    - create and track orders
    - validate transitions
    - assign drivers
    - record pickup / drop / verification events
    - produce audit-ready event logs
    """

    def __init__(self) -> None:
        self.orders: Dict[str, OrderRecord] = {}

    # --------------------------------------------------------
    # Core CRUD
    # --------------------------------------------------------

    def create_order(
        self,
        order_id: str,
        customer_id: str,
        merchant_id: str,
        zone_id: str = "",
        pickup_zone: str = "",
        dropoff_zone: str = "",
        offer_pay: float = 0.0,
        miles: float = 0.0,
        economic_miles: float = 0.0,
        notes: str = "",
    ) -> OrderRecord:
        if order_id in self.orders:
            raise ValueError(f"Order already exists: {order_id}")

        now = _utcnow()

        record = OrderRecord(
            order_id=order_id,
            customer_id=customer_id,
            merchant_id=merchant_id,
            current_state=OrderState.CREATED.value,
            created_at=now,
            updated_at=now,
            zone_id=zone_id,
            pickup_zone=pickup_zone,
            dropoff_zone=dropoff_zone,
            offer_pay=float(offer_pay),
            miles=float(miles),
            economic_miles=float(economic_miles),
        )

        record.events.append(
            OrderEvent(
                event_type="order_created",
                state=OrderState.CREATED.value,
                timestamp=now,
                actor="system",
                notes=notes,
            )
        )

        self.orders[order_id] = record
        return record

    def get_order(self, order_id: str) -> OrderRecord:
        if order_id not in self.orders:
            raise KeyError(f"Unknown order_id: {order_id}")
        return self.orders[order_id]

    def list_orders(self) -> List[OrderRecord]:
        return list(self.orders.values())

    # --------------------------------------------------------
    # Transition handling
    # --------------------------------------------------------

    def _transition(
        self,
        order_id: str,
        new_state: OrderState,
        actor: str = "system",
        event_type: Optional[str] = None,
        notes: str = "",
        payload: Optional[Dict[str, Any]] = None,
    ) -> OrderRecord:
        record = self.get_order(order_id)
        current_state = OrderState(record.current_state)

        allowed = VALID_TRANSITIONS[current_state]
        if new_state not in allowed:
            raise ValueError(
                f"Invalid transition for {order_id}: {current_state.value} -> {new_state.value}"
            )

        now = _utcnow()
        record.current_state = new_state.value
        record.updated_at = now

        record.events.append(
            OrderEvent(
                event_type=event_type or f"state_{new_state.value}",
                state=new_state.value,
                timestamp=now,
                actor=actor,
                notes=notes,
                payload=payload or {},
            )
        )

        return record

    # --------------------------------------------------------
    # Lifecycle methods
    # --------------------------------------------------------

    def begin_dispatch(
        self,
        order_id: str,
        actor: str = "dispatch_engine",
        notes: str = "",
    ) -> OrderRecord:
        return self._transition(
            order_id=order_id,
            new_state=OrderState.DISPATCHING,
            actor=actor,
            event_type="dispatch_started",
            notes=notes,
        )

    def assign_driver(
        self,
        order_id: str,
        driver_id: str,
        actor: str = "dispatch_engine",
        notes: str = "",
        payload: Optional[Dict[str, Any]] = None,
    ) -> OrderRecord:
        record = self._transition(
            order_id=order_id,
            new_state=OrderState.DRIVER_ASSIGNED,
            actor=actor,
            event_type="driver_assigned",
            notes=notes,
            payload=payload,
        )
        record.driver_id = driver_id
        return record

    def driver_en_route(
        self,
        order_id: str,
        actor: str = "driver_app",
        notes: str = "",
    ) -> OrderRecord:
        return self._transition(
            order_id=order_id,
            new_state=OrderState.DRIVER_EN_ROUTE,
            actor=actor,
            event_type="driver_en_route",
            notes=notes,
        )

    def arrived_pickup(
        self,
        order_id: str,
        actor: str = "driver_app",
        notes: str = "",
    ) -> OrderRecord:
        return self._transition(
            order_id=order_id,
            new_state=OrderState.ARRIVED_PICKUP,
            actor=actor,
            event_type="arrived_pickup",
            notes=notes,
        )

    def pickup_confirmed(
        self,
        order_id: str,
        actor: str = "driver_app",
        notes: str = "",
        payload: Optional[Dict[str, Any]] = None,
    ) -> OrderRecord:
        return self._transition(
            order_id=order_id,
            new_state=OrderState.PICKED_UP,
            actor=actor,
            event_type="pickup_confirmed",
            notes=notes,
            payload=payload,
        )

    def en_route_drop(
        self,
        order_id: str,
        actor: str = "driver_app",
        notes: str = "",
    ) -> OrderRecord:
        return self._transition(
            order_id=order_id,
            new_state=OrderState.EN_ROUTE_DROP,
            actor=actor,
            event_type="driver_heading_to_dropoff",
            notes=notes,
        )

    def arrived_drop(
        self,
        order_id: str,
        actor: str = "driver_app",
        notes: str = "",
    ) -> OrderRecord:
        return self._transition(
            order_id=order_id,
            new_state=OrderState.ARRIVED_DROP,
            actor=actor,
            event_type="arrived_dropoff",
            notes=notes,
        )

    def delivered(
        self,
        order_id: str,
        actor: str = "driver_app",
        notes: str = "",
        payload: Optional[Dict[str, Any]] = None,
    ) -> OrderRecord:
        return self._transition(
            order_id=order_id,
            new_state=OrderState.DELIVERED,
            actor=actor,
            event_type="delivery_marked_complete",
            notes=notes,
            payload=payload,
        )

    def verified(
        self,
        order_id: str,
        verification_status: str = "verified",
        actor: str = "delivery_verification_engine",
        notes: str = "",
        payload: Optional[Dict[str, Any]] = None,
    ) -> OrderRecord:
        record = self._transition(
            order_id=order_id,
            new_state=OrderState.VERIFIED,
            actor=actor,
            event_type="delivery_verified",
            notes=notes,
            payload=payload,
        )
        record.verification_status = verification_status
        return record

    def complete(
        self,
        order_id: str,
        actor: str = "system",
        notes: str = "",
    ) -> OrderRecord:
        return self._transition(
            order_id=order_id,
            new_state=OrderState.COMPLETED,
            actor=actor,
            event_type="order_completed",
            notes=notes,
        )

    def cancel(
        self,
        order_id: str,
        reason: str,
        actor: str = "system",
        notes: str = "",
        payload: Optional[Dict[str, Any]] = None,
    ) -> OrderRecord:
        record = self.get_order(order_id)
        current_state = OrderState(record.current_state)

        if OrderState.CANCELLED in VALID_TRANSITIONS[current_state]:
            now = _utcnow()
            record.current_state = OrderState.CANCELLED.value
            record.updated_at = now
            record.cancellation_reason = reason
            record.events.append(
                OrderEvent(
                    event_type="order_cancelled",
                    state=OrderState.CANCELLED.value,
                    timestamp=now,
                    actor=actor,
                    notes=notes,
                    payload=payload or {"reason": reason},
                )
            )
            return record

        raise ValueError(f"Cannot cancel order in state: {record.current_state}")

    def fail(
        self,
        order_id: str,
        reason: str,
        actor: str = "system",
        notes: str = "",
        payload: Optional[Dict[str, Any]] = None,
    ) -> OrderRecord:
        record = self.get_order(order_id)
        current_state = OrderState(record.current_state)

        if OrderState.FAILED in VALID_TRANSITIONS[current_state]:
            now = _utcnow()
            record.current_state = OrderState.FAILED.value
            record.updated_at = now
            record.failure_reason = reason
            record.events.append(
                OrderEvent(
                    event_type="order_failed",
                    state=OrderState.FAILED.value,
                    timestamp=now,
                    actor=actor,
                    notes=notes,
                    payload=payload or {"reason": reason},
                )
            )
            return record

        raise ValueError(f"Cannot fail order in state: {record.current_state}")

    # --------------------------------------------------------
    # Reporting
    # --------------------------------------------------------

    def to_dict(self, order_id: str) -> Dict[str, Any]:
        record = self.get_order(order_id)
        payload = asdict(record)
        return payload

    def summary(self) -> Dict[str, Any]:
        counts: Dict[str, int] = {}
        for record in self.orders.values():
            counts[record.current_state] = counts.get(record.current_state, 0) + 1

        return {
            "total_orders": len(self.orders),
            "state_counts": counts,
        }


# ============================================================
# Demo / standalone test
# ============================================================

def main() -> Dict[str, Any]:
    engine = OrderLifecycleEngine()

    order = engine.create_order(
        order_id="ORD-1001",
        customer_id="CUS-001",
        merchant_id="MER-001",
        zone_id="MORSE",
        pickup_zone="MORSE",
        dropoff_zone="CLINTONVILLE",
        offer_pay=8.75,
        miles=2.4,
        economic_miles=3.1,
        notes="demo order created",
    )

    engine.begin_dispatch(order.order_id)
    engine.assign_driver(order.order_id, driver_id="DRV-002", notes="best-ranked driver")
    engine.driver_en_route(order.order_id)
    engine.arrived_pickup(order.order_id)
    engine.pickup_confirmed(order.order_id, payload={"merchant_confirmed": True})
    engine.en_route_drop(order.order_id)
    engine.arrived_drop(order.order_id)
    engine.delivered(order.order_id, payload={"drop_method": "photo"})
    engine.verified(order.order_id, payload={"verification_score": 88})
    engine.complete(order.order_id)

    return {
        "order": engine.to_dict("ORD-1001"),
        "summary": engine.summary(),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(main(), indent=2))