from dataclasses import dataclass


@dataclass
class Driver:
    driver_id: str
    name: str
    zone: str
    distance_to_restaurant: float
    available: bool = True