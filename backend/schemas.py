from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, model_validator


PlatformName = Literal["doordash", "uber_eats", "grubhub", "shipt", "instacart", "unknown"]
MerchantCategory = Literal[
    "fast_food",
    "coffee",
    "grocery",
    "pharmacy",
    "retail",
    "restaurant",
    "convenience",
    "unknown",
]
OfferAction = Literal["accept", "borderline", "decline"]
LifecycleStatus = Literal["accepted", "assigned", "picked_up", "delivered", "cancelled"]


class ApiResponse(BaseModel):
    success: bool = True
    message: str = "ok"
    data: Optional[Dict[str, Any]] = None


class OrderObservation(BaseModel):
    """
    Canonical raw field evidence unit.
    This is the record you should use for real-world offer capture.
    """

    session_id: str
    observation_id: str

    platform: PlatformName = "unknown"
    zone: str = "unknown"

    merchant_name: str
    merchant_category: MerchantCategory = "unknown"

    # Offer economics shown by app
    offered_pay_total: float = 0.0
    base_pay: float = 0.0
    peak_pay: float = 0.0
    tip_shown: float = 0.0

    # Mileage
    offered_miles: float = 0.0
    actual_trip_miles: float = 0.0
    return_miles_estimate: float = 0.0
    zone_exit_miles: float = 0.0
    economic_miles: float = 0.0  # can be computed if left 0.0

    # Timing
    merchant_wait_minutes: float = 0.0
    idle_before_offer_minutes: float = 0.0
    delivery_minutes: float = 0.0

    # Order shape
    stack_count: int = 1
    accepted: bool = False
    declined: bool = False
    decline_reason: Optional[str] = None

    # Operational burdens
    proof_required: bool = False
    receipt_photo_required: bool = False
    dropoff_photo_required: bool = False
    drink_risk: bool = False
    merchant_delay_flag: bool = False
    app_error_flag: bool = False
    acceptance_rate_pressure_flag: bool = False

    # Zone / market signals
    hotspot_wait_estimate_minutes: float = 0.0
    busy_hotspot_zone: bool = False
    navigate_back_to_zone_flag: bool = False

    # Merchant friction feedback
    store_busy_long_line: bool = False
    order_not_started_until_arrival: bool = False
    order_still_being_prepared: bool = False
    could_not_get_help: bool = False
    drive_thru_busy_long_line: bool = False

    # Vehicle / gas state
    gas_state_start: Optional[float] = None
    gas_state_end: Optional[float] = None

    # Timestamps
    timestamp_offer_seen: Optional[datetime] = None
    timestamp_accept_decline: Optional[datetime] = None
    timestamp_arrive_store: Optional[datetime] = None
    timestamp_pickup_confirm: Optional[datetime] = None
    timestamp_dropoff_arrive: Optional[datetime] = None
    timestamp_complete: Optional[datetime] = None

    # Freeform evidence bucket
    notes: List[str] = Field(default_factory=list)
    raw_tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_accept_decline_state(self) -> "OrderObservation":
        if self.accepted and self.declined:
            raise ValueError("Observation cannot be both accepted and declined.")
        if not self.accepted and not self.declined:
            # allow for incomplete capture, but push to notes
            pass
        if self.stack_count < 1:
            raise ValueError("stack_count must be >= 1.")
        return self


class OfferScoreResult(BaseModel):
    observation_id: str
    session_id: str

    merchant_name: str
    platform: PlatformName
    zone: str

    score: float
    action: OfferAction

    pay_per_offered_mile: float
    pay_per_economic_mile: float
    effective_hourly_estimate: float

    economic_miles: float
    total_burden_minutes: float

    reasons: List[str] = Field(default_factory=list)
    reason_details: Dict[str, float] = Field(default_factory=dict)

    created_at: datetime = Field(default_factory=datetime.utcnow)


class ValidationResult(BaseModel):
    observation_id: str
    session_id: str

    recommended_action: OfferAction
    actual_driver_action: Literal["accepted", "declined", "unknown"]

    hindsight_label: Literal["good_accept", "bad_accept", "good_decline", "bad_decline", "unknown"]
    validation_score: float = 0.0

    realized_pay_per_economic_mile: float = 0.0
    realized_effective_hourly: float = 0.0

    notes: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SessionMetrics(BaseModel):
    session_id: str
    platform: PlatformName = "unknown"
    zone: str = "unknown"

    observation_count: int = 0
    accepted_count: int = 0
    declined_count: int = 0
    acceptance_rate: float = 0.0

    total_gross_pay: float = 0.0
    total_base_pay: float = 0.0
    total_peak_pay: float = 0.0
    total_tip_shown: float = 0.0

    total_offered_miles: float = 0.0
    total_actual_trip_miles: float = 0.0
    total_return_miles_estimate: float = 0.0
    total_zone_exit_miles: float = 0.0
    total_economic_miles: float = 0.0

    total_delivery_minutes: float = 0.0
    total_merchant_wait_minutes: float = 0.0
    total_idle_before_offer_minutes: float = 0.0
    total_burden_minutes: float = 0.0

    average_pay_per_offered_mile: float = 0.0
    average_pay_per_economic_mile: float = 0.0
    average_effective_hourly: float = 0.0

    merchant_delay_events: int = 0
    app_error_events: int = 0
    proof_burden_events: int = 0
    drink_risk_events: int = 0
    zone_exit_events: int = 0
    navigate_back_to_zone_events: int = 0
    hotspot_signal_events: int = 0

    score_distribution: Dict[str, int] = Field(default_factory=dict)
    action_distribution: Dict[str, int] = Field(default_factory=dict)

    notes: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class OrderResponse(BaseModel):
    order_id: str
    status: LifecycleStatus
    created_at: datetime
    updated_at: datetime


class DriverAcceptOfferRequest(BaseModel):
    driver_id: str
    observation_id: str


class OrderStatusUpdateRequest(BaseModel):
    status: LifecycleStatus