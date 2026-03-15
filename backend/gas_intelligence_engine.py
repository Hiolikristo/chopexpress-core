from __future__ import annotations

import os
import pandas as pd


INPUT_FILE = os.path.join("sim", "data", "delivery_log.csv")
OUTPUT_FILE = os.path.join("sim", "output", "gas_intelligence_report.csv")

DEFAULT_GAS_PRICE = 3.49
DEFAULT_MPG = 25.0


def run_gas_intelligence() -> None:
    print("Running gas intelligence analysis...")

    if not os.path.exists(INPUT_FILE):
        print(f"Skipping gas intelligence: missing input file {INPUT_FILE}")
        return

    df = pd.read_csv(INPUT_FILE)

    if "miles" not in df.columns:
        print("Skipping gas intelligence: 'miles' column not found.")
        return

    df["estimated_fuel_cost"] = df["miles"] * (DEFAULT_GAS_PRICE / DEFAULT_MPG)
    total_fuel = float(df["estimated_fuel_cost"].sum())

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)

    print("\n------ GAS INTELLIGENCE REPORT ------")
    print(f"Estimated fuel cost across runs: ${total_fuel:.2f}")
    print(f"Gas intelligence report written to {OUTPUT_FILE}")


def main() -> None:
    run_gas_intelligence()


if __name__ == "__main__":
    main()