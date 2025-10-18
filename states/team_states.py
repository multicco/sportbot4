from aiogram.fsm.state import State, StatesGroup

class JoinTeamStates(StatesGroup):
    """Состояния для присоединения к команде через код"""
    waiting_first_name = State()
    waiting_last_name = State()
    waiting_position = State()
    waiting_jersey_number = State()
