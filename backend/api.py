from __future__ import annotations

from typing import Any, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.order_pipeline import EngineContractError, evaluate_order_pipeline
from backend.market_simulation_engine import market_simulation_engine
from backend.driver_compliance_engine import driver_compliance_engine


app = FastAPI(
    title="ChopExpress Core API",
    version="0.3.0",
    description="Core evaluation, simulation, and compliance API for ChopExpress V1.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class OrderRequest(BaseModel):
    order_id: str = "TEST1001"
    merchant: str = "Test Kitchen"
    zone: str = "clintonville"
    tier: str = "professional"

    delivery_distance: float = 3.4
    pickup_distance: float = 2.1
    return_distance: float = 2.5

    order_value: float = 26.25
    offered_payout: float = 8.75
    tip: float = 4.0
    estimated_total_minutes: float = 24.0

    merchant_risk_score: float = 0.35
    zone_pressure_score: float = 1.2
    is_batched_order: bool = False

    sales_tax_rate: float = 0.075
    commission_rate: float = 0.18
    processing_rate: float = 0.03
    fixed_processing_fee: float = 0.30
    promo_support: float = 0.0

    merchant_id: str = "M-001"
    customer_month_orders: int = 14
    customer_points: int = 220


class MarketSimulationRequest(BaseModel):
    order_count: int = Field(default=100, ge=1, le=5000)
    zone: str = "clintonville"
    include_peak: bool = True


class DriverComplianceRequest(BaseModel):
    driver_id: str = "DRV-1001"
    background_check_passed: bool = True
    license_valid: bool = True
    insurance_valid: bool = True
    vehicle_inspection_passed: bool = True
    training_completed: bool = True
    recertification_current: bool = True


@app.get("/")
def root() -> Dict[str, str]:
    return {"message": "ChopExpress Core API is running."}


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "healthy", "service": "ChopExpress Core API"}


@app.post("/evaluate-order")
def evaluate_order(req: OrderRequest) -> Dict[str, Any]:
    try:
        result = evaluate_order_pipeline(req.model_dump())
        return {"success": True, "data": result}
    except EngineContractError as exc:
        return {
            "success": False,
            "status": "engine_contract_error",
            "message": str(exc),
        }
    except Exception as exc:
        return {
            "success": False,
            "status": "error",
            "message": str(exc),
        }


@app.post("/simulate-market")
def simulate_market(req: MarketSimulationRequest) -> Dict[str, Any]:
    try:
        result = market_simulation_engine(
            {
                "order_count": req.order_count,
                "zone": req.zone,
                "include_peak": req.include_peak,
            }
        )
        return {"success": True, "data": result}
    except Exception as exc:
        return {
            "success": False,
            "status": "error",
            "message": str(exc),
        }


@app.post("/evaluate-driver-compliance")
def evaluate_driver_compliance(req: DriverComplianceRequest) -> Dict[str, Any]:
    try:
        result = driver_compliance_engine(req.model_dump())
        return {"success": True, "data": result}
    except EngineContractError as exc:
        return {
            "success": False,
            "status": "engine_contract_error",
            "message": str(exc),
        }
    except Exception as exc:
        return {
            "success": False,
            "status": "error",
            "message": str(exc),
        }