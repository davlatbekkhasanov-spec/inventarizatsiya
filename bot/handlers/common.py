from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.config import get_settings
from bot.keyboards.worker import worker_idle_kb

router = Router(name="common")


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    mpp = get_settings().minutes_per_position
    await message.answer(
        "👋 <b>Mesta Nazorat Bot</b>\n\n"
        f"Mesta qo'yish jarayoni — norma: <b>1 pozitsiya = {mpp:g} daqiqa</b>.\n\n"
        "<b>Jarayon:</b>\n"
        "▶️ Boshlash → ish vaqti hisoblanadi\n"
        "⏸ Pauza → vaqt to'xtaydi\n"
        "🏁 Yakunlash → nechta pozitsiya qilganingizni kiriting\n\n"
        "Bot normaga tushganingizni yoki bekor sarflangan vaqtni hisoblab beradi.\n\n"
        "Admin: /stat_today · /stat_week · /stat_month",
        reply_markup=worker_idle_kb(),
    )
