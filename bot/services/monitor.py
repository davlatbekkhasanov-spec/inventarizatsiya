from __future__ import annotations

import asyncio
import logging

from aiogram import Bot

from bot.config import get_settings
from bot.database.session import require_session_local
from bot.services.mesta import list_active_for_monitor, mark_alerted
from bot.services.notify import send_group, work_reminder_message

log = logging.getLogger(__name__)


async def run_norm_monitor(bot: Bot) -> None:
    settings = get_settings()
    interval = max(60, int(settings.monitor_interval_minutes) * 60)
    log.info("Work reminder monitor started (every %s min)", settings.monitor_interval_minutes)

    while True:
        try:
            await _check_once(bot, settings.monitor_interval_minutes)
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("Monitor tick failed")
        await asyncio.sleep(interval)


async def _check_once(bot: Bot, cooldown_minutes: int) -> None:
    from bot.utils.time_fmt import now_dt

    factory = require_session_local()
    async with factory() as session:
        views = await list_active_for_monitor(session)
        now = now_dt()
        for view in views:
            ws = view.session
            if ws.last_alert_at:
                delta = (now - ws.last_alert_at).total_seconds() / 60.0
                if delta < cooldown_minutes:
                    continue
            text = work_reminder_message(name=view.user.full_name, work_minutes=view.norm.work_minutes)
            if await send_group(bot, text):
                await mark_alerted(session, ws)
        await session.commit()
