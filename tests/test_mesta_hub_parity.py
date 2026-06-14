"""Mesta hub summary — bot va yordamchi ball mosligi."""

from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
YROOT = os.path.join(os.path.dirname(ROOT), "davlat-yordamchi-bot")
sys.path.insert(0, ROOT)

from bot.utils.norm import kaizen_points, time_saved_minutes

sys.path.insert(0, YROOT)
from daily_report_card import score_bot_summary


def fmt_clock_from_seconds(sec: float) -> str:
    s = max(0, int(sec))
    h, rem = divmod(s, 3600)
    m, secs = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{secs:02d}"
    return f"{m}:{secs:02d}"


def _hub_summary_from_norm(*, poz: int, work_sec: int, pause_sec: int, mpp: float = 3.0) -> str:
    work_min = work_sec / 60.0
    pause_min = pause_sec / 60.0
    saved_min = time_saved_minutes(poz, work_min, mpp, pause_minutes=pause_min)
    saved_sec = int(saved_min * 60)
    pts = kaizen_points(saved_min, mpp)
    ish = fmt_clock_from_seconds(work_sec)
    dam = fmt_clock_from_seconds(pause_sec)
    tejash = fmt_clock_from_seconds(saved_sec)
    return f"Mesta: poz {poz}, ish {ish}, dam {dam}, tejash {tejash}, bekor 0:00, kaizen {pts}"


def test_toxirov_sessions_match_bot():
    """12.06 Toxirov — 5 ta sessiya botdagi Kaizen yig'indisi."""
    cases = [
        (13, 7 * 60 + 49, 0, 10),
        (15, 9 * 60 + 33, 0, 11),
        (33, 13 * 60 + 30, 0, 28),
        (11, 5 * 60 + 16, 0, 9),
        (18, 7 * 60 + 34, 0, 15),
    ]
    total_pts = 0
    for poz, work_sec, pause_sec, expected in cases:
        saved_min = time_saved_minutes(poz, work_sec / 60.0, 3.0, pause_minutes=pause_sec / 60.0)
        bot_pts = kaizen_points(saved_min, 3.0)
        assert bot_pts == expected, (poz, bot_pts, expected)

        summary = _hub_summary_from_norm(poz=poz, work_sec=work_sec, pause_sec=pause_sec)
        hub_pts = score_bot_summary("mesta", summary)[0]
        assert hub_pts == expected, (summary, hub_pts, expected)
        total_pts += hub_pts

    assert total_pts == 73


def test_long_teja_sh_format():
    """≥1 soat tejash H:MM:SS — yordamchi to'g'ri o'qiydi (eski xato: 1:25 = 85 son)."""
    summary = _hub_summary_from_norm(poz=33, work_sec=13 * 60 + 30, pause_sec=0)
    assert "1:25:30" in summary or "tejash 1:" in summary
    pts, _ = score_bot_summary("mesta", summary)
    assert pts == 28, (summary, pts)


if __name__ == "__main__":
    test_toxirov_sessions_match_bot()
    test_long_teja_sh_format()
    print("PASS test_mesta_hub_parity")
