"""Bugungi hub push — deploydan keyin qayta yuborish."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import HubDayPush


async def save_today_push(session: AsyncSession, *, day: str, tg_id: int, summary: str) -> None:
    text = " ".join(str(summary or "").split())[:420]
    if not text or not tg_id:
        return
    stmt = (
        insert(HubDayPush)
        .values(
            day=day,
            tg_id=int(tg_id),
            summary=text,
            updated_at=datetime.now().astimezone(),
        )
        .on_conflict_do_update(
            index_elements=["day", "tg_id"],
            set_={"summary": text, "updated_at": datetime.now().astimezone()},
        )
    )
    await session.execute(stmt)


async def list_today_pushes(session: AsyncSession, day: str) -> list[tuple[int, str]]:
    rows = await session.scalars(select(HubDayPush).where(HubDayPush.day == day))
    return [(int(r.tg_id), str(r.summary)) for r in rows.all()]
