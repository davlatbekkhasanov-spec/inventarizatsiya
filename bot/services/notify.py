from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from bot.config import get_settings
from bot.utils.norm import NormStatus, kaizen_points, norm_time_minutes, time_saved_minutes
from bot.utils.time_fmt import fmt_datetime, fmt_hm, fmt_minutes

log = logging.getLogger(__name__)

_SEP = "━━━━━━━━━━━━━━━━━"


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

    date_str = fmt_datetime(started_at).split(" ", 1)[0]
    work_str = fmt_minutes(norm.work_minutes)
    norm_str = fmt_minutes(norm_time)

    if waste >= 0.5:
        verdict = "⚠️ <b>NORMADAN SEKIN</b>"
        highlight = f"❌ Ortiqcha vaqt: <b>{fmt_minutes(waste)}</b>"
    elif saved >= mpp:
        verdict = "✅ <b>NORMADAN TEZ</b>"
        highlight = f"⚡ Tejash: <b>{fmt_minutes(saved)}</b>"
    elif saved > 0.5:
        verdict = "✅ <b>NORMADA</b>"
        highlight = f"⚡ Tejash: <b>{fmt_minutes(saved)}</b>"
    else:
        verdict = "✅ <b>NORMADA</b>"
        highlight = ""

    kaizen_line = f"🏆 Kaizen: <b>+{pts}</b> ball" if pts > 0 else ""

    pause_part = ""
    if norm.pause_minutes >= 0.5:
        pause_part = f"  ·  ⏸ <b>{fmt_minutes(norm.pause_minutes)}</b>"

    lines = [
        "📊 <b>MESTA YAKUNLANDI</b>",
        "",
        f"👤 <b>{name}</b>",
        f"🕐 {date_str}  ·  <b>{fmt_hm(started_at)}</b> → <b>{fmt_hm(finished_at)}</b>",
        "",
        _SEP,
        f"📦 <b>{actual}</b> pozitsiya{pause_part}",
        "",
        verdict,
    ]
    if highlight:
        lines.append(highlight)
    if kaizen_line:
        lines.append(kaizen_line)
    lines.extend(
        [
            "",
            _SEP,
            f"⏱ Ish: <b>{work_str}</b>  ·  📐 Norma: <b>{norm_str}</b>",
        ]
    )

    return "\n".join(lines)
