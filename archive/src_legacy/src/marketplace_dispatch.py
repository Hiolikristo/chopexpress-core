import random
from drivers import Driver

INITIAL_RADIUS = 2.5
RADIUS_STEP = 1.5
MAX_ROUNDS = 4
BATCH_SIZE = 4
ACCEPTANCE_THRESHOLD = 0.55


def get_eligible_drivers(drivers, radius):
    eligible = [
        d for d in drivers
        if d.available and d.distance_to_restaurant <= radius
    ]
    eligible.sort(key=lambda d: d.distance_to_restaurant)
    return eligible[:BATCH_SIZE]


def driver_accepts(driver):
    """
    Simulate whether a driver accepts.
    Closer drivers are more likely to accept.
    """
    distance_penalty = min(driver.distance_to_restaurant / 10, 0.35)
    acceptance_probability = ACCEPTANCE_THRESHOLD + (0.25 - distance_penalty)
    acceptance_probability = max(0.15, min(0.90, acceptance_probability))

    roll = random.random()
    accepted = roll <= acceptance_probability

    return accepted, acceptance_probability, roll


def dispatch_order_marketplace(drivers):
    radius = INITIAL_RADIUS

    for round_number in range(1, MAX_ROUNDS + 1):
        batch = get_eligible_drivers(drivers, radius)

        print(f"\n=== Dispatch Round {round_number} ===")
        print(f"Offer radius: {radius:.1f} miles")

        if not batch:
            print("No eligible drivers in this radius.")
            radius += RADIUS_STEP
            continue

        print("Offer batch:")
        for d in batch:
            print(f"- {d.name} ({d.driver_id}) at {d.distance_to_restaurant:.1f} miles")

        print("\nSimulating 20-second offer window...\n")

        for d in batch:
            accepted, probability, roll = driver_accepts(d)

            print(
                f"{d.name}: "
                f"accept_prob={probability:.2f}, roll={roll:.2f}, accepted={accepted}"
            )

            if accepted:
                print(f"\nAssigned driver: {d.name} ({d.driver_id})")
                return d

        print("\nNo one accepted this round. Expanding radius...")
        radius += RADIUS_STEP

    print("\nOrder unclaimed after max rounds. Reprice or cancel required.")
    return None


def main():
    drivers = [
        Driver("D001", "Alex", "easton", 1.2),
        Driver("D002", "Jamie", "easton", 2.1),
        Driver("D003", "Chris", "easton", 2.8),
        Driver("D004", "Taylor", "easton", 3.4),
        Driver("D005", "Jordan", "easton", 5.1),
        Driver("D006", "Morgan", "easton", 6.7),
    ]

    dispatch_order_marketplace(drivers)


if __name__ == "__main__":
    main()