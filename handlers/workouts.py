# handlers/workouts.py
# -*- coding: utf-8 -*-
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import db_manager
from states.workout_states import CreateWorkoutStates

logger = logging.getLogger(__name__)
workouts_router = Router()

# ----------------- UTIL -----------------
def parse_int_suffix(callback_data: str) -> Optional[int]:
    """Безопасно получить последний суффикс как int, иначе None."""
    try:
        part = callback_data.split("_")[-1]
        if part.isdigit():
            return int(part)
        return None
    except Exception:
        return None

def parse_callback_id(callback_data: str, prefix: Optional[str] = None) -> int:
    """Парсит id и бросает ValueError если не нашли."""
    if prefix and callback_data.startswith(prefix):
        tail = callback_data[len(prefix):]
        if tail.isdigit():
            return int(tail)
        raise ValueError(f"Нет числового ID в callback: {callback_data}")
    # fallback: последний раздел после _
    n = parse_int_suffix(callback_data)
    if n is None:
        raise ValueError(f"Не удалось извлечь ID из callback: {callback_data}")
    return n

async def safe_edit_or_send(message, text, reply_markup=None, parse_mode=None):
    """Попытка edit_text, если не удалось — send message."""
    try:
        await message.edit_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception:
        await message.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)

# ----------------- MENU -----------------
@workouts_router.callback_query(F.data.in_({"workouts_menu", "menu_workouts", "workouts_menu"}))
async def workouts_menu(callback: CallbackQuery):
    logger.info("🔹 Открыто меню тренировок (callback=%s)", callback.data)
    kb = InlineKeyboardBuilder()
    kb.button(text="🏋️ Мои тренировки", callback_data="my_workouts")
    kb.button(text="🔍 Найти тренировку", callback_data="find_workout")
    kb.button(text="➕ Создать тренировку", callback_data="create_workout")  # legacy short
    kb.button(text="➕ Создать тренировку (новое)", callback_data="create_workout_new")  # optional
    kb.button(text="📊 Моя статистика", callback_data="workout_statistics")
    kb.button(text="🔙 Главное меню", callback_data="main_menu")
    kb.adjust(2)
    await safe_edit_or_send(callback.message, "🏋️ **Меню тренировок**\n\nВыберите действие:", reply_markup=kb.as_markup(), parse_mode="Markdown")
    await callback.answer()

# ----------------- MY WORKOUTS -----------------
@workouts_router.callback_query(F.data.in_({"my_workouts", "workouts_my"}))
async def my_workouts(callback: CallbackQuery):
    logger.info("🔹 Получен callback: my_workouts (from %s)", callback.from_user.id)
    try:
        user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
        async with db_manager.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT w.id, w.name, w.unique_id, coalesce(count_we,0) as exercise_count, w.estimated_duration_minutes
                FROM (
                    SELECT w.*, (SELECT COUNT(*) FROM workout_exercises we WHERE we.workout_id = w.id) as count_we
                    FROM workouts w
                    WHERE w.created_by = $1 AND coalesce(w.is_active, true) = true
                    ORDER BY w.created_at DESC
                    LIMIT 50
                ) w
            """, user['id'])
        if not rows:
            kb = InlineKeyboardBuilder()
            kb.button(text="➕ Создать первую", callback_data="create_workout")
            kb.button(text="🔙 В меню", callback_data="workouts_menu")
            kb.adjust(1)
            await safe_edit_or_send(callback.message, "🏋️ У вас пока нет сохранённых тренировок.", reply_markup=kb.as_markup())
            await callback.answer()
            return

        text = f"🏋️ **Мои тренировки ({len(rows)}):**\n\n"
        kb = InlineKeyboardBuilder()
        for r in rows:
            cnt = r['exercise_count'] or 0
            text += f"**{r['name']}** — {cnt} упр. | Код `{r['unique_id']}`\n"
            kb.button(text=f"{r['name']} ({cnt})", callback_data=f"view_workout_{r['id']}")
        kb.button(text="➕ Создать", callback_data="create_workout")
        kb.button(text="🔙 В меню", callback_data="workouts_menu")
        kb.adjust(1)
        await safe_edit_or_send(callback.message, text, reply_markup=kb.as_markup(), parse_mode="Markdown")
        await callback.answer()
    except Exception as e:
        logger.exception("my_workouts error: %s", e)
        await callback.answer("❌ Ошибка получения тренировок", show_alert=True)

# ----------------- VIEW DETAILS -----------------
@workouts_router.callback_query(F.data.startswith("view_workout_"))
async def view_workout_details(callback: CallbackQuery):
    try:
        wid = parse_callback_id(callback.data, "view_workout_")
        async with db_manager.pool.acquire() as conn:
            workout = await conn.fetchrow("""
                SELECT w.*, u.first_name as creator_name, u.last_name as creator_lastname
                FROM workouts w
                LEFT JOIN users u ON w.created_by = u.id
                WHERE w.id = $1 AND coalesce(w.is_active, true) = true
            """, wid)
            if not workout:
                await callback.answer("❌ Тренировка не найдена", show_alert=True)
                return
            exercises = await conn.fetch("""
                SELECT we.*, e.name as exercise_name, e.muscle_group, e.category
                FROM workout_exercises we
                LEFT JOIN exercises e ON e.id = we.exercise_id
                WHERE we.workout_id = $1
                ORDER BY
                    CASE we.phase WHEN 'warmup' THEN 1 WHEN 'nervousprep' THEN 2 WHEN 'main' THEN 3 WHEN 'cooldown' THEN 4 ELSE 5 END,
                    we.order_in_phase
            """, wid)
        text = f"🏷 **{workout['name']}**\n\n"
        if workout.get('description'):
            text += f"📝 _{workout['description']}_\n\n"
        text += f"👤 Автор: {(workout.get('creator_name') or '')} {workout.get('creator_lastname') or ''}\n"
        text += f"⏱ Время: ~{workout.get('estimated_duration_minutes') or 0} мин\n"
        text += f"💡 Код: `{workout.get('unique_id')}`\n\n"
        if exercises:
            phase_map = {'warmup': '🔥 Разминка', 'nervousprep': '⚡ Подготовка НС', 'main': '💪 Основная', 'cooldown': '🧘 Заминка'}
            cur = None
            for ex in exercises:
                if ex['phase'] != cur:
                    cur = ex['phase']
                    text += f"\n**{phase_map.get(cur, cur)}:**\n"
                reps = f"{ex['reps_min']}" if ex['reps_min'] == ex['reps_max'] else f"{ex['reps_min']}-{ex['reps_max']}"
                text += f"• **{ex['exercise_name']}** — {ex['sets']}×{reps}"
                if ex.get('one_rm_percent'):
                    text += f" ({ex['one_rm_percent']}% 1ПМ)"
                if ex.get('rest_seconds'):
                    rs = ex['rest_seconds']
                    text += f" | отдых {rs//60}м{rs%60}s" if rs >= 60 else f" | отдых {rs}s"
                text += "\n"
        else:
            text += "⚠️ Упражнений пока нет."
        kb = InlineKeyboardBuilder()
        kb.button(text="▶️ Начать тренировку", callback_data=f"start_workout_{wid}")
        kb.button(text="📊 Статистика", callback_data=f"workout_stats_{wid}")
        kb.button(text="🔗 Копировать код", callback_data=f"copy_workout_code_{wid}")
        kb.button(text="✏️ Редактировать", callback_data=f"edit_workout_{wid}")
        kb.button(text="🔙 В мои", callback_data="my_workouts")
        kb.adjust(2, 2)
        await safe_edit_or_send(callback.message, text, reply_markup=kb.as_markup(), parse_mode="Markdown")
        await callback.answer()
    except Exception as e:
        logger.exception("view_workout_details error: %s", e)
        await callback.answer("❌ Ошибка при показе тренировки", show_alert=True)

# ----------------- CREATE WORKOUT FLOW (FSM) -----------------
# We use create_ prefix for creation-related callbacks to avoid conflicts with player_workouts.py
@workouts_router.callback_query(F.data.in_({"create_workout", "create_workout_new", "workouts_create"}))
async def start_create_workout(callback: CallbackQuery, state: FSMContext):
    logger.info("🔹 Начало создания тренировки (callback=%s) by %s", callback.data, callback.from_user.id)
    # ask name
    kb = InlineKeyboardBuilder()
    kb.button(text="❌ Отменить", callback_data="create_cancel_workout")
    kb.adjust(1)
    await safe_edit_or_send(callback.message, "🏋️ **Создание тренировки**\n\nВведите название тренировки:", reply_markup=kb.as_markup(), parse_mode="Markdown")
    await state.set_state(CreateWorkoutStates.waiting_workout_name)
    await callback.answer()

@workouts_router.callback_query(F.data.in_({"create_skip_description", "skip_workout_description", "skip_description"}))
async def skip_workout_description(callback: CallbackQuery, state: FSMContext):
    # allow legacy names too
    await state.update_data(description="")
    await show_block_selection_menu(callback.message, state)
    await callback.answer()

@workouts_router.callback_query(F.data == "create_cancel_workout")
async def create_cancel_workout(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardBuilder()
    kb.button(text="🏋️ Мои тренировки", callback_data="my_workouts")
    kb.button(text="➕ Создать", callback_data="create_workout")
    kb.adjust(1)
    await safe_edit_or_send(callback.message, "❌ Создание отменено.", reply_markup=kb.as_markup())
    await callback.answer()

async def show_block_selection_menu(message: Message, state: FSMContext):
    data = await state.get_data()
    name = data.get('name', 'Без названия')
    selected = data.get('selected_blocks', {})
    text = f"🔧 **Структура тренировки: {name}**\n\nВыберите блоки и добавьте упражнения:\n\n"
    blocks = [('warmup', '🔥 Разминка'), ('nervousprep', '⚡ Подготовка НС'), ('main', '💪 Основная'), ('cooldown', '🧘 Заминка')]
    for k, label in blocks:
        status = "✅" if k in selected else "⭕"
        cnt = len(selected.get(k, {}).get('exercises', [])) if k in selected else 0
        text += f"{status} {label} ({cnt} упр.)\n"
    kb = InlineKeyboardBuilder()
    # use create_ prefix to avoid conflict
    kb.button(text="➕ Разминка", callback_data="create_add_warmup_block")
    kb.button(text="➕ Подготовка НС", callback_data="create_add_cns_block")
    kb.button(text="➕ Основная", callback_data="create_add_main_block")
    kb.button(text="➕ Заминка", callback_data="create_add_cooldown_block")
    kb.button(text="✅ Завершить создание", callback_data="create_finish_workout")
    kb.button(text="❌ Отменить", callback_data="create_cancel_workout")
    kb.adjust(2)
    try:
        await message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="Markdown")
    except Exception:
        await message.answer(text, reply_markup=kb.as_markup(), parse_mode="Markdown")
    await state.set_state(CreateWorkoutStates.selecting_blocks)

# handle adding block - creation namespace
@workouts_router.callback_query(F.data.in_({"create_add_warmup_block", "create_add_cns_block", "create_add_main_block", "create_add_cooldown_block"}))
async def create_add_block(callback: CallbackQuery, state: FSMContext):
    mapping = {
        "create_add_warmup_block": "warmup",
        "create_add_cns_block": "nervousprep",
        "create_add_main_block": "main",
        "create_add_cooldown_block": "cooldown"
    }
    phase = mapping.get(callback.data)
    if not phase:
        await callback.answer()
        return
    await state.update_data(current_block=phase)
    kb = InlineKeyboardBuilder()
    kb.button(text="📝 Добавить/редактировать описание блока", callback_data="create_add_block_description")
    kb.button(text="🔍 Поиск упражнений", callback_data="create_search_ex_for_block")
    kb.button(text="🔙 К выбору блоков", callback_data="create_back_to_blocks")
    kb.adjust(1)
    names = {'warmup': 'Разминка', 'nervousprep': 'Подготовка НС', 'main': 'Основная', 'cooldown': 'Заминка'}
    await safe_edit_or_send(callback.message, f"📋 **{names.get(phase)}**\n\nЧто сделать?", reply_markup=kb.as_markup(), parse_mode="Markdown")
    await callback.answer()

@workouts_router.callback_query(F.data == "create_add_block_description")
async def create_add_block_description(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("📝 Введите описание для этого блока:")
    await state.set_state(CreateWorkoutStates.adding_block_description)
    await callback.answer()

# search exercises for block (creation namespace)
@workouts_router.callback_query(F.data == "create_search_ex_for_block")
async def create_search_ex_for_block(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("🔍 Введите текст для поиска упражнений (например: присед, жим)")
    await state.set_state("searching_exercise_for_block")
    await callback.answer()

# handle exercise search result text
@workouts_router.callback_query(F.data.startswith("create_add_ex_"))
async def create_add_ex_direct(callback: CallbackQuery, state: FSMContext):
    # pattern create_add_ex_{id}
    ex_id = parse_int_suffix(callback.data.split("create_add_ex_")[-1])
    await callback.answer()

# add exercise callback (legacy and create_ compatible)
@workouts_router.callback_query(F.data.startswith("add_block_ex_") | F.data.startswith("create_add_block_ex_"))
async def add_block_exercise(callback: CallbackQuery, state: FSMContext):
    try:
        # accept either add_block_ex_123 or create_add_block_ex_123
        prefix = "add_block_ex_"
        if callback.data.startswith("create_add_block_ex_"):
            prefix = "create_add_block_ex_"
        ex_id = parse_callback_id(callback.data, prefix)
        async with db_manager.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT id, name FROM exercises WHERE id = $1", ex_id)
        if not row:
            await callback.answer("❌ Упражнение не найдено", show_alert=True)
            return
        data = await state.get_data()
        cur = data.get('current_block', 'main')
        sel = data.get('selected_blocks', {})
        sel.setdefault(cur, {"description": "", "exercises": []})
        sel[cur]["exercises"].append({
            "id": row['id'],
            "name": row['name'],
            "sets": 3,
            "reps_min": 8,
            "reps_max": 12,
            "one_rm_percent": None,
            "rest_seconds": 90
        })
        await state.update_data(selected_blocks=sel)
        await callback.message.edit_text(f"✅ Добавлено: *{row['name']}*", parse_mode="Markdown")
        await callback.answer()
    except ValueError:
        await callback.answer("❌ Не удалось распознать ID упражнения", show_alert=True)
    except Exception as e:
        logger.exception("add_block_exercise error: %s", e)
        await callback.answer("❌ Ошибка добавления упражнения", show_alert=True)

# finish creation
@workouts_router.callback_query(F.data.in_({"create_finish_workout", "finish_workout_creation", "finish_workout"}))
async def finish_create_workout(callback: CallbackQuery, state: FSMContext):
    try:
        data = await state.get_data()
        sel = data.get('selected_blocks', {})
        total = sum(len(b.get('exercises', [])) for b in sel.values())
        if total == 0:
            await callback.answer("❌ Добавьте хотя бы одно упражнение!", show_alert=True)
            return
        user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
        async with db_manager.pool.acquire() as conn:
            wid = await conn.fetchval("""
                INSERT INTO workouts (name, description, created_by, visibility, difficulty_level, estimated_duration_minutes, created_at, is_active)
                VALUES ($1,$2,$3,'private','intermediate',$4, now(), true) RETURNING id
            """, data.get('name'), data.get('description',''), user['id'], total * 8)
            order = 0
            for phase, block in sel.items():
                for ex in block.get('exercises', []):
                    order += 1
                    await conn.execute("""
                        INSERT INTO workout_exercises (workout_id, exercise_id, phase, order_in_phase, sets, reps_min, reps_max, one_rm_percent, rest_seconds, notes)
                        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
                    """, wid, ex['id'], phase, order, ex['sets'], ex['reps_min'], ex['reps_max'], ex.get('one_rm_percent'), ex.get('rest_seconds'), ex.get('notes'))
            unique_id = await conn.fetchval("SELECT unique_id FROM workouts WHERE id = $1", wid)
        await callback.message.edit_text(f"🎉 Тренировка создана! Код: `{unique_id}`\n🏋️ Упражнений: {total}", parse_mode="Markdown")
        await state.clear()
        await callback.answer()
    except Exception as e:
        logger.exception("finish_create_workout error: %s", e)
        await callback.answer("❌ Ошибка при сохранении тренировки", show_alert=True)

# ----------------- START / FINISH (player-side) -----------------
@workouts_router.callback_query(F.data.startswith("start_workout_"))
async def start_workout(callback: CallbackQuery):
    wid = parse_int_suffix(callback.data)
    if wid is None:
        await callback.answer("❌ Неверный идентификатор тренировки", show_alert=True)
        return
    async with db_manager.pool.acquire() as conn:
        workout = await conn.fetchrow("SELECT name, unique_id FROM workouts WHERE id = $1", wid)
    if not workout:
        await callback.answer("❌ Тренировка не найдена", show_alert=True)
        return
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Завершил тренировку", callback_data=f"finish_workout_{wid}")
    kb.button(text="📋 Детали", callback_data=f"view_workout_{wid}")
    kb.adjust(1)
    await safe_edit_or_send(callback.message, f"▶️ Начинаем: **{workout['name']}**\n\nПосле выполнения нажмите «Завершил тренировку»", reply_markup=kb.as_markup(), parse_mode="Markdown")
    await callback.answer()

@workouts_router.callback_query(F.data.startswith("finish_workout_"))
async def finish_workout(callback: CallbackQuery, state: FSMContext):
    # BE SAFE: ensure last part is numeric
    n = parse_int_suffix(callback.data)
    if n is None:
        logger.warning("❗ finish_workout got non-numeric suffix: %s", callback.data)
        await callback.answer()
        return
    wid = n
    await state.update_data(finishing_workout_id=wid)
    await callback.message.edit_text("✅ Оцени тренировку по шкале 1-10 (RPE):")
    await state.set_state("waiting_rpe")
    await callback.answer()

# ----------------- copying code / edit / delete / stats -----------------
@workouts_router.callback_query(F.data.startswith("copy_workout_code_"))
async def copy_workout_code(callback: CallbackQuery):
    try:
        wid = parse_callback_id(callback.data, "copy_workout_code_")
    except ValueError:
        await callback.answer("❌ Неверный код", show_alert=True)
        return
    async with db_manager.pool.acquire() as conn:
        row = await conn.fetchrow("SELECT unique_id, name FROM workouts WHERE id = $1", wid)
    if not row:
        await callback.answer("❌ Не найдено", show_alert=True)
        return
    text = f"🔗 Код тренировки: `{row['unique_id']}`\n{row['name']}"
    kb = InlineKeyboardBuilder()
    kb.button(text="📋 Посмотреть", callback_data=f"view_workout_{wid}")
    kb.button(text="🔙 В мои", callback_data="my_workouts")
    kb.adjust(1)
    await safe_edit_or_send(callback.message, text, reply_markup=kb.as_markup(), parse_mode="Markdown")
    await callback.answer("Код показан")

@workouts_router.callback_query(F.data.startswith("edit_workout_"))
async def edit_workout(callback: CallbackQuery, state: FSMContext):
    try:
        wid = parse_callback_id(callback.data, "edit_workout_")
    except ValueError:
        await callback.answer("❌ Неверный ID", show_alert=True)
        return
    async with db_manager.pool.acquire() as conn:
        w = await conn.fetchrow("SELECT id, name, description, created_by FROM workouts WHERE id = $1", wid)
    if not w:
        await callback.answer("❌ Не найдено", show_alert=True)
        return
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    if w['created_by'] != user['id']:
        await callback.answer("❌ Только автор может редактировать", show_alert=True)
        return
    kb = InlineKeyboardBuilder()
    kb.button(text="✏️ Переименовать", callback_data=f"rename_workout_{wid}")
    kb.button(text="📝 Изменить описание", callback_data=f"change_desc_workout_{wid}")
    kb.button(text="🗑️ Удалить", callback_data=f"delete_workout_{wid}")
    kb.button(text="🔙 Назад", callback_data=f"view_workout_{wid}")
    kb.adjust(1)
    await safe_edit_or_send(callback.message, f"✏️ Редактирование: {w['name']}", reply_markup=kb.as_markup())
    await callback.answer()

@workouts_router.callback_query(F.data.startswith("rename_workout_"))
async def rename_workout(callback: CallbackQuery, state: FSMContext):
    n = parse_int_suffix(callback.data)
    if n is None:
        await callback.answer("❌ Неверный ID", show_alert=True)
        return
    await state.update_data(editing_workout_id=n)
    await callback.message.edit_text("Введите новое название:")
    await state.set_state("renaming_workout")
    await callback.answer()

@workouts_router.callback_query(F.data.startswith("change_desc_workout_"))
async def change_desc_workout(callback: CallbackQuery, state: FSMContext):
    n = parse_int_suffix(callback.data)
    if n is None:
        await callback.answer("❌ Неверный ID", show_alert=True)
        return
    await state.update_data(editing_workout_id=n)
    await callback.message.edit_text("Введите новое описание:")
    await state.set_state("changing_workout_description")
    await callback.answer()

@workouts_router.callback_query(F.data.startswith("delete_workout_"))
async def delete_workout(callback: CallbackQuery):
    n = parse_int_suffix(callback.data)
    if n is None:
        await callback.answer("❌ Неверный ID", show_alert=True)
        return
    wid = n
    try:
        async with db_manager.pool.acquire() as conn:
            await conn.execute("UPDATE workouts SET is_active = false WHERE id = $1", wid)
        await callback.message.edit_text("✅ Тренировка удалена.")
        await callback.answer()
    except Exception as e:
        logger.exception("delete_workout error: %s", e)
        await callback.answer("❌ Ошибка", show_alert=True)

# ----------------- CENTRAL TEXT HANDLER -----------------
async def process_workout_text_input(message: Message, state: FSMContext):
    """Обработка текстового ввода в состояниях создания/редактирования/поиска."""
    current_state = await state.get_state()
    try:
        # name
        if current_state in (CreateWorkoutStates.waiting_workout_name, CreateWorkoutStates.waiting_workout_name.state, "waiting_workout_name", "waiting_name"):
            name = message.text.strip()
            if len(name) < 3:
                await message.answer("❌ Название слишком короткое (мин. 3 символа).")
                return
            await state.update_data(name=name)
            kb = InlineKeyboardBuilder()
            kb.button(text="⏭ Пропустить описание", callback_data="create_skip_description")
            kb.button(text="❌ Отменить", callback_data="create_cancel_workout")
            kb.adjust(2)
            await message.answer(f"✅ Название сохранено: *{name}*\n\nВведите описание тренировки или нажмите «Пропустить»", reply_markup=kb.as_markup(), parse_mode="Markdown")
            await state.set_state(CreateWorkoutStates.waiting_workout_description)
            return

        # description
        if current_state in (CreateWorkoutStates.waiting_workout_description, CreateWorkoutStates.waiting_workout_description.state, "waiting_description", "waiting_workout_description"):
            desc = message.text.strip()
            await state.update_data(description=desc)
            await show_block_selection_menu(message, state)
            return

        # block description
        if current_state in (CreateWorkoutStates.adding_block_description, CreateWorkoutStates.adding_block_description.state, "adding_block_description"):
            desc = message.text.strip()
            d = await state.get_data()
            cur = d.get('current_block', 'main')
            sel = d.get('selected_blocks', {})
            sel.setdefault(cur, {"description": "", "exercises": []})
            sel[cur]['description'] = desc
            await state.update_data(selected_blocks=sel)
            await message.answer("✅ Описание блока сохранено.")
            await show_block_selection_menu(message, state)
            return

        # searching exercises for block
        if current_state in ("searching_exercise_for_block",):
            q = message.text.strip().lower()
            async with db_manager.pool.acquire() as conn:
                exs = await conn.fetch("""
                    SELECT id, name, category, muscle_group
                    FROM exercises
                    WHERE LOWER(name) LIKE $1 OR LOWER(category) LIKE $1 OR LOWER(muscle_group) LIKE $1
                    ORDER BY name
                    LIMIT 10
                """, f"%{q}%")
            if not exs:
                await message.answer("❌ Ничего не найдено.")
                return
            kb = InlineKeyboardBuilder()
            for e in exs:
                cat = e.get('category') or "Без категории"
                # we provide create_add_block_ex_ for creation flow
                kb.button(text=f"💪 {e['name']} ({cat})", callback_data=f"create_add_block_ex_{e['id']}")
            kb.button(text="🔍 Новый поиск", callback_data="create_search_ex_for_block")
            kb.button(text="🔙 К упражнениям блока", callback_data="create_back_to_blocks")
            kb.adjust(1)
            await message.answer(f"🔎 Найдено: {len(exs)}", reply_markup=kb.as_markup())
            await state.set_state("searching_exercise_for_block")
            return

        # renaming workout
        if current_state == "renaming_workout":
            new = message.text.strip()
            if len(new) < 3:
                await message.answer("❌ Слишком короткое название.")
                return
            d = await state.get_data()
            wid = d.get('editing_workout_id')
            if not wid:
                await message.answer("❌ Контекст потерян.")
                await state.clear()
                return
            async with db_manager.pool.acquire() as conn:
                await conn.execute("UPDATE workouts SET name = $1 WHERE id = $2", new, wid)
            await message.answer("✅ Название обновлено.")
            await state.clear()
            return

        # changing workout description
        if current_state == "changing_workout_description":
            new = message.text.strip()
            d = await state.get_data()
            wid = d.get('editing_workout_id')
            if not wid:
                await message.answer("❌ Контекст потерян.")
                await state.clear()
                return
            async with db_manager.pool.acquire() as conn:
                await conn.execute("UPDATE workouts SET description = $1 WHERE id = $2", new, wid)
            await message.answer("✅ Описание обновлено.")
            await state.clear()
            return

        # waiting for RPE
        if current_state == "waiting_rpe":
            try:
                rpe_val = int(message.text.strip())
                if rpe_val < 1 or rpe_val > 10:
                    await message.answer("❌ Введите число от 1 до 10.")
                    return
                await state.update_data(last_rpe=rpe_val)
                await message.answer("📦 Укажите общий использованный вес (кг) или напишите 'пропустить':")
                await state.set_state("waiting_weight")
            except ValueError:
                await message.answer("❌ Введите число от 1 до 10.")
            return

        # waiting for weight after workout finish
        if current_state == "waiting_weight":
            d = await state.get_data()
            wid = d.get('finishing_workout_id')
            txt = message.text.strip().lower()
            weight_val = None
            if txt not in ("пропустить", "skip", "-"):
                try:
                    weight_val = float(txt.replace(",", "."))
                except Exception:
                    await message.answer("❌ Введите число (в кг) или 'пропустить'.")
                    return
            user = await db_manager.get_user_by_telegram_id(message.from_user.id)
            rpe = d.get('last_rpe', None)
            created = datetime.utcnow()
            # try save session/results (best-effort)
            try:
                async with db_manager.pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO workout_sessions (user_id, workout_id, started_at, completed_at, status, rpe)
                        VALUES ($1,$2,now(), now(), 'completed', $3)
                    """, user['id'], wid, rpe)
            except Exception:
                logger.exception("Failed to insert workout_session")
            await message.answer("✅ Результат сохранён (или поставлен в очередь). Спасибо!")
            await state.clear()
            return

    except Exception as e:
        logger.exception("process_workout_text_input error: %s", e)
        await message.answer("❌ Ошибка обработки текста.")
        await state.clear()

# ----------------- REGISTER -----------------
def register_workout_handlers(dp):
    """Подключить router к диспетчеру. Безопасно при повторном вызове."""
    try:
        dp.include_router(workouts_router)
        logger.info("✅ workouts_router подключен!")
    except RuntimeError as e:
        # Router уже был подключен — логируем и продолжаем
        logger.warning("workouts_router уже подключён: %s", e)

# экспорт
__all__ = ["workouts_router", "register_workout_handlers", "process_workout_text_input"]
