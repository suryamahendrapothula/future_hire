"""Miscellaneous helpers."""

import re
import uuid
from datetime import datetime


def new_id(prefix: str = "") -> str:
    uid = uuid.uuid4().hex
    return f"{prefix}{uid}" if prefix else uid


def utcnow_iso() -> str:
    return datetime.utcnow().isoformat()


def safe_filename(name: str) -> str:
    return re.sub(r"[^\w.\-]+", "_", name).strip("_") or "resume"


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def average(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)
