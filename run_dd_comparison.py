import os
from pprint import pprint

from backend.dd_comparison_engine import (
    build_comparison,
    load_real_runs,
    load_sim_runs,
    write_comparison_outputs,
)

REAL_DATA_PATH = os.path.join("sim", "input", "real_driving_log.csv")
SIM_DATA_PATH = os.path.join("sim", "data", "orders.csv")

OUTPUT_JSON = os.path.join("sim", "analytics", "dd_vs_chopexpress_summary.json")
OUTPUT_CSV = os.path.join("sim", "analytics", "dd_vs_chopexpress_summary.csv")


def main() -> None:
    print("Loading real driving data...")
    real_runs = load_real_runs(REAL_DATA_PATH)
    print(f"Loaded real rows: {len(real_runs)}")

    print("Loading simulator data...")
    sim_runs = load_sim_runs(SIM_DATA_PATH)
    print(f"Loaded sim rows: {len(sim_runs)}")

    if not real_runs:
        raise RuntimeError(f"No real driving rows found in {REAL_DATA_PATH}")

    if not sim_runs:
        raise RuntimeError(f"No simulator rows found in {SIM_DATA_PATH}")

    print("Building comparison...")
    summary = build_comparison(real_runs, sim_runs)

    print("Writing outputs...")
    write_comparison_outputs(summary, OUTPUT_JSON, OUTPUT_CSV)

    print("\n=== COMPARISON RESULT ===\n")
    pprint(summary)

    print("\nFiles written:")
    print(f" - {OUTPUT_JSON}")
    print(f" - {OUTPUT_CSV}")


if __name__ == "__main__":
    main()