# handlers/exercises.py
"""
Модуль для работы с тренировками и упражнениями.
Содержит все обработчики для создания, поиска, редактирования тренировок.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import db_manager
from states.workout_states import CreateWorkoutStates

logger = logging.getLogger(__name__)

# ===== ИСПРАВЛЕНИЕ 1: Переименован router =====
exercises_router = Router()

# ----------------------- HELPERS -----------------------

async def _safe_edit_or_send(message_obj, text: str, **kwargs):
    """
    Попробовать edit_text, если не получилось — отправить новое сообщение.
    Работает с Message и CallbackQuery.message
    """
    try:
        await message_obj.edit_text(text, **kwargs)
    except Exception:
        # message_obj может быть CallbackQuery.message или Message
        try:
            await message_obj.answer(text, **kwargs)
        except Exception as e:
            logger.exception("Не удалось ни отредактировать, ни отправить сообщение: %s", e)

def _new_block_struct(name: str = "") -> Dict[str, Any]:
    """Создаёт новую структуру блока тренировки."""
    return {"name": name, "description": "", "exercises": []}

def _parse_int_suffix(data: str, sep: str = "_") -> Optional[int]:
    """Парсит число из строки вида 'callback_123'. Возвращает 123 или None."""
    try:
        return int(data.split(sep)[-1])
    except (ValueError, IndexError):
        return None

# ===== ИСПРАВЛЕНИЕ 2: Удалены DEBUG CATCH-ALL обработчики =====
# @exercises_router.callback_query()  # ← УДАЛЕНО: ловит ВСЕ callback
# @exercises_router.message()         # ← УДАЛЕНО: ловит ВСЕ messages

# ----------------------- MENU: главная точка входа в меню тренировок -----------------------

@exercises_router.callback_query(F.data == "workouts_menu")
async def workouts_menu(callback: CallbackQuery):
    """Основное меню тренировок."""
    kb = InlineKeyboardBuilder()
    kb.button(text="🏋️ Мои тренировки", callback_data="workouts_my")
    kb.button(text="🔍 Найти тренировку", callback_data="workouts_find")
    kb.button(text="➕ Создать тренировку", callback_data="create_workout")
    kb.button(text="📊 Моя статистика", callback_data="workout_statistics")
    kb.button(text="🔙 Главное меню", callback_data="main_menu")
    kb.adjust(2)
    await callback.message.edit_text("🏋️ **Меню тренировок**\n\nВыберите действие:", 
                                    reply_markup=kb.as_markup(), parse_mode="Markdown")
    await callback.answer()

# ----------------------- МОИ ТРЕНИРОВКИ (краткий список) -----------------------

@exercises_router.callback_query(F.data == "workouts_my")
async def my_workouts(callback: CallbackQuery):
    """Показывает список тренировок пользователя."""
    try:
        user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer("Пользователь в БД не найден.", show_alert=True)
            return

        async with db_manager.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT w.id, w.name, w.unique_id, w.estimated_duration_minutes,
                COUNT(we.id) AS exercise_count
                FROM workouts w
                LEFT JOIN workout_exercises we ON we.workout_id = w.id
                WHERE w.created_by = $1 AND w.is_active = true
                GROUP BY w.id
                ORDER BY w.created_at DESC
                LIMIT 20
                """,
                user["id"],
            )

        if not rows:
            kb = InlineKeyboardBuilder()
            kb.button(text="➕ Создать первую", callback_data="create_workout")
            kb.button(text="🔙 К меню", callback_data="workouts_menu")
            kb.adjust(1)
            await callback.message.edit_text("У вас ещё нет сохранённых тренировок.", reply_markup=kb.as_markup())
            await callback.answer()
            return

        text = f"🏋️ **Мои тренировки ({len(rows)})**\n\n"
        kb = InlineKeyboardBuilder()

        for r in rows:
            ex_count = r["exercise_count"] or 0
            text += f"• **{r['name']}** — {ex_count} уп. — ~{r['estimated_duration_minutes']} мин\n"
            kb.button(text=f"{r['name']}", callback_data=f"view_workout_{r['id']}")

        kb.button(text="➕ Создать новую", callback_data="create_workout")
        kb.button(text="🔙 К меню", callback_data="workouts_menu")
        kb.adjust(1)

        await callback.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="Markdown")
        await callback.answer()

    except Exception as e:
        logger.exception("Ошибка в my_workouts: %s", e)
        await callback.answer("Ошибка при получении тренировок.", show_alert=True)

# ----------------------- Просмотр тренировки -----------------------

def _format_time(seconds: Optional[int]) -> str:
    """Форматирует время в человеко-читаемый вид."""
    if not seconds:
        return ""
    m, s = divmod(seconds, 60)
    if m > 0:
        return f"{m}м {s}с" if s else f"{m}м"
    return f"{s}с"

@exercises_router.callback_query(F.data.startswith("view_workout_"))
async def view_workout_details(callback: CallbackQuery):
    """Показывает детали тренировки."""
    try:
        workout_id = _parse_int_suffix(callback.data)
        if workout_id is None:
            await callback.answer("Неверный идентификатор тренировки", show_alert=True)
            return

    except Exception:
        await callback.answer("Неверный идентификатор тренировки", show_alert=True)
        return

    try:
        async with db_manager.pool.acquire() as conn:
            workout = await conn.fetchrow(
                """
                SELECT w.*, u.first_name as creator_name, u.last_name as creator_lastname
                FROM workouts w
                LEFT JOIN users u ON w.created_by = u.id
                WHERE w.id = $1 AND w.is_active = true
                """,
                workout_id,
            )

            if not workout:
                await callback.answer("Тренировка не найдена", show_alert=True)
                return

            exercises = await conn.fetch(
                """
                SELECT we.*, e.name as exercise_name, e.muscle_group, e.category
                FROM workout_exercises we
                LEFT JOIN exercises e ON we.exercise_id = e.id
                WHERE we.workout_id = $1
                ORDER BY we.phase, we.order_in_phase
                """,
                workout_id,
            )

        creator = workout["creator_name"] or "Неизвестен"
        if workout["creator_lastname"]:
            creator += f" {workout['creator_lastname']}"

        text = f"🏋️ **{workout['name']}**\n\n"

        if workout["description"]:
            text += f"📝 _{workout['description']}_\n\n"

        text += f"👤 Автор: {creator}\n"
        text += f"⏱ ~{workout['estimated_duration_minutes']} мин\n"
        text += f"🔖 Код: `{workout['unique_id']}`\n\n"

        if exercises:
            phases = {}
            for ex in exercises:
                phase = ex["phase"] or "other"
                phases.setdefault(phase, []).append(ex)

            for phase, items in phases.items():
                text += f"**{phase.title()}:**\n"
                for it in items:
                    reps = f"{it['reps_min']}-{it['reps_max']}" if it["reps_min"] and it["reps_max"] else ""
                    one_rm = f" ({it['one_rm_percent']}% 1ПМ)" if it.get("one_rm_percent") else ""
                    rest = _format_time(it.get("rest_seconds"))
                    text += f"• {it['exercise_name']} — {it['sets']}x{reps}{one_rm} {(' | ' + rest) if rest else ''}\n"
                text += "\n"

        kb = InlineKeyboardBuilder()
        kb.button(text="▶️ Начинать тренировку", callback_data=f"start_workout_{workout_id}")
        kb.button(text="📊 Статистика", callback_data=f"workout_stats_{workout_id}")
        kb.button(text="🔁 Скопировать код", callback_data=f"copy_workout_code_{workout_id}")
        kb.button(text="✏️ Редактировать", callback_data=f"edit_workout_{workout_id}")
        kb.button(text="🔙 К моим", callback_data="workouts_my")
        kb.adjust(2)

        await callback.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="Markdown")
        await callback.answer()

    except Exception as e:
        logger.exception("Ошибка в view_workout_details: %s", e)
        await callback.answer("Ошибка при показе тренировки", show_alert=True)

# ----------------------- СОЗДАНИЕ ТРЕНИРОВКИ -----------------------

@exercises_router.callback_query(F.data == "create_workout")
async def create_workout_start(callback: CallbackQuery, state: FSMContext):
    """Начинает процесс создания тренировки."""
    logger.info("create_workout_start by %s", callback.from_user.id)
    kb = InlineKeyboardBuilder()
    kb.button(text="❌ Отменить", callback_data="create_cancel")
    kb.adjust(1)
    await _safe_edit_or_send(callback.message, 
                            "🏋️ **Создание тренировки**\n\nВведите название тренировки:", 
                            reply_markup=kb.as_markup(), parse_mode="Markdown")
    await state.set_state(CreateWorkoutStates.waiting_workout_name)
    await callback.answer()

@exercises_router.callback_query(F.data == "create_cancel")
async def cancel_workout_creation(callback: CallbackQuery, state: FSMContext):
    """Отменяет создание тренировки."""
    await state.clear()
    kb = InlineKeyboardBuilder()
    kb.button(text="🔙 В меню тренировок", callback_data="workouts_menu")
    kb.adjust(1)
    await _safe_edit_or_send(callback.message, "❌ Создание тренировки отменено.", reply_markup=kb.as_markup())
    await callback.answer()

# ===== ИСПРАВЛЕНИЕ 3: Использование StateFilter вместо ручной маршрутизации =====
@exercises_router.message(StateFilter(CreateWorkoutStates.waiting_workout_name))
async def handle_workout_name(message: Message, state: FSMContext):
    """Обрабатывает ввод названия тренировки."""
    name = (message.text or "").strip()

    if not name or len(name) < 3:
        await message.answer("Название слишком короткое — минимум 3 символа.")
        return

    await state.update_data(name=name)

    kb = InlineKeyboardBuilder()
    kb.button(text="Пропустить описание", callback_data="skip_workout_description")
    kb.button(text="Добавить описание", callback_data="add_workout_description")
    kb.adjust(1)

    await message.answer(f"✅ Название сохранено: *{name}*\n\nДобавьте описание или пропустите.", 
                        reply_markup=kb.as_markup(), parse_mode="Markdown")
    await state.set_state(CreateWorkoutStates.waiting_workout_description)

@exercises_router.callback_query(F.data == "skip_workout_description")
async def skip_workout_description(callback: CallbackQuery, state: FSMContext):
    """Пропускает описание тренировки."""
    await state.update_data(description="")
    await callback.answer("Описание пропущено")
    await show_block_selection_menu(callback.message, state)

@exercises_router.callback_query(F.data == "add_workout_description")
async def add_workout_description(callback: CallbackQuery):
    """Предлагает добавить описание."""
    await callback.message.edit_text("📝 Введите описание тренировки (необязательно):", parse_mode="Markdown")
    await callback.answer()

@exercises_router.message(StateFilter(CreateWorkoutStates.waiting_workout_description))
async def handle_workout_description(message: Message, state: FSMContext):
    """Обрабатывает ввод описания тренировки."""
    desc = (message.text or "").strip()
    await state.update_data(description=desc)
    await message.answer("Описание сохранено.")
    await show_block_selection_menu(message, state)

# Показать меню выбора блоков
async def show_block_selection_menu(message_obj, state: FSMContext):
    """Показывает меню выбора блоков тренировки."""
    data = await state.get_data()
    name = data.get("name", "<без названия>")
    selected = data.get("selected_blocks", {})

    text = f"🏗 **Конструктор тренировки: {name}**\n\nВыберите блоки для тренировки:\n\n"

    blocks_meta = [
        ("warmup", "🔥 Разминка"),
        ("nervous_prep", "⚡ ЦНС"),
        ("main", "🏋️ Основная часть"),
        ("cooldown", "🧘 Заминка"),
    ]

    for key, label in blocks_meta:
        if key in selected and selected[key].get("exercises"):
            cnt = len(selected[key]["exercises"])
            text += f"• {label} — {cnt} уп.\n"
        else:
            text += f"• {label}\n"

    kb = InlineKeyboardBuilder()
    for key, label in blocks_meta:
        kb.button(text=label, callback_data=f"add_block_{key}")

    kb.button(text="✅ Завершить и сохранить", callback_data="finish_workout_creation")
    kb.button(text="❌ Отмена", callback_data="create_cancel")
    kb.adjust(2)

    try:
        await message_obj.edit_text(text, reply_markup=kb.as_markup(), parse_mode="Markdown")
    except Exception:
        await message_obj.answer(text, reply_markup=kb.as_markup(), parse_mode="Markdown")

    await state.set_state(CreateWorkoutStates.selecting_blocks)

@exercises_router.callback_query(F.data.startswith("add_block_"))
async def add_block(callback: CallbackQuery, state: FSMContext):
    """Добавляет блок в тренировку."""
    key = callback.data.split("_", 2)[2]
    
    await state.update_data(current_block=key)

    kb = InlineKeyboardBuilder()
    kb.button(text="Добавить описание блока", callback_data="add_block_description")
    kb.button(text="Пропустить описание блока", callback_data="skip_block_description")
    kb.button(text="🔙 Назад", callback_data="back_to_constructor")
    kb.adjust(1)

    await callback.message.edit_text(f"✍️ Блок: *{key}*", reply_markup=kb.as_markup(), parse_mode="Markdown")
    await state.set_state(CreateWorkoutStates.adding_block_description)
    await callback.answer()

@exercises_router.callback_query(F.data == "back_to_constructor")
async def back_to_constructor(callback: CallbackQuery, state: FSMContext):
    """Возвращает в меню конструктора."""
    await show_block_selection_menu(callback.message, state)
    await callback.answer()

@exercises_router.callback_query(F.data == "add_block_description")
async def prompt_block_description(callback: CallbackQuery, state: FSMContext):
    """Просит описание блока."""
    await callback.message.edit_text("📝 Введите описание для этого блока (необязательно):", parse_mode="Markdown")
    await state.set_state(CreateWorkoutStates.adding_block_description)
    await callback.answer()

@exercises_router.callback_query(F.data == "skip_block_description")
async def skip_block_description(callback: CallbackQuery, state: FSMContext):
    """Пропускает описание блока."""
    data = await state.get_data()
    sel = data.get("selected_blocks", {})
    current = data.get("current_block")

    if current:
        sel.setdefault(current, _new_block_struct())
        await state.update_data(selected_blocks=sel)

    await callback.answer("Описание блока пропущено")
    await show_block_exercises_menu(callback.message, state)

@exercises_router.message(StateFilter(CreateWorkoutStates.adding_block_description))
async def handle_block_description(message: Message, state: FSMContext):
    """Обрабатывает ввод описания блока."""
    desc = (message.text or "").strip()
    data = await state.get_data()
    current = data.get("current_block")
    sel = data.get("selected_blocks", {})

    if not current:
        await message.answer("Не найден текущий блок. Вернитесь в конструктор.")
        return

    sel.setdefault(current, _new_block_struct())
    sel[current]["description"] = desc
    await state.update_data(selected_blocks=sel)

    await message.answer("Описание блока сохранено.")
    await show_block_exercises_menu(message, state)

# Показать меню упражнений для текущего блока
async def show_block_exercises_menu(message_obj, state: FSMContext):
    """Показывает меню для добавления упражнений в блок."""
    data = await state.get_data()
    current = data.get("current_block")

    if not current:
        await _safe_edit_or_send(message_obj, "Не выбран блок. Возврат в конструктор.")
        await show_block_selection_menu(message_obj, state)
        return

    text = f"🔎 **Упражнения для блока:** {current}\n\nВыберите действие:"

    kb = InlineKeyboardBuilder()
    kb.button(text="🔍 Найти упражнение", callback_data="search_exercise_for_block")
    kb.button(text="📝 Добавить вручную (текстом)", callback_data="manual_add_exercise")
    kb.button(text="✅ Завершить блок", callback_data="finish_current_block")
    kb.button(text="🔙 К блокам", callback_data="back_to_constructor")
    kb.adjust(1)

    try:
        await message_obj.edit_text(text, reply_markup=kb.as_markup(), parse_mode="Markdown")
    except Exception:
        await message_obj.answer(text, reply_markup=kb.as_markup(), parse_mode="Markdown")

@exercises_router.callback_query(F.data == "manual_add_exercise")
async def manual_add_exercise(callback: CallbackQuery, state: FSMContext):
    """Запускает ручное добавление упражнения."""
    await callback.message.edit_text("📝 Введите упражнение вручную (напр.: Присед 3x10 70% 90с):", 
                                    parse_mode="Markdown")
    await state.set_state(CreateWorkoutStates.manual_exercise_input)
    await callback.answer()

@exercises_router.message(StateFilter(CreateWorkoutStates.manual_exercise_input))
async def handle_manual_exercise_input(message: Message, state: FSMContext):
    """Обрабатывает ручной ввод упражнения."""
    text = (message.text or "").strip()

    if not text:
        await message.answer("Пустой ввод — отменено.")
        await state.set_state(CreateWorkoutStates.adding_exercises)
        return

    data = await state.get_data()
    current = data.get("current_block")

    if not current:
        await message.answer("Ошибка: не выбран текущий блок.")
        await state.set_state(CreateWorkoutStates.selecting_blocks)
        return

    sel = data.get("selected_blocks", {})
    sel.setdefault(current, _new_block_struct())

    # минимальная структура для ручного упражнения
    new_ex = {
        "id": None,
        "name": text,
        "sets": None,
        "reps_min": None,
        "reps_max": None,
        "one_rm_percent": None,
        "rest_seconds": None,
        "notes": None,
    }

    sel[current]["exercises"].append(new_ex)
    await state.update_data(selected_blocks=sel)

    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Добавить ещё", callback_data="manual_add_exercise")
    kb.button(text="🔙 К упражнениям блока", callback_data="back_to_block_exercises")
    kb.adjust(1)

    await message.answer(f"✅ Упражнение добавлено:\n{text}", reply_markup=kb.as_markup())
    await state.set_state(CreateWorkoutStates.adding_exercises)

@exercises_router.callback_query(F.data == "back_to_block_exercises")
async def back_to_block_exercises(callback: CallbackQuery, state: FSMContext):
    """Возвращает к меню упражнений блока."""
    await show_block_exercises_menu(callback.message, state)
    await callback.answer()

@exercises_router.callback_query(F.data == "finish_current_block")
async def finish_current_block(callback: CallbackQuery, state: FSMContext):
    """Завершает текущий блок."""
    await callback.answer("Блок сохранён")
    await show_block_selection_menu(callback.message, state)

@exercises_router.callback_query(F.data == "search_exercise_for_block")
async def search_exercise_for_block(callback: CallbackQuery, state: FSMContext):
    """Ищет упражнения в базе данных."""
    await callback.message.edit_text("🔍 Введите название упражнения для поиска:", parse_mode="Markdown")
    await state.set_state(CreateWorkoutStates.searching_exercises)
    await callback.answer()

@exercises_router.message(StateFilter(CreateWorkoutStates.searching_exercises))
async def handle_exercise_search(message: Message, state: FSMContext):
    """Обрабатывает поиск упражнений."""
    search_text = (message.text or "").strip()

    if not search_text or len(search_text) < 2:
        await message.answer("Введите минимум 2 символа для поиска.")
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
                f"%{search_text}%"
            )

        if not exercises:
            kb = InlineKeyboardBuilder()
            kb.button(text="🔙 Назад", callback_data="back_to_block_exercises")
            await message.answer(f"❌ Упражнения по '{search_text}' не найдены.", reply_markup=kb.as_markup())
            await state.set_state(CreateWorkoutStates.adding_exercises)
            return

        text = f"🔍 **Найдено упражнений:** {len(exercises)}\n\n"
        kb = InlineKeyboardBuilder()

        for ex in exercises:
            text += f"• **{ex['name']}** ({ex['muscle_group']}) — {ex['difficulty_level']}\n"
            kb.button(text=ex['name'], callback_data=f"select_exercise_{ex['id']}")

        kb.button(text="🔙 Назад", callback_data="back_to_block_exercises")
        kb.adjust(1)

        await message.answer(text, reply_markup=kb.as_markup(), parse_mode="Markdown")
        await state.set_state(CreateWorkoutStates.selecting_exercises)

    except Exception as e:
        logger.exception("Ошибка при поиске упражнений: %s", e)
        await message.answer("❌ Ошибка при поиске упражнений.")

@exercises_router.callback_query(F.data.startswith("select_exercise_"))
async def select_exercise_from_search(callback: CallbackQuery, state: FSMContext):
    """Выбирает упражнение из результатов поиска."""
    exercise_id = _parse_int_suffix(callback.data)

    if exercise_id is None:
        await callback.answer("❌ Неверный ID", show_alert=True)
        return

    try:
        async with db_manager.pool.acquire() as conn:
            exercise = await conn.fetchrow(
                "SELECT id, name FROM exercises WHERE id = $1 AND is_active = true",
                exercise_id
            )

        if not exercise:
            await callback.answer("❌ Упражнение не найдено", show_alert=True)
            return

        data = await state.get_data()
        current = data.get("current_block")
        sel = data.get("selected_blocks", {})

        if not current:
            await callback.answer("❌ Ошибка: блок не выбран", show_alert=True)
            return

        sel.setdefault(current, _new_block_struct())

        new_ex = {
            "id": exercise_id,
            "name": exercise["name"],
            "sets": 3,
            "reps_min": 8,
            "reps_max": 12,
            "one_rm_percent": None,
            "rest_seconds": None,
            "notes": None,
        }

        sel[current]["exercises"].append(new_ex)
        await state.update_data(selected_blocks=sel)

        kb = InlineKeyboardBuilder()
        kb.button(text="➕ Добавить ещё", callback_data="search_exercise_for_block")
        kb.button(text="✅ Завершить блок", callback_data="finish_current_block")
        kb.adjust(1)

        await callback.message.answer(f"✅ Упражнение добавлено: **{exercise['name']}**", 
                                     reply_markup=kb.as_markup(), parse_mode="Markdown")
        await callback.answer()

    except Exception as e:
        logger.exception("Ошибка при выборе упражнения: %s", e)
        await callback.answer("❌ Ошибка при добавлении упражнения", show_alert=True)

# Save workout to DB — вызывается при завершении
@exercises_router.callback_query(F.data == "finish_workout_creation")
async def finish_workout_creation(callback: CallbackQuery, state: FSMContext):
    """Сохраняет тренировку в базу данных."""
    data = await state.get_data()
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)

    if not user:
        await callback.answer("Пользователь не найден в базе", show_alert=True)
        return

    name = data.get("name")
    description = data.get("description", "")
    selected_blocks = data.get("selected_blocks", {})

    total_exercises = sum(len(block["exercises"]) for block in selected_blocks.values())

    if total_exercises == 0:
        await callback.answer("Добавьте хотя бы одно упражнение в тренировку", show_alert=True)
        return

    try:
        async with db_manager.pool.acquire() as conn:
            workout_id = await conn.fetchval(
                """
                INSERT INTO workouts (name, description, created_by, visibility, difficulty_level, 
                                    estimated_duration_minutes, created_at)
                VALUES ($1, $2, $3, 'private', 'intermediate', $4, now())
                RETURNING id
                """,
                name, description, user["id"], max(5, total_exercises * 5),
            )

            unique_id = await conn.fetchval("SELECT unique_id FROM workouts WHERE id = $1", workout_id)

            order = 0
            for phase, block in selected_blocks.items():
                for ex in block["exercises"]:
                    order += 1
                    await conn.execute(
                        """
                        INSERT INTO workout_exercises (
                        workout_id, exercise_id, phase, order_in_phase, sets, reps_min, reps_max, 
                        one_rm_percent, rest_seconds, notes
                        ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
                        """,
                        workout_id, ex.get("id"), phase, order, ex.get("sets"), 
                        ex.get("reps_min"), ex.get("reps_max"), ex.get("one_rm_percent"),
                        ex.get("rest_seconds"), ex.get("notes"),
                    )

        # success message
        text = f"✅ Тренировка *{name}* сохранена!\n\nКод: `{unique_id}`\nУпражнений: {total_exercises}"

        kb = InlineKeyboardBuilder()
        kb.button(text="🏋️ Мои тренировки", callback_data="workouts_my")
        kb.button(text="➕ Создать ещё", callback_data="create_workout")
        kb.button(text="🔙 Главное меню", callback_data="main_menu")
        kb.adjust(2)

        await callback.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="Markdown")
        await state.clear()
        await callback.answer()

    except Exception as e:
        logger.exception("Ошибка при сохранении тренировки: %s", e)
        await callback.answer("Ошибка при сохранении тренировки", show_alert=True)

# -------------- simple features: start workout, copy code placeholders --------------

@exercises_router.callback_query(F.data.startswith("start_workout_"))
async def start_workout_session(callback: CallbackQuery):
    """Запускает тренировку."""
    await callback.answer("Функция старта тренировки (в разработке).")

@exercises_router.callback_query(F.data.startswith("copy_workout_code_"))
async def copy_workout_code(callback: CallbackQuery):
    """Копирует код тренировки."""
    await callback.answer("Код скопирован в буфер (симуляция).")

@exercises_router.callback_query(F.data.startswith("workout_stats_"))
async def workout_stats(callback: CallbackQuery):
    """Показывает статистику тренировки."""
    await callback.answer("Функция статистики (в разработке).")

@exercises_router.callback_query(F.data.startswith("edit_workout_"))
async def edit_workout(callback: CallbackQuery):
    """Редактирует тренировку."""
    await callback.answer("Функция редактирования (в разработке).")

@exercises_router.callback_query(F.data == "workouts_find")
async def find_workouts(callback: CallbackQuery):
    """Поиск чужих тренировок."""
    await callback.answer("Функция поиска (в разработке).")

@exercises_router.callback_query(F.data == "workout_statistics")
async def workout_statistics(callback: CallbackQuery):
    """Показывает общую статистику."""
    await callback.answer("Функция статистики (в разработке).")

# -----------------------
# REGISTRATION
# -----------------------

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
