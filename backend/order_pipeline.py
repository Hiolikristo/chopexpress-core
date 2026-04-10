from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from backend.delivery_verification_engine import delivery_verification_engine
from backend.schemas import (
    DriverAcceptOfferRequest,
    LifecycleStatus,
    OrderObservation,
    OrderResponse,
    OrderStatusUpdateRequest,
)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def compute_economic_miles(observation: OrderObservation) -> float:
    actual_trip_miles = _safe_float(observation.actual_trip_miles)
    return_miles_estimate = _safe_float(observation.return_miles_estimate)
    zone_exit_miles = _safe_float(observation.zone_exit_miles)
    return round(actual_trip_miles + return_miles_estimate + zone_exit_miles, 4)


def build_verification_payload(observation: OrderObservation) -> Dict[str, Any]:
    return {
        "merchant_category": observation.merchant_category,
        "proof_required": observation.proof_required,
        "receipt_photo_required": observation.receipt_photo_required,
        "dropoff_photo_required": observation.dropoff_photo_required,
        "drink_risk": observation.drink_risk,
        "merchant_delay_flag": observation.merchant_delay_flag,
        "app_error_flag": observation.app_error_flag,
    }


def normalize_observation(observation: OrderObservation) -> OrderObservation:
    if observation.economic_miles and observation.economic_miles > 0:
        return observation
    return observation.model_copy(
        update={"economic_miles": compute_economic_miles(observation)}
    )


def evaluate_observation(observation: OrderObservation) -> Dict[str, Any]:
    normalized = normalize_observation(observation)
    verification = delivery_verification_engine(
        build_verification_payload(normalized)
    )
    return {
        "observation": normalized,
        "verification": verification,
        "economic_miles": normalized.economic_miles,
    }


def create_order_response(
    order_id: str,
    status: LifecycleStatus = "accepted",
    created_at: Optional[datetime] = None,
    updated_at: Optional[datetime] = None,
) -> OrderResponse:
    now = datetime.utcnow()
    return OrderResponse(
        order_id=order_id,
        status=status,
        created_at=created_at or now,
        updated_at=updated_at or now,
    )


def accept_driver_offer(
    request: DriverAcceptOfferRequest,
    current_status: LifecycleStatus = "accepted",
) -> Dict[str, Any]:
    return {
        "driver_id": request.driver_id,
        "observation_id": request.observation_id,
        "status": current_status,
        "accepted_at": datetime.utcnow().isoformat(),
    }


def apply_status_update(
    order_id: str,
    created_at: datetime,
    request: OrderStatusUpdateRequest,
) -> OrderResponse:
    return OrderResponse(
        order_id=order_id,
        status=request.status,
        created_at=created_at,
        updated_at=datetime.utcnow(),
    )