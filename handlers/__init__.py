# ===== ОБНОВЛЕННЫЙ handlers/__init__.py С БАТАРЕЯМИ ТЕСТОВ =====

from . import start
from . import exercises  
from . import workouts
from . import tests  # ← Индивидуальные тесты
from . import test_batteries  # ← НОВЫЙ модуль батарей тестов
# Остальные модули при наличии
try:
    from . import team_tests  # ← Командные тесты (наборы) - если есть
except ImportError:
    team_tests = None

try:
    from . import player_tests  # ← Участники командных тестов - если есть
except ImportError:
    player_tests = None

from . import teams

from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

def register_all_handlers(dp):
    """Регистрация всех обработчиков событий"""
    
    # Порядок регистрации важен!
    start.register_start_handlers(dp)
    exercises.register_exercise_handlers(dp) 
    workouts.register_workout_handlers(dp)
    tests.register_test_handlers(dp)  # ← Индивидуальные тесты
    test_batteries.register_battery_handlers(dp)  # ← НОВЫЙ! Батареи тестов
    
    
    # Если есть эти модули, то регистрируем
    if team_tests:
        team_tests.register_team_test_handlers(dp)
        
    if player_tests:
        player_tests.register_player_test_handlers(dp)
        
    teams.register_team_handlers(dp)
    
    # ГЛАВНЫЙ ОБРАБОТЧИК ВСЕХ ТЕКСТОВЫХ СООБЩЕНИЙ
    dp.message.register(handle_all_text_messages)

async def handle_all_text_messages(message: Message, state: FSMContext):
    """Единый обработчик всех текстовых сообщений"""
    current_state = await state.get_state()
    
    if current_state is None:
        # Если состояние не определено, показываем справку
        from keyboards.main_keyboards import get_main_menu_keyboard
        
        await message.answer(
            "ℹ️ Используйте меню бота для навигации.\n"
            "Нажмите /start для возврата в главное меню.",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    # ===== ОБРАБОТКА СОСТОЯНИЙ УПРАЖНЕНИЙ =====
    from states.exercise_states import CreateExerciseStates
    
    if current_state in [
        CreateExerciseStates.waiting_name,
        CreateExerciseStates.waiting_description, 
        CreateExerciseStates.waiting_instructions,
        "waiting_new_category",
        "waiting_new_muscle_group", 
        "waiting_custom_equipment",
        "waiting_search"
    ]:
        await exercises.process_exercise_text_input(message, state)
        return
    
    # ===== ОБРАБОТКА СОСТОЯНИЙ ТРЕНИРОВОК =====
    from states.workout_states import CreateWorkoutStates
    
    if current_state in [
        CreateWorkoutStates.waiting_name,
        CreateWorkoutStates.waiting_description,
        CreateWorkoutStates.adding_block_description,
        "simple_block_config",
        "advanced_block_config",
        "searching_exercise_for_block",
        "waiting_1rm_result",
        "waiting_1rm_data"
    ]:
        await workouts.process_workout_text_input(message, state)
        return
    
    # ===== ОБРАБОТКА СОСТОЯНИЙ ИНДИВИДУАЛЬНЫХ ТЕСТОВ =====
    if current_state in [
        "waiting_search_for_test",
        "waiting_strength_test_data",
        "waiting_endurance_test_data", 
        "waiting_speed_test_data",
        "waiting_quantity_test_data",
        "waiting_1rm_data",  # Совместимость со старым кодом
        "waiting_search_for_test"
    ]:
        await tests.process_test_text_input(message, state)
        return
    
    # ===== ОБРАБОТКА СОСТОЯНИЙ БАТАРЕЙ ТЕСТОВ =====  ← НОВОЕ!
    from handlers.test_batteries import CreateBatteryStates, EditBatteryStates, JoinBatteryStates
    
    if current_state in [
        CreateBatteryStates.waiting_name,
        CreateBatteryStates.waiting_description,
        CreateBatteryStates.selecting_exercises,
        EditBatteryStates.adding_exercises,
        JoinBatteryStates.waiting_battery_code
    ]:
        await test_batteries.process_battery_text_input(message, state)
        return
    
    # ===== ОБРАБОТКА СОСТОЯНИЙ КОМАНДНЫХ ТЕСТОВ (ЕСЛИ ЕСТЬ) =====
    if team_tests:
        try:
            from states.test_set_states import CreateTestSetStates
            
            if current_state in [
                CreateTestSetStates.waiting_name,
                CreateTestSetStates.waiting_description,
                "searching_exercise_for_test_set",
            ]:
                await team_tests.process_team_test_text_input(message, state)
                return
        except ImportError:
            pass  # Нет модуля test_set_states
    
    # ===== ОБРАБОТКА СОСТОЯНИЙ УЧАСТНИКОВ (ЕСЛИ ЕСТЬ) =====
    if player_tests:
        try:
            from states.test_set_states import JoinTestSetStates
            
            if current_state in [
                JoinTestSetStates.waiting_access_code,
            ]:
                await player_tests.process_player_test_text_input(message, state)
                return
        except ImportError:
            pass  # Нет модуля
    
    # Если состояние не распознано
    from keyboards.main_keyboards import get_main_menu_keyboard
    
    await message.answer(
        f"❓ Неожиданное состояние: {current_state}\n\n"
        f"Используйте меню для навигации.",
        reply_markup=get_main_menu_keyboard()
    )
    await state.clear()

__all__ = ['register_all_handlers', 'handle_all_text_messages']