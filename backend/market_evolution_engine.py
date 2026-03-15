import json
import os

OUTPUT_DIR = "sim/output"

SUMMARY_FILE = os.path.join(OUTPUT_DIR, "local_test_run_summary.json")
MIGRATION_FILE = os.path.join(OUTPUT_DIR, "driver_migration_projection.json")

OUTPUT_FILE = os.path.join(OUTPUT_DIR, "market_evolution_projection.json")


def load_json(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} not found")

    with open(path, "r") as f:
        return json.load(f)


def simulate_market(summary, migration):

    migration_rate = migration["driver_migration_projection"]["12_month"]

    doordash = 0.72
    uber = 0.22
    chop = 0.0
    others = 0.06

    years = []

    for year in range(5):

        growth = migration_rate * (1 - chop) * 0.5

        chop += growth
        doordash = max(0, doordash - growth * 0.8)
        uber = max(0, uber - growth * 0.2)

        years.append({
            "year": year,
            "doordash": round(doordash,3),
            "uber": round(uber,3),
            "chopexpress": round(chop,3),
            "others": round(others,3)
        })

    return {
        "starting_market": {
            "doordash":0.72,
            "uber":0.22,
            "others":0.06
        },
        "projection": years
    }


def main():

    print("Running market evolution simulation...")

    summary = load_json(SUMMARY_FILE)
    migration = load_json(MIGRATION_FILE)

    result = simulate_market(summary, migration)

    with open(OUTPUT_FILE, "w") as f:
        json.dump(result, f, indent=2)

    print("Market evolution projection written:")
    print(OUTPUT_FILE)

    return result


if __name__ == "__main__":
    main()