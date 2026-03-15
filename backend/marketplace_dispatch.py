from typing import Dict, List

from backend.notification_engine import NotificationEngine

notification_engine = NotificationEngine()


def dispatch_order(order: Dict, drivers: List[Dict]):

    best_driver = None
    best_score = -999

    for driver in drivers:

        distance = driver.get("distance_to_pickup", 10)
        rating = driver.get("rating", 4.5)

        score = (10 - distance) + rating

        if score > best_score:
            best_score = score
            best_driver = driver

    if not best_driver:
        return None

    # send driver notification
    notification_engine.send_driver_offer(order, best_driver)

    # send customer update
    notification_engine.send_driver_assigned(
        order,
        best_driver,
        order["customer_email"],
    )

    return best_driver