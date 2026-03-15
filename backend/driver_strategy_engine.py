from dataclasses import dataclass
from typing import Dict, List

from backend.dispatch_engine import DispatchDriver
from backend.market_pressure_engine import ZonePressureState


@dataclass
class DriverStrategyDecision:
    driver_id: str
    action: str
    from_zone: str
    to_zone: str
    reason: str
    attractiveness_gain: float


def apply_driver_strategy(
    drivers: List[DispatchDriver],
    pressure_map: Dict[str, ZonePressureState],
) -> List[DriverStrategyDecision]:
    decisions: List[DriverStrategyDecision] = []

    if not pressure_map:
        return decisions

    for driver in drivers:
        if not driver.is_dispatch_active:
            continue

        current_zone = driver.current_zone
        if current_zone not in pressure_map:
            continue

        current_state = pressure_map[current_zone]

        candidate_zones = [
            zone for zone in pressure_map.keys()
            if zone != current_zone
        ]

        if not candidate_zones:
            continue

        best_zone = max(
            candidate_zones,
            key=lambda zone: pressure_map[zone].driver_attraction_score,
        )

        best_state = pressure_map[best_zone]

        attractiveness_gain = round(
            best_state.driver_attraction_score - current_state.driver_attraction_score,
            2,
        )

        fatigue_penalty = round(driver.fatigue_score * 2.0, 2)
        move_threshold = 0.60 + fatigue_penalty

        # Strong urge to leave weak zones for much better nearby zones
        if attractiveness_gain >= move_threshold and best_state.is_hot_zone:
            old_zone = driver.current_zone
            driver.current_zone = best_zone

            decisions.append(
                DriverStrategyDecision(
                    driver_id=driver.driver_id,
                    action="reposition",
                    from_zone=old_zone,
                    to_zone=best_zone,
                    reason="chasing stronger earnings opportunity",
                    attractiveness_gain=attractiveness_gain,
                )
            )
            continue

        # If current zone is hot, driver stays put
        if current_state.is_hot_zone:
            decisions.append(
                DriverStrategyDecision(
                    driver_id=driver.driver_id,
                    action="hold",
                    from_zone=current_zone,
                    to_zone=current_zone,
                    reason="holding strong zone position",
                    attractiveness_gain=0.0,
                )
            )
            continue

        # Moderate repositioning for decent gains
        if attractiveness_gain >= 0.35 and driver.fatigue_score < 0.45:
            old_zone = driver.current_zone
            driver.current_zone = best_zone

            decisions.append(
                DriverStrategyDecision(
                    driver_id=driver.driver_id,
                    action="soft_reposition",
                    from_zone=old_zone,
                    to_zone=best_zone,
                    reason="incremental zone improvement",
                    attractiveness_gain=attractiveness_gain,
                )
            )
            continue

        decisions.append(
            DriverStrategyDecision(
                driver_id=driver.driver_id,
                action="idle_hold",
                from_zone=current_zone,
                to_zone=current_zone,
                reason="no materially better nearby opportunity",
                attractiveness_gain=0.0,
            )
        )

    return decisions