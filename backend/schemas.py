from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, EmailStr


# -------------------------
# Common / Health / Status
# -------------------------

class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: datetime


class StatusResponse(BaseModel):
    status: str
    service: str
    version: str
    environment: str
    timestamp: datetime


# -------------------------
# Simulator
# -------------------------

class SimulationRequest(BaseModel):
    city: str = "Columbus"
    total_orders: int = Field(default=1000, ge=1, le=100000)
    seed: int = 42


class NotificationRequest(BaseModel):
    recipients: List[EmailStr]
    subject: str
    text_content: str
    html_content: Optional[str] = None
    reply_to: Optional[EmailStr] = None


# -------------------------
# Merchant
# -------------------------

class MerchantCreate(BaseModel):
    merchant_name: str
    merchant_type: str
    contact_name: str
    email: EmailStr
    phone: str
    zone: str
    address: str
    prep_time_minutes: int = Field(default=15, ge=1, le=180)
    is_active: bool = True


class MerchantResponse(BaseModel):
    merchant_id: str
    merchant_name: str
    merchant_type: str
    contact_name: str
    email: EmailStr
    phone: str
    zone: str
    address: str
    prep_time_minutes: int
    is_active: bool
    created_at: datetime


class MenuItemCreate(BaseModel):
    merchant_id: str
    item_name: str
    category: str
    price: float = Field(..., gt=0)
    is_available: bool = True
    prep_time_minutes: int = Field(default=15, ge=1, le=180)


class MenuItemResponse(BaseModel):
    item_id: str
    merchant_id: str
    item_name: str
    category: str
    price: float
    is_available: bool
    prep_time_minutes: int
    created_at: datetime


# -------------------------
# Driver
# -------------------------

class DriverCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    zone: str
    vehicle_type: Literal["car", "bike", "scooter"]
    is_active: bool = True


class DriverResponse(BaseModel):
    driver_id: str
    full_name: str
    email: EmailStr
    phone: str
    zone: str
    vehicle_type: Literal["car", "bike", "scooter"]
    is_active: bool
    current_status: Literal["offline", "available", "busy"]
    total_completed_orders: int
    total_earnings: float
    created_at: datetime


class DriverAvailabilityUpdate(BaseModel):
    current_status: Literal["offline", "available", "busy"]


class DriverEarningsResponse(BaseModel):
    driver_id: str
    full_name: str
    total_completed_orders: int
    total_earnings: float
    avg_earnings_per_order: float
    current_status: str


# -------------------------
# Customer
# -------------------------

class CustomerCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    address: str
    zone: str
    apartment_dropoff: bool = False
    gated_dropoff: bool = False


class CustomerResponse(BaseModel):
    customer_id: str
    full_name: str
    email: EmailStr
    phone: str
    address: str
    zone: str
    apartment_dropoff: bool
    gated_dropoff: bool
    created_at: datetime


# -------------------------
# Orders
# -------------------------

class OrderItem(BaseModel):
    item_id: Optional[str] = None
    item_name: str
    quantity: int = Field(..., ge=1)
    unit_price: float = Field(..., gt=0)


class CustomerOrderCreate(BaseModel):
    customer_id: str
    merchant_id: str
    items: List[OrderItem]
    delivery_address: str
    zone: str
    apartment_dropoff: bool = False
    gated_dropoff: bool = False
    tip: float = Field(default=0, ge=0)
    notes: Optional[str] = None


class OrderResponse(BaseModel):
    order_id: str
    customer_id: str
    merchant_id: str
    driver_id: Optional[str]
    zone: str
    delivery_address: str
    apartment_dropoff: bool
    gated_dropoff: bool
    notes: Optional[str]
    items: List[OrderItem]
    subtotal: float
    tip: float
    customer_fee: float
    total_charged: float
    status: Literal[
        "created",
        "accepted",
        "assigned",
        "picked_up",
        "delivered",
        "cancelled",
    ]
    created_at: datetime
    updated_at: datetime


class DriverAcceptOrderRequest(BaseModel):
    driver_id: str


class OrderStatusUpdateRequest(BaseModel):
    status: Literal["accepted", "assigned", "picked_up", "delivered", "cancelled"]


# -------------------------
# Generic API wrapper
# -------------------------

class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None