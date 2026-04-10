import random
from drivers import Driver

INITIAL_RADIUS = 2.5
RADIUS_STEP = 1.5
MAX_ROUNDS = 4
BATCH_SIZE = 4


def offer_attractiveness(pay, miles):
    """
    Calculates attractiveness score for an offer
    """
    pay_per_mile = pay / miles
    base_score = pay_per_mile / 2.0

    score = min(0.9, max(0.15, base_score))

    return score


def driver_accepts(driver, pay, miles):

    attractiveness = offer_attractiveness(pay, miles)

    roll = random.random()

    accepted = roll <= attractiveness

    return accepted, attractiveness, roll


def get_eligible_drivers(drivers, radius):

    eligible = [
        d for d in drivers
        if d.available and d.distance_to_restaurant <= radius
    ]

    eligible.sort(key=lambda d: d.distance_to_restaurant)

    return eligible[:BATCH_SIZE]


def dispatch_order_priced(drivers, pay, miles):

    radius = INITIAL_RADIUS

    for round_number in range(1, MAX_ROUNDS + 1):

        batch = get_eligible_drivers(drivers, radius)

        print(f"\n=== Dispatch Round {round_number} ===")
        print(f"Offer radius: {radius:.1f} miles")
        print(f"Offer pay: ${pay}")

        if not batch:
            print("No drivers in radius")
            radius += RADIUS_STEP
            continue

        print("\nOffer batch:")
        for d in batch:
            print(f"- {d.name} ({d.driver_id}) {d.distance_to_restaurant:.1f} miles")

        print("\nSimulating driver decisions...\n")

        for d in batch:

            accepted, prob, roll = driver_accepts(d, pay, miles)

            print(
                f"{d.name}: accept_prob={prob:.2f}, roll={roll:.2f}, accepted={accepted}"
            )

            if accepted:
                print(f"\nAssigned driver: {d.name}")
                return d

        print("\nNo driver accepted. Increasing radius...")
        radius += RADIUS_STEP

    print("\nOrder unclaimed — payout may need increase")
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

    pay = 8.50
    miles = 3.2

    dispatch_order_priced(drivers, pay, miles)


if __name__ == "__main__":
    main()