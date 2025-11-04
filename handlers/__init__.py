import logging
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

# Импорт всех подмодулей
from . import start
from . import exercises
from . import workouts
from . import tests
from . import test_batteries
from handlers.teams import TeamStates
#from handlers import workouts
# Дополнительные модули (по наличию)
try:
    from . import team_tests
except ImportError:
    team_tests = None

try:
    from . import player_tests
except ImportError:
    player_tests = None

from . import teams

logger = logging.getLogger(__name__)


#from . import exercise_params
from aiogram.filters import StateFilter


# Общий роутер для текстовых сообщений
general_router = Router(name="general")


# @general_router.message(StateFilter(None))                                               на 3.11
# async def handle_all_text_messages(message: Message, state: FSMContext):
#     """Единый обработчик текстовых сообщений вне контекста других FSM."""
#     current_state = await state.get_state()
#     logger.info(f"Текст: '{message.text}' | Состояние: {current_state}")

#     # FSM состояний команд (TeamsStates)
#     # if current_state and current_state.startswith("TeamStates:"):
#     #     logger.debug(f"➡️ Передаём управление в teams_router для {current_state}")
        

#     if current_state is None:
#         await message.answer(
#             "ℹ️ Используйте меню бота для навигации.\n"
#             "Нажмите /start для возврата в главное меню."
#         )
#         return
#     logger.info(f"FSM: '{message.text}' | Состояние: {current_state}")
#     # Тесты (1ПМ, сила, выносливость и т.д.)
#     if current_state == "waiting_1rm_data":
#         await tests.process_1rm_test_input(message, state)
#         return

#     if current_state in [
#         "waiting_search_for_test",
#         "waiting_strength_test_data",
#         "waiting_endurance_test_data",
#         "waiting_speed_test_data",
#         "waiting_quantity_test_data",
#     ]:
#         await tests.process_test_text_input(message, state)
#         return

#     # Состояния упражнений
#     try:
#         from states.exercise_states import CreateExerciseStates
#         if current_state in [
#             CreateExerciseStates.waiting_name,
#             CreateExerciseStates.waiting_description,
#             CreateExerciseStates.waiting_instructions,
#             "waiting_new_category",
#             "waiting_new_muscle_group",
#             "waiting_custom_equipment",
#             "waiting_search",
#         ]:
#             await exercises.process_exercise_text_input(message, state)
#             return
#     except ImportError:
#         logger.warning("Модуль exercise_states не найден")

    
#     # Состояния тренировок
#     try:
#         from states.workout_states import CreateWorkoutStates
#         WORKOUT_TEXT_STATES = [
#             CreateWorkoutStates.waiting_workout_name,  # ← ЭТОТО!
#             CreateWorkoutStates.waiting_workout_description,
#             CreateWorkoutStates.adding_block_description,
#             CreateWorkoutStates.manual_exercise_input,
#             CreateWorkoutStates.waiting_rpe,
#             CreateWorkoutStates.configuring_exercise,
#         ]
#         if current_state in WORKOUT_TEXT_STATES:
#             await workouts.process_workout_text_input(message, state)
#             return
#     except ImportError:
#         logger.warning("Модуль workout_states не найден")

    

    
    

#     if current_state == CreateWorkoutStates.searching_exercise_for_block:
#                 # Используем ТУ ЖЕ функцию, что и в главном меню!
#                 from handlers.exercises import process_exercise_text_input
#                 await process_exercise_text_input(message, state)
#                 return     
#     # Батареи тестов
#     try:
#         from handlers.test_batteries import (
#             CreateBatteryStates,
#             EditBatteryStates,
#             JoinBatteryStates,
#         )
#         if current_state in [
#             CreateBatteryStates.waiting_name,
#             CreateBatteryStates.waiting_description,
#             CreateBatteryStates.selecting_exercises,
#             EditBatteryStates.adding_exercises,
#             JoinBatteryStates.waiting_battery_code,
#         ]:
#             await test_batteries.process_battery_text_input(message, state)
#             return
#     except ImportError:
#         logger.warning("Модуль test_batteries не найден")

#     # === ДОБАВЛЕНИЕ УПРАЖНЕНИЯ С ПАРАМЕТРАМИ (3 10 75 90) ===
#         if current_state == CreateWorkoutStates.configuring_exercise:
#             await workouts.process_param_input(message, state)
#             return

#     # Командные тесты (если есть)
#     if team_tests:
#         try:
#             from states.test_set_states import CreateTestSetStates
#             if current_state in [
#                 CreateTestSetStates.waiting_name,
#                 CreateTestSetStates.waiting_description,
#                 "searching_exercise_for_test_set",
#             ]:
#                 await team_tests.process_team_test_text_input(message, state)
#                 return
#         except ImportError:
#             pass

#     # Участники тестов (если есть)
#     if player_tests:
#         try:
#             from states.test_set_states import JoinTestSetStates
#             if current_state in [
#                 JoinTestSetStates.waiting_access_code,
#             ]:
#                 await player_tests.process_player_test_text_input(message, state)
#                 return
#         except ImportError:
#             pass

    
    
    
#     # Неопознанное состояние — очищаем
#     logger.warning(f"⚠️ Неизвестное состояние FSM: {current_state}")
    
#     await state.clear()


#  из гпт на 3.11 новый
#@general_router.message(StateFilter(None))
@general_router.message(~StateFilter(None))
async def handle_all_text_messages(message: Message, state: FSMContext):
    """Единый обработчик текстовых сообщений вне контекста других FSM."""
    current_state = await state.get_state()
    logger.info(f"📨 Текст: '{message.text}' | FSM состояние: {current_state}")

    # --- 1. Без состояния (пользователь вне FSM)
    if current_state is None:
        await message.answer(
            "ℹ️ Используйте меню бота для навигации.\n"
            "Нажмите /start для возврата в главное меню."
        )
        return

    # --- 2. Тесты (1ПМ, сила, выносливость и т.п.)
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





def register_all_handlers(dp):
    """Регистрация всех обработчиков и роутеров."""
    start.register_start_handlers(dp)
    exercises.register_exercise_handlers(dp)
    workouts.register_workout_handlers(dp)
    tests.register_test_handlers(dp)
    test_batteries.register_battery_handlers(dp)
    

    # Регистрация опциональных модулей (командные тесты)
    if team_tests:
        team_tests.register_team_test_handlers(dp)
    if player_tests:
        player_tests.register_player_test_handlers(dp)

    logger.info("Все обработчики успешно зарегистрированы")

__all__ = ["register_all_handlers", "handle_all_text_messages", "general_router"]