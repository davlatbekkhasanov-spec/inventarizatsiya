from __future__ import annotations

from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import get_settings
from bot.database.models import SessionStatus
from bot.handlers.states import FinishStates
from bot.keyboards.worker import worker_idle_kb
from bot.keyboards.worker import worker_active_kb, worker_paused_kb
from bot.services.live_timer import live_timer
from bot.services.mesta import get_open_session

router = Router(name="common")


@router.message(Command("start"))
async def cmd_start(message: Message, bot: Bot, db: AsyncSession, state: FSMContext) -> None:
    uid = message.from_user.id if message.from_user else 0
    ws = await get_open_session(db, uid)

    mpp = get_settings().minutes_per_position

    # /start bosilganda ham mavjud ishni bekor qilmaymiz:
    # aksi holda “Ochiq inventarizatsiya yo‘q” chiqishi mumkin.
    if ws:
        if ws.status == SessionStatus.awaiting_positions:
            await state.set_state(FinishStates.waiting_positions)
            await state.update_data(session_id=ws.id)
            await message.answer(
                "🏁 <b>Yakunlash davom etmoqda</b>\n\n"
                "Nechta pozitsiya qildingiz?\n"
                "Faqat raqam yuboring yoki /start bilan bekor qiling.",
                reply_markup=worker_idle_kb(),
            )
            return

        status = "⏸ pauzada" if ws.status == SessionStatus.paused else "▶️ ishlayapti"
        kb = worker_paused_kb() if ws.status == SessionStatus.paused else worker_active_kb()
        await message.answer(
            f"⚠️ <b>Sizda ochiq inventarizatsiya bor</b> ({status})\n\n"
            f"Boshlangan: <b>{ws.started_at:%H:%M}</b>\n\n"
            "Davom eting, «Yakunlash» tugmasini bosing yoki yangi ish uchun /start yuboring.",
            reply_markup=kb,
        )
        return

    await message.answer(
        "👋 <b>Inventarizatsiya Nazorat Bot</b>\n\n"
        f"Inventarizatsiya jarayoni — norma: <b>1 pozitsiya = {mpp:g} daqiqa</b>.\n\n"
        "<b>Jarayon:</b>\n"
        "▶️ Boshlash → onlayn sekundomer ishlaydi\n"
        "⏸ Pauza → vaqt to'xtaydi\n"
        "🏁 Yakunlash → nechta pozitsiya qilganingizni kiriting\n\n"
        "Bot normaga tushganingizni yoki bekor sarflangan vaqtni hisoblab beradi.\n\n"
        "Admin: /stat_today · /stat_week · /stat_month",
        reply_markup=worker_idle_kb(),
    )
