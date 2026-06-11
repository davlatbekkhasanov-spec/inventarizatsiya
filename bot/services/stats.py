from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from bot.database.models import SessionStatus, User, WorkSession
from bot.utils.time_fmt import now_dt, session_work_seconds, tz


@dataclass
class WorkerStat:
    name: str
    positions: int
    sessions: int
    avg_min_per_position: float | None


@dataclass
class PeriodReport:
    title: str
    since: datetime
    until: datetime
    total_positions: int
    total_sessions: int
    avg_min_per_position: float | None
    best: WorkerStat | None
    worst: WorkerStat | None
    workers: list[WorkerStat]


def _period_start(days: int | None) -> datetime:
    now = now_dt()
    if days is None:
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return start
    return now - timedelta(days=days)


async def build_period_report(session: AsyncSession, *, days: int | None, title: str) -> PeriodReport:
    since = _period_start(days)
    until = now_dt()

    q = (
        select(WorkSession)
        .where(
            WorkSession.status == SessionStatus.finished,
            WorkSession.finished_at.is_not(None),
            WorkSession.finished_at >= since,
            WorkSession.finished_at <= until,
        )
        .options(joinedload(WorkSession.user))
    )
    sessions = (await session.scalars(q)).all()

    total_positions = sum(s.total_positions for s in sessions)
    per_user: dict[int, dict] = {}

    for ws in sessions:
        uid = ws.user_id
        if uid not in per_user:
            per_user[uid] = {
                "name": ws.user.full_name if ws.user else "?",
                "positions": 0,
                "sessions": 0,
                "minutes": 0.0,
            }
        per_user[uid]["positions"] += ws.total_positions
        per_user[uid]["sessions"] += 1
        if ws.finished_at and ws.started_at:
            per_user[uid]["minutes"] += session_work_seconds(ws) / 60.0

    workers: list[WorkerStat] = []
    for data in per_user.values():
        pos = data["positions"]
        avg = (data["minutes"] / pos) if pos > 0 else None
        workers.append(
            WorkerStat(
                name=data["name"],
                positions=pos,
                sessions=data["sessions"],
                avg_min_per_position=avg,
            )
        )

    workers.sort(key=lambda w: (-w.positions, w.name))

    best = None
    worst = None
    rated = [w for w in workers if w.avg_min_per_position is not None and w.positions > 0]
    if rated:
        best = min(rated, key=lambda w: w.avg_min_per_position or 9999)
        worst = max(rated, key=lambda w: w.avg_min_per_position or 0)

    total_min = sum(d["minutes"] for d in per_user.values())
    global_avg = (total_min / total_positions) if total_positions > 0 else None

    return PeriodReport(
        title=title,
        since=since,
        until=until,
        total_positions=total_positions,
        total_sessions=len(sessions),
        avg_min_per_position=global_avg,
        best=best,
        worst=worst,
        workers=workers,
    )


def format_report(report: PeriodReport) -> str:
    lines = [
        f"📈 <b>{report.title}</b>",
        f"<i>{report.since.astimezone(tz()).strftime('%d.%m.%Y')} — "
        f"{report.until.astimezone(tz()).strftime('%d.%m.%Y %H:%M')}</i>\n",
        f"Umumiy pozitsiyalar: <b>{report.total_positions}</b>",
        f"Sessiyalar: <b>{report.total_sessions}</b>",
    ]
    if report.avg_min_per_position is not None:
        lines.append(f"O'rtacha pozitsiya vaqti: <b>{report.avg_min_per_position:.1f} daq</b>")
    else:
        lines.append("O'rtacha pozitsiya vaqti: <b>—</b>")

    if report.best:
        lines.append(
            f"\n🏆 Eng samarali: <b>{report.best.name}</b> "
            f"({report.best.avg_min_per_position:.1f} daq/poz, {report.best.positions} ta)"
        )
    if report.worst and report.worst.name != (report.best.name if report.best else ""):
        lines.append(
            f"🐢 Eng sekin: <b>{report.worst.name}</b> "
            f"({report.worst.avg_min_per_position:.1f} daq/poz, {report.worst.positions} ta)"
        )

    if report.workers:
        lines.append("\n<b>Xodimlar:</b>")
        for i, w in enumerate(report.workers[:15], 1):
            avg = f"{w.avg_min_per_position:.1f} daq" if w.avg_min_per_position is not None else "—"
            lines.append(f"{i}. {w.name} — {w.positions} poz · {avg}")
        if len(report.workers) > 15:
            lines.append(f"<i>… va yana {len(report.workers) - 15} kishi</i>")

    return "\n".join(lines)
