
# ===== ИСПРАВЛЕННЫЙ handlers/__init__.py =====

from . import start
from . import exercises  
from . import workouts
from . import tests
from . import test_batteries

try:
    from . import team_tests
except ImportError:
    team_tests = None

try:
    from . import player_tests  
except ImportError:
    player_tests = None

from . import teams  # ← ТВОЙ МОДУЛЬ КОМАНД

from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
import logging

logger = logging.getLogger(__name__)

def register_all_handlers(dp):
    """Регистрация всех обработчиков событий"""

    # Порядок регистрации важен!
    start.register_start_handlers(dp)
    exercises.register_exercise_handlers(dp)
    workouts.register_workout_handlers(dp) 
    tests.register_test_handlers(dp)
    test_batteries.register_battery_handlers(dp)

    # Если есть эти модули, то регистрируем
    if team_tests:
        team_tests.register_team_test_handlers(dp)
    if player_tests:
        player_tests.register_player_test_handlers(dp)

    # ТВОЙ МОДУЛЬ КОМАНД    
    teams.register_team_handlers(dp)

    # ГЛАВНЫЙ ОБРАБОТЧИК ТОЛЬКО ДЛЯ FSM СОСТОЯНИЙ
    dp.message.register(handle_fsm_text_messages)

    logger.info("✅ Все обработчики зарегистрированы")

async def handle_fsm_text_messages(message: Message, state: FSMContext):
    """ИСПРАВЛЕННЫЙ обработчик ТОЛЬКО для FSM состояний"""
    current_state = await state.get_state()

    # ВАЖНО: Если нет FSM состояния - НЕ ОБРАБАТЫВАЕМ!
    if current_state is None:
        return  # Пусть другие обработчики обработают

    # ===== ОБРАБОТКА ТЕСТОВ 1ПМ =====
    if current_state == "waiting_1rm_data":
        await tests.process_1rm_test_input(message, state)
        return

    # Другие состояния тестов
    if current_state in [
        "waiting_search_for_test",
        "waiting_strength_test_data", 
        "waiting_endurance_test_data",
        "waiting_speed_test_data",
        "waiting_quantity_test_data"
    ]:
        await tests.process_test_text_input(message, state)
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
        "searching_exercise_for_block"
    ]:
        await workouts.process_workout_text_input(message, state)
        return

    # ===== ОБРАБОТКА СОСТОЯНИЙ БАТАРЕЙ ТЕСТОВ =====
    try:
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
    except ImportError:
        logger.warning("Модуль test_batteries не найден")

    # ===== ОБРАБОТКА СОСТОЯНИЙ КОМАНДНЫХ ТЕСТОВ =====
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
            pass

    # ===== ОБРАБОТКА СОСТОЯНИЙ УЧАСТНИКОВ =====  
    if player_tests:
        try:
            from states.test_set_states import JoinTestSetStates
            if current_state in [
                JoinTestSetStates.waiting_access_code,
            ]:
                await player_tests.process_player_test_text_input(message, state)
                return
        except ImportError:
            pass

    # ЕСЛИ FSM СОСТОЯНИЕ НЕ РАСПОЗНАНО - СБРАСЫВАЕМ ЕГО
    logger.warning(f"Неизвестное FSM состояние: {current_state}, сбрасываем")
    await state.clear()
    await message.answer("❌ Операция сброшена. Используйте меню.")

__all__ = ['register_all_handlers', 'handle_fsm_text_messages']
