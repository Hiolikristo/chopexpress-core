from __future__ import annotations

from datetime import datetime
from typing import Dict

from backend.order_pipeline import apply_status_update, create_order_response
from backend.schemas import (
    DriverAcceptOfferRequest,
    LifecycleStatus,
    OrderResponse,
    OrderStatusUpdateRequest,
)


class OrderLifecycleEngine:
    @staticmethod
    def create(order_id: str, initial_status: LifecycleStatus = "accepted") -> OrderResponse:
        return create_order_response(order_id=order_id, status=initial_status)

    @staticmethod
    def update_status(
        order_id: str,
        created_at: datetime,
        request: OrderStatusUpdateRequest,
    ) -> OrderResponse:
        return apply_status_update(
            order_id=order_id,
            created_at=created_at,
            request=request,
        )

    @staticmethod
    def driver_accept(request: DriverAcceptOfferRequest) -> Dict[str, str]:
        return {
            "driver_id": request.driver_id,
            "observation_id": request.observation_id,
            "status": "accepted",
        }


def create_order(order_id: str, initial_status: LifecycleStatus = "accepted") -> OrderResponse:
    return OrderLifecycleEngine.create(order_id=order_id, initial_status=initial_status)


def update_order_status(
    order_id: str,
    created_at: datetime,
    request: OrderStatusUpdateRequest,
) -> OrderResponse:
    return OrderLifecycleEngine.update_status(
        order_id=order_id,
        created_at=created_at,
        request=request,
    )


def accept_order_offer(request: DriverAcceptOfferRequest) -> Dict[str, str]:
    return OrderLifecycleEngine.driver_accept(request)