import random
from dataclasses import dataclass
from typing import List


@dataclass
class DriverLifecycleState:
    driver_id: str
    fatigue_level: float
    hours_online_today: float
    earnings_today: float
    active: bool
    home_zone: str
    current_zone: str


def initialize_lifecycle(drivers):
    lifecycle_states = []

    for d in drivers:
        lifecycle_states.append(
            DriverLifecycleState(
                driver_id=d.driver_id,
                fatigue_level=random.uniform(0.05, 0.25),
                hours_online_today=0.0,
                earnings_today=0.0,
                active=True,
                home_zone=d.zone,
                current_zone=d.zone,
            )
        )

    return lifecycle_states


def update_fatigue(state: DriverLifecycleState):
    fatigue_increase = random.uniform(0.02, 0.06)
    state.fatigue_level += fatigue_increase
    state.fatigue_level = min(1.0, state.fatigue_level)


def driver_shift_decision(state: DriverLifecycleState):
    """
    Determines if driver logs off for the day.
    """
    if state.earnings_today >= 180:
        if random.random() < 0.6:
            state.active = False

    if state.hours_online_today >= 10:
        state.active = False

    if state.fatigue_level > 0.85:
        state.active = False


def driver_zone_relocation(state: DriverLifecycleState, hot_zones: List[str]):
    """
    Drivers relocate toward zones with higher order volume.
    """
    if not hot_zones:
        return

    if random.random() < 0.25:
        state.current_zone = random.choice(hot_zones)


def apply_driver_lifecycle(lifecycle_states, hours_passed, hot_zones):
    for state in lifecycle_states:
        if not state.active:
            continue

        state.hours_online_today += hours_passed

        update_fatigue(state)

        driver_zone_relocation(state, hot_zones)

        driver_shift_decision(state)

    return lifecycle_states