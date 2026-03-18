from typing import Any, Dict


def evaluate(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Dispatch engine.

    Produces a minimal dispatch decision object for the order pipeline.
    This keeps the pipeline contract stable while you expand routing,
    fairness, batching, and zone logic.
    """

    order_id = payload.get("order_id", "unknown")
    zone = payload.get("zone", "default")
    pickup_lat = payload.get("pickup_lat")
    pickup_lng = payload.get("pickup_lng")
    dropoff_lat = payload.get("dropoff_lat")
    dropoff_lng = payload.get("dropoff_lng")
    estimated_distance_miles = float(payload.get("estimated_distance_miles", 0.0) or 0.0)
    estimated_drive_minutes = float(payload.get("estimated_drive_minutes", 0.0) or 0.0)
    is_batched_order = bool(payload.get("is_batched_order", False))

    dispatch_mode = "single_order"
    if is_batched_order:
        dispatch_mode = "batched_order"

    priority_score = round(
        (estimated_distance_miles * 0.4) + (estimated_drive_minutes * 0.6),
        2,
    )

    return {
        "order_id": order_id,
        "zone": zone,
        "dispatch_mode": dispatch_mode,
        "priority_score": priority_score,
        "estimated_distance_miles": estimated_distance_miles,
        "estimated_drive_minutes": estimated_drive_minutes,
        "pickup": {
            "lat": pickup_lat,
            "lng": pickup_lng,
        },
        "dropoff": {
            "lat": dropoff_lat,
            "lng": dropoff_lng,
        },
        "status": "ok",
    }


def dispatch(payload: Dict[str, Any]) -> Dict[str, Any]:
    return evaluate(payload)


def evaluate_dispatch(payload: Dict[str, Any]) -> Dict[str, Any]:
    return evaluate(payload)


def dispatch_engine(payload: Dict[str, Any]) -> Dict[str, Any]:
    return evaluate(payload)