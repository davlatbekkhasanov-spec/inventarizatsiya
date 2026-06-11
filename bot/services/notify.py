from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from bot.config import get_settings
from bot.utils.norm import NormStatus
from bot.utils.time_fmt import fmt_datetime, fmt_hm, fmt_minutes

log = logging.getLogger(__name__)


async def send_group(bot: Bot, text: str) -> bool:
    gid = get_settings().group_chat_id
    if not gid:
        log.warning("GROUP_CHAT_ID yo'q — guruhga yuborilmadi")
        return False
    try:
        await bot.send_message(gid, text)
        return True
    except TelegramAPIError as exc:
        log.error("Guruhga yuborish xato (%s): %s", gid, exc)
        return False


def start_message(*, name: str, started_at) -> str:
    return (
        "🚀 <b>Mesta boshlandi</b>\n\n"
        f"Xodim: <b>{name}</b>\n"
        f"Boshlangan vaqt: <b>{fmt_hm(started_at)}</b>"
    )


def pause_message(*, name: str) -> str:
    return f"⏸ <b>Pauza</b>\n\nXodim: <b>{name}</b>"


def resume_message(*, name: str) -> str:
    return f"▶️ <b>Davom etdi</b>\n\nXodim: <b>{name}</b>"


def work_reminder_message(*, name: str, work_minutes: float) -> str:
    return (
        "⏰ <b>Eslatma</b>\n\n"
        f"Xodim: <b>{name}</b>\n"
        f"Ish vaqti: <b>{fmt_minutes(work_minutes)}</b>\n\n"
        "Tayyor bo'lgach «Yakunlash» tugmasini bosing va pozitsiya sonini kiriting."
    )


def finish_message(
    *,
    name: str,
    started_at,
    finished_at,
    norm: NormStatus,
    minutes_per_position: float,
) -> str:
    mpp = minutes_per_position if minutes_per_position > 0 else 3.0
    avg = (norm.work_minutes / norm.actual) if norm.actual > 0 else None
    avg_line = f"{avg:.1f} daqiqa" if avg is not None else "—"

    if norm.on_track and norm.waste_minutes < 0.5:
        norm_line = "✅ <b>Normaga tushdi</b>"
        waste_line = ""
    else:
        norm_line = "⚠️ <b>Normadan ortda</b>"
        waste_line = f"\nBekor sarflangan vaqt: <b>{fmt_minutes(norm.waste_minutes)}</b>"

    if norm.difference > 0:
        diff_line = f"−{norm.difference} pozitsiya (kamchilik)"
    elif norm.difference < 0:
        diff_line = f"+{-norm.difference} pozitsiya (ortiqcha)"
    else:
        diff_line = "0 (normada)"

    expected_min = norm.actual * mpp
    saved_min = max(0.0, expected_min - norm.work_minutes)
    kaizen_pts = int(saved_min // mpp) if mpp > 0 else 0
    tejash_line = (
        f"Tejash: <b>{fmt_minutes(saved_min)}</b> · Kaizen ball: <b>{kaizen_pts}</b>\n\n"
        if norm.actual > 0
        else ""
    )

    return (
        "📊 <b>Mesta yakunlandi</b>\n\n"
        f"Xodim: <b>{name}</b>\n\n"
        f"Boshlanish: <b>{fmt_datetime(started_at)}</b>\n"
        f"Tugash: <b>{fmt_datetime(finished_at)}</b>\n\n"
        f"Ish vaqti: <b>{fmt_minutes(norm.work_minutes)}</b>\n"
        f"Pauza: <b>{fmt_minutes(norm.pause_minutes)}</b>\n\n"
        f"Bajarilgan pozitsiya: <b>{norm.actual}</b>\n"
        f"Norma (1 poz = {mpp:g} daq): <b>{norm.expected}</b> kerak edi\n\n"
        f"{norm_line}\n"
        f"Farq: <b>{diff_line}</b>"
        f"{waste_line}\n\n"
        f"{tejash_line}"
        f"1 pozitsiyaga o'rtacha: <b>{avg_line}</b>"
    )
