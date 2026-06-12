from __future__ import annotations

from bot.config import get_settings
from bot.database.models import WorkSession
from bot.utils.norm import NormStatus, time_saved_minutes, time_waste_minutes
from bot.utils.time_fmt import fmt_clock_from_seconds, session_pause_seconds, session_work_seconds


def compact_hub_summary(ws: WorkSession, norm: NormStatus) -> str:
    mpp = get_settings().minutes_per_position
    work_sec = int(session_work_seconds(ws))
    pause_sec = int(session_pause_seconds(ws))
    work_min = work_sec / 60.0
    pause_min = pause_sec / 60.0
    waste_sec = int(time_waste_minutes(ws.total_positions, work_min, mpp, pause_minutes=pause_min) * 60)
    saved_sec = int(time_saved_minutes(ws.total_positions, work_min, mpp, pause_minutes=pause_min) * 60)
    ish = fmt_clock_from_seconds(work_sec)
    dam = fmt_clock_from_seconds(pause_sec)
    tejash = fmt_clock_from_seconds(saved_sec)
    bekor = fmt_clock_from_seconds(waste_sec)
    return f"Mesta: poz {ws.total_positions}, ish {ish}, dam {dam}, tejash {tejash}, bekor {bekor}"
