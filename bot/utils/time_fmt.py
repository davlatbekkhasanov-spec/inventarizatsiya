from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from bot.config import get_settings
from bot.database.models import SessionStatus, WorkSession


def tz() -> ZoneInfo:
    try:
        return ZoneInfo(get_settings().tz)
    except Exception:
        return ZoneInfo("Asia/Tashkent")


def now_dt() -> datetime:
    return datetime.now(tz())


def fmt_hm(dt: datetime) -> str:
    return dt.astimezone(tz()).strftime("%H:%M")


def fmt_hms(dt: datetime) -> str:
    return dt.astimezone(tz()).strftime("%H:%M:%S")


def fmt_datetime(dt: datetime) -> str:
    return dt.astimezone(tz()).strftime("%d.%m.%Y %H:%M")


def elapsed_minutes(start: datetime, end: datetime | None = None) -> float:
    end = end or now_dt()
    if start.tzinfo is None:
        start = start.replace(tzinfo=tz())
    if end.tzinfo is None:
        end = end.replace(tzinfo=tz())
    return max(0.0, (end - start).total_seconds() / 60.0)


def fmt_minutes(m: float) -> str:
    m = max(0.0, float(m))
    whole = int(m)
    sec = int(round((m - whole) * 60))
    if whole >= 60:
        h, mins = divmod(whole, 60)
        if mins or sec:
            return f"{h} soat {mins} daq" + (f" {sec} son" if sec else "")
        return f"{h} soat"
    if whole and sec:
        return f"{whole} daq {sec} son"
    if whole:
        return f"{whole} daqiqa"
    return f"{sec} soniya"


def fmt_clock_from_seconds(sec: float) -> str:
    """Hub uchun qisqa: 75:00 yoki 1:15:00."""
    s = max(0, int(sec))
    h, rem = divmod(s, 3600)
    m, secs = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}"
    return f"{m}:{secs:02d}"


def session_work_seconds(ws: WorkSession, end: datetime | None = None) -> float:
    end = end or ws.finished_at or now_dt()
    if ws.started_at.tzinfo is None:
        start = ws.started_at.replace(tzinfo=tz())
    else:
        start = ws.started_at
    if end.tzinfo is None:
        end = end.replace(tzinfo=tz())
    total = max(0.0, (end - start).total_seconds())
    pause = float(ws.total_pause_sec or 0)
    if ws.paused_at and ws.status == SessionStatus.paused:
        p = ws.paused_at
        if p.tzinfo is None:
            p = p.replace(tzinfo=tz())
        pause += max(0.0, (now_dt() - p).total_seconds())
    return max(0.0, total - pause)


def session_pause_seconds(ws: WorkSession, end: datetime | None = None) -> float:
    end = end or ws.finished_at or now_dt()
    if ws.started_at.tzinfo is None:
        start = ws.started_at.replace(tzinfo=tz())
    else:
        start = ws.started_at
    if end.tzinfo is None:
        end = end.replace(tzinfo=tz())
    total = max(0.0, (end - start).total_seconds())
    work = session_work_seconds(ws, end)
    return max(0.0, total - work)
