import random
from typing import Dict, List


class Driver:
    def __init__(self, driver_id: int):
        self.driver_id = driver_id
        self.platform = "competitor"
        self.daily_income = 0
        self.satisfaction = 0.5


def calculate_satisfaction(income: float, hours: float) -> float:
    hourly = income / max(hours, 1)

    if hourly >= 25:
        return 0.9
    elif hourly >= 20:
        return 0.75
    elif hourly >= 15:
        return 0.55
    else:
        return 0.35


def migration_probability(satisfaction: float) -> float:
    """
    Probability driver leaves competitor and joins ChopExpress
    """

    if satisfaction < 0.4:
        return 0.6
    elif satisfaction < 0.6:
        return 0.35
    else:
        return 0.1


def run_driver_migration(drivers: List[Driver]) -> Dict:
    migrated = 0

    for driver in drivers:

        income = random.uniform(80, 180)
        hours = random.uniform(4, 8)

        satisfaction = calculate_satisfaction(income, hours)

        driver.daily_income = income
        driver.satisfaction = satisfaction

        prob = migration_probability(satisfaction)

        if random.random() < prob:
            driver.platform = "chopexpress"
            migrated += 1

    return {
        "total_drivers": len(drivers),
        "migrated": migrated,
        "migration_rate": migrated / len(drivers)
    }


def generate_driver_pool(n: int = 200):
    return [Driver(i) for i in range(n)]


if __name__ == "__main__":

    drivers = generate_driver_pool(300)

    result = run_driver_migration(drivers)

    print("Driver Migration Simulation")
    print("---------------------------")
    print(f"Drivers simulated: {result['total_drivers']}")
    print(f"Migrated to ChopExpress: {result['migrated']}")
    print(f"Migration rate: {result['migration_rate']:.2f}")