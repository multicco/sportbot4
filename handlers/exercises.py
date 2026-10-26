import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from states.exercise_states import CreateExerciseStates
from states.workout_states import CreateWorkoutStates
from database import db_manager
from keyboards.exercise_keyboards import (
    get_exercise_search_keyboard, get_categories_keyboard,
    get_equipment_keyboard, get_difficulty_keyboard
)
from utils.validators import (
    validate_exercise_name, validate_exercise_description,
    validate_exercise_instructions
)
from utils.formatters import format_exercise_info
from utils.helpers import _safe_edit_or_send

logger = logging.getLogger(__name__)

exercises_router = Router()


# ===== НАВИГАЦИЯ: СОХРАНЕНИЕ КОНТЕКСТА ("ГДЕ Я БЫЛ") =====
#
# Проблема: кнопки "Назад" были не везде, и пользователь терял прогресс,
# возвращаясь в главное меню. Решение: перед каждым переходом запоминаем
# экран, с которого пришёл пользователь (state.update_data), а кнопка
# "🔙 Назад" ведёт ровно туда, а не в главное меню.
#
# exercise_nav_context может быть:
#   {"type": "search_menu"}                           — меню поиска
#   {"type": "categories"}                            — список категорий
#   {"type": "muscle_groups"}                         — список групп мышц
#   {"type": "category_exercises", "category": ...}   — упражнения категории
#   {"type": "muscle_exercises", "muscle_group": ...} — упражнения группы мышц
#   {"type": "search_results", "query": ...}          — результаты поиска по имени


def _back_button() -> tuple:
    """Текст и callback_data универсальной кнопки «Назад»."""
    return "🔙 Назад", "exercise_back"


async def _remember_context(state: FSMContext, context: dict):
    """Запомнить экран, на котором находится пользователь."""
    try:
        await state.update_data(exercise_nav_context=context)
    except Exception as e:  # state может быть None в редких вызовах
        logger.warning("Не удалось сохранить навигационный контекст: %s", e)


async def _get_context(state: FSMContext) -> dict:
    if state is None:
        return {"type": "search_menu"}
    data = await state.get_data()
    return data.get("exercise_nav_context") or {"type": "search_menu"}


def register_exercise_handlers(dp):
    """Регистрация обработчиков упражнений"""

    # Поиск упражнений
    dp.callback_query.register(search_exercise_menu, F.data == "search_exercise")
    dp.callback_query.register(search_exercise_by_name, F.data == "search_by_name")
    dp.callback_query.register(search_by_category, F.data == "search_by_category")
    dp.callback_query.register(search_by_muscle_group, F.data == "search_by_muscle")
    dp.callback_query.register(show_category_exercises, F.data.startswith("cat_"))
    dp.callback_query.register(show_muscle_group_exercises, F.data.startswith("muscle_"))

    # Детальный просмотр упражнения + универсальная кнопка "Назад"
    # dp.callback_query.register(show_exercise_details, F.data.startswith("exercise_"))
    # Стало (исключить навигационные колбэки exercise_back / exercise_cancel):
    dp.callback_query.register(
    show_exercise_details,
    F.data.startswith("exercise_") & ~F.data.in_(["exercise_back", "exercise_cancel"])
    )


    dp.callback_query.register(universal_back, F.data == "exercise_back")
    # Старый callback оставлен для совместимости со старыми сообщениями
    dp.callback_query.register(back_from_exercise_details, F.data == "back_from_exercise")

    # Создание упражнений (только для тренеров)
    dp.callback_query.register(start_add_exercise, F.data == "add_new_exercise")
    dp.callback_query.register(cancel_exercise_creation, F.data == "cancel_exercise_creation")

    # Выбор категории
    dp.callback_query.register(select_existing_category, F.data == "select_existing_category")
    dp.callback_query.register(choose_category, F.data.startswith("choose_cat_"))
    dp.callback_query.register(create_new_category, F.data == "create_new_category")

    # Выбор группы мышц
    dp.callback_query.register(choose_muscle_group, F.data.startswith("choose_mg_"))
    dp.callback_query.register(create_new_muscle_group, F.data == "create_new_muscle_group")

    # Выбор оборудования
    dp.callback_query.register(choose_equipment, F.data.startswith("choose_eq_"))

    # Выбор сложности
    dp.callback_query.register(choose_difficulty, F.data.startswith("diff_"))

    # Выбор типа теста (сила/скорость/выносливость/функциональные)
    dp.callback_query.register(choose_test_type, F.data.startswith("test_type_"))

    dp.callback_query.register(choose_exercise_category, F.data.startswith("category_"))


# ===== УНИВЕРСАЛЬНАЯ НАВИГАЦИЯ "НАЗАД" =====
async def universal_back(callback: CallbackQuery, state: FSMContext):
    """Возврат на предыдущий экран из любого места раздела упражнений.

    Куда вести — берётся из exercise_nav_context, который сохраняется при
    каждом переходе. Так пользователь не теряет место, откуда он пришёл,
    и ему не нужно выходить в главное меню.
    """
    ctx = await _get_context(state)
    nav_type = ctx.get("type", "search_menu")

    if nav_type == "categories":
        await search_by_category(callback, state)
    elif nav_type == "muscle_groups":
        await search_by_muscle_group(callback, state)
    elif nav_type == "category_exercises":
        # CallbackQuery в aiogram 3.x — frozen-модель pydantic, поле data
        # менять нельзя. Передаём категорию через отдельный helper.
        category = ctx.get("category")
        if category:
            await _render_category_exercises(callback.message, category, state)
        else:
            await search_by_category(callback, state)
    elif nav_type == "muscle_exercises":
        muscle_group = ctx.get("muscle_group")
        if muscle_group:
            await _render_muscle_group_exercises(callback.message, muscle_group, state)
        else:
            await search_by_muscle_group(callback, state)
    elif nav_type == "search_results":
        query = ctx.get("query")
        if query:
            await _show_search_results(callback.message, query)
        else:
            await search_exercise_menu(callback, state)
    elif nav_type == "workout_block":
        # Пользователь выбирал упражнение для блока тренировки —
        # возвращаем его обратно к поиску с сохранённым флагом блока.
        await search_exercise_menu(callback, state)
    else:
        await search_exercise_menu(callback, state)

    await callback.answer()


async def _show_search_results(message: Message, query: str):
    """Перерисовать результаты поиска по названию (для кнопки «Назад»)."""
    search_term = query.lower()
    try:
        async with db_manager.pool.acquire() as conn:
            exercises = await conn.fetch("""
                SELECT id, name, category, muscle_group, description, test_type, tags
                FROM exercises
                WHERE LOWER(name) LIKE $1
                   OR LOWER(category) LIKE $1
                   OR LOWER(muscle_group) LIKE $1
                   OR LOWER(tags) LIKE $1
                ORDER BY name
                LIMIT 15
            """, f"%{search_term}%")

        back_text, back_data = _back_button()

        if exercises:
            text = (
                f"🔍 **Результаты поиска: «{query}»**\n\n"
                f"**Найдено: {len(exercises)} упражнений**\n\n"
                f"💡 **Нажмите на упражнение для детального просмотра:**\n\n"
            )
            keyboard = InlineKeyboardBuilder()
            for ex in exercises:
                test_emoji = {
                    'strength': '🏋️', 'endurance': '⏱️',
                    'speed': '🏃', 'quantity': '🔢', 'none': '💪'
                }.get(ex['test_type'] or 'none', '💪')
                keyboard.button(
                    text=f"{test_emoji} {ex['name']} • {ex['muscle_group']}",
                    callback_data=f"exercise_{ex['id']}"
                )
            keyboard.button(text=back_text, callback_data=back_data)
            keyboard.button(text="🔍 Новый поиск", callback_data="search_by_name")
            keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
            keyboard.adjust(1)
            await message.edit_text(text, reply_markup=keyboard.as_markup(),
                                    parse_mode="Markdown")
        else:
            keyboard = InlineKeyboardBuilder()
            keyboard.button(text="🔙 К поиску", callback_data="search_exercise")
            keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
            await message.edit_text(
                f"❌ Упражнения по запросу «{query}» не найдены",
                reply_markup=keyboard.as_markup()
            )
    except Exception as e:
        await message.edit_text(f"❌ Ошибка: {e}")


# ===== ПОИСК УПРАЖНЕНИЙ =====
async def search_exercise_menu(callback: CallbackQuery, state: FSMContext = None):
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("❌ Пользователь не найден. Нажмите /start", show_alert=True)
        return
    keyboard = get_exercise_search_keyboard(user['role'])

    base_text = (
        "🔍 **Поиск упражнений**\n\n"
        "База содержит упражнения для всех групп мышц\n"
        "и различных уровней подготовки.\n\n"
        "💡 **Нажимайте на упражнения для подробной информации!**\n\n"
    )

    if user['role'] in ['coach', 'admin']:
        trainer_text = "🆕 **Для тренеров:** Можете добавлять новые упражнения!\n\n"
    else:
        trainer_text = ""

    full_text = base_text + trainer_text + "Выберите способ поиска:"

    await callback.message.edit_text(
        full_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

    if state:
        # Запоминаем: теперь пользователь находится в меню поиска
        await _remember_context(state, {"type": "search_menu"})
        current_data = await state.get_data()
        if current_data.get("searching_in_block"):
            await state.update_data(searching_in_block=current_data["searching_in_block"])


async def search_exercise_by_name(callback: CallbackQuery, state: FSMContext):
    # продлеваем контекст
    data = await state.get_data()
    flag = data.get("searching_in_block", False)

    await state.set_state(CreateExerciseStates.waiting_search)
    await state.update_data(searching_in_block=flag)

    # Помним, что пришли из меню поиска
    await _remember_context(state, {"type": "search_menu"})

    await callback.message.edit_text(
        "🔍 **Поиск упражнений по названию**\n\n"
        "Введите название упражнения для поиска:\n"
        "Например: `жим`, `приседания`, `планка`\n\n"
        "💡 **Найденные упражнения будут кликабельными!**",
        parse_mode="Markdown"
    )
    await callback.answer()


async def search_by_category(callback: CallbackQuery, state: FSMContext = None):
    try:
        async with db_manager.pool.acquire() as conn:
            categories = await conn.fetch("SELECT DISTINCT category FROM exercises ORDER BY category")

        back_text, back_data = _back_button()

        # Пересобираем клавиатуру сами, чтобы гарантированно добавить «Назад»
        keyboard = InlineKeyboardBuilder()
        for cat in categories:
            keyboard.button(text=f"📂 {cat['category']}",
                            callback_data=f"cat_{cat['category']}")
        keyboard.button(text=back_text, callback_data=back_data)
        keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
        keyboard.adjust(2)

        await callback.message.edit_text(
            "📂 **Выберите категорию:**\n\n"
            "💡 **Упражнения будут кликабельными для детального просмотра**",
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )
        if state:
            await _remember_context(state, {"type": "categories"})
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    await callback.answer()


async def search_by_muscle_group(callback: CallbackQuery, state: FSMContext = None):
    """Поиск упражнений по группам мышц"""
    try:
        async with db_manager.pool.acquire() as conn:
            muscle_groups = await conn.fetch("SELECT DISTINCT muscle_group FROM exercises ORDER BY muscle_group")

        keyboard = InlineKeyboardBuilder()
        back_text, back_data = _back_button()

        for mg in muscle_groups:
            keyboard.button(
                text=f"💪 {mg['muscle_group']}",
                callback_data=f"muscle_{mg['muscle_group']}"
            )

        keyboard.button(text=back_text, callback_data=back_data)
        keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
        keyboard.adjust(2)

        await callback.message.edit_text(
            "💪 **Выберите группу мышц:**\n\n"
            "💡 **Упражнения будут кликабельными для детального просмотра**",
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )
        if state:
            await _remember_context(state, {"type": "muscle_groups"})
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    await callback.answer()


async def _render_category_exercises(message: Message, category: str, state: FSMContext = None):
    """Отрисовать экран упражнений категории (без зависимости от callback.data).

    Используется и обработчиком клика, и кнопкой «Назад» (universal_back),
    у которой нельзя менять frozen-поле callback.data.
    """
    try:
        async with db_manager.pool.acquire() as conn:
            exercises = await conn.fetch(
                "SELECT id, name, muscle_group, description, test_type FROM exercises WHERE category = $1 ORDER BY name",
                category
            )

        back_text, back_data = _back_button()

        if exercises:
            text = f"📂 **Категория: {category}**\n\n"
            text += f"**Найдено упражнений: {len(exercises)}**\n"
            text += f"💡 **Нажмите на упражнение для детального просмотра**\n\n"

            keyboard = InlineKeyboardBuilder()

            for ex in exercises:
                test_emoji = {
                    'strength': '🏋️',
                    'endurance': '⏱️',
                    'speed': '🏃',
                    'quantity': '🔢',
                    'none': '💪'
                }.get(ex['test_type'] if ex['test_type'] else 'none', '💪')

                keyboard.button(
                    text=f"{test_emoji} {ex['name']}",
                    callback_data=f"exercise_{ex['id']}"
                )

            keyboard.button(text=back_text, callback_data=back_data)
            keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
            keyboard.adjust(1)

            await message.edit_text(
                text,
                reply_markup=keyboard.as_markup(),
                parse_mode="Markdown"
            )
            if state:
                # Запоминаем список упражнений этой категории — «Назад» из
                # карточки упражнения вернёт именно сюда
                await _remember_context(state, {"type": "category_exercises",
                                                "category": category})
        else:
            keyboard = InlineKeyboardBuilder()
            keyboard.button(text="🔙 К категориям", callback_data="search_by_category")
            keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
            await message.edit_text(
                f"❌ Упражнения в категории '{category}' не найдены",
                reply_markup=keyboard.as_markup()
            )

    except Exception as e:
        try:
            await message.edit_text(f"❌ Ошибка: {e}")
        except Exception:
            pass


async def show_category_exercises(callback: CallbackQuery, state: FSMContext = None):
    """Показать упражнения категории С КЛИКАБЕЛЬНЫМИ КНОПКАМИ"""
    category = callback.data[4:]
    await _render_category_exercises(callback.message, category, state)
    await callback.answer()


async def _render_muscle_group_exercises(message: Message, muscle_group: str, state: FSMContext = None):
    """Отрисовать экран упражнений группы мышц (без зависимости от callback.data)."""
    try:
        async with db_manager.pool.acquire() as conn:
            exercises = await conn.fetch(
                "SELECT id, name, category, description, test_type FROM exercises WHERE muscle_group = $1 ORDER BY name",
                muscle_group
            )

        back_text, back_data = _back_button()

        if exercises:
            text = f"💪 **Группа мышц: {muscle_group}**\n\n"
            text += f"**Найдено упражнений: {len(exercises)}**\n"
            text += f"💡 **Нажмите на упражнение для детального просмотра**\n\n"

            keyboard = InlineKeyboardBuilder()

            for ex in exercises:
                test_emoji = {
                    'strength': '🏋️',
                    'endurance': '⏱️',
                    'speed': '🏃',
                    'quantity': '🔢',
                    'none': '💪'
                }.get(ex['test_type'] if ex['test_type'] else 'none', '💪')

                keyboard.button(
                    text=f"{test_emoji} {ex['name']} ({ex['category']})",
                    callback_data=f"exercise_{ex['id']}"
                )

            keyboard.button(text=back_text, callback_data=back_data)
            keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
            keyboard.adjust(1)

            await message.edit_text(
                text,
                reply_markup=keyboard.as_markup(),
                parse_mode="Markdown"
            )
            if state:
                await _remember_context(state, {"type": "muscle_exercises",
                                                "muscle_group": muscle_group})
        else:
            keyboard = InlineKeyboardBuilder()
            keyboard.button(text="🔙 К группам мышц", callback_data="search_by_muscle")
            keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
            await message.edit_text(
                f"❌ Упражнения для группы '{muscle_group}' не найдены",
                reply_markup=keyboard.as_markup()
            )

    except Exception as e:
        try:
            await message.edit_text(f"❌ Ошибка: {e}")
        except Exception:
            pass


async def show_muscle_group_exercises(callback: CallbackQuery, state: FSMContext = None):
    """Показать упражнения группы мышц С КЛИКАБЕЛЬНЫМИ КНОПКАМИ"""
    muscle_group = callback.data[7:]  # Убираем "muscle_"
    await _render_muscle_group_exercises(callback.message, muscle_group, state)
    await callback.answer()


# ===== ДЕТАЛЬНЫЙ ПРОСМОТР УПРАЖНЕНИЯ =====
async def show_exercise_details(callback: CallbackQuery, state: FSMContext):
    """Показать детальную информацию об упражнении"""
    exercise_id = int(callback.data.split("_")[1])

    try:
        async with db_manager.pool.acquire() as conn:
            exercise = await conn.fetchrow("""
            SELECT e.*, u.first_name as author_name
            FROM exercises e
            LEFT JOIN users u ON e.created_by = u.id
            WHERE e.id = $1
            """, exercise_id)

        if not exercise:
            keyboard = InlineKeyboardBuilder()
            keyboard.button(text="🔙 Назад", callback_data="exercise_back")
            await callback.message.edit_text("❌ Упражнение не найдено",
                                             reply_markup=keyboard.as_markup())
            await callback.answer()
            return

        data = await state.get_data()
        current_block = data.get("current_block")  # Есть блок = создаём тренировку

        # Сохраняем для навигации
        await state.update_data(
            current_exercise_id=exercise_id,
            last_search_context="details"
        )

        user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer("❌ Пользователь не найден. Нажмите /start", show_alert=True)
            return

        personal_record = await get_user_best_test_result(user['id'], exercise_id)

        text = format_exercise_info(dict(exercise))

        if exercise['tags']:
            # Превращаем " #футбол,#дом " в красивый список
            tags_list = exercise['tags'].split(',')
            tags_text = " ".join(tags_list)
            text += f"\n\n🏷 **Теги:** {tags_text}"

        # format_exercise_info() уже выводит тип теста и единицу измерения,
        # поэтому здесь добавляем только персональный рекорд (без дубля).
        test_type = exercise['test_type'] or 'none'
        if test_type != 'none':
            if personal_record:
                text += (f"\n\n🏆 **Ваш рекорд:** {personal_record['result_value']} "
                         f"{personal_record['result_unit']}\n")
                text += (f"📅 Дата: "
                         f"{personal_record['tested_at'].strftime('%d.%m.%Y')}\n")
            else:
                text += f"\n\n📝 **Тестов пока нет** – пройдите первый!\n"

        if exercise['author_name']:
            text += f"\n👤 **Автор:** {exercise['author_name']}"

        keyboard = InlineKeyboardBuilder()

        if test_type != 'none':
            keyboard.button(text="🔬 Пройти тест",
                            callback_data=f"test_{exercise_id}")

        if current_block:
            keyboard.button(text="🏋️ Использовать в тренировке",
                            callback_data=f"use_in_workout_{exercise_id}")

        # Кнопка «Назад» ведёт туда, откуда пользователь открыл карточку
        # (список категории / группа мышц / результаты поиска / меню поиска)
        keyboard.button(text="🔙 Назад", callback_data="exercise_back")
        keyboard.button(text="🏠 Главное меню", callback_data="main_menu")

        keyboard.adjust(1)

        await callback.message.edit_text(text,
                                         reply_markup=keyboard.as_markup(),
                                         parse_mode="Markdown")

    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")

    await callback.answer()


async def back_from_exercise_details(callback: CallbackQuery, state: FSMContext):
    """Старый callback back_from_exercise — теперь работает как универсальный «Назад»."""
    await universal_back(callback, state)


# ===== СОЗДАНИЕ НОВОГО УПРАЖНЕНИЯ =====
async def start_add_exercise(callback: CallbackQuery, state: FSMContext):
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)

    # Проверка прав доступа
    if not user or user['role'] not in ['coach', 'admin']:
        await callback.answer("❌ Только тренеры могут добавлять упражнения!")
        return

    await callback.message.edit_text(
        "➕ **Добавление нового упражнения**\n\n"
        "🏋️ **Вы создаете упражнение для всех пользователей системы!**\n\n"
        "Введите **название упражнения**:\n"
        "_Например: \"Жим гантелей на наклонной скамье\" или \"Планка с подъемом ног\"_\n\n"
        "Чтобы отменить — отправьте `/cancel`",
        parse_mode="Markdown"
    )
    await state.set_state(CreateExerciseStates.waiting_name)
    await callback.answer()


async def cancel_exercise_creation(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔍 К поиску", callback_data="search_exercise")
    keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
    keyboard.adjust(1)
    await callback.message.edit_text(
        "❌ **Создание упражнения отменено**",
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()


async def select_existing_category(callback: CallbackQuery, state: FSMContext):
    try:
        async with db_manager.pool.acquire() as conn:
            categories = await conn.fetch("SELECT DISTINCT category FROM exercises ORDER BY category")

        keyboard = InlineKeyboardBuilder()

        for cat in categories:
            keyboard.button(
                text=f"📂 {cat['category']}",
                callback_data=f"choose_cat_{cat['category']}"
            )

        keyboard.button(text="📝 Создать новую категорию", callback_data="create_new_category")
        keyboard.button(text="❌ Отменить", callback_data="cancel_exercise_creation")
        keyboard.adjust(2)

        await callback.message.edit_text(
            "📂 **Выберите существующую категорию:**\n\n",
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    await callback.answer()


async def choose_category(callback: CallbackQuery, state: FSMContext):
    category = callback.data[11:]  # Убираем "choose_cat_"
    await state.update_data(category=category)
    await ask_muscle_group(callback.message, state, edit=True)
    await callback.answer()


async def create_new_category(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "📝 **Создание новой категории**\n\n"
        "Введите название новой категории упражнений:\n"
        "_Например: \"Кроссфит\", \"Реабилитация\", \"Йога\"_\n\n"
        "**Существующие категории:**\n"
        "• Силовые\n"
        "• Функциональные\n"
        "• Кардио\n"
        "• Растяжка\n\n"
        "Чтобы вернуться назад — отправьте `/cancel`",
        parse_mode="Markdown"
    )
    await state.set_state(CreateExerciseStates.waiting_new_category)
    await callback.answer()


async def ask_muscle_group(message: Message, state: FSMContext, edit: bool = False):
    try:
        async with db_manager.pool.acquire() as conn:
            muscle_groups = await conn.fetch("SELECT DISTINCT muscle_group FROM exercises ORDER BY muscle_group")

        keyboard = InlineKeyboardBuilder()

        for mg in muscle_groups:
            keyboard.button(
                text=f"💪 {mg['muscle_group']}",
                callback_data=f"choose_mg_{mg['muscle_group']}"
            )

        keyboard.button(text="📝 Создать новую группу", callback_data="create_new_muscle_group")
        keyboard.button(text="❌ Отменить", callback_data="cancel_exercise_creation")
        keyboard.adjust(3)

        text = "💪 **Выберите группу мышц:**\n\n"
        text += "_Отправить `/cancel` — отменить создание_\n"

        if edit:
            await message.edit_text(text, reply_markup=keyboard.as_markup(), parse_mode="Markdown")
        else:
            await message.answer(text, reply_markup=keyboard.as_markup(), parse_mode="Markdown")

    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


async def choose_muscle_group(callback: CallbackQuery, state: FSMContext):
    muscle_group = callback.data[10:]  # Убираем "choose_mg_"
    await state.update_data(muscle_group=muscle_group)
    await ask_equipment(callback.message, state, edit=True)
    await callback.answer()


async def create_new_muscle_group(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "💪 **Создание новой группы мышц**\n\n"
        "Введите название группы мышц:\n"
        "_Например: \"Предплечья\", \"Шея\", \"Стабилизаторы\"_\n\n"
        "Чтобы вернуться назад — отправьте `/cancel`",
        parse_mode="Markdown"
    )
    await state.set_state(CreateExerciseStates.waiting_new_muscle_group)
    await callback.answer()


async def ask_equipment(message: Message, state: FSMContext, edit: bool = False):
    keyboard = get_equipment_keyboard()
    text = ("🏋️ **Выберите необходимое оборудование:**\n\n"
            "_Отправить `/cancel` — отменить создание_\n")

    if edit:
        await message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")


async def choose_equipment(callback: CallbackQuery, state: FSMContext):
    equipment = callback.data[10:]  # Убираем "choose_eq_"

    if equipment == "Другое":
        await callback.message.edit_text(
            "🔧 **Укажите оборудование**\n\n"
            "Введите название оборудования:\n"
            "_Например: \"TRX петли\", \"Медицинский мяч\"_\n\n"
            "Чтобы вернуться назад — отправьте `/cancel`",
            parse_mode="Markdown"
        )
        await state.set_state(CreateExerciseStates.waiting_custom_equipment)
        await callback.answer()
        return

    await state.update_data(equipment=equipment)
    await ask_difficulty(callback.message, state, edit=True)
    await callback.answer()


async def ask_difficulty(message: Message, state: FSMContext, edit: bool = False):
    keyboard = get_difficulty_keyboard()
    text = ("⭐ **Выберите уровень сложности:**\n\n"
            "_Отправить `/cancel` — отменить создание_\n")

    if edit:
        await message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")


async def choose_difficulty(callback: CallbackQuery, state: FSMContext):
    difficulty = callback.data[5:]  # Убираем "diff_"
    await state.update_data(difficulty_level=difficulty)

    # Переходим к выбору типа теста (сила/скорость/выносливость/функциональные).
    # Раньше здесь клавиатура типа теста сразу перезатиралась текстом описания.
    await state.set_state(CreateExerciseStates.waiting_test_type)
    await ask_test_type(callback.message, state)
    await callback.answer()


# ===== ОБРАБОТКА ВВОДА ДАННЫХ =====
async def process_exercise_name(message: Message, state: FSMContext):
    exercise_name = message.text.strip()
    validation = validate_exercise_name(exercise_name)

    if not validation['valid']:
        await message.answer(validation['error'])
        return

    # Проверяем, нет ли уже такого упражнения
    try:
        async with db_manager.pool.acquire() as conn:
            existing = await conn.fetchrow(
                "SELECT name FROM exercises WHERE LOWER(name) = LOWER($1)",
                exercise_name
            )

        if existing:
            await message.answer(f"❌ Упражнение '{exercise_name}' уже существует в базе!")
            return

    except Exception as e:
        await message.answer(f"❌ Ошибка проверки: {e}")
        return

    await state.update_data(name=exercise_name)
    await ask_exercise_category(message, state)


async def ask_test_type(message: Message, state: FSMContext):
    kb = InlineKeyboardBuilder()
    kb.button(text="💪 Сила", callback_data="test_type_strength")
    kb.button(text="🏃 Скорость", callback_data="test_type_speed")
    kb.button(text="⏱️ Выносливость", callback_data="test_type_endurance")
    kb.button(text="🔢 Функциональные", callback_data="test_type_quantity")
    kb.button(text="❌ Отмена", callback_data="cancel_exercise_creation")
    kb.adjust(1)

    await _safe_edit_or_send(
        message,
        "🧩 **Выберите тип упражнения**\n\n"
        "Это важно для правильного расчёта % в тренировках:\n"
        "• Сила — вес от 1ПМ\n"
        "• Скорость — время (медленнее рекорда)\n"
        "• Выносливость — время (короче рекорда)\n"
        "• Функциональные — повторения",
        reply_markup=kb.as_markup(),
        parse_mode="Markdown"
    )


async def choose_test_type(callback: CallbackQuery, state: FSMContext):
    test_type_map = {
        "strength": "strength",
        "speed": "speed",
        "endurance": "endurance",
        "quantity": "quantity"
    }
    test_type = test_type_map.get(callback.data.split("_")[-1])

    if not test_type:
        await callback.answer("Ошибка выбора типа", show_alert=True)
        return

    await state.update_data(test_type=test_type)

    await callback.message.edit_text(
        "📝 **Введите описание упражнения**\n\n"
        "Кратко о технике и работающих мышцах (10–500 символов):\n\n"
        "Чтобы отменить — отправьте `/cancel`",
        parse_mode="Markdown"
    )
    await state.set_state(CreateExerciseStates.waiting_description)
    await callback.answer()


async def select_existing_category_for_new_exercise(message: Message, state: FSMContext):
    try:
        async with db_manager.pool.acquire() as conn:
            categories = await conn.fetch("SELECT DISTINCT category FROM exercises ORDER BY category")

        keyboard = InlineKeyboardBuilder()

        for cat in categories:
            keyboard.button(
                text=f"📂 {cat['category']}",
                callback_data=f"choose_cat_{cat['category']}"
            )

        keyboard.button(text="📝 Новая категория", callback_data="create_new_category")
        keyboard.button(text="❌ Отменить", callback_data="cancel_exercise_creation")
        keyboard.adjust(2)

        await message.answer(
            "📂 **Выберите категорию:**\n\n",
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


async def process_exercise_description(message: Message, state: FSMContext):
    description = message.text.strip()
    validation = validate_exercise_description(description)

    if not validation['valid']:
        await message.answer(validation['error'])
        return

    await state.update_data(description=description)

    await message.answer(
        "📋 **Инструкции по выполнению**\n\n"
        "Введите подробные инструкции по технике выполнения:\n\n"
        "Чтобы отменить — отправьте `/cancel`",
        parse_mode="Markdown"
    )
    await state.set_state(CreateExerciseStates.waiting_instructions)


async def process_exercise_instructions(message: Message, state: FSMContext):
    instructions = message.text.strip()
    validation = validate_exercise_instructions(instructions)
    if not validation['valid']:
        await message.answer(validation['error'])
        return

    await state.update_data(instructions=instructions)

    await state.set_state(CreateExerciseStates.waiting_tags)
    await message.answer(
        "🏷 **Хештеги для поиска**\n\n"
        "Введите теги через запятую (например: `дом, реабилитация, икры`).\n"
        "Чтобы пропустить, отправьте `-`\n\n"
        "Чтобы отменить — отправьте `/cancel`",
        parse_mode="Markdown"
    )


async def save_new_exercise(message: Message, state: FSMContext):
    data = await state.get_data()
    user = await db_manager.get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("❌ Пользователь не найден. Нажмите /start")
        return

    # Единица измерения зависит от типа теста
    test_type = data.get('test_type') or 'strength'
    measurement_unit = {
        'strength': 'kg',
        'speed': 'seconds',
        'endurance': 'seconds',
        'quantity': 'reps',
    }.get(test_type, 'kg')

    try:
        async with db_manager.pool.acquire() as conn:
            exercise_id = await conn.fetchval("""
                INSERT INTO exercises (
                    name, category, muscle_group, equipment,
                    difficulty_level, description, instructions,
                    test_type, created_by, tags, measurement_unit
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                RETURNING id
            """,
                data['name'], data['category'], data['muscle_group'],
                data['equipment'], data['difficulty_level'],
                data['description'], data['instructions'],
                test_type,
                user['id'],
                data.get('tags') or '',
                measurement_unit
            )

        # Успешное создание
        text = f"🎉 **Упражнение создано успешно!**\n\n"
        text += f"💪 **Название:** {data['name']}\n"
        text += f"📂 **Категория:** {data['category']}\n"
        text += f"🎯 **Группа мышц:** {data['muscle_group']}\n"
        text += f"🔧 **Оборудование:** {data['equipment']}\n"
        text += f"⭐ **Сложность:** {data['difficulty_level']}\n"
        text += f"**ID упражнения:** {exercise_id}"

        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="➕ Создать еще", callback_data="add_new_exercise")
        keyboard.button(text="🔍 К поиску", callback_data="search_exercise")
        keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
        keyboard.adjust(2)

        await message.answer(
            text,
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )

        await state.clear()

    except Exception as e:
        await message.answer(f"❌ Ошибка сохранения: {e}")


# ===== ОБРАБОТКА ПОИСКА УПРАЖНЕНИЙ =====
async def handle_exercise_search(message: Message, state: FSMContext):
    search_term = message.text.lower()

    # 1. сохраняем контекст «ищу для блока»
    data = await state.get_data()
    flag = data.get("searching_in_block", False)

    try:
        async with db_manager.pool.acquire() as conn:
            exercises = await conn.fetch("""
                SELECT id, name, category, muscle_group, description, test_type, tags
                FROM exercises
                WHERE LOWER(name) LIKE $1
                   OR LOWER(category) LIKE $1
                   OR LOWER(muscle_group) LIKE $1
                   OR LOWER(tags) LIKE $1  -- <--- ПОИСК ПО ТЕГАМ
                ORDER BY name
                LIMIT 15
            """, f"%{search_term}%")

        back_text, back_data = _back_button()

        if exercises:
            text = (
                f"🔍 **Найдено: {len(exercises)} упражнений**\n\n"
                f"💡 **Нажмите на упражнение для детального просмотра:**\n\n"
            )

            keyboard = InlineKeyboardBuilder()
            for ex in exercises:
                test_emoji = {
                    'strength': '🏋️', 'endurance': '⏱️',
                    'speed': '🏃', 'quantity': '🔢', 'none': '💪'
                }.get(ex['test_type'] or 'none', '💪')

                keyboard.button(
                    text=f"{test_emoji} {ex['name']} • {ex['muscle_group']}",
                    callback_data=f"exercise_{ex['id']}"
                )

            keyboard.button(text=back_text, callback_data=back_data)
            keyboard.button(text="🔍 Новый поиск", callback_data="search_by_name")
            keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
            keyboard.adjust(1)

            await message.answer(text, reply_markup=keyboard.as_markup(), parse_mode="Markdown")

        else:
            text = (
                f"❌ Упражнения по запросу '{search_term}' не найдены\n\n"
                f"Попробуйте другие ключевые слова."
            )
            keyboard = InlineKeyboardBuilder()
            keyboard.button(text="🔍 Новый поиск", callback_data="search_by_name")
            keyboard.button(text="🔙 К поиску", callback_data="search_exercise")
            keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
            keyboard.adjust(1)

            await message.answer(text, reply_markup=keyboard.as_markup(), parse_mode="Markdown")

        # 2. продлеваем флаг, очищаем только состояние ввода
        await state.update_data(searching_in_block=flag)
        await state.set_state(None)          # выходим из waiting_search, но данные остаются

        # 3. запоминаем результаты поиска — «Назад» из карточки вернёт сюда
        await _remember_context(state, {"type": "search_results", "query": message.text.strip()})

    except Exception as e:
        await message.answer(f"❌ Ошибка поиска: {e}")


# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====
async def get_user_best_test_result(user_id: int, exercise_id: int):
    """Получить ЛУЧШИЙ результат пользователя по упражнению.

    Для силовых и количественных тестов лучшим считается максимум,
    для скоростных и тестов на выносливость (время) — минимум.
    """
    try:
        async with db_manager.pool.acquire() as conn:
            # Проверяем есть ли таблица user_tests
            table_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'user_tests'
                )
            """)

            if not table_exists:
                return None

            rows = await conn.fetch("""
                SELECT result_value, result_unit, tested_at, test_type
                FROM user_tests
                WHERE user_id = $1 AND exercise_id = $2
                  AND result_value IS NOT NULL
            """, user_id, exercise_id)

        if not rows:
            return None

        records = [dict(r) for r in rows]
        test_type = records[0].get('test_type')

        if test_type in ('speed', 'endurance'):
            # Меньше времени — лучше результат
            best = min(records, key=lambda r: r['result_value'])
        else:
            # Больше вес/повторения — лучше результат
            best = max(records, key=lambda r: r['result_value'])

        return best
    except Exception:
        return None


# функция обработки хештегов
async def process_exercise_tags(message: Message, state: FSMContext):
    text = message.text.strip()
    tags = ""

    if text.lower() not in ['-', 'нет', 'no', 'skip']:
        # Нормализация: убираем лишние пробелы, приводим к нижнему регистру
        # Сохраняем в формате: #tag1,#tag2,#tag3
        raw_tags = [t.strip().lower() for t in text.split(',')]
        clean_tags = []
        for t in raw_tags:
            if t:
                if not t.startswith('#'):
                    t = '#' + t
                clean_tags.append(t)
        tags = ','.join(clean_tags)

    await state.update_data(tags=tags)
    await save_new_exercise(message, state)


# ===== ОБРАБОТКА ТЕКСТОВЫХ СОСТОЯНИЙ =====
async def process_exercise_text_input(message: Message, state: FSMContext):
    """Обработка текстовых вводов для создания упражнений"""
    current_state = await state.get_state()

    if current_state == CreateExerciseStates.waiting_name:
        await process_exercise_name(message, state)

    elif current_state == CreateExerciseStates.waiting_new_category:
        category = message.text.strip()
        if len(category) < 3 or len(category) > 50:
            await message.answer("❌ Название категории должно быть от 3 до 50 символов")
            return
        await state.update_data(category=category)
        await ask_muscle_group(message, state)

    elif current_state == CreateExerciseStates.waiting_new_muscle_group:
        muscle_group = message.text.strip()
        if len(muscle_group) < 3 or len(muscle_group) > 50:
            await message.answer("❌ Название группы мышц должно быть от 3 до 50 символов")
            return
        await state.update_data(muscle_group=muscle_group)
        await ask_equipment(message, state)

    elif current_state == CreateExerciseStates.waiting_custom_equipment:
        equipment = message.text.strip()
        if len(equipment) < 2 or len(equipment) > 50:
            await message.answer("❌ Название оборудования должно быть от 2 до 50 символов")
            return
        await state.update_data(equipment=equipment)
        await ask_difficulty(message, state)

    elif current_state == CreateExerciseStates.waiting_description:
        await process_exercise_description(message, state)

    elif current_state == CreateExerciseStates.waiting_instructions:
        await process_exercise_instructions(message, state)

    elif current_state == CreateExerciseStates.waiting_tags:
        await process_exercise_tags(message, state)

    elif current_state == CreateExerciseStates.waiting_search:
        await handle_exercise_search(message, state)


def get_exercise_category_keyboard() -> InlineKeyboardBuilder:
    """Клавиатура выбора категории + типа теста."""
    kb = InlineKeyboardBuilder()
    kb.button(text="💪 Силовые",        callback_data="category_strength")
    kb.button(text="🏃 Скорость",        callback_data="category_speed")
    kb.button(text="⏱️ Выносливость",   callback_data="category_endurance")
    kb.button(text="🔢 Функциональные", callback_data="category_quantity")
    kb.button(text="❌ Отмена",         callback_data="cancel_exercise_creation")
    kb.adjust(2, 2, 1)          # 2×2 и отдельная «Отмена»
    return kb


async def ask_exercise_category(message: Message, state: FSMContext, *, edit: bool = False):
    """Показать выбор категории после имени."""
    text = (
        "📂 Выберите категорию упражнения\n\n"
        "Это задаст тип теста для рекордов и %:\n"
        "• Силовые — вес от 1ПМ\n"
        "• Скорость — время (медленнее)\n"
        "• Выносливость — время (короче)\n"
        "• Функциональные — повторения\n\n"
        "_Отправить `/cancel` — отменить создание_\n"
    )
    kb = get_exercise_category_keyboard().as_markup()
    if edit:
        await message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    else:
        await message.answer(text, reply_markup=kb, parse_mode="Markdown")


async def choose_exercise_category(callback: CallbackQuery, state: FSMContext):
    """Сохраняем category + test_type и переходим к мышцам."""
    mapping = {
        "category_strength":   ("Силовые",        "strength"),
        "category_speed":      ("Скоростные",     "speed"),
        "category_endurance":  ("Выносливость",   "endurance"),
        "category_quantity":   ("Функциональные", "quantity"),
    }
    raw = callback.data                       # например "category_endurance"
    if raw not in mapping:
        await callback.answer("Неверная категория", show_alert=True)
        return
    category, test_type = mapping[raw]
    await state.update_data(category=category, test_type=test_type)
    await callback.answer()

    await ask_muscle_group(callback.message, state, edit=True)


__all__ = ['register_exercise_handlers', 'process_exercise_text_input']