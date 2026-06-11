from __future__ import annotations

from bot.database.models import WorkSession
from bot.utils.norm import NormStatus
from bot.utils.time_fmt import fmt_clock_from_seconds, session_pause_seconds, session_work_seconds


def compact_hub_summary(ws: WorkSession, norm: NormStatus) -> str:
    work_sec = int(session_work_seconds(ws))
    pause_sec = int(session_pause_seconds(ws))
    waste_sec = int(norm.waste_minutes * 60)
    expected_sec = int(ws.total_positions) * 3 * 60
    saved_sec = max(0, expected_sec - work_sec)
    ish = fmt_clock_from_seconds(work_sec)
    dam = fmt_clock_from_seconds(pause_sec)
    tejash = fmt_clock_from_seconds(saved_sec)
    bekor = fmt_clock_from_seconds(waste_sec)
    return f"Mesta: poz {ws.total_positions}, ish {ish}, dam {dam}, tejash {tejash}, bekor {bekor}"
