from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import get_settings
from bot.services.stats import build_period_report, format_report

router = Router(name="admin")


def _is_admin(user_id: int) -> bool:
    return user_id in get_settings().admin_id_set()


@router.message(Command("stat_today"))
async def stat_today(message: Message, db: AsyncSession) -> None:
    uid = message.from_user.id if message.from_user else 0
    if not _is_admin(uid):
        return await message.answer("⛔ Faqat admin.")
    report = await build_period_report(db, days=None, title="Bugungi statistika")
    await message.answer(format_report(report))


@router.message(Command("stat_week"))
async def stat_week(message: Message, db: AsyncSession) -> None:
    uid = message.from_user.id if message.from_user else 0
    if not _is_admin(uid):
        return await message.answer("⛔ Faqat admin.")
    report = await build_period_report(db, days=7, title="Haftalik statistika")
    await message.answer(format_report(report))


@router.message(Command("stat_month"))
async def stat_month(message: Message, db: AsyncSession) -> None:
    uid = message.from_user.id if message.from_user else 0
    if not _is_admin(uid):
        return await message.answer("⛔ Faqat admin.")
    report = await build_period_report(db, days=30, title="Oylik statistika")
    await message.answer(format_report(report))
