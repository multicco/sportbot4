# handlers/exercises.py
"""
Модуль для обработки упражнений в боте.
Содержит команды для поиска, добавления и управления упражнениями.
"""

import logging
from typing import Optional, Dict, Any, List

from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import db_manager
from states.workout_states import CreateWorkoutStates

logger = logging.getLogger(__name__)

# Создаём router для упражнений (не workouts_router!)
exercises_router = Router()


# ==================== HELPERS ====================

async def _safe_edit_or_send(message_obj, text: str, **kwargs):
    """
    Попробовать отредактировать текст, если не получилось — отправить новое сообщение.
    Работает с Message и CallbackQuery.message
    """
    try:
        await message_obj.edit_text(text, **kwargs)
    except Exception as e:
        logger.debug(f"Не удалось отредактировать сообщение: {e}")
        try:
            await message_obj.answer(text, **kwargs)
        except Exception as e:
            logger.exception(f"Критическая ошибка при отправке сообщения: {e}")


def _new_block_struct(name: str = "") -> Dict[str, Any]:
    """Создаёт новую структуру блока тренировки."""
    return {
        "name": name,
        "description": "",
        "exercises": []
    }


def _parse_int_suffix(data: str, sep: str = "_") -> Optional[int]:
    """Парсит число из строки вида 'callback_123'. Возвращает 123 или None."""
    try:
        return int(data.split(sep)[-1])
    except (ValueError, IndexError):
        return None


# ==================== ПОИСК УПРАЖНЕНИЙ ====================

@exercises_router.callback_query(F.data == "search_exercises")
async def search_exercises_start(callback: CallbackQuery, state: FSMContext):
    """Начинает процесс поиска упражнений."""
    logger.info(f"Поиск упражнений инициирован пользователем {callback.from_user.id}")
    
    kb = InlineKeyboardBuilder()
    kb.button(text="❌ Отменить", callback_data="cancel_search")
    kb.adjust(1)
    
    await _safe_edit_or_send(
        callback.message,
        "🔍 **Поиск упражнений**\n\nВведите название упражнения:",
        reply_markup=kb.as_markup(),
        parse_mode="Markdown"
    )
    
    await state.set_state(CreateWorkoutStates.searching_exercises)
    await callback.answer()


@exercises_router.message(StateFilter(CreateWorkoutStates.searching_exercises))
async def handle_exercise_search_input(message: Message, state: FSMContext):
    """Обрабатывает текст для поиска упражнений."""
    search_query = (message.text or "").strip()
    
    if not search_query or len(search_query) < 2:
        await message.answer("❌ Пожалуйста, введите минимум 2 символа для поиска.")
        return
    
    try:
        async with db_manager.pool.acquire() as conn:
            exercises = await conn.fetch(
                """
                SELECT id, name, muscle_group, category, difficulty_level
                FROM exercises
                WHERE name ILIKE $1 AND is_active = true
                ORDER BY name
                LIMIT 15
                """,
                f"%{search_query}%"
            )
        
        if not exercises:
            kb = InlineKeyboardBuilder()
            kb.button(text="🔙 Новый поиск", callback_data="search_exercises")
            kb.adjust(1)
            
            await message.answer(
                f"❌ Упражнения с названием '{search_query}' не найдены.",
                reply_markup=kb.as_markup()
            )
            return
        
        text = f"🔍 **Найдено упражнений:** {len(exercises)}\n\n"
        kb = InlineKeyboardBuilder()
        
        for ex in exercises:
            text += f"• **{ex['name']}** ({ex['muscle_group']}) — {ex['difficulty_level']}\n"
            kb.button(text=ex['name'], callback_data=f"select_exercise_{ex['id']}")
        
        kb.button(text="🔙 Новый поиск", callback_data="search_exercises")
        kb.adjust(1)
        
        await message.answer(text, reply_markup=kb.as_markup(), parse_mode="Markdown")
        await state.set_state(CreateWorkoutStates.selecting_exercises)
        
    except Exception as e:
        logger.exception(f"Ошибка при поиске упражнений: {e}")
        await message.answer("❌ Ошибка при поиске упражнений. Попробуйте позже.")


@exercises_router.callback_query(F.data.startswith("select_exercise_"))
async def select_exercise_for_workout(callback: CallbackQuery, state: FSMContext):
    """Выбирает упражнение для добавления в тренировку."""
    exercise_id = _parse_int_suffix(callback.data)
    
    if exercise_id is None:
        await callback.answer("❌ Неверный ID упражнения", show_alert=True)
        return
    
    try:
        async with db_manager.pool.acquire() as conn:
            exercise = await conn.fetchrow(
                """
                SELECT id, name, muscle_group, category, default_sets, default_reps_min, default_reps_max
                FROM exercises
                WHERE id = $1 AND is_active = true
                """,
                exercise_id
            )
        
        if not exercise:
            await callback.answer("❌ Упражнение не найдено", show_alert=True)
            return
        
        data = await state.get_data()
        selected_exercises = data.get("selected_exercises", [])
        
        # Проверяем, не добавлено ли уже
        if exercise_id in [ex.get("id") for ex in selected_exercises]:
            await callback.answer("⚠️ Это упражнение уже добавлено!", show_alert=True)
            return
        
        # Добавляем упражнение
        new_exercise = {
            "id": exercise_id,
            "name": exercise["name"],
            "sets": exercise.get("default_sets") or 3,
            "reps_min": exercise.get("default_reps_min") or 8,
            "reps_max": exercise.get("default_reps_max") or 12,
            "one_rm_percent": None,
            "rest_seconds": None,
            "notes": None
        }
        
        selected_exercises.append(new_exercise)
        await state.update_data(selected_exercises=selected_exercises)
        
        text = f"✅ Упражнение добавлено:\n**{exercise['name']}**\n"
        text += f"  Подходы: {new_exercise['sets']}\n"
        text += f"  Повторения: {new_exercise['reps_min']}-{new_exercise['reps_max']}"
        
        kb = InlineKeyboardBuilder()
        kb.button(text="➕ Добавить ещё", callback_data="search_exercises")
        kb.button(text="✅ Завершить", callback_data="finish_adding_exercises")
        kb.adjust(1)
        
        await callback.message.answer(text, reply_markup=kb.as_markup(), parse_mode="Markdown")
        await callback.answer()
        
    except Exception as e:
        logger.exception(f"Ошибка при выборе упражнения: {e}")
        await callback.answer("❌ Ошибка при добавлении упражнения", show_alert=True)


@exercises_router.callback_query(F.data == "cancel_search")
async def cancel_exercise_search(callback: CallbackQuery, state: FSMContext):
    """Отменяет поиск упражнений."""
    await state.clear()
    
    kb = InlineKeyboardBuilder()
    kb.button(text="🔙 К меню", callback_data="workouts_menu")
    kb.adjust(1)
    
    await _safe_edit_or_send(
        callback.message,
        "❌ Поиск упражнений отменён.",
        reply_markup=kb.as_markup()
    )
    await callback.answer()


# ==================== ДОБАВЛЕНИЕ УПРАЖНЕНИЯ ВРУЧНУЮ ====================

@exercises_router.callback_query(F.data == "manual_add_exercise")
async def manual_add_exercise_start(callback: CallbackQuery, state: FSMContext):
    """Запускает режим добавления упражнения вручную."""
    logger.info(f"Ручное добавление упражнения пользователем {callback.from_user.id}")
    
    kb = InlineKeyboardBuilder()
    kb.button(text="❌ Отменить", callback_data="cancel_manual_exercise")
    kb.adjust(1)
    
    await _safe_edit_or_send(
        callback.message,
        "📝 **Добавление упражнения вручную**\n\nВведите название упражнения:",
        reply_markup=kb.as_markup(),
        parse_mode="Markdown"
    )
    
    await state.set_state(CreateWorkoutStates.adding_manual_exercise_name)
    await callback.answer()


@exercises_router.message(StateFilter(CreateWorkoutStates.adding_manual_exercise_name))
async def handle_manual_exercise_name(message: Message, state: FSMContext):
    """Обрабатывает название упражнения при ручном добавлении."""
    exercise_name = (message.text or "").strip()
    
    if not exercise_name or len(exercise_name) < 2:
        await message.answer("❌ Название упражнения должно быть минимум 2 символа.")
        return
    
    await state.update_data(manual_exercise_name=exercise_name)
    
    kb = InlineKeyboardBuilder()
    kb.button(text="❌ Отменить", callback_data="cancel_manual_exercise")
    kb.adjust(1)
    
    await message.answer(
        f"✅ Название: **{exercise_name}**\n\nТеперь введите количество подходов (число):",
        reply_markup=kb.as_markup(),
        parse_mode="Markdown"
    )
    
    await state.set_state(CreateWorkoutStates.adding_manual_exercise_sets)


@exercises_router.message(StateFilter(CreateWorkoutStates.adding_manual_exercise_sets))
async def handle_manual_exercise_sets(message: Message, state: FSMContext):
    """Обрабатывает количество подходов."""
    try:
        sets = int((message.text or "").strip())
        if sets < 1 or sets > 20:
            raise ValueError("Количество подходов должно быть от 1 до 20")
    except ValueError:
        await message.answer("❌ Пожалуйста, введите число от 1 до 20.")
        return
    
    await state.update_data(manual_exercise_sets=sets)
    
    kb = InlineKeyboardBuilder()
    kb.button(text="❌ Отменить", callback_data="cancel_manual_exercise")
    kb.adjust(1)
    
    await message.answer(
        f"✅ Подходы: **{sets}**\n\nВведите количество повторений (например: 8-12):",
        reply_markup=kb.as_markup(),
        parse_mode="Markdown"
    )
    
    await state.set_state(CreateWorkoutStates.adding_manual_exercise_reps)


@exercises_router.message(StateFilter(CreateWorkoutStates.adding_manual_exercise_reps))
async def handle_manual_exercise_reps(message: Message, state: FSMContext):
    """Обрабатывает количество повторений."""
    reps_text = (message.text or "").strip()
    
    try:
        if "-" in reps_text:
            parts = reps_text.split("-")
            reps_min = int(parts[0].strip())
            reps_max = int(parts[1].strip())
        else:
            reps_min = reps_max = int(reps_text)
        
        if reps_min < 1 or reps_max < reps_min or reps_max > 100:
            raise ValueError("Неверный диапазон повторений")
    except ValueError:
        await message.answer("❌ Пожалуйста, введите число или диапазон (например: 8-12).")
        return
    
    data = await state.get_data()
    
    new_exercise = {
        "id": None,
        "name": data.get("manual_exercise_name"),
        "sets": data.get("manual_exercise_sets"),
        "reps_min": reps_min,
        "reps_max": reps_max,
        "one_rm_percent": None,
        "rest_seconds": None,
        "notes": None
    }
    
    selected_exercises = data.get("selected_exercises", [])
    selected_exercises.append(new_exercise)
    await state.update_data(selected_exercises=selected_exercises)
    
    text = f"✅ Упражнение добавлено:\n"
    text += f"**{new_exercise['name']}** — {new_exercise['sets']}x{reps_min}-{reps_max}"
    
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Добавить ещё", callback_data="manual_add_exercise")
    kb.button(text="✅ Завершить", callback_data="finish_adding_exercises")
    kb.adjust(1)
    
    await message.answer(text, reply_markup=kb.as_markup(), parse_mode="Markdown")
    await state.set_state(CreateWorkoutStates.adding_exercises)


@exercises_router.callback_query(F.data == "cancel_manual_exercise")
async def cancel_manual_exercise(callback: CallbackQuery, state: FSMContext):
    """Отменяет добавление упражнения вручную."""
    await state.clear()
    
    kb = InlineKeyboardBuilder()
    kb.button(text="🔙 К меню", callback_data="workouts_menu")
    kb.adjust(1)
    
    await _safe_edit_or_send(
        callback.message,
        "❌ Добавление упражнения отменено.",
        reply_markup=kb.as_markup()
    )
    await callback.answer()


@exercises_router.callback_query(F.data == "finish_adding_exercises")
async def finish_adding_exercises(callback: CallbackQuery, state: FSMContext):
    """Завершает добавление упражнений и возвращает в меню."""
    data = await state.get_data()
    selected_exercises = data.get("selected_exercises", [])
    
    if not selected_exercises:
        await callback.answer("❌ Добавьте хотя бы одно упражнение!", show_alert=True)
        return
    
    text = f"✅ **Добавлено упражнений:** {len(selected_exercises)}\n\n"
    for ex in selected_exercises:
        text += f"• {ex['name']} — {ex['sets']}x{ex['reps_min']}-{ex['reps_max']}\n"
    
    kb = InlineKeyboardBuilder()
    kb.button(text="🏋️ Мои тренировки", callback_data="workouts_my")
    kb.button(text="➕ Создать новую", callback_data="create_workout")
    kb.adjust(1)
    
    await _safe_edit_or_send(
        callback.message,
        text,
        reply_markup=kb.as_markup(),
        parse_mode="Markdown"
    )
    
    await callback.answer()


# ==================== РЕГИСТРАЦИЯ ====================

def register_exercise_handlers(dp):
    """
    Регистрирует router упражнений в диспетчере.
    Должна вызваться один раз из handlers/__init__.py или main.py
    """
    try:
        dp.include_router(exercises_router)
        logger.info("✅ exercises_router успешно подключён!")
    except RuntimeError as e:
        logger.warning(f"⚠️ exercises_router уже был подключён: {e}")
