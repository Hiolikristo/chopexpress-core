from __future__ import annotations

import random
from dataclasses import dataclass
from statistics import mean
from typing import Any, Dict, List, Optional

from backend.order_pipeline import evaluate_order_pipeline


ZONES = [
    "clintonville",
    "short_north",
    "osu",
    "downtown",
    "westerville",
    "dublin",
    "gahanna",
]

MERCHANTS = [
    {"merchant_id": "M-001", "merchant": "Test Kitchen", "zone": "clintonville"},
    {"merchant_id": "M-002", "merchant": "Campus Bites", "zone": "osu"},
    {"merchant_id": "M-003", "merchant": "Downtown Grill", "zone": "downtown"},
    {"merchant_id": "M-004", "merchant": "North Pizza", "zone": "short_north"},
    {"merchant_id": "M-005", "merchant": "Dublin Curry House", "zone": "dublin"},
    {"merchant_id": "M-006", "merchant": "Westerville Wings", "zone": "westerville"},
    {"merchant_id": "M-007", "merchant": "Gahanna Bowl", "zone": "gahanna"},
]

TIERS = ["casual", "professional", "elite"]


@dataclass
class SimulationConfig:
    order_count: int = 100
    random_seed: int = 42
    sales_tax_rate: float = 0.075
    commission_rate: float = 0.18
    processing_rate: float = 0.03
    fixed_processing_fee: float = 0.30
    promo_probability: float = 0.18
    batch_probability: float = 0.14


def _round2(value: float) -> float:
    return round(float(value), 2)


def _safe_get(d: Dict[str, Any], *keys: str, default: float = 0.0) -> float:
    current: Any = d
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    try:
        return float(current)
    except (TypeError, ValueError):
        return default


def _weighted_choice(rng: random.Random, items: List[Any], weights: List[float]) -> Any:
    return rng.choices(items, weights=weights, k=1)[0]


def _make_order(index: int, cfg: SimulationConfig, rng: random.Random) -> Dict[str, Any]:
    merchant = rng.choice(MERCHANTS)
    zone = merchant["zone"]
    tier = _weighted_choice(rng, TIERS, [0.45, 0.40, 0.15])

    delivery_distance = round(rng.uniform(1.0, 6.5), 1)
    pickup_distance = round(rng.uniform(0.4, 3.2), 1)
    return_distance = round(rng.uniform(0.2, 3.5), 1)

    order_value = round(rng.uniform(12.0, 55.0), 2)
    tip = round(max(0.0, rng.gauss(order_value * 0.12, 2.0)), 2)

    estimated_total_minutes = int(rng.uniform(15, 42))
    merchant_risk_score = round(min(1.0, max(0.05, rng.gauss(0.35, 0.18))), 2)
    zone_pressure_score = round(min(1.8, max(0.6, rng.gauss(1.05, 0.22))), 2)

    promo_support = round(order_value * rng.uniform(0.00, 0.08), 2) if rng.random() < cfg.promo_probability else 0.0
    is_batched_order = rng.random() < cfg.batch_probability

    # Offered payout is intentionally imperfect so the simulator can test fair-pay logic.
    base_offer = (
        2.25
        + delivery_distance * rng.uniform(0.65, 0.95)
        + pickup_distance * rng.uniform(0.15, 0.35)
        + tip * rng.uniform(0.55, 0.90)
    )
    offered_payout = round(max(3.00, base_offer), 2)

    customer_month_orders = int(max(0, rng.gauss(9, 6)))
    customer_points = int(max(0, rng.gauss(140, 90)))

    return {
        "order_id": f"SIM-{index:05d}",
        "merchant_id": merchant["merchant_id"],
        "merchant": merchant["merchant"],
        "zone": zone,
        "tier": tier,
        "delivery_distance": delivery_distance,
        "pickup_distance": pickup_distance,
        "return_distance": return_distance,
        "order_value": order_value,
        "offered_payout": offered_payout,
        "tip": tip,
        "estimated_total_minutes": estimated_total_minutes,
        "merchant_risk_score": merchant_risk_score,
        "zone_pressure_score": zone_pressure_score,
        "is_batched_order": is_batched_order,
        "sales_tax_rate": cfg.sales_tax_rate,
        "commission_rate": cfg.commission_rate,
        "processing_rate": cfg.processing_rate,
        "fixed_processing_fee": cfg.fixed_processing_fee,
        "promo_support": promo_support,
        "customer_month_orders": customer_month_orders,
        "customer_points": customer_points,
    }


def _summarize_zone(rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}

    for row in rows:
        zone = str(row.get("zone", "unknown"))
        grouped.setdefault(zone, []).append(row)

    summary: Dict[str, Dict[str, Any]] = {}
    for zone, zone_rows in grouped.items():
        accepted = sum(1 for r in zone_rows if r["dispatch"]["recommended_action"] == "accept")
        rejected = len(zone_rows) - accepted

        summary[zone] = {
            "orders": len(zone_rows),
            "accepted": accepted,
            "rejected": rejected,
            "accept_rate": _round2(accepted / len(zone_rows)) if zone_rows else 0.0,
            "avg_driver_total": _round2(mean(r["fair_offer"]["fair_driver_total"] for r in zone_rows)),
            "avg_platform_net": _round2(mean(r["settlement"]["platform_net"] for r in zone_rows)),
            "avg_merchant_net": _round2(mean(r["settlement"]["merchant_net"] for r in zone_rows)),
        }

    return summary


def _extract_row(order: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
    breakdown = result.get("breakdown", {})
    fair_offer = result.get("fair_offer", {})
    dispatch = result.get("dispatch", {})
    driver_ms = result.get("driver_ms", {})
    insurance = result.get("insurance", {})
    verification = result.get("verification", {})
    merchant_finance = result.get("merchant_finance", {})
    merchant_tax = result.get("merchant_tax", {})
    settlement = result.get("settlement", {})
    driver_tax = result.get("driver_tax", {})
    customer_loyalty = result.get("customer_loyalty", {})

    return {
        "order_id": order["order_id"],
        "merchant": order["merchant"],
        "zone": order["zone"],
        "tier": order["tier"],
        "order_value": _safe_get(breakdown, "order_value", default=order["order_value"]),
        "driver_payout_raw": _safe_get(breakdown, "driver_payout"),
        "fair_offer": fair_offer,
        "dispatch": dispatch,
        "driver_ms": driver_ms,
        "insurance": insurance,
        "verification": verification,
        "merchant_finance": merchant_finance,
        "merchant_tax": merchant_tax,
        "settlement": settlement,
        "driver_tax": driver_tax,
        "customer_loyalty": customer_loyalty,
    }


def run_market_simulation(
    order_count: int = 100,
    random_seed: int = 42,
    include_orders: bool = True,
) -> Dict[str, Any]:
    cfg = SimulationConfig(order_count=order_count, random_seed=random_seed)
    rng = random.Random(cfg.random_seed)

    rows: List[Dict[str, Any]] = []
    engine_errors: List[Dict[str, str]] = []

    for i in range(1, cfg.order_count + 1):
        order = _make_order(i, cfg, rng)
        result = evaluate_order_pipeline(order)

        if result.get("status") in {"error", "engine_contract_error"}:
            engine_errors.append(
                {
                    "order_id": order["order_id"],
                    "status": str(result.get("status")),
                    "message": str(result.get("message", "Unknown pipeline error")),
                }
            )
            continue

        rows.append(_extract_row(order, result))

    total_orders = cfg.order_count
    processed_orders = len(rows)
    failed_orders = len(engine_errors)

    accepted_orders = sum(1 for r in rows if r["dispatch"].get("recommended_action") == "accept")
    rejected_orders = processed_orders - accepted_orders

    avg_driver_total = _round2(mean(_safe_get(r, "fair_offer", "fair_driver_total") for r in rows)) if rows else 0.0
    avg_effective_hourly = _round2(mean(_safe_get(r, "dispatch", "effective_hourly") for r in rows)) if rows else 0.0
    avg_platform_net = _round2(mean(_safe_get(r, "settlement", "platform_net") for r in rows)) if rows else 0.0
    avg_merchant_net = _round2(mean(_safe_get(r, "settlement", "merchant_net") for r in rows)) if rows else 0.0
    avg_driver_tax_reserve = _round2(mean(_safe_get(r, "driver_tax", "estimated_tax_reserve") for r in rows)) if rows else 0.0
    avg_customer_retention = _round2(mean(_safe_get(r, "customer_loyalty", "retention_score") for r in rows)) if rows else 0.0

    total_gross_order_value = _round2(sum(_safe_get(r, "breakdown", "order_value") for r in rows))
    total_driver_cost = _round2(sum(_safe_get(r, "fair_offer", "fair_driver_total") for r in rows))
    total_platform_net = _round2(sum(_safe_get(r, "settlement", "platform_net") for r in rows))
    total_merchant_net = _round2(sum(_safe_get(r, "settlement", "merchant_net") for r in rows))
    total_driver_tax_reserve = _round2(sum(_safe_get(r, "driver_tax", "estimated_tax_reserve") for r in rows))

    zone_summary = _summarize_zone(rows)

    result: Dict[str, Any] = {
        "summary": {
            "simulation_orders_requested": total_orders,
            "processed_orders": processed_orders,
            "failed_orders": failed_orders,
            "accepted_orders": accepted_orders,
            "rejected_orders": rejected_orders,
            "accept_rate": _round2(accepted_orders / processed_orders) if processed_orders else 0.0,
            "avg_driver_total": avg_driver_total,
            "avg_effective_hourly": avg_effective_hourly,
            "avg_platform_net": avg_platform_net,
            "avg_merchant_net": avg_merchant_net,
            "avg_driver_tax_reserve": avg_driver_tax_reserve,
            "avg_customer_retention": avg_customer_retention,
            "total_gross_order_value": total_gross_order_value,
            "total_driver_cost": total_driver_cost,
            "total_platform_net": total_platform_net,
            "total_merchant_net": total_merchant_net,
            "total_driver_tax_reserve": total_driver_tax_reserve,
        },
        "zone_summary": zone_summary,
        "engine_errors": engine_errors,
    }

    if include_orders:
        result["orders"] = rows

    return result


def market_simulation_engine(payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    payload = payload or {}
    order_count = int(payload.get("order_count", 100))
    random_seed = int(payload.get("random_seed", 42))
    include_orders = bool(payload.get("include_orders", True))

    return run_market_simulation(
        order_count=order_count,
        random_seed=random_seed,
        include_orders=include_orders,
    )


def main() -> None:
    result = run_market_simulation(order_count=100, random_seed=42, include_orders=False)

    print("ChopExpress Market Simulation")
    print("-" * 40)
    for key, value in result["summary"].items():
        print(f"{key}: {value}")

    print("\nZone Summary")
    print("-" * 40)
    for zone, data in result["zone_summary"].items():
        print(zone, data)

    if result["engine_errors"]:
        print("\nEngine Errors")
        print("-" * 40)
        for err in result["engine_errors"][:10]:
            print(err)


if __name__ == "__main__":
    main()