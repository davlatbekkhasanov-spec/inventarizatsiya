from __future__ import annotations

import math
from dataclasses import dataclass

from bot.config import get_settings


@dataclass(frozen=True)
class NormStatus:
    elapsed_minutes: float
    expected: int
    actual: int
    on_track: bool
    shortage: int
    surplus: int

    @property
    def difference(self) -> int:
        """Ijobiy = kamchilik, manfiy = ortiqcha."""
        return self.expected - self.actual


def expected_positions(elapsed_minutes: float, minutes_per_position: float | None = None) -> int:
    mpp = minutes_per_position or get_settings().minutes_per_position
    if mpp <= 0:
        mpp = 4.0
    return int(math.floor(elapsed_minutes / mpp))


def evaluate_norm(actual: int, elapsed_minutes: float, minutes_per_position: float | None = None) -> NormStatus:
    exp = expected_positions(elapsed_minutes, minutes_per_position)
    shortage = max(0, exp - actual)
    surplus = max(0, actual - exp)
    return NormStatus(
        elapsed_minutes=elapsed_minutes,
        expected=exp,
        actual=actual,
        on_track=actual >= exp,
        shortage=shortage,
        surplus=surplus,
    )
