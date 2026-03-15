import time
import math
from dataclasses import dataclass
from typing import Dict, Any


def distance(a, b):
    ax, ay = a
    bx, by = b
    return math.sqrt((ax - bx) ** 2 + (ay - by) ** 2)


@dataclass
class DeliveryVerificationResult:
    order_id: str
    verified: bool
    method: str
    gps_distance: float
    timestamp: float
    notes: str


class DeliveryVerificationEngine:

    MAX_GPS_DISTANCE = 0.25  # miles

    def verify_delivery(
        self,
        driver_location: Dict[str, float],
        dropoff_location: Dict[str, float],
        verification_payload: Dict[str, Any],
    ) -> DeliveryVerificationResult:

        driver_xy = (driver_location["x"], driver_location["y"])
        drop_xy = (dropoff_location["x"], dropoff_location["y"])

        gps_distance = distance(driver_xy, drop_xy)

        method = verification_payload.get("method", "unknown")

        if gps_distance > self.MAX_GPS_DISTANCE:
            return DeliveryVerificationResult(
                order_id=verification_payload["order_id"],
                verified=False,
                method=method,
                gps_distance=gps_distance,
                timestamp=time.time(),
                notes="driver_not_at_dropoff_location",
            )

        if method == "photo":

            photo = verification_payload.get("photo")

            if not photo:
                return DeliveryVerificationResult(
                    order_id=verification_payload["order_id"],
                    verified=False,
                    method=method,
                    gps_distance=gps_distance,
                    timestamp=time.time(),
                    notes="missing_photo",
                )

            return DeliveryVerificationResult(
                order_id=verification_payload["order_id"],
                verified=True,
                method="leave_at_door_photo",
                gps_distance=gps_distance,
                timestamp=time.time(),
                notes="photo_verified",
            )

        elif method == "handoff":

            pin = verification_payload.get("customer_pin")

            if not pin:
                return DeliveryVerificationResult(
                    order_id=verification_payload["order_id"],
                    verified=False,
                    method=method,
                    gps_distance=gps_distance,
                    timestamp=time.time(),
                    notes="missing_customer_pin",
                )

            return DeliveryVerificationResult(
                order_id=verification_payload["order_id"],
                verified=True,
                method="customer_pin_handoff",
                gps_distance=gps_distance,
                timestamp=time.time(),
                notes="handoff_confirmed",
            )

        else:

            return DeliveryVerificationResult(
                order_id=verification_payload["order_id"],
                verified=False,
                method=method,
                gps_distance=gps_distance,
                timestamp=time.time(),
                notes="unknown_verification_method",
            )


def main():

    engine = DeliveryVerificationEngine()

    driver_location = {"x": 10.0, "y": 5.0}
    dropoff_location = {"x": 10.1, "y": 5.05}

    payload = {
        "order_id": "O1",
        "method": "photo",
        "photo": "photo_hash_123"
    }

    result = engine.verify_delivery(driver_location, dropoff_location, payload)

    print(result)


if __name__ == "__main__":
    main()