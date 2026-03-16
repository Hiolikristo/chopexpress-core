from typing import Any, Dict

from fastapi import FastAPI
from pydantic import BaseModel, Field

from backend.order_pipeline import EngineContractError, evaluate_order_pipeline

app = FastAPI(title="ChopExpress Core API")


class OrderRequest(BaseModel):
    order_id: str = Field(..., description="Unique order identifier")
    merchant: str = Field(..., description="Merchant name")
    zone: str = Field(..., description="Delivery zone")
    tier: str = Field(..., description="Driver tier")

    delivery_distance: float = Field(..., description="Delivery miles")
    pickup_distance: float = Field(..., description="Pickup miles")
    return_distance: float = Field(..., description="Estimated return miles")
    order_value: float = Field(..., description="Customer basket total")
    offered_payout: float = Field(..., description="Driver offered payout")
    tip: float = Field(0.0, description="Tip amount")

    estimated_total_minutes: float = Field(24.0, description="Estimated trip time")
    merchant_risk_score: float = Field(0.3, description="Merchant friction score")
    zone_pressure_score: float = Field(1.0, description="Zone demand pressure")
    is_batched_order: bool = Field(False, description="Whether order is batched")

    sales_tax_rate: float = Field(0.075, description="Merchant sales tax rate")
    commission_rate: float = Field(0.18, description="Platform commission rate")
    processing_rate: float = Field(0.03, description="Card processing percentage")
    fixed_processing_fee: float = Field(0.30, description="Fixed payment fee")
    promo_support: float = Field(0.0, description="Platform promo contribution")
    merchant_id: str = Field("M-001", description="Merchant ID")

    customer_month_orders: int = Field(0, description="Customer monthly order count")
    customer_points: int = Field(0, description="Customer loyalty points")


@app.get("/")
def root() -> Dict[str, str]:
    return {"message": "ChopExpress Core API running"}


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/evaluate-order")
def evaluate_order(order: OrderRequest) -> Dict[str, Any]:
    payload = order.model_dump()

    try:
        return evaluate_order_pipeline(payload)
    except EngineContractError as exc:
        return {
            "status": "engine_contract_error",
            "message": str(exc),
        }
    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc),
        }