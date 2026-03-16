from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .order_pipeline import evaluate_order_pipeline, EngineContractError


app = FastAPI(title="ChopExpress Core API")


class OrderRequest(BaseModel):
    order_id: str = Field(..., description="Unique order identifier")
    merchant: str = Field(..., description="Merchant name")
    zone: str = Field(..., description="Operational zone")
    tier: str = Field(..., description="Driver tier")
    delivery_distance: float = Field(..., ge=0)
    pickup_distance: float = Field(..., ge=0)
    return_distance: float = Field(..., ge=0)
    order_value: float = Field(..., ge=0)
    offered_payout: float = Field(..., ge=0)
    tip: float = Field(0, ge=0)


def safe_dict(value: Any) -> Dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "dict"):
        return value.dict()
    return {"value": value}


@app.get("/")
def root() -> Dict[str, str]:
    return {"status": "ChopExpress API running"}


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "healthy"}


@app.post("/evaluate-order")
def evaluate_order(order: OrderRequest) -> Dict[str, Dict[str, Any]]:
    try:
        payload = order.model_dump()
        result = evaluate_order_pipeline(payload)

        return {
            "breakdown": safe_dict(result.get("breakdown")),
            "fair_offer": safe_dict(result.get("fair_offer")),
            "dispatch": safe_dict(result.get("dispatch")),
            "driver_ms": safe_dict(result.get("driver_ms")),
            "insurance": safe_dict(result.get("insurance")),
        }
    except EngineContractError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unhandled pipeline error: {str(exc)}") from exc