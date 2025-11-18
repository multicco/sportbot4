import logging
from aiogram import Router, F, Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

# Импорт всех подмодулей
from . import start
from . import exercises
from . import workouts
from . import tests
from . import test_batteries
from handlers.teams import TeamStates

# Дополнительные модули (по наличию)
try:
    from . import team_tests
except ImportError:
    team_tests = None

try:
    from . import player_tests
except ImportError:
    player_tests = None

# ✅ ГЛАВНЫЕ РОУТЕРЫ
from . import teams
from .trainees_menu import trainees_router
from .workouts import workouts_router  # ← ДОБАВЛЕНО!
 # ← МОЖЕТ БЫТЬ НУЖНО

logger = logging.getLogger(__name__)

from aiogram.filters import StateFilter

# Общий роутер для текстовых сообщений
general_router = Router(name="general")

# Обработчик текстовых сообщений в FSM
@general_router.message(~StateFilter(None))
async def handle_all_text_messages(message: Message, state: FSMContext):
    """Единый обработчик текстовых сообщений вне контекста других FSM."""
    current_state = await state.get_state()
    logger.info(f"📨 Текст: '{message.text}' | FSM состояние: {current_state}")

    # --- 1. Без состояния
    if current_state is None:
        await message.answer(
            "ℹ️ Используйте меню бота для навигации.\n"
            "Нажмите /start для возврата в главное меню."
        )
        return

    # --- 2. Тесты
    if current_state == "waiting_1rm_data":
        await tests.process_1rm_test_input(message, state)
        return

    if current_state in [
        "waiting_search_for_test",
        "waiting_strength_test_data",
        "waiting_endurance_test_data",
        "waiting_speed_test_data",
        "waiting_quantity_test_data",
    ]:
        await tests.process_test_text_input(message, state)
        return

    # --- 3. Упражнения
    try:
        from states.exercise_states import CreateExerciseStates
        if current_state in [
            CreateExerciseStates.waiting_name,
            CreateExerciseStates.waiting_description,
            CreateExerciseStates.waiting_instructions,
            "waiting_new_category",
            "waiting_new_muscle_group",
            "waiting_custom_equipment",
            "waiting_search",
        ]:
            await exercises.process_exercise_text_input(message, state)
            return
    except ImportError:
        logger.warning("⚠️ Модуль exercise_states не найден")

    # --- 4. Тренировки
    try:
        from states.workout_states import CreateWorkoutStates
        WORKOUT_TEXT_STATES = [
            CreateWorkoutStates.waiting_workout_name,
            CreateWorkoutStates.waiting_workout_description,
            CreateWorkoutStates.adding_block_description,
            CreateWorkoutStates.manual_exercise_input,
            CreateWorkoutStates.waiting_rpe,
            CreateWorkoutStates.configuring_exercise,
        ]
        if current_state in WORKOUT_TEXT_STATES:
            await workouts.process_workout_text_input(message, state)
            return

        # Поиск упражнения внутри блока
        if current_state == CreateWorkoutStates.searching_exercise_for_block:
            from handlers.exercises import process_exercise_text_input
            await process_exercise_text_input(message, state)
            return
    except ImportError:
        logger.warning("⚠️ Модуль workout_states не найден")

    # --- 5. Батареи тестов
    try:
        from handlers.test_batteries import (
            CreateBatteryStates,
            EditBatteryStates,
            JoinBatteryStates,
        )
        if current_state in [
            CreateBatteryStates.waiting_name,
            CreateBatteryStates.waiting_description,
            CreateBatteryStates.selecting_exercises,
            EditBatteryStates.adding_exercises,
            JoinBatteryStates.waiting_battery_code,
        ]:
            await test_batteries.process_battery_text_input(message, state)
            return
    except ImportError:
        logger.warning("⚠️ Модуль test_batteries не найден")

    # --- 6. Командные тесты
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

    # --- 7. Участники тестов
    if player_tests:
        try:
            from states.test_set_states import JoinTestSetStates
            if current_state == JoinTestSetStates.waiting_access_code:
                await player_tests.process_player_test_text_input(message, state)
                return
        except ImportError:
            pass

    # --- 8. Неопознанное состояние
    logger.warning(f"⚠️ Неизвестное FSM состояние: {current_state} — очищаем")
    await state.clear()


def register_all_handlers(dp: Dispatcher):
    """✅ Регистрация всех обработчиков и роутеров в правильном порядке"""
    
    logger.info("=" * 60)
    logger.info("🔗 Начинаю регистрацию всех роутеров и обработчиков...")
    logger.info("=" * 60)
    
    # 1. Регистрация функций обработчиков
    start.register_start_handlers(dp)
    logger.info("✅ start handlers зарегистрированы")
    
    exercises.register_exercise_handlers(dp)
    logger.info("✅ exercises handlers зарегистрированы")
    
    workouts.register_workout_handlers(dp)
    logger.info("✅ workouts handlers зарегистрированы")
    
    tests.register_test_handlers(dp)
    logger.info("✅ tests handlers зарегистрированы")
    
    test_batteries.register_battery_handlers(dp)
    logger.info("✅ test_batteries handlers зарегистрированы")
    
    # 2. ✅ ГЛАВНЫЕ РОУТЕРЫ - включаем в правильном порядке!
    dp.include_router(teams.teams_router)
    logger.info("✅ teams_router зарегистрирован (ГЛАВНЫЙ ПРИОРИТЕТ)")
    
    dp.include_router(trainees_router)
    logger.info("✅ trainees_router зарегистрирован")
    
    dp.include_router(workouts_router)
    logger.info("✅ workouts_router зарегистрирован")
    
    # # Попытка регистрации exercises_router если он существует
    # try:
    #     №dp.include_router(exercises_router)
    #     logger.info("✅ exercises_router зарегистрирован")
    # except Exception as e:
    #     logger.warning(f"⚠️ exercises_router не зарегистрирован: {e}")
    
    # 3. Общий роутер в конце (самый низкий приоритет)
    dp.include_router(general_router)
    logger.info("✅ general_router зарегистрирован (последний приоритет)")
    
    # 4. Дополнительные модули
    if team_tests:
        team_tests.register_team_test_handlers(dp)
        logger.info("✅ team_tests handlers зарегистрированы")
    
    if player_tests:
        player_tests.register_player_test_handlers(dp)
        logger.info("✅ player_tests handlers зарегистрированы")
    
    logger.info("=" * 60)
    logger.info("🎉 ВСЕ роутеры и обработчики успешно зарегистрированы!")
    logger.info("=" * 60)


__all__ = ["register_all_handlers", "handle_all_text_messages", "general_router"]