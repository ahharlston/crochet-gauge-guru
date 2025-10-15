from dataclasses import dataclass
from typing import Optional

@dataclass
class Gauge:
    sts_per_in: Optional[float] = None
    rows_per_in: Optional[float] = None

def cast_on_for_circumference(circumference_in: float, sts_per_in: float, ease: float = 0.95, multiple: int = 1) -> int:
    base = circumference_in * max(sts_per_in, 1e-6) * ease
    return int(round(base / multiple) * multiple)

def rows_for_height(height_in: float, rows_per_in: float) -> int:
    return int(round(height_in * max(rows_per_in, 1e-6)))

def beanie_height_from_circumference(circ_in: float) -> float:
    return 0.36 * circ_in

def estimate_yardage(area_in2: float, sts_per_in: float, stitch_type: str = "dc") -> float:
    constants = {"sc": 48.0, "hdc": 42.0, "dc": 38.0, "tr": 34.0, "granny": 30.0}
    k = constants.get(stitch_type, 42.0)
    return (area_in2 * k) / max(sts_per_in, 1e-6)

def crown_increase_rounds(target_circ_in: float, sts_per_in: float, stitch_height_mult: float = 0.33) -> int:
    radius_in = target_circ_in / (2 * 3.14159)
    return max(1, int(round(radius_in / stitch_height_mult)))
