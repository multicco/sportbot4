# ===== СОСТОЯНИЯ ДЛЯ СОЗДАНИЯ УПРАЖНЕНИЙ =====

from aiogram.fsm.state import State, StatesGroup

class CreateExerciseStates(StatesGroup):
    waiting_name = State()
    waiting_category = State()
    waiting_muscle_group = State()
    waiting_equipment = State()
    waiting_difficulty = State()
    waiting_test_type = State()
    waiting_description = State()
    waiting_instructions = State()
    waiting_tags = State()

    # Пользовательский ввод названий (вместо «сырых» строковых состояний)
    waiting_new_category = State()
    waiting_new_muscle_group = State()
    waiting_custom_equipment = State()

    # Поиск упражнений по названию
    waiting_search = State()

__all__ = ['CreateExerciseStates']