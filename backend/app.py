from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.persistence import load_state, next_id, save_state
from backend.schemas import (
    ApiResponse,
    CustomerCreate,
    CustomerOrderCreate,
    CustomerResponse,
    DriverAcceptOrderRequest,
    DriverAvailabilityUpdate,
    DriverCreate,
    DriverEarningsResponse,
    DriverResponse,
    HealthResponse,
    MenuItemCreate,
    MenuItemResponse,
    MerchantCreate,
    MerchantResponse,
    NotificationRequest,
    OrderResponse,
    OrderStatusUpdateRequest,
    SimulationRequest,
    StatusResponse,
)

try:
    from backend.notification_engine import NotificationEngine
except Exception:
    NotificationEngine = None

try:
    from backend.city_market_simulator_engine import CityMarketSimulatorEngine
except Exception:
    CityMarketSimulatorEngine = None


app = FastAPI(
    title="ChopExpress Backend",
    version="1.0.0",
    description="Fairness-first logistics backend for ChopExpress V1",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------
# Helpers
# -------------------------

def utc_now() -> datetime:
    return datetime.utcnow()


def compute_subtotal(items: List[Dict[str, Any]]) -> float:
    return round(sum(item["quantity"] * item["unit_price"] for item in items), 2)


def compute_customer_fee(subtotal: float, zone: str) -> float:
    zone_fee_map = {
        "north": 5.25,
        "south": 5.50,
        "east": 5.00,
        "west": 5.25,
        "downtown": 6.50,
        "campus": 4.99,
        "suburban": 6.25,
        "columbus": 5.50,
    }
    fee = zone_fee_map.get(zone.strip().lower(), 5.50)
    if subtotal >= 50:
        fee = max(3.99, fee - 1.50)
    return round(fee, 2)


def get_state() -> Dict[str, Any]:
    return load_state()


def persist_state(state: Dict[str, Any]) -> None:
    save_state(state)


def require_driver(state: Dict[str, Any], driver_id: str) -> Dict[str, Any]:
    driver = state["drivers"].get(driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail=f"Driver not found: {driver_id}")
    return driver


def require_customer(state: Dict[str, Any], customer_id: str) -> Dict[str, Any]:
    customer = state["customers"].get(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer not found: {customer_id}")
    return customer


def require_merchant(state: Dict[str, Any], merchant_id: str) -> Dict[str, Any]:
    merchant = state["merchants"].get(merchant_id)
    if not merchant:
        raise HTTPException(status_code=404, detail=f"Merchant not found: {merchant_id}")
    return merchant


def require_order(state: Dict[str, Any], order_id: str) -> Dict[str, Any]:
    order = state["orders"].get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail=f"Order not found: {order_id}")
    return order


# -------------------------
# Core endpoints
# -------------------------

@app.get("/", response_model=ApiResponse)
def root() -> ApiResponse:
    return ApiResponse(
        success=True,
        message="ChopExpress backend is running.",
        data={"service": "ChopExpress Backend", "version": "1.0.0"},
    )


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="ChopExpress Backend",
        timestamp=utc_now(),
    )


@app.get("/status", response_model=StatusResponse)
def status() -> StatusResponse:
    return StatusResponse(
        status="running",
        service="ChopExpress Backend",
        version="1.0.0",
        environment=os.getenv("ENVIRONMENT", "development"),
        timestamp=utc_now(),
    )


# -------------------------
# Merchant endpoints
# -------------------------

@app.post("/merchant/register", response_model=ApiResponse)
def register_merchant(payload: MerchantCreate) -> ApiResponse:
    state = get_state()

    merchant_id = next_id(state, "merchant", "MER")
    record = {
        "merchant_id": merchant_id,
        "merchant_name": payload.merchant_name,
        "merchant_type": payload.merchant_type,
        "contact_name": payload.contact_name,
        "email": str(payload.email),
        "phone": payload.phone,
        "zone": payload.zone,
        "address": payload.address,
        "prep_time_minutes": payload.prep_time_minutes,
        "is_active": payload.is_active,
        "created_at": utc_now().isoformat(),
    }

    state["merchants"][merchant_id] = record
    persist_state(state)

    return ApiResponse(
        success=True,
        message="Merchant registered successfully.",
        data=record,
    )


@app.get("/merchant/{merchant_id}", response_model=MerchantResponse)
def get_merchant(merchant_id: str) -> MerchantResponse:
    state = get_state()
    merchant = require_merchant(state, merchant_id)
    return MerchantResponse(**merchant)


@app.get("/merchant", response_model=List[MerchantResponse])
def list_merchants() -> List[MerchantResponse]:
    state = get_state()
    return [MerchantResponse(**m) for m in state["merchants"].values()]


@app.post("/merchant/menu", response_model=ApiResponse)
def create_menu_item(payload: MenuItemCreate) -> ApiResponse:
    state = get_state()
    require_merchant(state, payload.merchant_id)

    item_id = next_id(state, "menu_item", "ITEM")
    record = {
        "item_id": item_id,
        "merchant_id": payload.merchant_id,
        "item_name": payload.item_name,
        "category": payload.category,
        "price": payload.price,
        "is_available": payload.is_available,
        "prep_time_minutes": payload.prep_time_minutes,
        "created_at": utc_now().isoformat(),
    }

    state["menu_items"][item_id] = record
    persist_state(state)

    return ApiResponse(
        success=True,
        message="Menu item created successfully.",
        data=record,
    )


@app.get("/merchant/{merchant_id}/menu", response_model=List[MenuItemResponse])
def get_merchant_menu(merchant_id: str) -> List[MenuItemResponse]:
    state = get_state()
    require_merchant(state, merchant_id)

    items = [
        MenuItemResponse(**item)
        for item in state["menu_items"].values()
        if item["merchant_id"] == merchant_id
    ]
    return items


@app.get("/merchant/{merchant_id}/orders", response_model=List[OrderResponse])
def get_merchant_orders(merchant_id: str) -> List[OrderResponse]:
    state = get_state()
    require_merchant(state, merchant_id)

    orders = [
        OrderResponse(**order)
        for order in state["orders"].values()
        if order["merchant_id"] == merchant_id
    ]
    return orders


# -------------------------
# Driver endpoints
# -------------------------

@app.post("/driver/register", response_model=ApiResponse)
def register_driver(payload: DriverCreate) -> ApiResponse:
    state = get_state()

    driver_id = next_id(state, "driver", "DRV")
    record = {
        "driver_id": driver_id,
        "full_name": payload.full_name,
        "email": str(payload.email),
        "phone": payload.phone,
        "zone": payload.zone,
        "vehicle_type": payload.vehicle_type,
        "is_active": payload.is_active,
        "current_status": "offline",
        "total_completed_orders": 0,
        "total_earnings": 0.0,
        "created_at": utc_now().isoformat(),
    }

    state["drivers"][driver_id] = record
    persist_state(state)

    return ApiResponse(
        success=True,
        message="Driver registered successfully.",
        data=record,
    )


@app.get("/driver/{driver_id}", response_model=DriverResponse)
def get_driver(driver_id: str) -> DriverResponse:
    state = get_state()
    driver = require_driver(state, driver_id)
    return DriverResponse(**driver)


@app.get("/driver", response_model=List[DriverResponse])
def list_drivers() -> List[DriverResponse]:
    state = get_state()
    return [DriverResponse(**d) for d in state["drivers"].values()]


@app.patch("/driver/{driver_id}/availability", response_model=ApiResponse)
def update_driver_availability(driver_id: str, payload: DriverAvailabilityUpdate) -> ApiResponse:
    state = get_state()
    driver = require_driver(state, driver_id)

    driver["current_status"] = payload.current_status
    persist_state(state)

    return ApiResponse(
        success=True,
        message="Driver availability updated.",
        data=driver,
    )


@app.get("/driver/{driver_id}/jobs", response_model=List[OrderResponse])
def get_driver_jobs(driver_id: str) -> List[OrderResponse]:
    state = get_state()
    driver = require_driver(state, driver_id)

    jobs = [
        OrderResponse(**order)
        for order in state["orders"].values()
        if (
            order["zone"].strip().lower() == driver["zone"].strip().lower()
            and order["status"] in ["created", "accepted", "assigned"]
        )
    ]
    return jobs


@app.post("/driver/{driver_id}/accept/{order_id}", response_model=ApiResponse)
def driver_accept_order(driver_id: str, order_id: str, payload: Optional[DriverAcceptOrderRequest] = None) -> ApiResponse:
    state = get_state()
    driver = require_driver(state, driver_id)
    order = require_order(state, order_id)

    if order["status"] not in ["created", "accepted"]:
        raise HTTPException(status_code=400, detail="Order is not available for acceptance.")

    if driver["current_status"] not in ["available", "busy"]:
        raise HTTPException(status_code=400, detail="Driver must be available or busy-ready to accept orders.")

    order["driver_id"] = driver_id
    order["status"] = "assigned"
    order["updated_at"] = utc_now().isoformat()
    driver["current_status"] = "busy"

    persist_state(state)

    return ApiResponse(
        success=True,
        message="Order assigned to driver.",
        data={"driver": driver, "order": order},
    )


@app.get("/driver/{driver_id}/earnings", response_model=DriverEarningsResponse)
def get_driver_earnings(driver_id: str) -> DriverEarningsResponse:
    state = get_state()
    driver = require_driver(state, driver_id)

    total_completed = driver["total_completed_orders"]
    total_earnings = round(driver["total_earnings"], 2)
    avg = round(total_earnings / total_completed, 2) if total_completed else 0.0

    return DriverEarningsResponse(
        driver_id=driver["driver_id"],
        full_name=driver["full_name"],
        total_completed_orders=total_completed,
        total_earnings=total_earnings,
        avg_earnings_per_order=avg,
        current_status=driver["current_status"],
    )


# -------------------------
# Customer endpoints
# -------------------------

@app.post("/customer/register", response_model=ApiResponse)
def register_customer(payload: CustomerCreate) -> ApiResponse:
    state = get_state()

    customer_id = next_id(state, "customer", "CUS")
    record = {
        "customer_id": customer_id,
        "full_name": payload.full_name,
        "email": str(payload.email),
        "phone": payload.phone,
        "address": payload.address,
        "zone": payload.zone,
        "apartment_dropoff": payload.apartment_dropoff,
        "gated_dropoff": payload.gated_dropoff,
        "created_at": utc_now().isoformat(),
    }

    state["customers"][customer_id] = record
    persist_state(state)

    return ApiResponse(
        success=True,
        message="Customer registered successfully.",
        data=record,
    )


@app.get("/customer/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: str) -> CustomerResponse:
    state = get_state()
    customer = require_customer(state, customer_id)
    return CustomerResponse(**customer)


@app.get("/customer", response_model=List[CustomerResponse])
def list_customers() -> List[CustomerResponse]:
    state = get_state()
    return [CustomerResponse(**c) for c in state["customers"].values()]


@app.post("/customer/order", response_model=ApiResponse)
def create_customer_order(payload: CustomerOrderCreate) -> ApiResponse:
    state = get_state()
    require_customer(state, payload.customer_id)
    require_merchant(state, payload.merchant_id)

    order_id = next_id(state, "order", "ORD")

    item_dicts = [item.model_dump() for item in payload.items]
    subtotal = compute_subtotal(item_dicts)
    customer_fee = compute_customer_fee(subtotal, payload.zone)
    total_charged = round(subtotal + payload.tip + customer_fee, 2)

    record = {
        "order_id": order_id,
        "customer_id": payload.customer_id,
        "merchant_id": payload.merchant_id,
        "driver_id": None,
        "zone": payload.zone,
        "delivery_address": payload.delivery_address,
        "apartment_dropoff": payload.apartment_dropoff,
        "gated_dropoff": payload.gated_dropoff,
        "notes": payload.notes,
        "items": item_dicts,
        "subtotal": subtotal,
        "tip": payload.tip,
        "customer_fee": customer_fee,
        "total_charged": total_charged,
        "status": "created",
        "created_at": utc_now().isoformat(),
        "updated_at": utc_now().isoformat(),
    }

    state["orders"][order_id] = record
    persist_state(state)

    return ApiResponse(
        success=True,
        message="Customer order created successfully.",
        data=record,
    )


@app.get("/customer/{customer_id}/orders", response_model=List[OrderResponse])
def get_customer_orders(customer_id: str) -> List[OrderResponse]:
    state = get_state()
    require_customer(state, customer_id)

    orders = [
        OrderResponse(**order)
        for order in state["orders"].values()
        if order["customer_id"] == customer_id
    ]
    return orders


# -------------------------
# Order endpoints
# -------------------------

@app.get("/order/{order_id}", response_model=OrderResponse)
def get_order(order_id: str) -> OrderResponse:
    state = get_state()
    order = require_order(state, order_id)
    return OrderResponse(**order)


@app.patch("/order/{order_id}/status", response_model=ApiResponse)
def update_order_status(order_id: str, payload: OrderStatusUpdateRequest) -> ApiResponse:
    state = get_state()
    order = require_order(state, order_id)

    old_status = order["status"]
    order["status"] = payload.status
    order["updated_at"] = utc_now().isoformat()

    if payload.status == "delivered" and order.get("driver_id"):
        driver = require_driver(state, order["driver_id"])
        driver["current_status"] = "available"
        driver["total_completed_orders"] += 1

        driver_payout = round((order["customer_fee"] * 0.75) + order["tip"], 2)
        driver["total_earnings"] = round(driver["total_earnings"] + driver_payout, 2)

    persist_state(state)

    return ApiResponse(
        success=True,
        message=f"Order status updated from {old_status} to {payload.status}.",
        data=order,
    )


@app.get("/orders", response_model=List[OrderResponse])
def list_orders() -> List[OrderResponse]:
    state = get_state()
    return [OrderResponse(**o) for o in state["orders"].values()]


# -------------------------
# Notification endpoint
# -------------------------

@app.post("/notify", response_model=ApiResponse)
def notify(payload: NotificationRequest) -> ApiResponse:
    if NotificationEngine is None:
        return ApiResponse(
            success=False,
            message="Notification engine is not available yet.",
            data={"hint": "Check backend.notification_engine imports and email service wiring."},
        )

    try:
        engine = NotificationEngine()
        result = engine.send_email(
            recipients=[str(r) for r in payload.recipients],
            subject=payload.subject,
            text_content=payload.text_content,
            html_content=payload.html_content,
            reply_to=str(payload.reply_to) if payload.reply_to else None,
        )
        return ApiResponse(success=True, message="Notification processed.", data={"result": result})
    except Exception as exc:
        return ApiResponse(success=False, message=f"Notification failed: {exc}", data=None)


# -------------------------
# Simulation endpoints
# -------------------------

@app.post("/simulate/city-market", response_model=ApiResponse)
def simulate_city_market(payload: SimulationRequest) -> ApiResponse:
    if CityMarketSimulatorEngine is None:
        raise HTTPException(
            status_code=500,
            detail="CityMarketSimulatorEngine is not available. Check backend.city_market_simulator_engine imports."
        )

    try:
        engine = CityMarketSimulatorEngine(city_name=payload.city, seed=payload.seed)
        result = engine.run(total_orders=payload.total_orders)
        return ApiResponse(
            success=True,
            message="City market simulation completed.",
            data={"city": payload.city, "result": result},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {exc}")


@app.get("/simulate/columbus", response_model=ApiResponse)
def simulate_columbus(total_orders: int = 1000, seed: int = 42) -> ApiResponse:
    if CityMarketSimulatorEngine is None:
        raise HTTPException(
            status_code=500,
            detail="CityMarketSimulatorEngine is not available. Check backend.city_market_simulator_engine imports."
        )

    try:
        engine = CityMarketSimulatorEngine(city_name="Columbus", seed=seed)
        result = engine.run(total_orders=total_orders)
        return ApiResponse(
            success=True,
            message="Columbus simulation completed.",
            data={"city": "Columbus", "result": result},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Columbus simulation failed: {exc}")