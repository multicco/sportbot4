# ===== СОСТОЯНИЯ ДЛЯ СОЗДАНИЯ УПРАЖНЕНИЙ =====

from aiogram.fsm.state import State, StatesGroup

class CreateExerciseStates(StatesGroup):
    waiting_name = State()
    waiting_category = State()
    waiting_muscle_group = State()
    waiting_equipment = State()
    waiting_difficulty = State()
    waiting_description = State()
    waiting_instructions = State()

__all__ = ['CreateExerciseStates']