# ===== FIXED handlers/workouts.py =====
import logging
from typing import Optional, List, Dict

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import db_manager
from states.workout_states import CreateWorkoutStates

# Импортируем меню поиска упражнений из handlers/exercises
# (предполагается, что файл handlers/exercises.py находится в том же пакете)
try:
    from handlers.exercises import search_exercise_menu
except Exception:
    # Если прямой импорт невозможен — оставляем None, но логируем
    search_exercise_menu = None

logger = logging.getLogger(__name__)

# Роутер для обработчиков тренировок
workouts_router = Router()

# ===== УТИЛИТЫ =====

def parse_callback_id(callback_data: str, expected_prefix: str = None) -> int:
    """Универсальная функция для парсинга ID из callback_data"""
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


# ===== ГЛАВНОЕ МЕНЮ ТРЕНИРОВОК =====
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
        "🆕 **Блочная структура тренировок:**\n"
        "• 🔥 Разминка\n"
        "• ⚡ Подготовка нервной системы\n"
        "• 💪 Основная часть\n"
        "• 🧘 Заминка\n\n"
        "Выберите действие:",
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()


# ===== СОЗДАНИЕ ТРЕНИРОВКИ =====
@workouts_router.callback_query(F.data == "create_workout")
async def start_create_workout(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🏋️ **Создание новой тренировки**\n\n"
        "🆕 **Блочная структура тренировки:**\n"
        "• 🔥 Разминка - подготовка тела\n"
        "• ⚡ Подготовка НС - активация нервной системы\n"
        "• 💪 Основная часть - главная нагрузка\n"
        "• 🧘 Заминка - восстановление\n\n"
        "Введите название вашей тренировки:\n"
        "_Например: \"Силовая тренировка верха\" или \"ОФП для новичков\"_",
        parse_mode="Markdown"
    )
    await state.set_state(CreateWorkoutStates.waiting_workout_name)

    # Инициализируем структуру блоков
    await state.update_data(selected_blocks={})

    await callback.answer()


@workouts_router.callback_query(F.data == "skip_workout_description")
async def skip_description(callback: CallbackQuery, state: FSMContext):
    """Пропустить описание тренировки"""
    data = await state.get_data()

    if 'name' not in data:
        await callback.answer("❌ Сначала введите название тренировки", show_alert=True)
        await callback.message.edit_text(
            "🏋️ **Создание новой тренировки**\n\n"
            "Введите название вашей тренировки:\n"
            "_Например: \"Силовая тренировка верха\" или \"ОФП для новичков\"_",
            parse_mode="Markdown"
        )
        await state.set_state(CreateWorkoutStates.waiting_workout_name)
        return

    await state.update_data(description="")
    await show_block_selection_menu(callback.message, state)
    await callback.answer()


# ===== ВЫБОР БЛОКОВ =====
async def show_block_selection_menu(message: Message, state: FSMContext):
    data = await state.get_data()

    workout_name = data.get('name', 'Без названия')
    selected_blocks = data.get('selected_blocks', {})

    text = f"🏗️ **Структура тренировки: {workout_name}**\n\n"
    text += f"📋 **Выберите блоки для вашей тренировки:**\n\n"

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
        keyboard.button(
            text=f"{action} {block_name.split(' ', 1)[1]}", 
            callback_data=f"select_block_{block_key}"
        )

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
    block_key = callback.data.split("_")[2]

    block_info = {
        'warmup': {
            'name': '🔥 Разминка',
            'description': 'Подготовка тела к нагрузке, разогрев мышц и суставов',
            'examples': 'Легкое кардио, динамическая растяжка, суставная гимнастика'
        },
        'nervous_prep': {
            'name': '⚡ Подготовка нервной системы',
            'description': 'Активация нервной системы перед основной работой',
            'examples': 'Взрывные движения, активационные упражнения, плиометрика'
        },
        'main': {
            'name': '💪 Основная часть',
            'description': 'Главная тренировочная нагрузка',
            'examples': 'Основные упражнения, силовая работа, технические элементы'
        },
        'cooldown': {
            'name': '🧘 Заминка',
            'description': 'Восстановление и расслабление после тренировки',
            'examples': 'Статическая растяжка, дыхательные упражнения, расслабление'
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
    keyboard.button(text="⏭️ Сразу к упражнениям", callback_data="skip_block_description")
    keyboard.button(text="🗑️ Пропустить блок", callback_data="skip_entire_block")
    keyboard.button(text="🔙 К выбору блоков", callback_data="back_to_blocks")
    keyboard.adjust(1)

    await callback.message.edit_text(
        text,
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()


@workouts_router.callback_query(F.data == "add_block_description")
async def add_block_description(callback: CallbackQuery, state: FSMContext):
    """Добавить описание к блоку"""
    data = await state.get_data()
    block_key = data.get('current_block')

    if not block_key:
        await callback.answer("❌ Сначала выберите блок", show_alert=True)
        await show_block_selection_menu(callback.message, state)
        return

    block_names = {
        'warmup': '🔥 Разминка',
        'nervous_prep': '⚡ Подготовка нервной системы',
        'main': '💪 Основная часть',   
        'cooldown': '🧘 Заминка'
    }

    await callback.message.edit_text(
        f"📝 **Описание блока: {block_names[block_key]}**\n\n"
        f"Введите описание для этого блока:\n"
        f"_Например: \"10 минут легкого кардио + суставная разминка\"_\n\n"
        f"Или опишите цели и особенности данного блока.",
        parse_mode="Markdown"
    )
    await state.set_state(CreateWorkoutStates.adding_block_description)
    await callback.answer()


# ===== ПЕРЕХОД К ПОИСКУ УПРАЖНЕНИЙ =====
@workouts_router.callback_query(F.data == "skip_block_description")
async def skip_block_description(callback: CallbackQuery, state: FSMContext):
    """Пропустить описание блока и перейти к поиску упражнений"""
    data = await state.get_data()

    if 'current_block' not in data or not data.get('current_block'):
        await callback.answer("❌ Ошибка: блок не выбран", show_alert=True)
        await show_block_selection_menu(callback.message, state)
        return

    # Сохраняем контекст, что пользователь сейчас добавляет упражнение в блок
    await state.update_data(adding_exercise_for_block=data['current_block'])

    # Если доступно меню поиска упражнений — вызываем его напрямую
    if search_exercise_menu:
        await search_exercise_menu(callback)
        # search_exercise_menu себе может установить соответствующие состояния (в exercises.py)
    else:
        # Если импорт не удался, показываем кнопку, чтобы пользователь перешел к поиску
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="🔍 Перейти к поиску упражнений", callback_data="search_exercise")
        keyboard.button(text="🔙 Назад к блоку", callback_data="select_block_" + data['current_block'])
        keyboard.adjust(1)

        await callback.message.edit_text(
            "🔍 Меню поиска упражнений недоступно (импорт не выполнен).\n"
            "Нажмите кнопку чтобы перейти к поиску.",
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )

    await callback.answer()


# ===== ОБРАБОТЧИК ДОБАВЛЕНИЯ ВЫБРАННОГО УПРАЖНЕНИЯ В БЛОК =====
@workouts_router.callback_query(F.data.startswith("use_in_workout_"))
async def use_exercise_in_workout(callback: CallbackQuery, state: FSMContext):
    """Добавить выбранное упражнение в текущий блок тренировки"""
    try:
        exercise_id = parse_callback_id(callback.data, "use_in_workout_")
    except ValueError:
        await callback.answer("❌ Неверный ID упражнения", show_alert=True)
        return

    data = await state.get_data()
    current_block = data.get('adding_exercise_for_block') or data.get('current_block')

    if not current_block:
        await callback.answer("❌ Контекст блока потерян. Выберите блок заново.", show_alert=True)
        await show_block_selection_menu(callback.message, state)
        return

    try:
        async with db_manager.pool.acquire() as conn:
            exercise = await conn.fetchrow(
                "SELECT id, name, muscle_group, category FROM exercises WHERE id = $1",
                exercise_id
            )

        if not exercise:
            await callback.answer("❌ Упражнение не найдено", show_alert=True)
            return

        # Подготовим структуру selected_blocks
        selected_blocks = data.get('selected_blocks', {})
        if current_block not in selected_blocks:
            selected_blocks[current_block] = {'description': None, 'exercises': []}

        # Добавляем упражнение с дефолтными параметрами
        exercise_entry = {
            'id': exercise['id'],
            'name': exercise['name'],
            'muscle_group': exercise['muscle_group'],
            'category': exercise['category'],
            # Дефолтные параметры (пользователь сможет редактировать позже)
            'sets': 3,
            'reps_min': 8,
            'reps_max': 12,
            'one_rm_percent': None,
            'rest_seconds': 90
        }

        selected_blocks[current_block]['exercises'].append(exercise_entry)

        await state.update_data(selected_blocks=selected_blocks)

        await callback.message.edit_text(
            f"✅ Упражнение **{exercise['name']}** добавлено в блок!\n\n"
            f"Возвращаемся к выбору блоков...",
            parse_mode="Markdown"
        )

        # Сбрасываем временный контекст добавления упражнения
        await state.update_data(adding_exercise_for_block=None)

        # Показываем меню блоков с обновлениями
        await show_block_selection_menu(callback.message, state)

    except Exception as e:
        logger.error(f"Ошибка добавления упражнения в блок: {e}")
        await callback.answer("❌ Ошибка при добавлении упражнения", show_alert=True)


# ===== ДОБАВЛЕНИЕ ОПИСАНИЯ БЛОКА (ТЕКСТОВЫЙ ВВОД) =====
async def process_block_description(message: Message, state: FSMContext):
    description = message.text.strip()

    if len(description) > 200:
        await message.answer("❌ Описание слишком длинное. Максимум 200 символов.")
        return

    data = await state.get_data()
    current_block = data.get('current_block')

    if not current_block:
        await message.answer("❌ Ошибка: блок не выбран")
        await show_block_selection_menu(message, state)
        return

    selected_blocks = data.get('selected_blocks', {})
    if current_block not in selected_blocks:
        selected_blocks[current_block] = {'description': description, 'exercises': []}
    else:
        selected_blocks[current_block]['description'] = description

    await state.update_data(selected_blocks=selected_blocks)

    await message.answer(
        f"✅ **Описание блока сохранено**\n\n"
        f"_{description}_\n\n"
        f"Теперь вы можете добавить упражнения в блок через поиск.",
        parse_mode="Markdown"
    )

    # Возвращаемся в меню блоков
    await show_block_selection_menu(message, state)


# ===== ЗАВЕРШЕНИЕ СОЗДАНИЯ ТРЕНИРОВКИ =====
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

            # Сохраняем упражнения
            for phase, block_data in selected_blocks.items():
                order_in_phase = 0
                for exercise in block_data.get('exercises', []):
                    order_in_phase += 1
                    await conn.execute("""
                        INSERT INTO workout_exercises (
                            workout_id, exercise_id, phase, order_in_phase, sets,   
                            reps_min, reps_max, one_rm_percent, rest_seconds
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    """, workout_id, exercise['id'], phase, order_in_phase, exercise['sets'],
                    exercise['reps_min'], exercise['reps_max'], exercise['one_rm_percent'], exercise['rest_seconds'])

        text = f"🎉 **Тренировка создана успешно!**\n\n"
        text += f"🏋️ **Название:** {data['name']}\n"
        text += f"🆔 **Код:** `{workout_unique_id}`\n"
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
        keyboard.button(text="➕ Создать еще", callback_data="create_workout")
        keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
        keyboard.adjust(2)

        await callback.message.edit_text(
            text,
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )

        await state.clear()

    except Exception as e:
        logger.error(f"Ошибка создания тренировки: {e}")
        await callback.message.edit_text(f"❌ Ошибка сохранения: {e}")

    await callback.answer()


# ===== ОТМЕНА =====
@workouts_router.callback_query(F.data == "cancel_workout_creation")
async def cancel_workout_creation(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🏋️ Мои тренировки", callback_data="my_workouts")
    keyboard.button(text="➕ Создать новую", callback_data="create_workout")
    keyboard.button(text="🔙 К тренировкам", callback_data="workouts_menu")
    keyboard.adjust(2)

    await callback.message.edit_text(
        "❌ **Создание тренировки отменено**\n\n"
        "Данные не сохранены.",
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()



# ===== ОБРАБОТКА ТЕКСТОВОГО ВВОДА =====
async def process_workout_text_input(message: Message, state: FSMContext):
    """Главный обработчик текстовых сообщений во время создания тренировки"""
    data = await state.get_data()
    current_state = await state.get_state()

    # === 1. Ввод названия тренировки ===
    if current_state == CreateWorkoutStates.waiting_workout_name.state:
        workout_name = message.text.strip()

        if len(workout_name) < 3:
            await message.answer("❌ Название слишком короткое. Минимум 3 символа.")
            return
        if len(workout_name) > 50:
            await message.answer("❌ Название слишком длинное. Максимум 50 символов.")
            return

        await state.update_data(name=workout_name)

        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="📝 Добавить описание", callback_data="add_workout_description")
        keyboard.button(text="⏭️ Пропустить описание", callback_data="skip_workout_description")
        keyboard.adjust(1)

        await message.answer(
            f"✅ **Название сохранено:** {workout_name}\n\n"
            f"Хотите добавить описание тренировки?",
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )
        await state.set_state(CreateWorkoutStates.waiting_workout_description)
        return

    # === 2. Ввод описания тренировки ===
    if current_state == CreateWorkoutStates.waiting_workout_description.state:
        description = message.text.strip()
        if len(description) > 200:
            await message.answer("❌ Описание слишком длинное. Максимум 200 символов.")
            return

        await state.update_data(description=description)
        await show_block_selection_menu(message, state)
        return

    # === 3. Ввод описания блока ===
    if current_state == CreateWorkoutStates.adding_block_description.state:
        await process_block_description(message, state)
        return

    # === Если текст не подходит ни под одно состояние ===
    await message.answer("ℹ️ Пожалуйста, используйте кнопки меню для навигации.")


# ===== РЕГИСТРАЦИЯ =====

def register_workout_handlers(dp):
    dp.include_router(workouts_router)
    logger.info("🏋️ Обработчики тренировок зарегистрированы")


__all__ = [
    'workouts_router', 'register_workout_handlers', 'process_workout_text_input'
]
