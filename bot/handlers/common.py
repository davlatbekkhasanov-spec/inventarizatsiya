from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.keyboards.worker import worker_idle_kb

router = Router(name="common")


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    await message.answer(
        "👋 <b>Mesta Nazorat Bot</b>\n\n"
        "Mesta qo'yish jarayonini kuzatish va Kaizen normasi (1 poz = 4 daq) bo'yicha nazorat.\n\n"
        "<b>Buyruqlar:</b>\n"
        "/start_mesta — ishni boshlash\n"
        "/add 10 — pozitsiya qo'shish\n"
        "/finish_mesta — yakunlash\n"
        "/active_mesta — aktiv xodimlar\n\n"
        "Admin: /stat_today · /stat_week · /stat_month",
        reply_markup=worker_idle_kb(),
    )
