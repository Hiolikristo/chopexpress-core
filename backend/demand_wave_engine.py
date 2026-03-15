import csv
import json
import os
import random
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Dict, List, Optional

from backend.demand_wave_engine import get_demand_wave_state, get_hourly_order_target
from backend.driver_migration_engine import apply_driver_migration


@dataclass
class SimOrder:
    order_id: str
    hour_local: int
    pickup_zone: str
    dropoff_zone: str
    status: str
    trip_miles: float
    base_pay: float
    expected_tip: float
    effective_pay_per_mile: float
    effective_hourly_rate: float
    surge_multiplier: float
    pressure_score: float
    demand_wave: str
    wave_multiplier: float
    zone_wave_multiplier: float
    effective_wave_multiplier: float
    online_drivers_at_dispatch: int
    migrated_driver_inflow: int


class MarketSimulator:
    def __init__(
        self,
        total_orders: int = 1000,
        total_drivers: int = 90,
        market_hours: int = 8,
        start_hour_local: int = 10,
        random_seed: int = 42,
        is_weekend: bool = False,
    ) -> None:
        self.total_orders = total_orders
        self.total_drivers = total_drivers
        self.market_hours = market_hours
        self.start_hour_local = start_hour_local
        self.random_seed = random_seed
        self.is_weekend = is_weekend

        random.seed(self.random_seed)

        self.zones = [
            "Polaris",
            "Westerville",
            "Easton",
            "Clintonville",
            "Gahanna",
            "Downtown",
        ]

        self.zone_base_order_weights = {
            "Polaris": 0.18,
            "Westerville": 0.16,
            "Easton": 0.16,
            "Clintonville": 0.15,
            "Gahanna": 0.15,
            "Downtown": 0.20,
        }

        self.zone_base_driver_weights = {
            "Polaris": 0.18,
            "Westerville": 0.17,
            "Easton": 0.16,
            "Clintonville": 0.15,
            "Gahanna": 0.14,
            "Downtown": 0.20,
        }

    def _safe_div(self, numerator: float, denominator: float) -> float:
        if denominator == 0:
            return 0.0
        return numerator / denominator

    def _build_driver_supply_map(self) -> Dict[str, int]:
        supply_map: Dict[str, int] = {}
        assigned = 0

        for index, zone in enumerate(self.zones):
            if index == len(self.zones) - 1:
                supply_map[zone] = self.total_drivers - assigned
                break

            count = int(round(self.total_drivers * self.zone_base_driver_weights[zone]))
            supply_map[zone] = count
            assigned += count

        return supply_map

    def _build_hourly_order_budget(self) -> Dict[int, Dict[str, int]]:
        base_zone_orders = {
            zone: max(1, int(round(self.total_orders * self.zone_base_order_weights[zone] / self.market_hours)))
            for zone in self.zones
        }

        hourly_budget: Dict[int, Dict[str, int]] = {}

        for offset in range(self.market_hours):
            hour_local = (self.start_hour_local + offset) % 24
            hourly_budget[hour_local] = {}

            for zone in self.zones:
                hourly_budget[hour_local][zone] = get_hourly_order_target(
                    base_orders_for_zone=base_zone_orders[zone],
                    zone=zone,
                    hour_local=hour_local,
                    is_weekend=self.is_weekend,
                )

        return hourly_budget

    def _choose_dropoff_zone(self, pickup_zone: str) -> str:
        other_zones = [zone for zone in self.zones if zone != pickup_zone]
        return random.choice(other_zones)

    def _estimate_trip_miles(self, pickup_zone: str, dropoff_zone: str) -> float:
        if pickup_zone == "Downtown" or dropoff_zone == "Downtown":
            return round(random.uniform(1.8, 4.8), 2)

        if pickup_zone in {"Polaris", "Westerville"} or dropoff_zone in {"Polaris", "Westerville"}:
            return round(random.uniform(2.5, 6.8), 2)

        return round(random.uniform(2.0, 5.9), 2)

    def _pressure_score(self, open_orders: int, online_drivers: int, backlog: int) -> float:
        demand_supply_ratio = self._safe_div(open_orders + backlog, max(1, online_drivers))
        pressure = (demand_supply_ratio * 0.7) + (backlog * 0.08)
        return round(max(0.0, pressure), 4)

    def _surge_multiplier(self, pressure_score: float) -> float:
        if pressure_score < 0.9:
            return 1.0
        if pressure_score < 1.2:
            return 1.08
        if pressure_score < 1.6:
            return 1.18
        if pressure_score < 2.0:
            return 1.35
        return 1.55

    def _base_pay(self, trip_miles: float, surge_multiplier: float) -> float:
        base = 3.25 + (trip_miles * 1.22)
        return round(base * surge_multiplier, 2)

    def _expected_tip(self, pickup_zone: str, demand_wave: str) -> float:
        base_tip = {
            "Polaris": 4.10,
            "Westerville": 3.90,
            "Easton": 4.00,
            "Clintonville": 3.60,
            "Gahanna": 3.55,
            "Downtown": 3.20,
        }.get(pickup_zone, 3.50)

        wave_bonus = {
            "breakfast": 0.2,
            "lunch": 0.45,
            "afternoon": 0.15,
            "dinner": 0.7,
            "late_night": 0.35,
            "overnight": 0.1,
        }.get(demand_wave, 0.0)

        tip = base_tip + wave_bonus + random.uniform(-0.65, 0.85)
        return round(max(0.0, tip), 2)

    def _effective_hourly(self, pay: float, trip_miles: float, pickup_zone: str) -> float:
        mph = 18.0 if pickup_zone == "Downtown" else 24.0
        service_minutes = 10.0 if pickup_zone == "Downtown" else 7.0
        trip_minutes = (trip_miles / mph) * 60.0
        total_minutes = max(12.0, trip_minutes + service_minutes)
        hourly = pay / (total_minutes / 60.0)
        return round(hourly, 2)

    def _build_orders(self) -> List[SimOrder]:
        online_driver_map = self._build_driver_supply_map()
        hourly_budget = self._build_hourly_order_budget()

        orders: List[SimOrder] = []
        sequence = 1
        migration_log: Dict[int, Dict[str, int]] = {}

        for hour_local, zone_budget in hourly_budget.items():
            zone_pressure_map: Dict[str, float] = {}

            for pickup_zone, open_orders in zone_budget.items():
                online_drivers = max(1, online_driver_map.get(pickup_zone, 1))
                backlog = max(0, int(round(open_orders * random.uniform(0.02, 0.18))))
                zone_pressure_map[pickup_zone] = self._pressure_score(
                    open_orders=open_orders,
                    online_drivers=online_drivers,
                    backlog=backlog,
                )

            before_migration = dict(online_driver_map)
            decisions = apply_driver_migration(
                online_driver_map=online_driver_map,
                zone_pressure_map=zone_pressure_map,
            )

            inflow_map = {zone: 0 for zone in self.zones}
            for d in decisions:
                inflow_map[d.target_zone] = inflow_map.get(d.target_zone, 0) + d.migrating_drivers

            migration_log[hour_local] = inflow_map

            for pickup_zone, open_orders in zone_budget.items():
                online_drivers = max(1, online_driver_map.get(pickup_zone, 1))
                backlog = max(0, int(round(open_orders * random.uniform(0.02, 0.18))))

                pressure_score = self._pressure_score(
                    open_orders=open_orders,
                    online_drivers=online_drivers,
                    backlog=backlog,
                )

                surge_multiplier = self._surge_multiplier(pressure_score)

                wave_state = get_demand_wave_state(
                    zone=pickup_zone,
                    hour_local=hour_local,
                    is_weekend=self.is_weekend,
                )

                completion_probability = 0.985 - min(0.22, pressure_score * 0.08)
                completion_probability = max(0.75, completion_probability)

                for _ in range(open_orders):
                    dropoff_zone = self._choose_dropoff_zone(pickup_zone)
                    trip_miles = self._estimate_trip_miles(pickup_zone, dropoff_zone)

                    status = "completed" if random.random() <= completion_probability else "unclaimed"

                    base_pay = self._base_pay(
                        trip_miles=trip_miles,
                        surge_multiplier=surge_multiplier,
                    )

                    expected_tip = self._expected_tip(
                        pickup_zone=pickup_zone,
                        demand_wave=wave_state.wave_name,
                    )

                    total_pay = base_pay + expected_tip
                    effective_ppm = round(self._safe_div(total_pay, trip_miles), 2)
                    effective_hourly = self._effective_hourly(
                        pay=total_pay,
                        trip_miles=trip_miles,
                        pickup_zone=pickup_zone,
                    )

                    orders.append(
                        SimOrder(
                            order_id=f"O{sequence:05d}",
                            hour_local=hour_local,
                            pickup_zone=pickup_zone,
                            dropoff_zone=dropoff_zone,
                            status=status,
                            trip_miles=trip_miles,
                            base_pay=base_pay,
                            expected_tip=expected_tip,
                            effective_pay_per_mile=effective_ppm,
                            effective_hourly_rate=effective_hourly,
                            surge_multiplier=round(surge_multiplier, 2),
                            pressure_score=pressure_score,
                            demand_wave=wave_state.wave_name,
                            wave_multiplier=wave_state.wave_multiplier,
                            zone_wave_multiplier=wave_state.zone_multiplier,
                            effective_wave_multiplier=wave_state.effective_multiplier,
                            online_drivers_at_dispatch=online_drivers,
                            migrated_driver_inflow=inflow_map.get(pickup_zone, 0),
                        )
                    )
                    sequence += 1

        return orders

    def _summarize(self, orders: List[SimOrder]) -> Dict:
        completed = [o for o in orders if o.status == "completed"]

        total_orders = len(orders)
        completed_orders = len(completed)
        unclaimed_orders = total_orders - completed_orders
        completion_rate = round(self._safe_div(completed_orders, total_orders), 4)

        total_earnings = round(sum(o.base_pay + o.expected_tip for o in completed), 2)
        total_miles = round(sum(o.trip_miles for o in completed), 2)
        avg_pay_per_order = round(self._safe_div(total_earnings, completed_orders), 2)
        avg_pay_per_mile = round(self._safe_div(total_earnings, total_miles), 2)

        wave_summary: Dict[str, Dict] = {}
        for wave_name in {"breakfast", "lunch", "afternoon", "dinner", "late_night", "overnight"}:
            wave_rows = [o for o in orders if o.demand_wave == wave_name]
            wave_completed = [o for o in wave_rows if o.status == "completed"]

            if not wave_rows:
                continue

            wave_summary[wave_name] = {
                "orders": len(wave_rows),
                "completed_orders": len(wave_completed),
                "completion_rate": round(self._safe_div(len(wave_completed), len(wave_rows)), 4),
                "earnings": round(sum(o.base_pay + o.expected_tip for o in wave_completed), 2),
                "avg_pay_per_mile": round(
                    self._safe_div(
                        sum(o.base_pay + o.expected_tip for o in wave_completed),
                        sum(o.trip_miles for o in wave_completed),
                    ),
                    2,
                ),
            }

        return {
            "label": None,
            "generated_at": datetime.utcnow().isoformat(),
            "is_weekend": self.is_weekend,
            "total_orders": total_orders,
            "completed_orders": completed_orders,
            "unclaimed_orders": unclaimed_orders,
            "completion_rate": completion_rate,
            "total_earnings": total_earnings,
            "total_miles": total_miles,
            "avg_pay_per_order": avg_pay_per_order,
            "avg_pay_per_mile": avg_pay_per_mile,
            "wave_summary": wave_summary,
        }

    def _write_outputs(self, label: Optional[str], orders: List[SimOrder], summary: Dict) -> None:
        output_dir = os.path.join("sim", "output")
        data_dir = os.path.join("sim", "data")
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(data_dir, exist_ok=True)

        normalized_label = label or "latest"

        market_log_path = os.path.join(output_dir, f"{normalized_label}_run_market_log.csv")
        summary_path = os.path.join(output_dir, f"{normalized_label}_run_summary.json")
        orders_csv_path = os.path.join(data_dir, "orders.csv")

        rows = [asdict(o) for o in orders]

        if rows:
            fieldnames = list(rows[0].keys())

            for path in [market_log_path, orders_csv_path]:
                with open(path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(rows)

        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        latest_console_summary_path = os.path.join(output_dir, "latest_console_summary.json")
        with open(latest_console_summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

    def _print_console(self, summary: Dict, orders: List[SimOrder]) -> None:
        print(f"Label: {'weekend_wave_run' if self.is_weekend else 'weekday_wave_run'}")
        print(f"Total orders: {summary['total_orders']}")
        print(f"Completed orders: {summary['completed_orders']}")
        print(f"Unclaimed orders: {summary['unclaimed_orders']}")
        print(f"Completion rate: {summary['completion_rate']}")
        print(f"Total payout: ${summary['total_earnings']}")
        print(f"Total miles: {summary['total_miles']}")
        print(f"Avg pay/order: ${summary['avg_pay_per_order']}")
        print(f"Avg pay/mile: ${summary['avg_pay_per_mile']}")
        print()

        completed = [o for o in orders if o.status == "completed"]
        top_orders = sorted(
            completed,
            key=lambda o: o.effective_hourly_rate,
            reverse=True,
        )[:5]

        print("=== TOP 5 ORDERS BY HOURLY RATE ===")
        for row in top_orders:
            print(
                f"{row.order_id} | {row.pickup_zone} | {row.demand_wave} | "
                f"hour={row.hour_local} | pay=${round(row.base_pay + row.expected_tip, 2)} | "
                f"hourly=${row.effective_hourly_rate} | ppm=${row.effective_pay_per_mile}/mile | "
                f"drivers={row.online_drivers_at_dispatch} | inflow={row.migrated_driver_inflow}"
            )

        print()
        print("=== WAVE SUMMARY ===")
        for wave_name, wave_data in summary["wave_summary"].items():
            print(
                f"{wave_name}: orders={wave_data['orders']}, "
                f"completed={wave_data['completed_orders']}, "
                f"completion_rate={wave_data['completion_rate']}, "
                f"earnings=${wave_data['earnings']}, "
                f"avg_ppm=${wave_data['avg_pay_per_mile']}"
            )

    def run(self, label: Optional[str] = None) -> Dict:
        orders = self._build_orders()
        summary = self._summarize(orders)
        summary["label"] = label or ("weekend_wave_run" if self.is_weekend else "weekday_wave_run")

        self._write_outputs(label=label or summary["label"], orders=orders, summary=summary)
        self._print_console(summary=summary, orders=orders)

        return summary