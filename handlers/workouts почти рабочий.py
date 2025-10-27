# handlers/workouts.py
# UTF-8 version — восстановленная и расширенная логика тренировок
import logging
from typing import Optional, List, Dict
from datetime import datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import db_manager
from states.workout_states import CreateWorkoutStates

logger = logging.getLogger(__name__)

workouts_router = Router()

# -----------------------
# Utilities
# -----------------------
def parse_callback_id(callback_data: str, expected_prefix: str = None) -> int:
    """Универсальная функция парсинга ID из callback_data"""
    try:
        if expected_prefix and callback_data.startswith(expected_prefix):
            return int(callback_data.replace(expected_prefix, ""))

        parts = callback_data.split("_")
        if len(parts) < 2:
            raise ValueError(f"Неверный формат callback_data: {callback_data}")

        return int(parts[-1])

    except (ValueError, IndexError) as e:
        logger.error(f"Ошибка парсинга callback_data '{callback_data}': {e}")
        raise ValueError(f"Не удалось извлечь ID из callback_data: {callback_data}")

# -----------------------
# Меню тренировок
# -----------------------
@workouts_router.callback_query(F.data == "workouts_menu")
async def workouts_menu(callback: CallbackQuery):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🏋️ Мои тренировки", callback_data="my_workouts")
    keyboard.button(text="🔍 Найти тренировку", callback_data="find_workout")
    keyboard.button(text="➕ Создать тренировку", callback_data="create_workout")
    keyboard.button(text="📊 Моя статистика", callback_data="workout_statistics")
    keyboard.button(text="🔙 Главное меню", callback_data="main_menu")
    keyboard.adjust(2)

    await callback.message.edit_text(
        "🏋️ **Меню тренировок**\n\n"
        "Выберите действие:",
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()

# -----------------------
# Мои тренировки
# -----------------------
@workouts_router.callback_query(F.data == "my_workouts")
async def my_workouts(callback: CallbackQuery):
    """Показать тренировки пользователя (последние 10 активных)"""
    try:
        user = await db_manager.get_user_by_telegram_id(callback.from_user.id)

        async with db_manager.pool.acquire() as conn:
            workouts = await conn.fetch("""
                SELECT w.*, COUNT(we.id) as exercise_count
                FROM workouts w
                LEFT JOIN workout_exercises we ON w.id = we.workout_id
                WHERE w.created_by = $1 AND w.is_active = true
                GROUP BY w.id
                ORDER BY w.created_at DESC
                LIMIT 10
            """, user['id'])

        if workouts:
            text = f"🏋️ **Мои тренировки ({len(workouts)}):**\n\n"
            keyboard = InlineKeyboardBuilder()

            for workout in workouts:
                exercise_count = workout['exercise_count'] or 0
                duration = workout.get('estimated_duration_minutes') or 0

                button_text = f"🏋️ {workout['name']}"
                if exercise_count > 0:
                    button_text += f" ({exercise_count} упр.)"

                keyboard.button(
                    text=button_text,
                    callback_data=f"view_workout_{workout['id']}"
                )

                text += f"**{workout['name']}**\n"
                text += f"📋 Упражнений: {exercise_count} | ⏱ ~{duration} мин\n"
                text += f"💡 Код: `{workout['unique_id']}`\n\n"

            keyboard.button(text="➕ Создать новую", callback_data="create_workout")
            keyboard.button(text="🔙 К тренингам", callback_data="workouts_menu")
            keyboard.adjust(1)

        else:
            text = ("🏋️ **Мои тренировки**\n\n"
                    "У вас пока нет сохранённых тренировок.\n\n"
                    "Создайте первую тренировку с блочной структурой!")
            keyboard = InlineKeyboardBuilder()
            keyboard.button(text="➕ Создать первую", callback_data="create_workout")
            keyboard.button(text="🔙 К тренировкам", callback_data="workouts_menu")

        await callback.message.edit_text(text, reply_markup=keyboard.as_markup(), parse_mode="Markdown")
        await callback.answer()

    except Exception as e:
        logger.exception("Ошибка в my_workouts: %s", e)
        await callback.answer("❌ Ошибка при получении тренировок.", show_alert=True)

# -----------------------
# Просмотр деталей тренировки
# -----------------------
@workouts_router.callback_query(F.data.startswith("view_workout_"))
async def view_workout_details(callback: CallbackQuery):
    try:
        workout_id = parse_callback_id(callback.data, "view_workout_")

        logger.info("Просмотр тренировки ID: %s", workout_id)

        async with db_manager.pool.acquire() as conn:
            workout = await conn.fetchrow("""
                SELECT w.*, u.first_name as creator_name, u.last_name as creator_lastname
                FROM workouts w
                LEFT JOIN users u ON w.created_by = u.id  
                WHERE w.id = $1 AND w.is_active = true
            """, workout_id)

            if not workout:
                await callback.answer("❌ Тренировка не найдена", show_alert=True)
                return

            exercises = await conn.fetch("""
                SELECT we.*, e.name as exercise_name, e.muscle_group, e.category, we.order_in_phase
                FROM workout_exercises we
                JOIN exercises e ON we.exercise_id = e.id
                WHERE we.workout_id = $1
                ORDER BY 
                    CASE we.phase 
                        WHEN 'warmup' THEN 1
                        WHEN 'nervous_prep' THEN 2
                        WHEN 'main' THEN 3
                        WHEN 'cooldown' THEN 4
                        ELSE 5
                    END,
                    we.order_in_phase
            """, workout_id)

        creator_name = workout.get('creator_name') or ''
        if workout.get('creator_lastname'):
            creator_name = f"{creator_name} {workout.get('creator_lastname')}"

        text = f"🏋️ **{workout['name']}**\n\n"
        if workout.get('description'):
            text += f"📝 _{workout['description']}_\n\n"

        text += f"👤 **Автор:** {creator_name or 'неизвестен'}\n"
        text += f"⏱ **Время:** ~{workout.get('estimated_duration_minutes') or 0} мин\n"
        text += f"⚙️ **Сложность:** {str(workout.get('difficulty_level') or '').title()}\n"
        text += f"🏷 **Категория:** {str(workout.get('category') or 'general').title()}\n"
        text += f"💡 **Код:** `{workout.get('unique_id')}`\n"
        text += f"🔒 **Видимость:** {workout.get('visibility')}\n\n"

        if exercises:
            phase_names = {
                'warmup': '🔥 Разминка',
                'nervous_prep': '⚡ Подготовка НС',
                'main': '💪 Основная часть',
                'cooldown': '🧘 Заминка'
            }

            current_phase = None
            exercise_count = 0

            for exercise in exercises:
                if exercise['phase'] != current_phase:
                    current_phase = exercise['phase']
                    phase_display = phase_names.get(current_phase, current_phase.title())
                    text += f"\n**{phase_display}:**\n"

                exercise_count += 1

                if exercise['reps_min'] == exercise['reps_max']:
                    reps_text = f"{exercise['reps_min']}"
                else:
                    reps_text = f"{exercise['reps_min']}-{exercise['reps_max']}"

                text += f"• **{exercise['exercise_name']}**\n"
                text += f"  🔁 {exercise['sets']} подходов × {reps_text} повт."

                if exercise.get('one_rm_percent'):
                    text += f" ({exercise['one_rm_percent']}% 1ПМ)"

                rest_seconds = exercise.get('rest_seconds') or 0
                if rest_seconds > 0:
                    rest_min = rest_seconds // 60
                    rest_sec = rest_seconds % 60
                    if rest_min > 0:
                        if rest_sec > 0:
                            text += f" | Отдых: {rest_min} мин {rest_sec} с"
                        else:
                            text += f" | Отдых: {rest_min} мин"
                    else:
                        text += f" | Отдых: {rest_sec} с"

                text += f"\n  🧠 {exercise.get('muscle_group', '-') } | {exercise.get('category', '-')}\n"

                if exercise.get('notes'):
                    text += f"  📝 _{exercise['notes']}_\n"

                text += "\n"

            text += f"✅ **Всего упражнений:** {exercise_count}\n"
        else:
            text += "⚠️ В тренировке пока нет упражнений.\n"

        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="▶️ Начать тренировку", callback_data=f"start_workout_{workout_id}")
        keyboard.button(text="📊 Статистика", callback_data=f"workout_stats_{workout_id}")
        keyboard.button(text="🔗 Копировать код", callback_data=f"copy_workout_code_{workout_id}")
        keyboard.button(text="✏️ Редактировать", callback_data=f"edit_workout_{workout_id}")
        keyboard.button(text="🔙 В тренировки", callback_data="workouts_menu")
        keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
        keyboard.adjust(2, 2)

        await callback.message.edit_text(text, reply_markup=keyboard.as_markup(), parse_mode="Markdown")
        await callback.answer()

    except ValueError as e:
        logger.error("Ошибка парсинга ID тренировки: %s", e)
        await callback.answer("❌ Неверный формат ID", show_alert=True)
    except Exception as e:
        logger.exception("Ошибка в view_workout_details: %s", e)
        await callback.answer("❌ Ошибка при показе тренировки", show_alert=True)

# -----------------------
# Создание тренировки
# -----------------------
@workouts_router.callback_query(F.data == "create_workout")
async def start_create_workout(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🏋️ **Создание новой тренировки**\n\n"
        "Структура: разминка / подготовка НС / основная часть / заминка\n\n"
        "Введите название вашей тренировки:\n_Пример: \"Силовая тренировка верха\"_",
        parse_mode="Markdown"
    )
    await state.set_state(CreateWorkoutStates.waiting_workout_name)
    await callback.answer()

@workouts_router.callback_query(F.data == "skip_workout_description")
async def skip_description(callback: CallbackQuery, state: FSMContext):
    await state.update_data(description="")
    await show_block_selection_menu(callback.message, state)
    await callback.answer()

# show_block_selection_menu and other block helpers kept from old file:
async def show_block_selection_menu(message: Message, state: FSMContext):
    data = await state.get_data()
    selected_blocks = data.get('selected_blocks', {})

    text = f"🔧 **Структура тренировки: {data.get('name','Без названия')}**\n\n"
    text += "📋 **Выберите блоки для вашей тренировки:**\n\n"

    blocks = {
        'warmup': '🔥 Разминка',
        'nervous_prep': '⚡ Подготовка нервной системы',
        'main': '💪 Основная часть',
        'cooldown': '🧘 Заминка'
    }

    for block_key, block_name in blocks.items():
        status = "✅" if block_key in selected_blocks else "⭕"
        text += f"{status} **{block_name}**"
        if block_key in selected_blocks:
            exercises_count = len(selected_blocks[block_key].get('exercises', []))
            text += f" ({exercises_count} упр.)"
            if selected_blocks[block_key].get('description'):
                text += f"\n _{selected_blocks[block_key]['description'][:50]}..._"
        text += "\n\n"

    keyboard = InlineKeyboardBuilder()

    for block_key, block_name in blocks.items():
        action = "✏️ Изменить" if block_key in selected_blocks else "➕ Добавить"
        # keep callback consistent
        keyboard.button(text=f"{action} {block_name.split(' ',1)[1]}", callback_data=f"select_block_{block_key}")

    if selected_blocks:
        keyboard.button(text="✅ Завершить создание", callback_data="finish_workout_creation")

    keyboard.button(text="❌ Отменить", callback_data="cancel_workout_creation")
    keyboard.adjust(2)

    try:
        await message.edit_text(text, reply_markup=keyboard.as_markup(), parse_mode="Markdown")
    except Exception:
        await message.answer(text, reply_markup=keyboard.as_markup(), parse_mode="Markdown")

    await state.set_state(CreateWorkoutStates.selecting_blocks)

@workouts_router.callback_query(F.data.startswith("select_block_"))
async def select_workout_block(callback: CallbackQuery, state: FSMContext):
    block_key = callback.data.split("_", 2)[2]
    block_info = {
        'warmup': {
            'name': '🔥 Разминка',
            'description': 'Подготовка тела к нагрузке, разогрев мышц и суставов',
            'examples': 'Лёгкое кардио, динамическая растяжка, суставная гимнастика'
        },
        'nervous_prep': {
            'name': '⚡ Подготовка нервной системы',
            'description': 'Активация нервной системы перед основной работой',
            'examples': 'Взрывные движения, активационные упражнения, плиометрика'
        },
        'main': {
            'name': '💪 Основная часть',
            'description': 'Главная тренировочная нагрузка',
            'examples': 'Основные упражнения, силовая работа'
        },
        'cooldown': {
            'name': '🧘 Заминка',
            'description': 'Восстановление после тренировки',
            'examples': 'Статическая растяжка, дыхательные упражнения'
        }
    }

    info = block_info.get(block_key)
    if not info:
        await callback.answer("❌ Неверный блок", show_alert=True)
        return

    await state.update_data(current_block=block_key)

    text = f"📋 **{info['name']}**\n\n"
    text += f"**Описание:**\n{info['description']}\n\n"
    text += f"**Примеры упражнений:**\n{info['examples']}\n\n"
    text += f"**Что вы хотите сделать с этим блоком?**"

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="📝 Добавить описание блока", callback_data="add_block_description")
    keyboard.button(text="⏭️ Сразу к упражнениям", callback_data="searchexerciseforblock")
    keyboard.button(text="🗑️ Пропустить блок", callback_data="skip_entire_block")
    keyboard.button(text="🔙 К выбору блоков", callback_data="back_to_blocks")
    keyboard.adjust(1)

    await callback.message.edit_text(text, reply_markup=keyboard.as_markup(), parse_mode="Markdown")
    await callback.answer()

@workouts_router.callback_query(F.data == "add_block_description")
async def add_block_description(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    block_key = data.get('current_block')
    block_names = {
        'warmup': '🔥 Разминка',
        'nervous_prep': '⚡ Подготовка нервной системы',
        'main': '💪 Основная часть',
        'cooldown': '🧘 Заминка'
    }

    await callback.message.edit_text(
        f"📝 **Описание блока: {block_names.get(block_key,'Блок')}**\n\n"
        f"Введите описание для этого блока:\n"
        f"_Например: \"10 минут лёгкого кардио + суставная разминка\"_",
        parse_mode="Markdown"
    )
    await state.set_state(CreateWorkoutStates.adding_block_description)
    await callback.answer()

@workouts_router.callback_query(F.data == "skip_entire_block")
async def skip_entire_block(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_block = data.get('current_block')
    if not current_block:
        await callback.answer("❌ Блок не выбран", show_alert=True)
        return
    selected_blocks = data.get('selected_blocks', {})
    if current_block in selected_blocks:
        del selected_blocks[current_block]
    await state.update_data(selected_blocks=selected_blocks)
    await show_block_selection_menu(callback.message, state)
    await callback.answer()

@workouts_router.callback_query(F.data == "back_to_blocks")
async def back_to_blocks(callback: CallbackQuery, state: FSMContext):
    await show_block_selection_menu(callback.message, state)
    await callback.answer()

# -----------------------
# Поиск упражнений / категории / добавление
# -----------------------
@workouts_router.callback_query(F.data == "searchexerciseforblock")
async def searchexerciseforblock(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🔍 **Поиск упражнения для блока**\n\n"
        "Введите название упражнения:\n_Например: жим, приседания, планка_",
        parse_mode="Markdown"
    )
    await state.set_state("searching_exercise_for_block")
    await callback.answer()

@workouts_router.message(F.text)
async def handleblockexercisesearch(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state != "searching_exercise_for_block":
        return

    search_term = message.text.strip().lower()
    try:
        async with db_manager.pool.acquire() as conn:
            exercises = await conn.fetch(
                """
                SELECT id, name, category, muscle_group
                FROM exercises
                WHERE LOWER(name) LIKE $1 OR LOWER(category) LIKE $1 OR LOWER(muscle_group) LIKE $1
                ORDER BY name
                LIMIT 10
                """,
                f"%{search_term}%"
            )

        if not exercises:
            await message.answer(f"❌ По запросу '{search_term}' ничего не найдено.")
            await state.clear()
            return

        keyboard = InlineKeyboardBuilder()
        for ex in exercises:
            category = ex['category'] or "Без категории"
            keyboard.button(
                text=f"💪 {ex['name']} ({category})",
                callback_data=f"add_block_ex_{ex['id']}"
            )

        keyboard.button(text="🔍 Новый поиск", callback_data="searchexerciseforblock")
        keyboard.button(text="🔙 К упражнениям блока", callback_data="back_to_block_exercises")
        keyboard.adjust(1)

        await message.answer(
            f"🔍 **Найдено упражнений: {len(exercises)}**",
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )
        await state.set_state("searching_exercise_for_block")

    except Exception as e:
        logger.exception("Ошибка поиска упражнений: %s", e)
        await message.answer("❌ Ошибка поиска упражнений.")
        await state.clear()

@workouts_router.callback_query(F.data == "browsecategoriesforblock")
async def browsecategoriesforblock(callback: CallbackQuery):
    try:
        async with db_manager.pool.acquire() as conn:
            categories = await conn.fetch("SELECT DISTINCT category FROM exercises ORDER BY category")

        if not categories:
            await callback.message.edit_text("❌ Категории упражнений не найдены.")
            await callback.answer()
            return

        keyboard = InlineKeyboardBuilder()
        for cat in categories:
            name = cat['category'] or "Без категории"
            keyboard.button(text=f"📂 {name}", callback_data=f"block_cat_{name}")
        keyboard.button(text="🔙 К упражнениям блока", callback_data="back_to_block_exercises")
        keyboard.adjust(2)

        await callback.message.edit_text("📂 **Выберите категорию упражнений:**", reply_markup=keyboard.as_markup(), parse_mode="Markdown")
        await callback.answer()

    except Exception as e:
        logger.exception("Ошибка получения категорий: %s", e)
        await callback.message.edit_text("❌ Ошибка получения категорий.")
        await callback.answer()

@workouts_router.callback_query(F.data.startswith("block_cat_"))
async def showblockcategoryexercises(callback: CallbackQuery):
    category = callback.data[10:]
    try:
        async with db_manager.pool.acquire() as conn:
            exercises = await conn.fetch(
                "SELECT id, name, muscle_group FROM exercises WHERE category = $1 ORDER BY name",
                category
            )

        if not exercises:
            await callback.message.edit_text(f"❌ Упражнения в категории '{category}' не найдены.")
            await callback.answer()
            return

        keyboard = InlineKeyboardBuilder()
        for ex in exercises:
            mg = ex["muscle_group"] or "-"
            keyboard.button(text=f"{ex['name']} ({mg})", callback_data=f"add_block_ex_{ex['id']}")
        keyboard.button(text="🔙 К категориям", callback_data="browsecategoriesforblock")
        keyboard.adjust(1)

        await callback.message.edit_text(f"📂 **{category} упражнения:**", reply_markup=keyboard.as_markup(), parse_mode="Markdown")
        await callback.answer()

    except Exception as e:
        logger.exception("Ошибка получения упражнений категории: %s", e)
        await callback.message.edit_text("❌ Ошибка получения упражнений.")
        await callback.answer()

@workouts_router.callback_query(F.data.startswith("add_block_ex_"))
async def add_block_exercise(callback: CallbackQuery, state: FSMContext):
    try:
        ex_id = int(callback.data.split("_")[-1])

        async with db_manager.pool.acquire() as conn:
            exercise = await conn.fetchrow("SELECT name FROM exercises WHERE id = $1", ex_id)

        if not exercise:
            await callback.answer("❌ Упражнение не найдено.", show_alert=True)
            return

        data = await state.get_data()
        current_block = data.get("current_block", "main")

        selected_blocks = data.get("selected_blocks", {})
        selected_blocks.setdefault(current_block, {"description": "", "exercises": []})
        selected_blocks[current_block]["exercises"].append({
            "id": ex_id,
            "name": exercise["name"],
            "sets": 3,
            "reps_min": 8,
            "reps_max": 12,
            "one_rm_percent": None,
            "rest_seconds": 90
        })

        await state.update_data(selected_blocks=selected_blocks)
        await callback.message.edit_text(f"✅ Добавлено упражнение: *{exercise['name']}*", parse_mode="Markdown")
        await callback.answer()

    except Exception as e:
        logger.exception("Ошибка при добавлении упражнения: %s", e)
        await callback.message.answer("❌ Ошибка при добавлении упражнения.")
        await callback.answer()

# -----------------------
# Завершение создания тренировки
# -----------------------
@workouts_router.callback_query(F.data == "finish_workout_creation")
async def finish_workout_creation(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    selected_blocks = data.get('selected_blocks', {})

    try:
        total_exercises = sum(len(block_data.get('exercises', [])) for block_data in selected_blocks.values())

        if total_exercises == 0:
            await callback.answer("❌ Добавьте хотя бы одно упражнение!")
            return

        async with db_manager.pool.acquire() as conn:
            workout_id = await conn.fetchval("""
                INSERT INTO workouts (name, description, created_by, visibility, difficulty_level, estimated_duration_minutes)
                VALUES ($1, $2, $3, 'private', 'intermediate', $4)
                RETURNING id
            """, data['name'], data.get('description', ''), user['id'], total_exercises * 8)

            workout_unique_id = await conn.fetchval("SELECT unique_id FROM workouts WHERE id = $1", workout_id)

            order_in_phase = 0
            for phase, block_data in selected_blocks.items():
                for exercise in block_data.get('exercises', []):
                    order_in_phase += 1
                    await conn.execute("""
                        INSERT INTO workout_exercises (
                            workout_id, exercise_id, phase, order_in_phase, sets,   
                            reps_min, reps_max, one_rm_percent, rest_seconds
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    """, workout_id, exercise['id'], phase, order_in_phase, exercise['sets'],
                         exercise['reps_min'], exercise['reps_max'],
                         exercise['one_rm_percent'], exercise['rest_seconds'])

        text = f"🎉 **Тренировка создана успешно!**\n\n"
        text += f"🏋️ **Название:** {data['name']}\n"
        text += f"💡 **Код:** `{workout_unique_id}`\n"
        text += f"📋 **Всего упражнений:** {total_exercises}\n\n"

        block_names = {
            'warmup': '🔥 Разминка',
            'nervous_prep': '⚡ Подготовка НС',
            'main': '💪 Основная часть',
            'cooldown': '🧘 Заминка'
        }

        for phase, block_data in selected_blocks.items():
            if block_data.get('exercises'):
                text += f"**{block_names.get(phase, phase)}:** {len(block_data['exercises'])} упр.\n"
                if block_data.get('description'):
                    text += f" _{block_data['description']}_\n"

        text += f"\n💡 **Поделитесь кодом** `{workout_unique_id}` с другими!"

        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="🏋️ Мои тренировки", callback_data="my_workouts")
        keyboard.button(text="➕ Создать ещё", callback_data="create_workout")
        keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
        keyboard.adjust(2)

        await callback.message.edit_text(text, reply_markup=keyboard.as_markup(), parse_mode="Markdown")
        await state.clear()

    except Exception as e:
        logger.exception("Ошибка создания тренировки: %s", e)
        await callback.message.edit_text(f"❌ Ошибка сохранения: {e}")

    await callback.answer()

@workouts_router.callback_query(F.data == "cancel_workout_creation")
async def cancel_workout_creation(callback: CallbackQuery, state: FSMContext):
    await state.clear()

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🏋️ Мои тренировки", callback_data="my_workouts")
    keyboard.button(text="➕ Создать новую", callback_data="create_workout")
    keyboard.button(text="🔙 К тренировкам", callback_data="workouts_menu")
    keyboard.adjust(2)

    await callback.message.edit_text(
        "❌ **Создание тренировки отменено**\n\nДанные не сохранены.",
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()

# -----------------------
# Start workout (and finish -> save RPE/weight)
# -----------------------
@workouts_router.callback_query(F.data.startswith("start_workout_"))
async def start_workout_session(callback: CallbackQuery):
    try:
        workout_id = parse_callback_id(callback.data, "start_workout_")

        async with db_manager.pool.acquire() as conn:
            workout = await conn.fetchrow("SELECT name, unique_id FROM workouts WHERE id = $1", workout_id)

        if workout:
            text = f"▶️ **Начинаем тренировку!**\n\n"
            text += f"🏋️ **{workout['name']}**\n"
            text += f"💡 Код: `{workout['unique_id']}`\n\n"
            text += "Функция выполнения тренировки в разработке...\n\n"
            text += "После завершения нажмите кнопку «Завершил тренировку», чтобы оценить RPE и указать вес."

            keyboard = InlineKeyboardBuilder()
            keyboard.button(text="✅ Завершил тренировку", callback_data=f"finish_workout_{workout_id}")
            keyboard.button(text="📋 Детали", callback_data=f"view_workout_{workout_id}")
            keyboard.button(text="🏋️ Мои тренировки", callback_data="my_workouts")
            keyboard.adjust(1)

            await callback.message.edit_text(text, reply_markup=keyboard.as_markup(), parse_mode="Markdown")
        else:
            await callback.answer("❌ Тренировка не найдена.", show_alert=True)

    except ValueError:
        await callback.answer("❌ Неверный ID тренировки.", show_alert=True)
    except Exception as e:
        logger.exception("Ошибка start_workout_session: %s", e)
        await callback.answer("❌ Ошибка при запуске тренировки.", show_alert=True)

@workouts_router.callback_query(F.data.startswith("finish_workout_"))
async def finish_workout(callback: CallbackQuery, state: FSMContext):
    try:
        workout_id = parse_callback_id(callback.data, "finish_workout_")
        await state.update_data(finishing_workout_id=workout_id)
        await callback.message.edit_text("✅ Отлично! Оцените ваше ощущение после тренировки по шкале 1-10 (где 10 — очень тяжело):")
        await state.set_state("waiting_rpe")
        await callback.answer()
    except Exception as e:
        logger.exception("Ошибка при finish_workout: %s", e)
        await callback.answer("❌ Ошибка.", show_alert=True)

# -----------------------
# Process RPE and optional weight
# -----------------------
async def _try_insert_result(workout_id: int, user_id: int, rpe: int, weight: Optional[float]):
    try:
        async with db_manager.pool.acquire() as conn:
            # Попытка вставить в workout_results; если такой таблицы нет — будет исключение
            await conn.execute("""
                INSERT INTO workout_results (workout_id, user_id, rpe, weight, created_at)
                VALUES ($1, $2, $3, $4, $5)
            """, workout_id, user_id, rpe, weight, datetime.utcnow())
        return True
    except Exception as e:
        logger.warning("Не удалось записать результат в workout_results: %s", e)
        return False

# -----------------------
# Feature replacements: find_workout, workout_statistics, edit_workout
# -----------------------
@workouts_router.callback_query(F.data == "find_workout")
async def start_find_workout(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("🔎 Введите часть названия тренировки для поиска (покажем публичные + ваши):")
    await state.set_state("finding_workout_name")
    await callback.answer()

@workouts_router.callback_query(F.data == "workout_statistics")
async def show_workout_statistics(callback: CallbackQuery):
    try:
        user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
        async with db_manager.pool.acquire() as conn:
            total_workouts = await conn.fetchval("SELECT COUNT(*) FROM workouts WHERE created_by = $1", user['id'])
            total_public = await conn.fetchval("SELECT COUNT(*) FROM workouts WHERE visibility = 'public'")
            total_exercises = await conn.fetchval("""
                SELECT COUNT(*) FROM workout_exercises we
                JOIN workouts w ON we.workout_id = w.id
                WHERE w.created_by = $1
            """, user['id'])

        text = f"📊 **Ваша статистика**\n\n"
        text += f"🏋️ Тренировок создано: {total_workouts}\n"
        text += f"🌐 Публичных тренировок: {total_public}\n"
        text += f"📋 Упражнений всего в ваших тренировках: {total_exercises}\n"
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="🏋️ Мои тренировки", callback_data="my_workouts")
        keyboard.button(text="🔙 В меню", callback_data="workouts_menu")
        keyboard.adjust(1)

        await callback.message.edit_text(text, reply_markup=keyboard.as_markup(), parse_mode="Markdown")
        await callback.answer()
    except Exception as e:
        logger.exception("Ошибка статистики: %s", e)
        await callback.answer("❌ Ошибка при получении статистики", show_alert=True)

@workouts_router.callback_query(F.data.startswith("edit_workout_"))
async def edit_workout(callback: CallbackQuery, state: FSMContext):
    try:
        workout_id = parse_callback_id(callback.data, "edit_workout_")
        async with db_manager.pool.acquire() as conn:
            workout = await conn.fetchrow("SELECT id, name, description, created_by FROM workouts WHERE id = $1", workout_id)

        if not workout:
            await callback.answer("❌ Тренировка не найдена", show_alert=True)
            return

        # только автор может редактировать
        user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
        if workout['created_by'] != user['id']:
            await callback.answer("❌ Только автор может редактировать эту тренировку", show_alert=True)
            return

        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="✏️ Изменить название", callback_data=f"rename_workout_{workout_id}")
        keyboard.button(text="📝 Изменить описание", callback_data=f"change_desc_workout_{workout_id}")
        keyboard.button(text="🗑️ Удалить тренировку", callback_data=f"delete_workout_{workout_id}")
        keyboard.button(text="🔙 Назад", callback_data=f"view_workout_{workout_id}")
        keyboard.adjust(1)

        await callback.message.edit_text(
            f"✏️ **Редактирование:** {workout['name']}\n\nВыберите действие:",
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )
        await callback.answer()

    except Exception as e:
        logger.exception("Ошибка edit_workout: %s", e)
        await callback.answer("❌ Ошибка", show_alert=True)

@workouts_router.callback_query(F.data.startswith("rename_workout_"))
async def rename_workout(callback: CallbackQuery, state: FSMContext):
    try:
        workout_id = parse_callback_id(callback.data, "rename_workout_")
        await state.update_data(editing_workout_id=workout_id)
        await callback.message.edit_text("Введите новое название тренировки:")
        await state.set_state("renaming_workout")
        await callback.answer()
    except Exception as e:
        logger.exception("rename_workout error: %s", e)
        await callback.answer("❌ Ошибка", show_alert=True)

@workouts_router.callback_query(F.data.startswith("change_desc_workout_"))
async def change_workout_desc(callback: CallbackQuery, state: FSMContext):
    try:
        workout_id = parse_callback_id(callback.data, "change_desc_workout_")
        await state.update_data(editing_workout_id=workout_id)
        await callback.message.edit_text("Введите новое описание тренировки:")
        await state.set_state("changing_workout_description")
        await callback.answer()
    except Exception as e:
        logger.exception("change_workout_desc error: %s", e)
        await callback.answer("❌ Ошибка", show_alert=True)

@workouts_router.callback_query(F.data.startswith("delete_workout_"))
async def delete_workout(callback: CallbackQuery):
    try:
        workout_id = parse_callback_id(callback.data, "delete_workout_")
        async with db_manager.pool.acquire() as conn:
            await conn.execute("UPDATE workouts SET is_active = false WHERE id = $1", workout_id)
        await callback.answer("Тренировка удалена.", show_alert=True)
        await callback.message.edit_text("✅ Тренировка успешно удалена.")
    except Exception as e:
        logger.exception("delete_workout error: %s", e)
        await callback.answer("❌ Ошибка", show_alert=True)

# -----------------------
# Find workout by name (text flow)
# -----------------------
@workouts_router.message(F.text)
async def generic_text_handler(message: Message, state: FSMContext):
    """
    Универсальный обработчик текстовых сообщений для нескольких состояний:
    - создание тренировки (name/description)
    - поиск тренировки (finding_workout_name)
    - renaming/changing description
    - waiting_rpe / waiting_weight
    """
    current_state = await state.get_state()

    # -- создание --
    if current_state == CreateWorkoutStates.waiting_workout_name.state:
        await process_workout_name(message, state)
        return
    if current_state == CreateWorkoutStates.waiting_workout_description.state:
        await process_workout_description(message, state)
        return

    # -- поиск по названию (публичные + свои) --
    if current_state == "finding_workout_name":
        query = message.text.strip().lower()
        try:
            user = await db_manager.get_user_by_telegram_id(message.from_user.id)
            async with db_manager.pool.acquire() as conn:
                results = await conn.fetch(
                    """
                    SELECT id, name, description, unique_id, visibility
                    FROM workouts
                    WHERE (visibility = 'public' OR created_by = $2)
                      AND LOWER(name) LIKE $1
                    ORDER BY created_at DESC
                    LIMIT 12
                    """, f"%{query}%", user['id']
                )

            if not results:
                await message.answer("❌ Ничего не найдено.")
                await state.clear()
                return

            text = "🔎 **Найденные тренировки:**\n\n"
            keyboard = InlineKeyboardBuilder()
            for w in results:
                text += f"🏷 **{w['name']}** — `{w['unique_id']}` ({w['visibility']})\n"
                if w.get('description'):
                    text += f"_{w['description']}_\n"
                keyboard.button(text=f"{w['name']}", callback_data=f"view_workout_{w['id']}")

            keyboard.button(text="🔙 В меню тренировок", callback_data="workouts_menu")
            keyboard.adjust(1)
            await message.answer(text, reply_markup=keyboard.as_markup(), parse_mode="Markdown")
            await state.clear()
            return
        except Exception as e:
            logger.exception("find_workout error: %s", e)
            await message.answer("❌ Ошибка поиска.")
            await state.clear()
            return

    # -- renaming
    if current_state == "renaming_workout":
        data = await state.get_data()
        workout_id = data.get('editing_workout_id')
        new_name = message.text.strip()
        if not workout_id:
            await message.answer("❌ Контекст потерян.")
            await state.clear()
            return
        if len(new_name) < 3:
            await message.answer("❌ Название слишком короткое (мин 3 символа).")
            return
        try:
            async with db_manager.pool.acquire() as conn:
                await conn.execute("UPDATE workouts SET name = $1 WHERE id = $2", new_name, workout_id)
            await message.answer("✅ Название обновлено.")
            await state.clear()
            # показываем обновлённую страницу
            await message.answer(f"Откройте тренировку: /view {workout_id} (или нажмите в меню)")
        except Exception as e:
            logger.exception("rename_workout db error: %s", e)
            await message.answer("❌ Ошибка обновления.")
            await state.clear()
        return

    # -- change description
    if current_state == "changing_workout_description":
        data = await state.get_data()
        workout_id = data.get('editing_workout_id')
        new_desc = message.text.strip()
        if not workout_id:
            await message.answer("❌ Контекст потерян.")
            await state.clear()
            return
        try:
            async with db_manager.pool.acquire() as conn:
                await conn.execute("UPDATE workouts SET description = $1 WHERE id = $2", new_desc, workout_id)
            await message.answer("✅ Описание обновлено.")
            await state.clear()
        except Exception as e:
            logger.exception("change description db error: %s", e)
            await message.answer("❌ Ошибка обновления.")
            await state.clear()
        return

    # -- waiting for RPE
    if current_state == "waiting_rpe":
        try:
            rpe_val = int(message.text.strip())
            if rpe_val < 1 or rpe_val > 10:
                await message.answer("❌ Введите число от 1 до 10.")
                return
            data = await state.get_data()
            workout_id = data.get('finishing_workout_id')
            await state.update_data(last_rpe=rpe_val)
            # ask for weight
            await message.answer("📦 Укажите использованный общий вес (кг) или 'пропустить':")
            await state.set_state("waiting_weight")
        except ValueError:
            await message.answer("❌ Введите число от 1 до 10.")
        return

    # -- waiting for weight
    if current_state == "waiting_weight":
        data = await state.get_data()
        workout_id = data.get('finishing_workout_id')
        rpe_val = data.get('last_rpe')
        txt = message.text.strip().lower()
        weight_val: Optional[float] = None
        if txt not in ("пропустить", "skip", "-"):
            try:
                weight_val = float(txt.replace(",", "."))
            except ValueError:
                await message.answer("❌ Введите число (в кг) или 'пропустить'.")
                return
        success = await _try_insert_result(workout_id, (await db_manager.get_user_by_telegram_id(message.from_user.id))['id'], rpe_val, weight_val)
        if success:
            await message.answer("✅ Результат сохранён. Спасибо!")
        else:
            await message.answer("⚠️ Результат не удалось записать в таблицу (возможно таблица отсутствует). Результат всё равно принят.")
        await state.clear()
        return

# -----------------------
# Utility small processors (used by generic_text_handler)
# -----------------------
async def process_workout_name(message: Message, state: FSMContext):
    workout_name = message.text.strip()
    if len(workout_name) < 3:
        await message.answer("❌ Название слишком короткое. Минимум 3 символа.")
        return
    if len(workout_name) > 100:
        await message.answer("❌ Название слишком длинное. Максимум 100 символов.")
        return
    await state.update_data(name=workout_name)
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="⏭️ Пропустить описание", callback_data="skip_workout_description")
    await message.answer(f"✅ **Название:** {workout_name}\n\nВведите описание (или пропустите):", reply_markup=keyboard.as_markup(), parse_mode="Markdown")
    await state.set_state(CreateWorkoutStates.waiting_workout_description)

async def process_workout_description(message: Message, state: FSMContext):
    description = message.text.strip()
    await state.update_data(description=description)
    await show_block_selection_menu(message, state)

# -----------------------
# Copy code
# -----------------------
@workouts_router.callback_query(F.data.startswith("copy_workout_code_"))
async def copy_workout_code(callback: CallbackQuery):
    try:
        workout_id = parse_callback_id(callback.data, "copy_workout_code_")

        async with db_manager.pool.acquire() as conn:
            workout = await conn.fetchrow("SELECT unique_id, name FROM workouts WHERE id = $1", workout_id)

        if workout:
            text = f"🔗 **Код тренировки скопирован!**\n\n"
            text += f"🏋️ **{workout['name']}**\n"
            text += f"💡 Код: `{workout['unique_id']}`\n\n"
            keyboard = InlineKeyboardBuilder()
            keyboard.button(text="📋 Посмотреть", callback_data=f"view_workout_{workout_id}")
            keyboard.button(text="🏋️ Мои тренировки", callback_data="my_workouts")
            await callback.message.edit_text(text, reply_markup=keyboard.as_markup(), parse_mode="Markdown")
            await callback.answer("Код скопирован в буфер (показываю).")
        else:
            await callback.answer("❌ Тренировка не найдена.", show_alert=True)

    except Exception as e:
        logger.exception("copy_workout_code error: %s", e)
        await callback.answer("❌ Ошибка копирования", show_alert=True)

# -----------------------
# Feature coming soon handler removed — replaced by real implementations
# -----------------------

# -----------------------
# Registration helper
# -----------------------
def register_workout_handlers(dp):
    dp.include_router(workouts_router)
    logger.info("🏋️ Обработчики тренировок зарегистрированы")

__all__ = [
    'workouts_router',
    'register_workout_handlers',
]
