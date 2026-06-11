from __future__ import annotations

import re

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.worker import (
    BTN_ADD_5,
    BTN_ADD_10,
    BTN_FINISH,
    add_inline_kb,
    worker_idle_kb,
    worker_reply_kb,
)
from bot.services.mesta import add_positions, finish_session, list_active_sessions, start_session
from bot.services.notify import finish_message, norm_message, send_group, start_message
from bot.utils.time_fmt import elapsed_minutes, fmt_hm, fmt_minutes

router = Router(name="mesta")


def _user(message: Message) -> tuple[int, str]:
    u = message.from_user
    return (u.id if u else 0, (u.full_name if u else "") or "Noma'lum")


async def _do_add(message: Message, bot: Bot, db: AsyncSession, count: int) -> None:
    uid, _ = _user(message)
    view, err = await add_positions(db, uid, count)
    if err:
        return await message.answer(f"⚠️ {err}")
    assert view
    await send_group(bot, norm_message(name=view.user.full_name, norm=view.norm))
    await message.answer(
        f"✅ <b>+{count}</b> pozitsiya qo'shildi.\n"
        f"Jami: <b>{view.session.total_positions}</b>\n"
        f"Norma: <b>{view.norm.expected}</b> kerak · <b>{view.norm.actual}</b> kiritildi",
        reply_markup=worker_reply_kb(),
    )


@router.message(Command("start_mesta"))
async def cmd_start_mesta(message: Message, bot: Bot, db: AsyncSession) -> None:
    uid, name = _user(message)
    ws, err = await start_session(db, uid, name)
    if err:
        return await message.answer(f"⚠️ {err}")
    assert ws
    await send_group(bot, start_message(name=ws.user.full_name, started_at=ws.started_at))
    await message.answer(
        "🚀 <b>Mesta boshlandi!</b>\n\n"
        f"Vaqt: <b>{fmt_hm(ws.started_at)}</b>\n\n"
        "Pozitsiya qo'shing: tugma, /add 10 yoki inline.",
        reply_markup=worker_reply_kb(),
    )
    await message.answer("Tez qo'shish:", reply_markup=add_inline_kb())


@router.message(Command("add"))
async def cmd_add(message: Message, bot: Bot, db: AsyncSession, command: CommandObject) -> None:
    raw = (command.args or "").strip()
    if not raw or not raw.isdigit():
        return await message.answer("Foydalanish: <code>/add 10</code>")
    await _do_add(message, bot, db, int(raw))


@router.message(F.text.in_({BTN_ADD_5, BTN_ADD_10}))
async def btn_add(message: Message, bot: Bot, db: AsyncSession) -> None:
    count = 10 if message.text == BTN_ADD_10 else 5
    await _do_add(message, bot, db, count)


@router.callback_query(F.data.regexp(r"^add:\d+$"))
async def cb_add(callback: CallbackQuery, bot: Bot, db: AsyncSession) -> None:
    assert callback.data
    count = int(callback.data.split(":")[1])
    if callback.message:
        await _do_add(callback.message, bot, db, count)
    await callback.answer(f"+{count}")


@router.message(Command("finish_mesta"))
@router.message(F.text == BTN_FINISH)
async def cmd_finish(message: Message, bot: Bot, db: AsyncSession) -> None:
    uid, _ = _user(message)
    view, err = await finish_session(db, uid)
    if err:
        return await message.answer(f"⚠️ {err}")
    assert view
    ws = view.session
    total_min = elapsed_minutes(ws.started_at, ws.finished_at)
    avg = (total_min / ws.total_positions) if ws.total_positions > 0 else None
    report = finish_message(
        name=view.user.full_name,
        started_at=ws.started_at,
        finished_at=ws.finished_at,
        total_minutes=total_min,
        positions=ws.total_positions,
        norm=view.norm,
        avg_min_per_position=avg,
    )
    await send_group(bot, report)
    await message.answer(report, reply_markup=worker_idle_kb())


@router.message(Command("active_mesta"))
async def cmd_active(message: Message, db: AsyncSession) -> None:
    views = await list_active_sessions(db)
    if not views:
        return await message.answer("Hozir mesta bilan ishlayotganlar yo'q.")
    lines = ["<b>Hozir mesta bilan ishlayotganlar:</b>\n"]
    for i, v in enumerate(views, 1):
        lines.append(
            f"{i}. <b>{v.user.full_name}</b>\n"
            f"   Boshlagan: {fmt_hm(v.session.started_at)}\n"
            f"   Pozitsiya: {v.session.total_positions}\n"
            f"   Vaqt: {fmt_minutes(v.norm.elapsed_minutes)} · norma {v.norm.expected}"
        )
    await message.answer("\n".join(lines))


@router.message(F.text.regexp(re.compile(r"^\+(\d+)\s*poz", re.I)))
async def text_add_pattern(message: Message, bot: Bot, db: AsyncSession) -> None:
    m = re.match(r"^\+(\d+)", message.text or "", re.I)
    if not m:
        return
    await _do_add(message, bot, db, int(m.group(1)))
