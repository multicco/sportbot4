# ===== ПОЛНЫЙ ФАЙЛ handlers/workouts.py =====
import asyncio
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

# Роутер для обработчиков тренировок
workouts_router = Router()

# ===== УТИЛИТЫ =====
def parse_callback_id(callback_data: str, expected_prefix: str = None) -> int:
    """Универсальная функция для парсинга ID из callback_data"""
    try:
        # Если задан префикс, пытаемся его убрать
        if expected_prefix and callback_data.startswith(expected_prefix):
            return int(callback_data.replace(expected_prefix, ""))

        # Иначе берем последний элемент после разделения по _
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
    """Главное меню тренировок"""
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

# ===== МОИ ТРЕНИРОВКИ =====
@workouts_router.callback_query(F.data == "my_workouts")
async def my_workouts(callback: CallbackQuery):
    """Показать тренировки пользователя"""
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
                    duration = workout['estimated_duration_minutes']

                    button_text = f"🏋️ {workout['name']}"
                    if exercise_count > 0:
                        button_text += f" ({exercise_count} упр.)"

                    keyboard.button(
                        text=button_text,
                        callback_data=f"view_workout_{workout['id']}"
                    )

                    # Добавляем краткое описание
                    text += f"**{workout['name']}**\n"
                    text += f"📋 Упражнений: {exercise_count} | ⏱️ ~{duration}мин\n"
                    text += f"🆔 Код: `{workout['unique_id']}`\n\n"

                keyboard.button(text="➕ Создать новую", callback_data="create_workout")
                keyboard.button(text="🔙 К тренировкам", callback_data="workouts_menu")
                keyboard.adjust(1)

            else:
                text = ("🏋️ **Мои тренировки**\n\n"
                       "У вас пока нет созданных тренировок.\n\n"
                       "Создайте первую тренировку с блочной структурой!")

                keyboard = InlineKeyboardBuilder()
                keyboard.button(text="➕ Создать первую", callback_data="create_workout")
                keyboard.button(text="🔙 К тренировкам", callback_data="workouts_menu")

            await callback.message.edit_text(
                text,
                reply_markup=keyboard.as_markup(),
                parse_mode="Markdown"
            )
            await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка в my_workouts: {e}")
        await callback.answer("❌ Ошибка загрузки тренировок", show_alert=True)

# ===== ПРОСМОТР ДЕТАЛЕЙ ТРЕНИРОВКИ =====
@workouts_router.callback_query(F.data.startswith("view_workout_"))
async def view_workout_details(callback: CallbackQuery):
    """ИСПРАВЛЕННАЯ функция просмотра деталей тренировки"""
    try:
        # ✅ ИСПРАВЛЕНИЕ: Правильный парсинг callback_data
        workout_id = parse_callback_id(callback.data, "view_workout_")

        logger.info(f"Просмотр тренировки ID: {workout_id}")

        # Получаем данные тренировки из БД
        async with db_manager.pool.acquire() as conn:
            # Основная информация о тренировке
            workout = await conn.fetchrow("""
                SELECT w.*, u.first_name as creator_name, u.last_name as creator_lastname
                FROM workouts w
                LEFT JOIN users u ON w.created_by = u.id  
                WHERE w.id = $1 AND w.is_active = true
            """, workout_id)

            if not workout:
                await callback.answer("❌ Тренировка не найдена", show_alert=True)
                return

            # Получаем упражнения тренировки
            exercises = await conn.fetch("""
                SELECT we.*, e.name as exercise_name, e.muscle_group, e.category
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

        # Формируем детальное описание тренировки
        creator_name = workout['creator_name']
        if workout['creator_lastname']:
            creator_name += f" {workout['creator_lastname']}"

        text = f"🏋️ **{workout['name']}**\n\n"

        if workout['description']:
            text += f"📝 _{workout['description']}_\n\n"

        text += f"👤 **Автор:** {creator_name or 'Неизвестен'}\n"
        text += f"⏱️ **Время:** ~{workout['estimated_duration_minutes']} мин\n"
        text += f"📈 **Уровень:** {workout['difficulty_level'].title()}\n"
        text += f"📂 **Категория:** {workout.get('category', 'general').title()}\n"
        text += f"🆔 **Код тренировки:** `{workout['unique_id']}`\n"
        text += f"👥 **Доступ:** {workout['visibility'].title()}\n\n"

        if exercises:
            # Группируем упражнения по фазам
            phase_names = {
                'warmup': '🔥 Разминка',
                'nervous_prep': '⚡ Подготовка нервной системы', 
                'main': '💪 Основная часть',
                'cooldown': '🧘 Заминка'
            }

            current_phase = None
            exercise_count = 0

            for exercise in exercises:
                # Новая фаза - добавляем заголовок
                if exercise['phase'] != current_phase:
                    current_phase = exercise['phase']
                    phase_display = phase_names.get(current_phase, current_phase.title())
                    text += f"\n**{phase_display}:**\n"

                exercise_count += 1

                # Форматируем повторения
                if exercise['reps_min'] == exercise['reps_max']:
                    reps_text = f"{exercise['reps_min']}"
                else:
                    reps_text = f"{exercise['reps_min']}-{exercise['reps_max']}"

                # Основная информация об упражнении
                text += f"• **{exercise['exercise_name']}**\n"
                text += f"  📊 {exercise['sets']} подх. × {reps_text} повт."

                # Процент от 1ПМ если указан
                if exercise['one_rm_percent']:
                    text += f" ({exercise['one_rm_percent']}% 1ПМ)"

                # Отдых между подходами
                if exercise['rest_seconds'] and exercise['rest_seconds'] > 0:
                    rest_min = exercise['rest_seconds'] // 60
                    rest_sec = exercise['rest_seconds'] % 60
                    if rest_min > 0:
                        text += f" | Отдых: {rest_min}мин {rest_sec}с" if rest_sec > 0 else f" | Отдых: {rest_min}мин"
                    else:
                        text += f" | Отдых: {rest_sec}с"

                text += f"\n  🎯 {exercise['muscle_group']} | {exercise['category']}\n"

                # Дополнительные заметки
                if exercise.get('notes'):
                    text += f"  📝 _{exercise['notes']}_\n"

                text += "\n"

            text += f"📋 **Всего упражнений:** {exercise_count}"
        else:
            text += "⚠️ В тренировке пока нет упражнений."

        # Создаем интерактивную клавиатуру
        keyboard = InlineKeyboardBuilder()

        # Основные действия
        keyboard.button(
            text="🏃 Начать тренировку", 
            callback_data=f"start_workout_{workout_id}"
        )
        keyboard.button(
            text="📊 Статистика", 
            callback_data=f"workout_stats_{workout_id}"
        )

        # Дополнительные действия  
        keyboard.button(
            text="📋 Скопировать код", 
            callback_data=f"copy_workout_code_{workout_id}"
        )
        keyboard.button(
            text="✏️ Редактировать", 
            callback_data=f"edit_workout_{workout_id}"
        )

        # Навигация
        keyboard.button(
            text="🔙 К тренировкам", 
            callback_data="workouts_menu"
        )
        keyboard.button(
            text="🏠 Главное меню", 
            callback_data="main_menu"
        )

        keyboard.adjust(2, 2, 2)  # Первые 4 кнопки в 2 ряда по 2, остальные тоже по 2

        # Отправляем сообщение
        await callback.message.edit_text(
            text,
            reply_markup=keyboard.as_markup(), 
            parse_mode="Markdown"
        )
        await callback.answer()

    except ValueError as e:
        logger.error(f"Ошибка парсинга ID тренировки: {e}")
        await callback.answer("❌ Неверный формат ID тренировки", show_alert=True)
    except Exception as e:
        logger.error(f"Ошибка в view_workout_details: {e}")
        await callback.answer("❌ Ошибка загрузки тренировки", show_alert=True)

# ===== СОЗДАНИЕ ТРЕНИРОВКИ =====
@workouts_router.callback_query(F.data == "create_workout")
async def start_create_workout(callback: CallbackQuery, state: FSMContext):
    """Начать создание новой тренировки"""
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

    await callback.answer()

@workouts_router.callback_query(F.data == "skip_workout_description")
async def skip_description(callback: CallbackQuery, state: FSMContext):
    """Пропустить описание тренировки"""
    await state.update_data(description="")
    await show_block_selection_menu(callback.message, state)
    await callback.answer()

# ===== ФУНКЦИИ СОЗДАНИЯ БЛОКОВ =====
async def show_block_selection_menu(message: Message, state: FSMContext):
    """Показать меню выбора блоков тренировки"""
    data = await state.get_data()
    selected_blocks = data.get('selected_blocks', {})

    text = f"🏗️ **Структура тренировки: {data['name']}**\n\n"
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
    except:
        await message.answer(text, reply_markup=keyboard.as_markup(), parse_mode="Markdown")

    await state.set_state(CreateWorkoutStates.selecting_blocks)

@workouts_router.callback_query(F.data.startswith("select_block_"))
async def select_workout_block(callback: CallbackQuery, state: FSMContext):
    """Выбрать блок для редактирования"""
    block_key = callback.data.split("_", 2)[2]

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

    info = block_info[block_key]
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

# ===== ЗАВЕРШЕНИЕ СОЗДАНИЯ ТРЕНИРОВКИ =====
@workouts_router.callback_query(F.data == "finish_workout_creation")
async def finish_workout_creation(callback: CallbackQuery, state: FSMContext):
    """Завершить создание тренировки"""
    data = await state.get_data()
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    selected_blocks = data.get('selected_blocks', {})

    try:
        total_exercises = sum(len(block_data['exercises']) for block_data in selected_blocks.values())

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

            exercise_order = 0
            for phase, block_data in selected_blocks.items():
                for exercise in block_data['exercises']:
                    exercise_order += 1
                    await conn.execute("""
                        INSERT INTO workout_exercises (
                            workout_id, exercise_id, phase, order_in_phase, sets,   
                            reps_min, reps_max, one_rm_percent, rest_seconds
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    """, workout_id, exercise['id'], phase, exercise_order, exercise['sets'],   
                    exercise['reps_min'], exercise['reps_max'],   
                    exercise['one_rm_percent'], exercise['rest_seconds'])

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
            if block_data['exercises']:
                text += f"**{block_names[phase]}:** {len(block_data['exercises'])} упр.\n"
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


@workouts_router.callback_query(F.data == "cancel_workout_creation")
async def cancel_workout_creation(callback: CallbackQuery, state: FSMContext):
    """Отменить создание тренировки"""
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



# ===== ДРУГИЕ ФУНКЦИИ =====
@workouts_router.callback_query(F.data.startswith("start_workout_"))
async def start_workout_session(callback: CallbackQuery):
    """Начать выполнение тренировки"""
    try:
        workout_id = parse_callback_id(callback.data, "start_workout_")

        # Получаем информацию о тренировке
        async with db_manager.pool.acquire() as conn:
            workout = await conn.fetchrow(
                "SELECT name, unique_id FROM workouts WHERE id = $1", 
                workout_id
            )

            if workout:
                text = f"🏃 **Начинаем тренировку!**\n\n"
                text += f"🏋️ **{workout['name']}**\n"
                text += f"🆔 Код: `{workout['unique_id']}`\n\n"
                text += f"⚠️ Функция выполнения тренировок в разработке...\n\n"
                text += f"Скоро здесь будет:\n"
                text += f"• ⏱️ Таймер отдыха\n"
                text += f"• 📊 Ввод результатов\n"
                text += f"• 📈 Оценка RPE\n"
                text += f"• 💪 Автоматический расчет весов"

                keyboard = InlineKeyboardBuilder()
                keyboard.button(text="🔙 К деталям", callback_data=f"view_workout_{workout_id}")
                keyboard.button(text="🏋️ Мои тренировки", callback_data="my_workouts")

                await callback.message.edit_text(
                    text,
                    reply_markup=keyboard.as_markup(),
                    parse_mode="Markdown"
                )
            else:
                await callback.answer("❌ Тренировка не найдена", show_alert=True)

    except ValueError:
        await callback.answer("❌ Ошибка ID тренировки", show_alert=True)
    except Exception as e:
        logger.error(f"Ошибка запуска тренировки: {e}")
        await callback.answer("❌ Ошибка запуска тренировки", show_alert=True)

@workouts_router.callback_query(F.data.startswith("copy_workout_code_"))
async def copy_workout_code(callback: CallbackQuery):
    """Скопировать код тренировки"""
    try:
        workout_id = parse_callback_id(callback.data, "copy_workout_code_")

        async with db_manager.pool.acquire() as conn:
            workout = await conn.fetchrow(
                "SELECT unique_id, name FROM workouts WHERE id = $1", 
                workout_id
            )

            if workout:
                text = f"📋 **Код тренировки скопирован!**\n\n"
                text += f"🏋️ **{workout['name']}**\n"
                text += f"🆔 Код: `{workout['unique_id']}`\n\n"
                text += f"Отправьте этот код другим пользователям,\n"
                text += f"чтобы они могли найти и использовать\n"
                text += f"вашу тренировку!"

                keyboard = InlineKeyboardBuilder()
                keyboard.button(text="🔙 К деталям", callback_data=f"view_workout_{workout_id}")
                keyboard.button(text="🏋️ Мои тренировки", callback_data="my_workouts")

                await callback.message.edit_text(
                    text,
                    reply_markup=keyboard.as_markup(),
                    parse_mode="Markdown"
                )
                await callback.answer("✅ Код скопирован в сообщение!")
            else:
                await callback.answer("❌ Тренировка не найдена", show_alert=True)

    except ValueError:
        await callback.answer("❌ Ошибка ID тренировки", show_alert=True)
    except Exception as e:
        logger.error(f"Ошибка копирования кода: {e}")
        await callback.answer("❌ Ошибка копирования", show_alert=True)

# ===== ЗАГЛУШКИ ДЛЯ БУДУЩИХ ФУНКЦИЙ =====
@workouts_router.callback_query(F.data.in_([
    "find_workout", "workout_statistics", "edit_workout", "workout_stats"
]))
async def feature_coming_soon(callback: CallbackQuery):
    """Заглушка для функций в разработке"""
    feature_names = {
        "find_workout": "Поиск тренировок",
        "workout_statistics": "Статистика тренировок",   
        "edit_workout": "Редактирование тренировки",
        "workout_stats": "Статистика тренировки"
    }

    # Проверяем, есть ли ID в callback_data
    feature_key = callback.data
    if "_" in callback.data:
        feature_key = "_".join(callback.data.split("_")[:-1])

    feature_name = feature_names.get(feature_key, "Эта функция")

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔙 К тренировкам", callback_data="workouts_menu")

    await callback.message.edit_text(
        f"🚧 **{feature_name}**\n\n"
        f"Функция находится в разработке.\n"
        f"Скоро будет доступна!\n\n"
        f"**Планируемые возможности:**\n"
        f"• 📊 Детальная статистика\n"
        f"• 📈 Анализ прогресса\n"
        f"• 🎯 Рекомендации по улучшению\n"
        f"• 📱 Экспорт данных",
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()

# ===== ОБРАБОТКА ТЕКСТОВОГО ВВОДА =====
async def process_workout_text_input(message: Message, state: FSMContext):
    """Обработка текстового ввода для создания тренировок"""
    current_state = await state.get_state()

    if current_state == CreateWorkoutStates.waiting_workout_name:
        await process_workout_name(message, state)
    elif current_state == CreateWorkoutStates.waiting_workout_description:
        await process_workout_description(message, state)

    else:
        await message.answer(
            "❓ Используйте кнопки меню для навигации.",
            parse_mode="Markdown"
        )
        await state.clear()

async def process_workout_name(message: Message, state: FSMContext):
    """Обработка названия тренировки"""
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

    await message.answer(
        f"✅ **Название:** {workout_name}\n\n"
        f"📝 Теперь введите описание тренировки:\n"
        f"_Например: \"Программа для развития силы основных групп мышц\"_\n\n"
        f"Или нажмите кнопку чтобы пропустить:",
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    await state.set_state(CreateWorkoutStates.waiting_workout_description)  # ✅ ПРАВИЛЬНО



async def process_workout_description(message: Message, state: FSMContext):
    """Обработка описания тренировки"""
    description = message.text.strip()
    await state.update_data(description=description)
    await show_block_selection_menu(message, state)

async def process_block_description(message: Message, state: FSMContext):
    """Обработка описания блока"""
    description = message.text.strip()

    if len(description) > 200:
        await message.answer("❌ Описание слишком длинное. Максимум 200 символов.")
        return

    await state.update_data(current_block_description=description)

    await message.answer(
        f"✅ **Описание блока сохранено:**\n\n"
        f"_{description}_\n\n"
        f"Переходим к добавлению упражнений в блок...",
        parse_mode="Markdown"
    )

    # Здесь должна быть функция show_block_exercises_menu, но она не помещается
    # В реальном проекте она должна быть добавлена
async def notify_team_about_workout(team_id: int, workout_id: int, workout_name: str):
    """Отправить уведомление команде о новой тренировке"""
    from main import bot
    
    # Получаем игроков с telegram_id
    players = await teams_database.get_team_players(team_id)
    
    notified_count = 0
    for player in players:
        if player.telegram_id:
            try:
                await bot.send_message(
                    player.telegram_id,
                    f"🏋️ **Новая тренировка!**\n\n"
                    f"📋 {workout_name}\n"
                    f"🆔 Код: `{workout_id}`\n\n"
                    f"Нажмите /myteam для просмотра.",
                    parse_mode="Markdown"
                )
                notified_count += 1
            except Exception as e:
                logger.error(f"Failed to notify player {player.id}: {e}")
    
    logger.info(f"Notified {notified_count} players about workout {workout_id}")
    return notified_count

# ===== ФУНКЦИЯ РЕГИСТРАЦИИ =====
def register_workout_handlers(dp):
    """Регистрация всех обработчиков тренировок"""
    dp.include_router(workouts_router)
    logger.info("🏋️ Обработчики тренировок зарегистрированы")
