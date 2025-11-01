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

    # Алиасы для старого кода (совместимость)
    waiting_name = waiting_workout_name
    waiting_description = waiting_workout_description

     # ДОБАВЬТЕ ЭТИ СОСТОЯНИЯ:
    searching_exercise_for_block = State()
    waiting_rpe = State()
    waiting_weight = State()
    renaming_workout = State()
    changing_workout_description = State()
    manual_exercise_input = State()
    
    
    


__all__ = ['CreateWorkoutStates']


