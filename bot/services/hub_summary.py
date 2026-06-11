from __future__ import annotations

from bot.config import get_settings
from bot.database.models import WorkSession
from bot.utils.norm import NormStatus, norm_time_minutes, time_saved_minutes
from bot.utils.time_fmt import fmt_clock_from_seconds, session_pause_seconds, session_work_seconds


def compact_hub_summary(ws: WorkSession, norm: NormStatus) -> str:
    mpp = get_settings().minutes_per_position
    work_sec = int(session_work_seconds(ws))
    pause_sec = int(session_pause_seconds(ws))
    waste_sec = int(norm.waste_minutes * 60)
    expected_sec = int(norm_time_minutes(ws.total_positions, mpp) * 60)
    saved_sec = int(time_saved_minutes(ws.total_positions, work_sec / 60.0, mpp) * 60)
    ish = fmt_clock_from_seconds(work_sec)
    dam = fmt_clock_from_seconds(pause_sec)
    tejash = fmt_clock_from_seconds(saved_sec)
    bekor = fmt_clock_from_seconds(waste_sec)
    return f"Mesta: poz {ws.total_positions}, ish {ish}, dam {dam}, tejash {tejash}, bekor {bekor}"
