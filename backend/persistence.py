from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data_store"
DATA_FILE = DATA_DIR / "platform_state.json"


def _json_default(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def ensure_data_store() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        default_state = {
            "drivers": {},
            "customers": {},
            "merchants": {},
            "menu_items": {},
            "orders": {},
            "counters": {
                "driver": 0,
                "customer": 0,
                "merchant": 0,
                "menu_item": 0,
                "order": 0,
            },
        }
        save_state(default_state)


def load_state() -> Dict[str, Any]:
    ensure_data_store()
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state: Dict[str, Any]) -> None:
    ensure_data_store()
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, default=_json_default)


def next_id(state: Dict[str, Any], key: str, prefix: str) -> str:
    state["counters"][key] += 1
    return f"{prefix}-{state['counters'][key]:06d}"