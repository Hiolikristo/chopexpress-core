# backend/driver_profitability_engine.py

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional


@dataclass
class ProfitabilityBreakdown:
    order_id: str
    zone_id: str
    merchant_name: str
    offer_pay: float
    subtotal: float
    tip: float
    customer_fee: float
    total_miles: float
    deadhead_return_miles: float
    economic_miles: float
    trip_time_minutes: float
    prep_minutes: float
    merchant_delay_minutes: float
    delivery_minutes: float
    return_buffer_minutes: float
    gas_cost: float
    maintenance_cost: float
    depreciation_cost: float
    fixed_cost_per_order: float
    total_driver_cost: float
    net_profit: float
    hourly_rate: float
    effective_pay_per_mile: float