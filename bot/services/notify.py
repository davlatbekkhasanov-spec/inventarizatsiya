from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from bot.config import get_settings
from bot.utils.norm import NormStatus, kaizen_points, norm_time_minutes, time_saved_minutes
from bot.utils.time_fmt import fmt_datetime, fmt_hm, fmt_minutes

log = logging.getLogger(__name__)

_SEP = "─────────────────"


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
        f"👤 <b>{name}</b>\n"
        f"🕐 <b>{fmt_hm(started_at)}</b>"
    )


def pause_message(*, name: str) -> str:
    return f"⏸ <b>Pauza</b>\n\n👤 <b>{name}</b>"


def resume_message(*, name: str) -> str:
    return f"▶️ <b>Davom etdi</b>\n\n👤 <b>{name}</b>"


def work_reminder_message(*, name: str, work_minutes: float) -> str:
    return (
        "⏰ <b>Eslatma</b>\n\n"
        f"👤 <b>{name}</b>\n"
        f"⏱ Ish vaqti: <b>{fmt_minutes(work_minutes)}</b>\n\n"
        "Tayyor bo'lgach «Yakunlash» tugmasini bosing va pozitsiya sonini kiriting."
    )


def _fmt_avg_per_position(work_minutes: float, actual: int) -> str:
    if actual <= 0:
        return "—"
    avg_min = work_minutes / actual
    if avg_min < 1:
        sec = max(1, int(round(avg_min * 60)))
        return f"{sec} soniya"
    return f"{avg_min:.1f} daqiqa"


def _pace_line(*, actual: int, work_minutes: float, mpp: float) -> str:
    """Ish vaqtiga qarab kutilgan pozitsiya (faqat ma'noli bo'lsa)."""
    if work_minutes < mpp:
        return ""
    expected_pos = int(work_minutes // mpp)
    diff = actual - expected_pos
    if diff > 0:
        return f"📈 Sur'at: <b>+{diff}</b> poz (vaqtga nisbatan ortiqcha)\n"
    if diff < 0:
        return f"📉 Sur'at: <b>{diff}</b> poz (vaqtga nisbatan kam)\n"
    return "📊 Sur'at: vaqt bo'yicha normada\n"


def finish_message(
    *,
    name: str,
    started_at,
    finished_at,
    norm: NormStatus,
    minutes_per_position: float,
) -> str:
    mpp = minutes_per_position if minutes_per_position > 0 else 3.0
    actual = norm.actual
    norm_time = norm_time_minutes(actual, mpp)
    saved = time_saved_minutes(actual, norm.work_minutes, mpp)
    waste = norm.waste_minutes
    pts = kaizen_points(saved, mpp)

    if waste < 0.5:
        if saved >= mpp:
            verdict = "✅ <b>Normadan tez — vaqt tejaldi</b>"
        elif saved > 0.5:
            verdict = "✅ <b>Normaga tushdi</b>"
        else:
            verdict = "✅ <b>Normaga tushdi</b>"
    else:
        verdict = "⚠️ <b>Normadan sekin — ortiqcha vaqt sarflandi</b>"

    norm_block = (
        f"📐 Kerakli vaqt: <b>{fmt_minutes(norm_time)}</b>\n"
        f"   <i>({actual} poz × {mpp:g} daq)</i>\n"
        f"⏱ Sarflangan: <b>{fmt_minutes(norm.work_minutes)}</b>\n\n"
        f"{verdict}\n"
    )

    if saved >= 0.5:
        norm_block += f"⚡ Tejash: <b>{fmt_minutes(saved)}</b>\n"
    if waste >= 0.5:
        norm_block += f"❌ Ortiqcha vaqt: <b>{fmt_minutes(waste)}</b>\n"
    if actual > 0 and pts > 0:
        norm_block += f"🏆 Kaizen ball: <b>+{pts}</b> <i>(har {mpp:g} daq tejash = 1 ball)</i>\n"

    pace = _pace_line(actual=actual, work_minutes=norm.work_minutes, mpp=mpp)

    return (
        "📊 <b>Mesta yakunlandi</b>\n\n"
        f"👤 <b>{name}</b>\n"
        f"🕐 <b>{fmt_hm(started_at)}</b> → <b>{fmt_hm(finished_at)}</b>\n"
        f"📅 {fmt_datetime(started_at).split(' ', 1)[0]}\n\n"
        f"{_SEP}\n"
        "<b>Natija</b>\n"
        f"📦 Pozitsiya: <b>{actual} ta</b>\n"
        f"⏱ Ish vaqti: <b>{fmt_minutes(norm.work_minutes)}</b>\n"
        f"⏸ Pauza: <b>{fmt_minutes(norm.pause_minutes)}</b>\n\n"
        f"{_SEP}\n"
        f"<b>Norma</b> <i>(1 poz = {mpp:g} daq)</i>\n"
        f"{norm_block}\n"
        f"{pace}"
        f"📌 1 pozitsiya: o'rtacha <b>{_fmt_avg_per_position(norm.work_minutes, actual)}</b>"
    )
