from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any

RUN_STATES = [
    "offered",
    "accepted",
    "to_pickup",
    "arrived_pickup",
    "picked_up",
    "to_dropoff",
    "delivered",
    "returning",
    "closed",
    "exception"
]

@dataclass
class Run:
    run_id: str
    order_id: str
    driver_id: str
    merchant_id: str
    customer_id: str
    state: str
    created_at: datetime
    updated_at: datetime

def create_run(order: Dict[str, Any], driver: Dict[str, Any]) -> Run:
    return Run(
        run_id=f"run_{order['id']}",
        order_id=order["id"],
        driver_id=driver["id"],
        merchant_id=order["merchant_id"],
        customer_id=order["customer_id"],
        state="accepted",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

def update_state(run: Run, new_state: str) -> Run:
    if new_state not in RUN_STATES:
        raise ValueError("Invalid run state")

    run.state = new_state
    run.updated_at = datetime.utcnow()
    return run