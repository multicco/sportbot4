# ===== СОСТОЯНИЯ FSM ДЛЯ БАТАРЕЙ ТЕСТОВ =====

from aiogram.fsm.state import State, StatesGroup

class CreateBatteryStates(StatesGroup):
    """Состояния создания батареи тестов"""
    waiting_name = State()
    waiting_description = State()
    selecting_exercises = State()
    reviewing_battery = State()

class EditBatteryStates(StatesGroup):
    """Состояния редактирования батареи тестов"""
    editing_info = State()
    adding_exercises = State()
    confirming_changes = State()
    searching_exercises = State()

class AssignBatteryStates(StatesGroup):
    """Состояния назначения батареи участникам"""
    selecting_battery = State()
    selecting_participants = State()
    confirming_assignment = State()

class JoinBatteryStates(StatesGroup):
    """Состояния присоединения к батарее"""
    waiting_battery_code = State()
    confirming_join = State()

class BatteryTestStates(StatesGroup):
    """Состояния прохождения тестов из батареи"""
    selecting_test = State()
    waiting_test_data = State()
    waiting_strength_data = State()
    waiting_endurance_data = State()
    waiting_speed_data = State()
    waiting_quantity_data = State()
    confirming_result = State()

__all__ = [
    'CreateBatteryStates',
    'EditBatteryStates',
    'AssignBatteryStates',
    'JoinBatteryStates',
    'BatteryTestStates'
]