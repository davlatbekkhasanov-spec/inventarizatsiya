from __future__ import annotations

import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import get_settings
from bot.handlers.states import FinishStates
from bot.keyboards.worker import (
    BTN_FINISH,
    BTN_PAUSE,
    BTN_RESUME,
    BTN_START,
    worker_active_kb,
    worker_idle_kb,
    worker_paused_kb,
)
from bot.services.hub_day import save_today_push
from bot.services.hub_summary import compact_hub_summary
from bot.services.mesta import (
    complete_finish,
    list_active_sessions,
    pause_session,
    request_finish,
    resume_session,
    start_session,
)
from bot.services.notify import (
    finish_message,
    pause_message,
    resume_message,
    send_group,
    start_message,
)
from bot.utils.time_fmt import fmt_hm, fmt_minutes
from bot.yordamchi_push import push_to_yordamchi_hub, push_to_yordamchi_hub_background, today_iso

router = Router(name="mesta")
log = logging.getLogger(__name__)


def _user(message: Message) -> tuple[int, str]:
    u = message.from_user
    return (u.id if u else 0, (u.full_name if u else "") or "Noma'lum")


async def _push_hub(db: AsyncSession, *, tg_id: int, summary: str) -> None:
    day = today_iso()
    await save_today_push(db, day=day, tg_id=tg_id, summary=summary)
    ok, via = await push_to_yordamchi_hub(tg_id=tg_id, bot_key="mesta", summary=summary, day_iso=day)
    if not ok:
        log.warning("mesta hub push failed uid=%s via=%s", tg_id, via)
        push_to_yordamchi_hub_background(tg_id=tg_id, bot_key="mesta", summary=summary, day_iso=day)


@router.message(Command("start_mesta"))
@router.message(F.text == BTN_START)
async def cmd_start_mesta(message: Message, bot: Bot, db: AsyncSession) -> None:
    uid, name = _user(message)
    ws, err = await start_session(db, uid, name)
    if err:
        return await message.answer(f"⚠️ {err}")
    assert ws
    await send_group(bot, start_message(name=ws.user.full_name, started_at=ws.started_at))
    mpp = get_settings().minutes_per_position
    await message.answer(
        "🚀 <b>Mesta boshlandi!</b>\n\n"
        f"Vaqt: <b>{fmt_hm(ws.started_at)}</b>\n"
        f"Norma: <b>1 pozitsiya = {mpp:g} daqiqa</b>\n\n"
        "Ish tugagach «Yakunlash» tugmasini bosing va nechta pozitsiya qilganingizni kiriting.",
        reply_markup=worker_active_kb(),
    )


@router.message(Command("pause_mesta"))
@router.message(F.text == BTN_PAUSE)
async def cmd_pause(message: Message, bot: Bot, db: AsyncSession) -> None:
    uid, _ = _user(message)
    view, err = await pause_session(db, uid)
    if err:
        return await message.answer(f"⚠️ {err}")
    assert view
    await send_group(bot, pause_message(name=view.user.full_name))
    await message.answer(
        "⏸ <b>Pauza</b>\n\nVaqt hisobi to'xtadi. Davom etish uchun tugmani bosing.",
        reply_markup=worker_paused_kb(),
    )


@router.message(Command("resume_mesta"))
@router.message(F.text == BTN_RESUME)
async def cmd_resume(message: Message, bot: Bot, db: AsyncSession) -> None:
    uid, _ = _user(message)
    view, err = await resume_session(db, uid)
    if err:
        return await message.answer(f"⚠️ {err}")
    assert view
    await send_group(bot, resume_message(name=view.user.full_name))
    await message.answer(
        "▶️ <b>Davom etildi</b>\n\nVaqt hisobi qayta boshlandi.",
        reply_markup=worker_active_kb(),
    )


@router.message(Command("finish_mesta"))
@router.message(F.text == BTN_FINISH)
async def cmd_finish(message: Message, state: FSMContext, db: AsyncSession) -> None:
    uid, _ = _user(message)
    ws, err = await request_finish(db, uid)
    if err:
        return await message.answer(f"⚠️ {err}")
    assert ws
    await state.set_state(FinishStates.waiting_positions)
    await state.update_data(session_id=ws.id)
    await message.answer(
        "🏁 <b>Yakunlash</b>\n\n"
        "Nechta pozitsiya qildingiz?\n"
        "Faqat raqam yuboring, masalan: <code>25</code>",
        reply_markup=worker_idle_kb(),
    )


@router.message(FinishStates.waiting_positions, F.text.regexp(r"^\d+$"))
async def finish_positions(message: Message, bot: Bot, db: AsyncSession, state: FSMContext) -> None:
    uid, _ = _user(message)
    count = int((message.text or "0").strip())
    view, err = await complete_finish(db, uid, count)
    if err:
        return await message.answer(f"⚠️ {err}")
    assert view
    await state.clear()

    ws = view.session
    settings = get_settings()
    report = finish_message(
        name=view.user.full_name,
        started_at=ws.started_at,
        finished_at=ws.finished_at,
        norm=view.norm,
        minutes_per_position=settings.minutes_per_position,
    )
    hub_summary = compact_hub_summary(ws, view.norm)
    await _push_hub(db, tg_id=uid, summary=hub_summary)
    await send_group(bot, report)
    await message.answer(report, reply_markup=worker_idle_kb())


@router.message(FinishStates.waiting_positions)
async def finish_positions_invalid(message: Message) -> None:
    await message.answer("⚠️ Faqat musbat raqam kiriting, masalan: <code>18</code>")


@router.message(Command("active_mesta"))
async def cmd_active(message: Message, db: AsyncSession) -> None:
    views = await list_active_sessions(db)
    if not views:
        return await message.answer("Hozir mesta bilan ishlayotganlar yo'q.")
    lines = ["<b>Hozir mesta bilan ishlayotganlar:</b>\n"]
    for i, v in enumerate(views, 1):
        status = "⏸ pauza" if v.session.status == "paused" else "▶️ ish"
        lines.append(
            f"{i}. <b>{v.user.full_name}</b> ({status})\n"
            f"   Boshlagan: {fmt_hm(v.session.started_at)}\n"
            f"   Ish vaqti: {fmt_minutes(v.norm.work_minutes)}"
        )
    await message.answer("\n".join(lines))
