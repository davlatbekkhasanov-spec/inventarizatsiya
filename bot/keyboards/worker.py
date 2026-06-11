from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

BTN_FINISH = "🏁 Yakunlash"
BTN_ADD_5 = "+5 pozitsiya"
BTN_ADD_10 = "+10 pozitsiya"


def worker_reply_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_ADD_10), KeyboardButton(text=BTN_ADD_5)],
            [KeyboardButton(text=BTN_FINISH)],
        ],
        resize_keyboard=True,
    )


def worker_idle_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="/start_mesta")]],
        resize_keyboard=True,
    )


def add_inline_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="+5 pozitsiya", callback_data="add:5"),
                InlineKeyboardButton(text="+10 pozitsiya", callback_data="add:10"),
            ],
            [
                InlineKeyboardButton(text="+20 pozitsiya", callback_data="add:20"),
            ],
        ]
    )
