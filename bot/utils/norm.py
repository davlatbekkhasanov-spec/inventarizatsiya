from __future__ import annotations

import math
from dataclasses import dataclass

from bot.config import get_settings


@dataclass(frozen=True)
class NormStatus:
    work_minutes: float
    pause_minutes: float
    expected: int
    actual: int
    on_track: bool
    shortage: int
    surplus: int
    waste_minutes: float

    @property
    def elapsed_minutes(self) -> float:
        return self.work_minutes

    @property
    def difference(self) -> int:
        """Ijobiy = kamchilik, manfiy = ortiqcha."""
        return self.expected - self.actual


def expected_positions(work_minutes: float, minutes_per_position: float | None = None) -> int:
    mpp = minutes_per_position or get_settings().minutes_per_position
    if mpp <= 0:
        mpp = 3.0
    return int(math.floor(work_minutes / mpp))


def norm_time_minutes(actual: int, minutes_per_position: float) -> float:
    mpp = minutes_per_position if minutes_per_position > 0 else 3.0
    return max(0.0, actual * mpp)


def time_saved_minutes(actual: int, work_minutes: float, minutes_per_position: float) -> float:
    return max(0.0, norm_time_minutes(actual, minutes_per_position) - work_minutes)


def kaizen_points(saved_minutes: float, minutes_per_position: float) -> int:
    mpp = minutes_per_position if minutes_per_position > 0 else 3.0
    return int(saved_minutes // mpp) if mpp > 0 else 0


def evaluate_norm(
    actual: int,
    work_minutes: float,
    *,
    pause_minutes: float = 0.0,
    minutes_per_position: float | None = None,
) -> NormStatus:
    mpp = minutes_per_position or get_settings().minutes_per_position
    if mpp <= 0:
        mpp = 3.0
    exp = expected_positions(work_minutes, mpp)
    shortage = max(0, exp - actual)
    surplus = max(0, actual - exp)
    waste = max(0.0, work_minutes - actual * mpp)
    return NormStatus(
        work_minutes=work_minutes,
        pause_minutes=pause_minutes,
        expected=exp,
        actual=actual,
        on_track=actual >= exp,
        shortage=shortage,
        surplus=surplus,
        waste_minutes=waste,
    )
