import os
from pprint import pprint

from backend.zone_heatmap_engine import (
    load_market_log,
    build_zone_heatmap,
    build_investor_summary,
    write_zone_heatmap_outputs,
)

MARKET_LOG_PATH = os.path.join("sim", "output", "local_1000_run_market_log.csv")

HEATMAP_JSON = os.path.join("sim", "analytics", "zone_heatmap.json")
HEATMAP_CSV = os.path.join("sim", "analytics", "pilot_zone_ranking.csv")
INVESTOR_JSON = os.path.join("sim", "analytics", "investor_summary.json")


def main() -> None:
    print("Loading market log...")
    rows = load_market_log(MARKET_LOG_PATH)
    print(f"Loaded log rows: {len(rows)}")

    if not rows:
        raise RuntimeError(f"No market log rows found in {MARKET_LOG_PATH}")

    print("Building zone heatmap...")
    zone_heatmap = build_zone_heatmap(rows)

    print("Building investor summary...")
    investor_summary = build_investor_summary(zone_heatmap)

    print("Writing outputs...")
    write_zone_heatmap_outputs(
        zone_heatmap=zone_heatmap,
        investor_summary=investor_summary,
        json_path=HEATMAP_JSON,
        csv_path=HEATMAP_CSV,
        investor_json_path=INVESTOR_JSON,
    )

    print("\n=== TOP ZONES ===\n")
    pprint(zone_heatmap[:5])

    print("\n=== INVESTOR SUMMARY ===\n")
    pprint(investor_summary)

    print("\nFiles written:")
    print(f" - {HEATMAP_JSON}")
    print(f" - {HEATMAP_CSV}")
    print(f" - {INVESTOR_JSON}")


if __name__ == "__main__":
    main()