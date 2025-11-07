# ===== СОСТОЯНИЯ ДЛЯ СОЗДАНИЯ ТРЕНИРОВОК =====
from aiogram.fsm.state import State, StatesGroup


class CreateWorkoutStates(StatesGroup):
    waiting_workout_name = State()
    
    waiting_workout_description = State()
    selecting_blocks = State()
    adding_block_description = State()
    adding_exercises = State()
    selecting_exercises = State()
    configuring_exercise = State()
    searching_exercise_for_block = State()
    waiting_description = waiting_workout_description
    searching_exercise_for_block = State()
    waiting_rpe = State()
    waiting_weight = State()
    renaming_workout = State()
    changing_workout_description = State()
    manual_exercise_input = State()
    searching_by_code = State()      # Поиск по коду
    searching_by_name = State()      # Поиск по названию
    
    
    


__all__ = ['CreateWorkoutStates']


