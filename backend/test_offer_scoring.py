from __future__ import annotations

import json

from backend.fair_offer_engine import classify_offer
from backend.sample_observations import load_sample_observations


def main() -> None:
    observations = load_sample_observations()

    for obs in observations:
        result = classify_offer(obs)

        print("=" * 72)
        print(f"OBS: {obs.observation_id}")
        print(f"MERCHANT: {obs.merchant_name}")
        print(f"OFFER PAY: {obs.offered_pay_total}")
        print(f"OFFERED MILES: {obs.offered_miles}")
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()