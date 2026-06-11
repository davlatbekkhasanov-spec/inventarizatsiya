from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from bot.database.models import PositionLog, SessionStatus, User, WorkSession
from bot.utils.norm import NormStatus, evaluate_norm
from bot.utils.time_fmt import elapsed_minutes, now_dt


@dataclass
class SessionView:
    session: WorkSession
    user: User
    norm: NormStatus


async def get_or_create_user(session: AsyncSession, telegram_id: int, full_name: str) -> User:
    user = await session.scalar(select(User).where(User.telegram_id == telegram_id))
    if user:
        if full_name and user.full_name != full_name:
            user.full_name = full_name
        return user
    user = User(telegram_id=telegram_id, full_name=full_name or "Noma'lum")
    session.add(user)
    await session.flush()
    return user


async def get_active_session(session: AsyncSession, telegram_id: int) -> WorkSession | None:
    q = (
        select(WorkSession)
        .join(User)
        .where(User.telegram_id == telegram_id, WorkSession.status == SessionStatus.active)
        .options(joinedload(WorkSession.user))
    )
    return await session.scalar(q)


async def start_session(session: AsyncSession, telegram_id: int, full_name: str) -> tuple[WorkSession | None, str]:
    existing = await get_active_session(session, telegram_id)
    if existing:
        return None, "Sizda allaqachon aktiv mesta bor. Avval /finish_mesta bosing."

    user = await get_or_create_user(session, telegram_id, full_name)
    ws = WorkSession(user_id=user.id, started_at=now_dt(), status=SessionStatus.active, total_positions=0)
    session.add(ws)
    await session.flush()
    ws.user = user
    return ws, ""


async def add_positions(
    session: AsyncSession, telegram_id: int, count: int
) -> tuple[SessionView | None, str]:
    if count <= 0:
        return None, "Pozitsiya soni 0 dan katta bo'lishi kerak."

    ws = await get_active_session(session, telegram_id)
    if not ws:
        return None, "Aktiv mesta yo'q. /start_mesta bilan boshlang."

    ws.total_positions += count
    session.add(
        PositionLog(session_id=ws.id, count=count, total_after=ws.total_positions, logged_at=now_dt())
    )
    await session.flush()
    mins = elapsed_minutes(ws.started_at)
    norm = evaluate_norm(ws.total_positions, mins)
    return SessionView(session=ws, user=ws.user, norm=norm), ""


async def finish_session(session: AsyncSession, telegram_id: int) -> tuple[SessionView | None, str]:
    ws = await get_active_session(session, telegram_id)
    if not ws:
        return None, "Aktiv mesta yo'q."

    finished = now_dt()
    ws.finished_at = finished
    ws.status = SessionStatus.finished
    mins = elapsed_minutes(ws.started_at, finished)
    norm = evaluate_norm(ws.total_positions, mins)
    await session.flush()
    return SessionView(session=ws, user=ws.user, norm=norm), ""


async def list_active_sessions(session: AsyncSession) -> list[SessionView]:
    q = (
        select(WorkSession)
        .where(WorkSession.status == SessionStatus.active)
        .options(joinedload(WorkSession.user))
        .order_by(WorkSession.started_at.asc())
    )
    rows = (await session.scalars(q)).all()
    out: list[SessionView] = []
    for ws in rows:
        norm = evaluate_norm(ws.total_positions, elapsed_minutes(ws.started_at))
        out.append(SessionView(session=ws, user=ws.user, norm=norm))
    return out


async def list_active_for_monitor(session: AsyncSession) -> list[SessionView]:
    return await list_active_sessions(session)


async def mark_alerted(session: AsyncSession, ws: WorkSession) -> None:
    ws.last_alert_at = now_dt()
    await session.flush()
