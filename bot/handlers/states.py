"""FSM — yakunlashda pozitsiya soni."""

from aiogram.fsm.state import State, StatesGroup


class FinishStates(StatesGroup):
    waiting_positions = State()
