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


def norm_message(*, name: str, norm: NormStatus) -> str:
    mins = fmt_minutes(norm.elapsed_minutes)
    if norm.on_track:
        return (
            "✅ <b>Norma bajarilmoqda</b>\n\n"
            f"Xodim: <b>{name}</b>\n"
            f"O'tgan vaqt: <b>{mins}</b>\n"
            f"Kerak edi: <b>{norm.expected}</b>\n"
            f"Kiritildi: <b>{norm.actual}</b>"
        )
    return (
        "⚠️ <b>Normadan ortda qolmoqda</b>\n\n"
        f"Xodim: <b>{name}</b>\n"
        f"O'tgan vaqt: <b>{mins}</b>\n"
        f"Kerak edi: <b>{norm.expected}</b>\n"
        f"Kiritildi: <b>{norm.actual}</b>\n"
        f"Kamchilik: <b>{norm.shortage}</b>"
    )


def finish_message(
    *,
    name: str,
    started_at,
    finished_at,
    total_minutes: float,
    positions: int,
    norm: NormStatus,
    avg_min_per_position: float | None,
) -> str:
    diff = norm.difference
    if diff > 0:
        diff_line = f"−{diff} (kamchilik)"
    elif diff < 0:
        diff_line = f"+{-diff} (ortiqcha)"
    else:
        diff_line = "0 (normada)"

    avg_line = f"{avg_min_per_position:.1f} daqiqa" if avg_min_per_position is not None else "—"

    return (
        "📊 <b>Mesta yakunlandi</b>\n\n"
        f"Xodim: <b>{name}</b>\n\n"
        f"Boshlanish: <b>{fmt_datetime(started_at)}</b>\n"
        f"Tugash: <b>{fmt_datetime(finished_at)}</b>\n\n"
        f"Umumiy vaqt: <b>{fmt_minutes(total_minutes)}</b>\n\n"
        f"Kiritilgan pozitsiya:\n<b>{positions}</b>\n\n"
        f"Norma:\n<b>{norm.expected}</b>\n\n"
        f"Farq:\n<b>{diff_line}</b>\n\n"
        f"1 pozitsiyaga o'rtacha:\n<b>{avg_line}</b>"
    )
