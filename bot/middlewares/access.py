from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from bot.employee_registry import is_team_member


class TeamAccessMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message) or not event.from_user:
            return await handler(event, data)

        uid = event.from_user.id
        if is_team_member(uid):
            return await handler(event, data)

        await event.answer(
            "⛔ <b>Bu bot faqat jamoa a'zolari uchun.</b>\n\n"
            "Agar siz jamoada bo'lsangiz, administratorga Telegram IDingizni yuboring."
        )
        return None
