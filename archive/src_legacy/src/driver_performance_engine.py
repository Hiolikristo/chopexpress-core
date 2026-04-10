"""
ChopExpress Driver Performance Engine
V1 Locked Governance System

Tracks:
- Acceptance rate
- Completion rate
- Driver rating
- Violation points
- Recovery via completed deliveries

Recovery Rules:
- Minor violation recovery: 30 successful deliveries
- Complaint recovery: 50 successful deliveries
"""

from collections import deque


MIN_ACCEPTANCE_RATE = 0.35
MIN_COMPLETION_RATE = 0.92
MIN_DRIVER_RATING = 4.2

MINOR_RECOVERY_DELIVERIES = 30
COMPLAINT_RECOVERY_DELIVERIES = 50

WINDOW_OFFERS = 50
WINDOW_DELIVERIES = 50
WINDOW_RATINGS = 50


class DriverPerformance:

    def __init__(self, driver_id):

        self.driver_id = driver_id

        self.offer_history = deque(maxlen=WINDOW_OFFERS)
        self.delivery_history = deque(maxlen=WINDOW_DELIVERIES)
        self.rating_history = deque(maxlen=WINDOW_RATINGS)

        self.violation_points = 0

        self.recovery_counter = 0

        self.total_offers = 0
        self.total_accepts = 0

    # ---------------------------
    # Offer Tracking
    # ---------------------------

    def record_offer(self, accepted: bool):

        self.offer_history.append(accepted)

        self.total_offers += 1

        if accepted:
            self.total_accepts += 1

    def acceptance_rate(self):

        if not self.offer_history:
            return 1.0

        return sum(self.offer_history) / len(self.offer_history)

    # ---------------------------
    # Delivery Tracking
    # ---------------------------

    def record_delivery(self, completed: bool):

        self.delivery_history.append(completed)

        if not completed:
            self.add_minor_violation()

        else:
            self.process_recovery()

    def completion_rate(self):

        if not self.delivery_history:
            return 1.0

        return sum(self.delivery_history) / len(self.delivery_history)

    # ---------------------------
    # Rating Tracking
    # ---------------------------

    def record_rating(self, rating: float):

        self.rating_history.append(rating)

        if rating < 3:
            self.add_complaint()

    def average_rating(self):

        if not self.rating_history:
            return 5.0

        return sum(self.rating_history) / len(self.rating_history)

    # ---------------------------
    # Violations
    # ---------------------------

    def add_minor_violation(self):

        self.violation_points += 1
        self.recovery_counter = 0

    def add_complaint(self):

        self.violation_points += 2
        self.recovery_counter = 0

    # ---------------------------
    # Recovery
    # ---------------------------

    def process_recovery(self):

        if self.violation_points == 0:
            return

        self.recovery_counter += 1

        if self.recovery_counter >= MINOR_RECOVERY_DELIVERIES:

            self.violation_points -= 1
            self.recovery_counter = 0

    # ---------------------------
    # Performance Check
    # ---------------------------

    def performance_status(self):

        acceptance = self.acceptance_rate()
        completion = self.completion_rate()
        rating = self.average_rating()

        status = {
            "driver_id": self.driver_id,
            "acceptance_rate": round(acceptance, 3),
            "completion_rate": round(completion, 3),
            "rating": round(rating, 2),
            "violation_points": self.violation_points
        }

        if completion < MIN_COMPLETION_RATE:
            status["warning"] = "Low completion rate"

        if rating < MIN_DRIVER_RATING:
            status["warning"] = "Low customer rating"

        return status


# ---------------------------------
# Example Testing
# ---------------------------------

if __name__ == "__main__":

    driver = DriverPerformance("D001")

    # simulate offers
    for _ in range(40):
        driver.record_offer(True)

    for _ in range(10):
        driver.record_offer(False)

    # simulate deliveries
    for _ in range(45):
        driver.record_delivery(True)

    driver.record_delivery(False)

    # simulate ratings
    ratings = [5, 5, 4, 5, 4, 5, 5, 3]

    for r in ratings:
        driver.record_rating(r)

    print(driver.performance_status())