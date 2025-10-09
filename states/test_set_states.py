# ===== СОСТОЯНИЯ FSM ДЛЯ КОМАНДНЫХ ТЕСТОВ =====

from aiogram.fsm.state import State, StatesGroup

class CreateTestSetStates(StatesGroup):
    """Состояния создания набора тестов"""
    waiting_name = State()
    waiting_description = State()
    selecting_visibility = State()
    adding_exercises = State()
    configuring_exercise = State()
    setting_requirements = State()
    reviewing_set = State()

class JoinTestSetStates(StatesGroup):
    """Состояния присоединения к набору тестов"""
    waiting_access_code = State()
    confirming_join = State()

class TestExecutionStates(StatesGroup):
    """Состояния выполнения тестов из набора"""
    selecting_test = State()
    waiting_test_data = State()
    waiting_strength_data = State()
    waiting_endurance_data = State()
    waiting_speed_data = State()
    waiting_quantity_data = State()
    confirming_result = State()

__all__ = [
    'CreateTestSetStates',
    'JoinTestSetStates', 
    'TestExecutionStates'
]