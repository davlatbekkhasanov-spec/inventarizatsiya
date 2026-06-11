from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramAPIError

from bot.config import get_settings
from bot.database.models import SessionStatus, WorkSession
from bot.database.session import require_session_local
from bot.services.mesta import get_open_session
from bot.utils.time_fmt import session_pause_seconds, session_work_seconds
from bot.utils.visual import clock_box, fmt_stopwatch

log = logging.getLogger(__name__)

_SEP = "━━━━━━━━━━━━━━━━━"
_TICK_SEC = 1.0
_ACTIVE = (SessionStatus.active, SessionStatus.paused)
_RUN_FRAMES = ("▶️", "🔸", "▶️", "🔹")


@dataclass
class _TimerEntry:
    chat_id: int
    message_id: int
    name: str
    tick: int = 0
    task: asyncio.Task | None = field(default=None, repr=False)


class LiveTimerService:
    def __init__(self) -> None:
        self._entries: dict[int, _TimerEntry] = {}

    def _render(self, ws: WorkSession, name: str, *, tick: int) -> str:
        mpp = get_settings().minutes_per_position
        work_sec = session_work_seconds(ws)
        pause_sec = session_pause_seconds(ws)
        clock = fmt_stopwatch(work_sec)

        if ws.status == SessionStatus.paused:
            header = "⏸ <b>PAUZADA</b>"
            sub = "Sekundomer to'xtatilgan"
        else:
            pulse = _RUN_FRAMES[tick % len(_RUN_FRAMES)]
            header = f"{pulse} <b>MESTA — ONLAYN SEKUNDOMER</b> {pulse}"
            sub = "Ish vaqti hisoblanmoqda..."

        lines = [
            header,
            "",
            f"👤 <b>{name}</b>",
            clock_box(clock),
            f"<i>{sub}</i>",
        ]
        if pause_sec >= 1:
            lines.append(f"⏸ Pauza: <b>{fmt_stopwatch(pause_sec)}</b>")
        lines.extend(
            [
                "",
                _SEP,
                f"📐 Norma: <b>1 poz = {mpp:g} daq</b>",
                "<i>Tayyor bo'lsa «Yakunlash» bosing</i>",
            ]
        )
        return "\n".join(lines)

    async def _edit(self, bot: Bot, entry: _TimerEntry, text: str) -> None:
        try:
            await bot.edit_message_text(
                text,
                chat_id=entry.chat_id,
                message_id=entry.message_id,
            )
        except TelegramBadRequest as exc:
            if "message is not modified" not in str(exc).lower():
                raise
        except TelegramAPIError as exc:
            log.warning("timer edit failed uid chat=%s: %s", entry.chat_id, exc)

    async def _loop(self, bot: Bot, tg_id: int) -> None:
        try:
            while True:
                entry = self._entries.get(tg_id)
                if not entry:
                    return

                factory = require_session_local()
                async with factory() as session:
                    ws = await get_open_session(session, tg_id)

                if not ws or ws.status not in _ACTIVE:
                    self._entries.pop(tg_id, None)
                    return

                text = self._render(ws, entry.name, tick=entry.tick)
                await self._edit(bot, entry, text)
                entry.tick += 1
                await asyncio.sleep(_TICK_SEC)
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("live timer loop error tg_id=%s", tg_id)

    async def start(
        self,
        bot: Bot,
        *,
        tg_id: int,
        chat_id: int,
        message_id: int,
        name: str,
        ws: WorkSession,
    ) -> None:
        await self.stop(tg_id)
        entry = _TimerEntry(chat_id=chat_id, message_id=message_id, name=name)
        self._entries[tg_id] = entry
        await self._edit(bot, entry, self._render(ws, name, tick=0))
        entry.task = asyncio.create_task(self._loop(bot, tg_id))

    async def refresh(self, bot: Bot, tg_id: int) -> None:
        entry = self._entries.get(tg_id)
        if not entry:
            return
        factory = require_session_local()
        async with factory() as session:
            ws = await get_open_session(session, tg_id)
        if not ws or ws.status not in _ACTIVE:
            await self.stop(tg_id)
            return
        await self._edit(bot, entry, self._render(ws, entry.name, tick=entry.tick))

    async def stop(self, tg_id: int, *, bot: Bot | None = None, final_text: str | None = None) -> None:
        entry = self._entries.pop(tg_id, None)
        if not entry:
            return
        if entry.task and not entry.task.done():
            entry.task.cancel()
            try:
                await entry.task
            except asyncio.CancelledError:
                pass
        if bot and final_text:
            await self._edit(bot, entry, final_text)

    async def stop_with_work_time(self, bot: Bot, tg_id: int, *, header: str) -> None:
        entry = self._entries.get(tg_id)
        if not entry:
            return
        factory = require_session_local()
        async with factory() as session:
            ws = await get_open_session(session, tg_id)
        work = fmt_stopwatch(session_work_seconds(ws)) if ws else "00:00"
        final = f"{header}\n\n{clock_box(work)}"
        await self.stop(tg_id, bot=bot, final_text=final)


live_timer = LiveTimerService()
