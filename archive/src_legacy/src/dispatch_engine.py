from drivers import Driver

INITIAL_RADIUS = 2.5
RADIUS_STEP = 1.5
MAX_ROUNDS = 4
BATCH_SIZE = 4


def get_eligible_drivers(drivers, radius):

    eligible = [
        d for d in drivers
        if d.available and d.distance_to_restaurant <= radius
    ]

    eligible.sort(key=lambda d: d.distance_to_restaurant)

    return eligible[:BATCH_SIZE]


def dispatch_order(drivers):

    radius = INITIAL_RADIUS

    for round_number in range(1, MAX_ROUNDS + 1):

        batch = get_eligible_drivers(drivers, radius)

        if batch:

            print("\nRound", round_number)
            print("Radius:", radius, "miles")

            print("\nEligible drivers:")

            for d in batch:
                print(d.name, "-", d.distance_to_restaurant, "miles")

            chosen = batch[0]

            print("\nAssigned driver:", chosen.name)

            return chosen

        radius += RADIUS_STEP

    print("\nNo driver found")

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

    dispatch_order(drivers)


if __name__ == "__main__":
    main()