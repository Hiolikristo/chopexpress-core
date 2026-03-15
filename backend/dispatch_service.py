from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.dispatch_engine import assign_best_driver
from backend.notification_engine import NotificationEngine


@dataclass
class DispatchDecision:
    selected_driver_id: str
    estimated_pickup_minutes: int
    compatibility_score: float
    reason: str


@dataclass
class DispatchEvent:
    event_type: str
    state: str
    timestamp: str
    actor: str
    notes: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)


class DispatchService:
    def __init__(
        self,
        notification_engine: Optional[NotificationEngine] = None,
    ) -> None:
        self.notification_engine = notification_engine
        self.events: List[DispatchEvent] = []
        self.orders: Dict[str, Dict[str, Any]] = {}
        self.drivers: Dict[str, Dict[str, Any]] = {}

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _record_event(
        self,
        event_type: str,
        state: str,
        actor: str,
        notes: str = "",
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.events.append(
            DispatchEvent(
                event_type=event_type,
                state=state,
                timestamp=self._now(),
                actor=actor,
                notes=notes,
                payload=payload or {},
            )
        )

    def add_driver(self, driver: Dict[str, Any]) -> None:
        if "id" not in driver:
            raise ValueError("Driver requires an 'id'.")
        self.drivers[driver["id"]] = dict(driver)

    def add_drivers(self, drivers: List[Dict[str, Any]]) -> None:
        for driver in drivers:
            self.add_driver(driver)

    def get_driver(self, driver_id: str) -> Optional[Dict[str, Any]]:
        return self.drivers.get(driver_id)

    def list_drivers(self) -> List[Dict[str, Any]]:
        return list(self.drivers.values())

    def create_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        if "id" not in order:
            raise ValueError("Order requires an 'id'.")

        order_copy = dict(order)
        order_copy.setdefault("state", "created")
        order_copy.setdefault("created_at", self._now())
        order_copy.setdefault("assigned_driver_id", None)
        order_copy.setdefault("offer_amount", None)

        self.orders[order_copy["id"]] = order_copy

        self._record_event(
            event_type="order_created",
            state=order_copy["state"],
            actor="system",
            payload={
                "order_id": order_copy["id"],
                "merchant_name": order_copy.get("merchant_name"),
                "zone": order_copy.get("zone"),
            },
        )
        return order_copy

    def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        return self.orders.get(order_id)

    def list_orders(self) -> List[Dict[str, Any]]:
        return list(self.orders.values())

    def update_order_state(
        self,
        order_id: str,
        state: str,
        actor: str = "system",
        notes: str = "",
        extra_payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if order_id not in self.orders:
            raise ValueError(f"Order '{order_id}' not found.")

        self.orders[order_id]["state"] = state
        self.orders[order_id]["updated_at"] = self._now()

        self._record_event(
            event_type="order_state_changed",
            state=state,
            actor=actor,
            notes=notes,
            payload={
                "order_id": order_id,
                **(extra_payload or {}),
            },
        )
        return self.orders[order_id]

    def dispatch_order(
        self,
        order_payload: Dict[str, Any],
        drivers_payload: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        decision = assign_best_driver(order_payload, drivers_payload)

        assigned_driver_id = decision.get("assigned_driver_id")
        offer_amount = decision.get("offer_amount")

        order_id = order_payload.get("id") or order_payload.get("order_id")
        if order_id and order_id in self.orders:
            self.orders[order_id]["assigned_driver_id"] = assigned_driver_id
            self.orders[order_id]["offer_amount"] = offer_amount
            self.orders[order_id]["dispatch_decision"] = decision
            self.orders[order_id]["state"] = "assigned" if assigned_driver_id else "unassigned"
            self.orders[order_id]["updated_at"] = self._now()

        self._record_event(
            event_type="order_dispatched",
            state="assigned" if assigned_driver_id else "unassigned",
            actor="dispatch_engine",
            payload={
                "order_id": order_id,
                "assigned_driver_id": assigned_driver_id,
                "offer_amount": offer_amount,
                "decision": decision,
            },
        )

        return decision

    def create_and_dispatch_order(
        self,
        order_payload: Dict[str, Any],
        drivers_payload: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        created_order = self.create_order(order_payload)
        available_drivers = drivers_payload if drivers_payload is not None else self.list_drivers()
        decision = self.dispatch_order(created_order, available_drivers)

        return {
            "order": self.get_order(created_order["id"]),
            "decision": decision,
        }

    def get_events(self) -> List[Dict[str, Any]]:
        return [event.__dict__ for event in self.events]

    def clear_all(self) -> None:
        self.orders.clear()
        self.drivers.clear()
        self.events.clear()