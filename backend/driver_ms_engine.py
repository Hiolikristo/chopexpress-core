from typing import Any, Dict


def evaluate(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Driver MS engine.

    MS = migration / matching / suitability layer for now.
    Keeps a stable pipeline contract while the richer driver-state logic
    is still being built out.
    """

    driver_id = payload.get("driver_id", "unknown")
    zone = payload.get("zone", "default")
    driver_tier = payload.get("driver_tier", "casual")
    acceptance_rate = float(payload.get("acceptance_rate", 0.0) or 0.0)
    completion_rate = float(payload.get("completion_rate", 1.0) or 1.0)
    rolling_miles_30d = float(payload.get("rolling_miles_30d", 0.0) or 0.0)
    is_batched_order = bool(payload.get("is_batched_order", False))

    suitability_score = 1.0

    if acceptance_rate < 0.50:
        suitability_score -= 0.15

    if completion_rate < 0.90:
        suitability_score -= 0.20

    if is_batched_order:
        suitability_score -= 0.05

    if driver_tier in {"pro", "pro_plus", "elite", "professional"}:
        suitability_score += 0.10

    if rolling_miles_30d >= 1000:
        suitability_score += 0.05

    suitability_score = round(max(0.0, min(1.0, suitability_score)), 2)

    migration_risk = "low"
    if suitability_score < 0.50:
        migration_risk = "high"
    elif suitability_score < 0.75:
        migration_risk = "medium"

    return {
        "driver_id": driver_id,
        "zone": zone,
        "driver_tier": driver_tier,
        "acceptance_rate": acceptance_rate,
        "completion_rate": completion_rate,
        "rolling_miles_30d": rolling_miles_30d,
        "suitability_score": suitability_score,
        "migration_risk": migration_risk,
        "status": "ok",
    }


def driver_ms(payload: Dict[str, Any]) -> Dict[str, Any]:
    return evaluate(payload)


def evaluate_driver_ms(payload: Dict[str, Any]) -> Dict[str, Any]:
    return evaluate(payload)


def driver_ms_engine(payload: Dict[str, Any]) -> Dict[str, Any]:
    return evaluate(payload)