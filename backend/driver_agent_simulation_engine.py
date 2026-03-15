# backend/driver_agent_simulation_engine.py

from __future__ import annotations

import csv
import json
import os
import random
from dataclasses import dataclass, asdict
from statistics import mean
from typing import Any, Dict, List, Optional, Tuple

SIM_OUTPUT_DIR = os.path.join("sim", "output")
DEFAULT_MARKET_SUMMARY_PATH = os.path.join(SIM_OUTPUT_DIR, "local_test_run_summary.json")
DEFAULT_MARKET_LOG_PATH = os.path.join(SIM_OUTPUT_DIR, "local_test_run_market_log.csv")
DEFAULT_DD_RESULTS_PATH = os.path.join(SIM_OUTPUT_DIR, "dd_comparison_results.json")

OUTPUT_JSON = os.path.join(SIM_OUTPUT_DIR, "driver_agent_simulation_report.json")
OUTPUT_CSV = os.path.join(SIM_OUTPUT_DIR, "driver_agent_simulation_runs.csv")

DEFAULT_RANDOM_SEED = 42
DEFAULT_AGENT_COUNT = 120
DEFAULT_SIMULATION_ROUNDS = 6


@dataclass
class DriverAgent:
    agent_id: str
    strategy: str
    current_platform: str
    acceptance_threshold_ppm: float
    acceptance_threshold_hourly: float
    fuel_sensitivity: float
    fairness_sensitivity: float
    migration_bias: float
    fatigue_limit_hours: float
    preferred_zones: List[str]
    active: bool = True


@dataclass
class AgentRoundResult:
    round_index: int
    agent_id: str
    strategy: str
    starting_platform: str
    ending_platform: str
    zone: str
    offer_count: int
    accepted_count: int
    rejected_count: int
    avg_offer_pay: float
    avg_offer_miles: float
    avg_offer_ppm: float
    avg_hourly_rate: float
    estimated_fuel_cost: float
    fairness_score: float
    migrated: bool
    went_offline: bool


def ensure_output_dir() -> None:
    os.makedirs(SIM_OUTPUT_DIR, exist_ok=True)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def load_json_if_exists(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_market_summary(path: str = DEFAULT_MARKET_SUMMARY_PATH) -> Dict[str, Any]:
    return load_json_if_exists(path)


def load_dd_metrics(path: str = DEFAULT_DD_RESULTS_PATH) -> Dict[str, Any]:
    data = load_json_if_exists(path)
    if isinstance(data, dict):
        return data
    return {}


def load_market_log(path: str = DEFAULT_MARKET_LOG_PATH) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []

    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            normalized = {str(k).strip(): v for k, v in row.items()}
            rows.append(normalized)
    return rows


def infer_zone_pool(
    market_log: List[Dict[str, Any]],
    market_summary: Dict[str, Any],
) -> List[str]:
    zones = set()

    for row in market_log:
        for key in ("zone", "pickup_zone", "dropoff_zone", "origin_zone", "target_zone"):
            value = row.get(key)
            if value:
                zones.add(str(value).strip())

    zone_summary = market_summary.get("zone_summary") or market_summary.get("zones") or {}
    if isinstance(zone_summary, dict):
        for key in zone_summary.keys():
            zones.add(str(key).strip())

    if not zones:
        zones = {
            "Easton",
            "Clintonville",
            "Worthington",
            "Westerville",
            "Gahanna",
            "Dublin-Granville",
            "Northland",
        }

    return sorted(z for z in zones if z)


def summarize_market_offers(market_log: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not market_log:
        return {
            "offer_count": 0,
            "avg_offer_pay": 8.25,
            "avg_offer_miles": 4.8,
            "avg_offer_ppm": 1.72,
            "avg_hourly_rate": 18.5,
            "avg_fairness_score": 0.58,
        }

    pay_candidates: List[float] = []
    mile_candidates: List[float] = []
    ppm_candidates: List[float] = []
    hourly_candidates: List[float] = []
    fairness_candidates: List[float] = []

    for row in market_log:
        pay = 0.0
        for key in (
            "offer_pay",
            "pay",
            "earnings",
            "total_pay",
            "guaranteed_pay",
            "payout",
        ):
            if key in row:
                pay = _safe_float(row.get(key), pay)

        miles = 0.0
        for key in (
            "economic_miles",
            "miles",
            "trip_miles",
            "distance_miles",
            "offer_miles",
        ):
            if key in row:
                miles = _safe_float(row.get(key), miles)

        ppm = _safe_float(row.get("pay_per_mile"))
        if ppm <= 0 and miles > 0:
            ppm = pay / miles

        hourly = 0.0
        for key in (
            "net_hourly_rate",
            "hourly_rate",
            "effective_hourly_rate",
            "earnings_per_hour",
        ):
            if key in row:
                hourly = _safe_float(row.get(key), hourly)

        fairness = _safe_float(row.get("fairness_score"), 0.0)

        if pay > 0:
            pay_candidates.append(pay)
        if miles > 0:
            mile_candidates.append(miles)
        if ppm > 0:
            ppm_candidates.append(ppm)
        if hourly > 0:
            hourly_candidates.append(hourly)
        if fairness > 0:
            fairness_candidates.append(fairness)

    avg_pay = mean(pay_candidates) if pay_candidates else 8.25
    avg_miles = mean(mile_candidates) if mile_candidates else 4.8
    avg_ppm = mean(ppm_candidates) if ppm_candidates else (avg_pay / avg_miles if avg_miles else 1.72)
    avg_hourly = mean(hourly_candidates) if hourly_candidates else 18.5
    avg_fairness = mean(fairness_candidates) if fairness_candidates else 0.58

    return {
        "offer_count": len(market_log),
        "avg_offer_pay": avg_pay,
        "avg_offer_miles": avg_miles,
        "avg_offer_ppm": avg_ppm,
        "avg_hourly_rate": avg_hourly,
        "avg_fairness_score": avg_fairness,
    }


def build_agents(
    agent_count: int,
    zones: List[str],
    seed: int = DEFAULT_RANDOM_SEED,
) -> List[DriverAgent]:
    random.seed(seed)

    strategies = ["cautious", "balanced", "aggressive", "zone_hunter", "fairness_first"]
    platforms = ["doordash", "uber_eats", "chopexpress_shadow"]

    agents: List[DriverAgent] = []
    for i in range(agent_count):
        strategy = random.choices(
            strategies,
            weights=[22, 32, 18, 14, 14],
            k=1,
        )[0]

        current_platform = random.choices(
            platforms,
            weights=[58, 30, 12],
            k=1,
        )[0]

        preferred_zone_count = min(len(zones), max(1, random.randint(1, 3)))
        preferred_zones = random.sample(zones, preferred_zone_count)

        base_ppm = {
            "cautious": random.uniform(1.70, 2.20),
            "balanced": random.uniform(1.35, 1.95),
            "aggressive": random.uniform(1.05, 1.60),
            "zone_hunter": random.uniform(1.25, 1.85),
            "fairness_first": random.uniform(1.55, 2.10),
        }[strategy]

        base_hourly = {
            "cautious": random.uniform(20.0, 26.0),
            "balanced": random.uniform(17.0, 23.0),
            "aggressive": random.uniform(14.0, 20.0),
            "zone_hunter": random.uniform(16.0, 22.0),
            "fairness_first": random.uniform(18.0, 24.0),
        }[strategy]

        fairness_sensitivity = {
            "cautious": random.uniform(0.45, 0.72),
            "balanced": random.uniform(0.35, 0.62),
            "aggressive": random.uniform(0.15, 0.42),
            "zone_hunter": random.uniform(0.25, 0.50),
            "fairness_first": random.uniform(0.70, 0.95),
        }[strategy]

        agent = DriverAgent(
            agent_id=f"agent_{i+1:03d}",
            strategy=strategy,
            current_platform=current_platform,
            acceptance_threshold_ppm=round(base_ppm, 3),
            acceptance_threshold_hourly=round(base_hourly, 3),
            fuel_sensitivity=round(random.uniform(0.2, 1.0), 3),
            fairness_sensitivity=round(fairness_sensitivity, 3),
            migration_bias=round(random.uniform(0.2, 0.95), 3),
            fatigue_limit_hours=round(random.uniform(2.0, 8.0), 2),
            preferred_zones=preferred_zones,
        )
        agents.append(agent)

    return agents


def compute_platform_baselines(
    market_summary: Dict[str, Any],
    dd_metrics: Dict[str, Any],
    market_offer_summary: Dict[str, Any],
) -> Dict[str, Dict[str, float]]:
    chop_ppm = _safe_float(
        market_summary.get("pay_per_mile"),
        market_offer_summary.get("avg_offer_ppm", 1.72),
    )
    chop_hourly = _safe_float(
        market_summary.get("net_hourly_rate"),
        market_offer_summary.get("avg_hourly_rate", 18.5),
    )
    chop_fairness = _safe_float(
        market_summary.get("fairness_score"),
        market_offer_summary.get("avg_fairness_score", 0.58),
    )

    dd_ppm = _safe_float(
        dd_metrics.get("doordash_pay_per_mile"),
        dd_metrics.get("pay_per_mile"),
    )
    if dd_ppm <= 0:
        dd_ppm = max(0.85, chop_ppm * 0.78)

    dd_hourly = _safe_float(
        dd_metrics.get("doordash_hourly_rate"),
        dd_metrics.get("hourly_rate"),
    )
    if dd_hourly <= 0:
        dd_hourly = max(12.0, chop_hourly * 0.84)

    ue_ppm = max(0.90, chop_ppm * 0.82)
    ue_hourly = max(12.0, chop_hourly * 0.86)

    return {
        "chopexpress": {
            "ppm": round(max(chop_ppm, 1.0), 3),
            "hourly": round(max(chop_hourly, 12.0), 3),
            "fairness": round(max(chop_fairness, 0.55), 3),
        },
        "doordash": {
            "ppm": round(dd_ppm, 3),
            "hourly": round(dd_hourly, 3),
            "fairness": 0.42,
        },
        "uber_eats": {
            "ppm": round(ue_ppm, 3),
            "hourly": round(ue_hourly, 3),
            "fairness": 0.46,
        },
        "chopexpress_shadow": {
            "ppm": round(max(chop_ppm * 1.03, 1.1), 3),
            "hourly": round(max(chop_hourly * 1.02, 12.5), 3),
            "fairness": round(max(chop_fairness, 0.62), 3),
        },
    }


def choose_zone(agent: DriverAgent, all_zones: List[str]) -> str:
    if agent.preferred_zones and random.random() < 0.72:
        return random.choice(agent.preferred_zones)
    return random.choice(all_zones)


def estimate_offer_count(strategy: str) -> int:
    if strategy == "aggressive":
        return random.randint(7, 14)
    if strategy == "zone_hunter":
        return random.randint(6, 12)
    if strategy == "cautious":
        return random.randint(4, 9)
    if strategy == "fairness_first":
        return random.randint(4, 8)
    return random.randint(5, 10)


def simulate_round_for_agent(
    agent: DriverAgent,
    round_index: int,
    zones: List[str],
    baselines: Dict[str, Dict[str, float]],
) -> AgentRoundResult:
    zone = choose_zone(agent, zones)
    platform_key = agent.current_platform if agent.current_platform in baselines else "doordash"
    baseline = baselines[platform_key]

    offer_count = estimate_offer_count(agent.strategy)
    pay_samples: List[float] = []
    mile_samples: List[float] = []
    ppm_samples: List[float] = []
    hourly_samples: List[float] = []

    accepted = 0
    rejected = 0
    total_hours = 0.0
    estimated_fuel_cost = 0.0

    fairness_score = max(
        0.0,
        min(
            1.0,
            baseline["fairness"]
            + random.uniform(-0.08, 0.08)
            + (0.03 if zone in agent.preferred_zones else -0.01),
        ),
    )

    for _ in range(offer_count):
        base_pay = random.uniform(0.65, 1.35) * baseline["ppm"] * random.uniform(2.0, 7.5)
        miles = random.uniform(1.2, 9.0)
        ppm = base_pay / miles if miles > 0 else 0.0

        hourly_rate = (
            baseline["hourly"]
            + random.uniform(-4.5, 4.5)
            + (1.0 if zone in agent.preferred_zones else -0.5)
        )

        accept_score = 0.0
        accept_score += 0.65 if ppm >= agent.acceptance_threshold_ppm else -0.55
        accept_score += 0.45 if hourly_rate >= agent.acceptance_threshold_hourly else -0.35
        accept_score += (fairness_score - agent.fairness_sensitivity) * 0.9
        accept_score -= agent.fuel_sensitivity * max(0.0, 0.28 * miles - 1.2)

        if agent.strategy == "aggressive":
            accept_score += 0.18
        elif agent.strategy == "cautious":
            accept_score -= 0.14
        elif agent.strategy == "fairness_first":
            accept_score += (fairness_score - 0.5) * 0.7

        accepted_this_offer = accept_score > random.uniform(-0.28, 0.28)

        pay_samples.append(round(base_pay, 2))
        mile_samples.append(round(miles, 2))
        ppm_samples.append(round(ppm, 3))
        hourly_samples.append(round(hourly_rate, 2))

        if accepted_this_offer:
            accepted += 1
            trip_hours = random.uniform(0.18, 0.55)
            total_hours += trip_hours
            estimated_fuel_cost += miles * random.uniform(0.18, 0.30)
        else:
            rejected += 1

    went_offline = total_hours >= agent.fatigue_limit_hours

    chop = baselines["chopexpress"]
    migration_pressure = 0.0
    migration_pressure += max(0.0, chop["ppm"] - baseline["ppm"]) * 0.55
    migration_pressure += max(0.0, chop["hourly"] - baseline["hourly"]) * 0.03
    migration_pressure += max(0.0, chop["fairness"] - fairness_score) * 0.9
    migration_pressure += agent.migration_bias * 0.25
    migration_pressure += agent.fairness_sensitivity * 0.35

    migrated = False
    ending_platform = platform_key

    if platform_key != "chopexpress" and platform_key != "chopexpress_shadow":
        if migration_pressure > random.uniform(0.38, 1.22):
            ending_platform = "chopexpress"
            migrated = True

    agent.current_platform = ending_platform
    if went_offline:
        agent.active = False

    avg_offer_pay = mean(pay_samples) if pay_samples else 0.0
    avg_offer_miles = mean(mile_samples) if mile_samples else 0.0
    avg_offer_ppm = mean(ppm_samples) if ppm_samples else 0.0
    avg_hourly_rate = mean(hourly_samples) if hourly_samples else 0.0

    return AgentRoundResult(
        round_index=round_index,
        agent_id=agent.agent_id,
        strategy=agent.strategy,
        starting_platform=platform_key,
        ending_platform=ending_platform,
        zone=zone,
        offer_count=offer_count,
        accepted_count=accepted,
        rejected_count=rejected,
        avg_offer_pay=round(avg_offer_pay, 2),
        avg_offer_miles=round(avg_offer_miles, 2),
        avg_offer_ppm=round(avg_offer_ppm, 3),
        avg_hourly_rate=round(avg_hourly_rate, 2),
        estimated_fuel_cost=round(estimated_fuel_cost, 2),
        fairness_score=round(fairness_score, 3),
        migrated=migrated,
        went_offline=went_offline,
    )


def aggregate_results(
    results: List[AgentRoundResult],
    agents: List[DriverAgent],
    baselines: Dict[str, Dict[str, float]],
) -> Dict[str, Any]:
    if not results:
        return {
            "total_agents": len(agents),
            "total_round_results": 0,
            "migration_count": 0,
            "platform_distribution_end": {},
            "avg_offer_ppm": 0.0,
            "avg_hourly_rate": 0.0,
            "avg_fairness_score": 0.0,
            "avg_fuel_cost_per_agent_round": 0.0,
            "acceptance_rate": 0.0,
            "notes": "No results generated.",
        }

    total_offers = sum(r.offer_count for r in results)
    total_accepted = sum(r.accepted_count for r in results)
    migration_count = sum(1 for r in results if r.migrated)

    platform_distribution_end: Dict[str, int] = {}
    for agent in agents:
        platform_distribution_end[agent.current_platform] = platform_distribution_end.get(agent.current_platform, 0) + 1

    return {
        "total_agents": len(agents),
        "total_round_results": len(results),
        "simulation_rounds": max(r.round_index for r in results) if results else 0,
        "migration_count": migration_count,
        "migration_rate": round(migration_count / len(results), 4) if results else 0.0,
        "platform_distribution_end": platform_distribution_end,
        "avg_offer_ppm": round(mean(r.avg_offer_ppm for r in results), 3),
        "avg_hourly_rate": round(mean(r.avg_hourly_rate for r in results), 2),
        "avg_fairness_score": round(mean(r.fairness_score for r in results), 3),
        "avg_fuel_cost_per_agent_round": round(mean(r.estimated_fuel_cost for r in results), 2),
        "acceptance_rate": round(total_accepted / total_offers, 4) if total_offers else 0.0,
        "baseline_platforms": baselines,
    }


def save_results_csv(results: List[AgentRoundResult], path: str = OUTPUT_CSV) -> None:
    ensure_output_dir()
    fieldnames = list(asdict(results[0]).keys()) if results else [
        "round_index",
        "agent_id",
        "strategy",
        "starting_platform",
        "ending_platform",
        "zone",
        "offer_count",
        "accepted_count",
        "rejected_count",
        "avg_offer_pay",
        "avg_offer_miles",
        "avg_offer_ppm",
        "avg_hourly_rate",
        "estimated_fuel_cost",
        "fairness_score",
        "migrated",
        "went_offline",
    ]

    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(asdict(result))


def save_report_json(report: Dict[str, Any], path: str = OUTPUT_JSON) -> None:
    ensure_output_dir()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)


def run_driver_agent_simulation(
    agent_count: int = DEFAULT_AGENT_COUNT,
    simulation_rounds: int = DEFAULT_SIMULATION_ROUNDS,
    seed: int = DEFAULT_RANDOM_SEED,
) -> Dict[str, Any]:
    random.seed(seed)

    market_summary = load_market_summary()
    market_log = load_market_log()
    dd_metrics = load_dd_metrics()

    zones = infer_zone_pool(market_log, market_summary)
    market_offer_summary = summarize_market_offers(market_log)
    baselines = compute_platform_baselines(market_summary, dd_metrics, market_offer_summary)
    agents = build_agents(agent_count=agent_count, zones=zones, seed=seed)

    results: List[AgentRoundResult] = []
    for round_index in range(1, simulation_rounds + 1):
        for agent in agents:
            if not agent.active and random.random() < 0.45:
                continue
            if not agent.active and random.random() >= 0.45:
                agent.active = True

            result = simulate_round_for_agent(
                agent=agent,
                round_index=round_index,
                zones=zones,
                baselines=baselines,
            )
            results.append(result)

    aggregate = aggregate_results(results, agents, baselines)

    report = {
        "engine": "driver_agent_simulation_engine",
        "seed": seed,
        "agent_count_requested": agent_count,
        "simulation_rounds_requested": simulation_rounds,
        "zones_modeled": zones,
        "market_offer_summary": market_offer_summary,
        "aggregate": aggregate,
        "sample_agents": [asdict(agent) for agent in agents[:10]],
        "notes": [
            "This is a behavior-layer simulation for V1 strategy analysis.",
            "Agents model acceptance, fatigue, fairness sensitivity, and migration pressure.",
            "This is not yet a full geospatial microsimulation.",
        ],
    }

    save_results_csv(results, OUTPUT_CSV)
    save_report_json(report, OUTPUT_JSON)

    print("------ DRIVER AGENT SIMULATION REPORT ------")
    print(f"Agents modeled: {agent_count}")
    print(f"Simulation rounds: {simulation_rounds}")
    print(f"Migration count: {aggregate.get('migration_count', 0)}")
    print(f"Acceptance rate: {aggregate.get('acceptance_rate', 0.0)}")
    print(f"Report written to {OUTPUT_JSON}")
    print(f"Run table written to {OUTPUT_CSV}")

    return report


def main() -> Dict[str, Any]:
    print("Running driver agent simulation...")
    return run_driver_agent_simulation()


if __name__ == "__main__":
    main()