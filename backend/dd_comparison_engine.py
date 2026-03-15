import csv
import json
import os
from typing import Any, Dict, List


class DDComparisonEngine:
    def __init__(self) -> None:
        self.real_data_path = os.path.join("sim", "input", "real_driving_log.csv")
        self.sim_summary_path = os.path.join("sim", "output", "latest_console_summary.json")
        self.output_json_path = os.path.join("sim", "output", "dd_comparison_results.json")
        self.output_csv_path = os.path.join("sim", "output", "dd_comparison_results.csv")

    def _safe_float(self, value: Any, default: float = 0.0) -> float:
        try:
            if value is None or value == "":
                return default
            return float(value)
        except (TypeError, ValueError):
            return default

    def _safe_int(self, value: Any, default: int = 0) -> int:
        try:
            if value is None or value == "":
                return default
            return int(float(value))
        except (TypeError, ValueError):
            return default

    def load_real_runs(self, path: str) -> List[Dict[str, Any]]:
        runs: List[Dict[str, Any]] = []

        if not os.path.exists(path):
            return runs

        with open(path, newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)

            for row in reader:
                miles = self._safe_float(row.get("miles"))
                earnings = self._safe_float(row.get("earnings"))
                orders = self._safe_int(row.get("orders"), 1)

                hours = self._safe_float(row.get("hours"))
                if hours <= 0:
                    minutes = self._safe_float(row.get("minutes"))
                    if minutes > 0:
                        hours = round(minutes / 60.0, 4)

                fuel_cost = self._safe_float(row.get("fuel_cost"))
                other_cost = self._safe_float(row.get("other_cost"))
                total_cost = round(fuel_cost + other_cost, 2)

                runs.append(
                    {
                        "date": row.get("date", ""),
                        "platform": row.get("platform", "DoorDash"),
                        "zone": row.get("zone", ""),
                        "miles": miles,
                        "earnings": earnings,
                        "orders": orders,
                        "hours": hours,
                        "fuel_cost": fuel_cost,
                        "other_cost": other_cost,
                        "total_cost": total_cost,
                        "net_profit": round(earnings - total_cost, 2),
                    }
                )

        return runs

    def load_simulation_summary(self, path: str) -> Dict[str, Any]:
        if not os.path.exists(path):
            return {}

        with open(path, "r", encoding="utf-8") as file:
            try:
                data = json.load(file)
                if isinstance(data, dict):
                    return data
            except json.JSONDecodeError:
                return {}

        return {}

    def summarize_real_world(self, runs: List[Dict[str, Any]]) -> Dict[str, Any]:
        total_runs = len(runs)
        total_miles = round(sum(run["miles"] for run in runs), 2)
        total_earnings = round(sum(run["earnings"] for run in runs), 2)
        total_orders = sum(run["orders"] for run in runs)
        total_hours = round(sum(run["hours"] for run in runs), 2)
        total_cost = round(sum(run["total_cost"] for run in runs), 2)
        total_net_profit = round(sum(run["net_profit"] for run in runs), 2)

        pay_per_mile = round(total_earnings / total_miles, 2) if total_miles > 0 else 0.0
        pay_per_order = round(total_earnings / total_orders, 2) if total_orders > 0 else 0.0
        hourly_rate = round(total_earnings / total_hours, 2) if total_hours > 0 else 0.0
        net_hourly_rate = round(total_net_profit / total_hours, 2) if total_hours > 0 else 0.0
        cost_per_mile = round(total_cost / total_miles, 2) if total_miles > 0 else 0.0

        return {
            "runs_loaded": total_runs,
            "total_miles": total_miles,
            "total_earnings": total_earnings,
            "total_orders": total_orders,
            "total_hours": total_hours,
            "total_cost": total_cost,
            "total_net_profit": total_net_profit,
            "pay_per_mile": pay_per_mile,
            "pay_per_order": pay_per_order,
            "hourly_rate": hourly_rate,
            "net_hourly_rate": net_hourly_rate,
            "cost_per_mile": cost_per_mile,
        }

    def summarize_chopexpress_simulation(self, sim_summary: Dict[str, Any]) -> Dict[str, Any]:
        total_orders = self._safe_int(sim_summary.get("total_orders"))
        total_offer_pay = self._safe_float(sim_summary.get("total_offer_pay"))
        total_economic_miles = self._safe_float(sim_summary.get("total_economic_miles"))
        avg_ppem = self._safe_float(sim_summary.get("avg_ppem"))
        avg_net_profit = self._safe_float(sim_summary.get("avg_net_profit"))
        avg_hourly_rate = self._safe_float(sim_summary.get("avg_hourly_rate"))
        approved_orders = self._safe_int(sim_summary.get("approved_orders"))
        rejected_orders = self._safe_int(sim_summary.get("rejected_orders"))
        approval_rate = self._safe_float(sim_summary.get("approval_rate"))

        pay_per_order = round(total_offer_pay / total_orders, 2) if total_orders > 0 else 0.0

        return {
            "total_orders": total_orders,
            "approved_orders": approved_orders,
            "rejected_orders": rejected_orders,
            "approval_rate": approval_rate,
            "total_offer_pay": round(total_offer_pay, 2),
            "total_economic_miles": round(total_economic_miles, 2),
            "avg_ppem": round(avg_ppem, 2),
            "avg_net_profit": round(avg_net_profit, 2),
            "avg_hourly_rate": round(avg_hourly_rate, 2),
            "pay_per_order": pay_per_order,
        }

    def compare(self, real_summary: Dict[str, Any], sim_summary: Dict[str, Any]) -> Dict[str, Any]:
        real_pay_per_mile = self._safe_float(real_summary.get("pay_per_mile"))
        real_hourly_rate = self._safe_float(real_summary.get("hourly_rate"))
        real_net_hourly_rate = self._safe_float(real_summary.get("net_hourly_rate"))
        real_pay_per_order = self._safe_float(real_summary.get("pay_per_order"))

        chop_ppem = self._safe_float(sim_summary.get("avg_ppem"))
        chop_hourly_rate = self._safe_float(sim_summary.get("avg_hourly_rate"))
        chop_net_profit = self._safe_float(sim_summary.get("avg_net_profit"))
        chop_pay_per_order = self._safe_float(sim_summary.get("pay_per_order"))

        return {
            "pay_per_mile_diff": round(chop_ppem - real_pay_per_mile, 2),
            "hourly_rate_diff": round(chop_hourly_rate - real_hourly_rate, 2),
            "pay_per_order_diff": round(chop_pay_per_order - real_pay_per_order, 2),
            "chop_avg_net_profit_minus_real_net_hourly": round(chop_net_profit - real_net_hourly_rate, 2),
        }

    def write_comparison_outputs(self, summary: Dict[str, Any], json_path: str, csv_path: str) -> None:
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)

        with open(json_path, "w", encoding="utf-8") as json_file:
            json.dump(summary, json_file, indent=4)

        with open(csv_path, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["section", "metric", "value"])

            for section_name, section_value in summary.items():
                if isinstance(section_value, dict):
                    for metric, value in section_value.items():
                        writer.writerow([section_name, metric, value])
                else:
                    writer.writerow(["root", section_name, section_value])

    def run(self) -> Dict[str, Any]:
        print("ChopExpress DoorDash Comparison Engine Starting...")

        real_runs = self.load_real_runs(self.real_data_path)
        sim_summary_raw = self.load_simulation_summary(self.sim_summary_path)

        real_world_summary = self.summarize_real_world(real_runs)
        chopexpress_summary = self.summarize_chopexpress_simulation(sim_summary_raw)
        difference_summary = self.compare(real_world_summary, chopexpress_summary)

        summary = {
            "real_world": real_world_summary,
            "chopexpress_simulation": chopexpress_summary,
            "difference": difference_summary,
            "paths": {
                "real_data_path": self.real_data_path,
                "simulation_summary_path": self.sim_summary_path,
                "output_json_path": self.output_json_path,
                "output_csv_path": self.output_csv_path,
            },
        }

        self.write_comparison_outputs(summary, self.output_json_path, self.output_csv_path)

        print(f"Loaded {real_world_summary['runs_loaded']} real runs")
        print("Comparison results written:")
        print(self.output_json_path)
        print(self.output_csv_path)

        return summary


def main() -> None:
    engine = DDComparisonEngine()
    engine.run()


if __name__ == "__main__":
    main()