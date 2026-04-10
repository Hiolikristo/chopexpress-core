from __future__ import annotations

import json

from backend.market_simulator import MarketSimulator


def main() -> None:
    simulator = MarketSimulator()

    summary = simulator.run(
        driver_count=40,
        order_count=120,
        start_hour_local=0,
        market_hours=24,
        label="local_test_run",
    )

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()