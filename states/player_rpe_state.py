from aiogram.fsm.state import StatesGroup, State

class PlayerRPEState(StatesGroup):
    waiting = State()