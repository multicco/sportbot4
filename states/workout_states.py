# ===== СОСТОЯНИЯ ДЛЯ СОЗДАНИЯ ТРЕНИРОВОК =====

from aiogram.fsm.state import State, StatesGroup

class CreateWorkoutStates(StatesGroup):
    waiting_name = State()
    waiting_description = State()  
    selecting_blocks = State()
    adding_block_description = State()
    adding_exercises = State()
    configuring_exercise = State()
    selecting_exercises = State()        # ← ДОБАВЬТЕ
    configuring_exercise = State()
    

__all__ = ['CreateWorkoutStates']