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

from aiogram.fsm.state import State
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram import F
from states.workout_states import CreateWorkoutStates
#from aiogram.filters import StateFilter, Text


logger = logging.getLogger(__name__)
workouts_router = Router()




@workouts_router.message()
async def _debug_all_messages(message: Message, state: FSMContext):
    current_state = await state.get_state()
    print(f"💬 DEBUG: Получено сообщение '{message.text}' при состоянии {current_state}")


# ----------------- HELPERS -----------------
def _parse_int_suffix(callback_data: str) -> Optional[int]:
    """Возвращает целый суффикс после '_' или None."""
    try:
        part = callback_data.split("_")[-1]
        return int(part) if part.isdigit() else None
    except Exception:
        return None

def _parse_id_with_prefix(callback_data: str, prefix: str) -> int:
    """Парсит ID после prefix, бросает ValueError, если не число."""
    if not callback_data.startswith(prefix):
        raise ValueError("prefix mismatch")
    tail = callback_data[len(prefix):]
    if tail.isdigit():
        return int(tail)
    raise ValueError("no numeric id")

async def _safe_edit_or_send(message, text, reply_markup=None, parse_mode=None):
    """Пробуем edit_text, если не удалось — answer."""
    try:
        await message.edit_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception:
        await message.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)

# ----------------- MENU -----------------
@workouts_router.callback_query(F.data == "workouts_menu")
async def workouts_menu(callback: CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.button(text="🏋️ Мои тренировки", callback_data="my_workouts")
    kb.button(text="🔍 Найти тренировку", callback_data="find_workout")
    kb.button(text="➕ Создать тренировку", callback_data="create_workout")
    kb.button(text="📊 Моя статистика", callback_data="workout_statistics")
    kb.button(text="🔙 Главное меню", callback_data="main_menu")
    kb.adjust(2)
    await _safe_edit_or_send(callback.message, "🏋️ **Меню тренировок**\n\nВыберите действие:", reply_markup=kb.as_markup(), parse_mode="Markdown")
    await callback.answer()

@workouts_router.callback_query(F.data == "manual_add_exercise")
async def add_exercise_manually(callback: CallbackQuery, state: FSMContext):
    """Ручное добавление упражнения текстом"""
    await callback.message.edit_text(
        "📝 Введите упражнение вручную:\n\n"
        "_Например:_ «Жим лёжа 3х10 70% от 1ПМ, отдых 90 сек.»",
        parse_mode="Markdown"
    )
    await state.set_state("manual_exercise_input")
    await callback.answer()

# @workouts_router.message(CreateWorkoutStates.manual_exercise_input)
# async def handle_manual_exercise_input(message: Message, state: FSMContext):
#     """Обрабатывает ручной ввод упражнения"""
#     user_input = message.text.strip()
#     data = await state.get_data()

#     await message.answer(f"✅ Добавлено упражнение:\n\n{user_input}")
    
#     # Добавляем в список временных упражнений
#     exercises = data.get("manual_exercises", [])
#     exercises.append(user_input)
#     await state.update_data(manual_exercises=exercises)

#     # Возврат в меню блока
#     keyboard = InlineKeyboardBuilder()
#     keyboard.button(text="➕ Добавить ещё", callback_data="manual_add_exercise")
#     keyboard.button(text="⬅️ Назад", callback_data="back_to_constructor")
#     keyboard.adjust(1)
#     await message.answer("Что дальше?", reply_markup=keyboard.as_markup())

#     # Возвращаем состояние к добавлению упражнений
#     await state.set_state(CreateWorkoutStates.adding_exercises)

@workouts_router.message(CreateWorkoutStates.manual_exercise_input)
async def handle_manual_exercise_input(message: Message, state: FSMContext):
    text = message.text.strip()
    data = await state.get_data()
    exercises = data.get("manual_exercises", [])
    exercises.append(text)
    await state.update_data(manual_exercises=exercises)

    await message.answer(f"✅ Добавлено упражнение:\n\n{text}")

    # Клавиатура для следующего шага
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Добавить ещё", callback_data="manual_add_exercise")
    kb.button(text="⬅️ Назад", callback_data="back_to_constructor")
    kb.adjust(1)
    await message.answer("Что дальше?", reply_markup=kb.as_markup())

    await state.set_state(CreateWorkoutStates.adding_exercises)


# ----------------- MY WORKOUTS -----------------
@workouts_router.callback_query(F.data == "my_workouts")
async def my_workouts(callback: CallbackQuery):
    logger.info("my_workouts by user %s", callback.from_user.id)
    try:
        user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
        async with db_manager.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT w.id, w.name, w.unique_id,
                    (SELECT COUNT(*) FROM workout_exercises we WHERE we.workout_id = w.id) as exercise_count,
                    w.estimated_duration_minutes
                FROM workouts w
                WHERE w.created_by = $1 AND coalesce(w.is_active, true) = true
                ORDER BY w.created_at DESC
                LIMIT 50
            """, user['id'])
        if not rows:
            kb = InlineKeyboardBuilder()
            kb.button(text="➕ Создать первую", callback_data="create_workout")
            kb.button(text="🔙 В меню", callback_data="workouts_menu")
            kb.adjust(1)
            await _safe_edit_or_send(callback.message, "У вас пока нет тренировок.", reply_markup=kb.as_markup())
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
        await _safe_edit_or_send(callback.message, text, reply_markup=kb.as_markup(), parse_mode="Markdown")
        await callback.answer()
    except Exception as e:
        logger.exception("my_workouts error: %s", e)
        await callback.answer("Ошибка получения тренировок", show_alert=True)

# ----------------- VIEW DETAILS -----------------
@workouts_router.callback_query(F.data.startswith("view_workout_"))
async def view_workout_details(callback: CallbackQuery):
    try:
        wid = _parse_id_with_prefix(callback.data, "view_workout_")
    except ValueError:
        await callback.answer("Некорректный ID", show_alert=True)
        return

    try:
        async with db_manager.pool.acquire() as conn:
            workout = await conn.fetchrow("""
                SELECT w.*, u.first_name as creator_name, u.last_name as creator_lastname
                FROM workouts w
                LEFT JOIN users u ON w.created_by = u.id
                WHERE w.id = $1 AND coalesce(w.is_active, true) = true
            """, wid)
            if not workout:
                await callback.answer("Тренировка не найдена", show_alert=True)
                return
            exercises = await conn.fetch("""
                SELECT we.*, e.name as exercise_name, e.muscle_group, e.category
                FROM workout_exercises we
                LEFT JOIN exercises e ON e.id = we.exercise_id
                WHERE we.workout_id = $1
                ORDER BY we.phase, we.order_in_phase
            """, wid)
    except Exception as e:
        logger.exception("view_workout_details db error: %s", e)
        await callback.answer("Ошибка БД", show_alert=True)
        return

    text = f"🏷 **{workout['name']}**\n\n"
    if workout.get('description'):
        text += f"📝 _{workout['description']}_\n\n"
    text += f"👤 Автор: {workout.get('creator_name') or ''} {workout.get('creator_lastname') or ''}\n"
    text += f"⏱ Время: ~{workout.get('estimated_duration_minutes') or 0} мин\n"
    text += f"💡 Код: `{workout.get('unique_id')}`\n\n"

    if exercises:
        phase_map = {'warmup': '🔥 Разминка', 'nervousprep': '⚡ Подготовка НС', 'main': '💪 Основная', 'cooldown': '🧘 Заминка'}
        cur = None
        for ex in exercises:
            if ex['phase'] != cur:
                cur = ex['phase']
                text += f"\n**{phase_map.get(cur, cur)}:**\n"
            # show minimal info
            reps = ""
            if ex.get('reps_min') is not None:
                if ex.get('reps_max') is not None and ex['reps_min'] != ex['reps_max']:
                    reps = f"{ex['reps_min']}-{ex['reps_max']}"
                else:
                    reps = f"{ex['reps_min']}"
            else:
                reps = "-"
            sets = ex.get('sets') or "-"
            text += f"• **{ex['exercise_name']}** — {sets}×{reps}"
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
    kb.button(text="✏️ Редактировать", callback_data=f"edit_workout_{wid}")
    kb.button(text="🗑️ Удалить", callback_data=f"delete_workout_{wid}")
    kb.button(text="🔙 В мои", callback_data="my_workouts")
    kb.adjust(2)
    await _safe_edit_or_send(callback.message, text, reply_markup=kb.as_markup(), parse_mode="Markdown")
    await callback.answer()

# ----------------- CREATE FLOW (FSM) -----------------
@workouts_router.callback_query(F.data == "create_workout")
async def create_workout_start(callback: CallbackQuery, state: FSMContext):
    logger.info("create_workout_start by %s", callback.from_user.id)
    kb = InlineKeyboardBuilder()
    kb.button(text="❌ Отменить", callback_data="create_cancel")
    kb.adjust(1)
    await _safe_edit_or_send(callback.message, "🏋️ **Создание тренировки**\n\nВведите название тренировки:", reply_markup=kb.as_markup(), parse_mode="Markdown")
    await state.set_state(CreateWorkoutStates.waiting_workout_name)
    await callback.answer()

@workouts_router.callback_query(F.data == "create_cancel")
async def create_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardBuilder()
    kb.button(text="🏋️ Мои тренировки", callback_data="my_workouts")
    kb.button(text="🔙 В меню", callback_data="workouts_menu")
    kb.adjust(1)
    await _safe_edit_or_send(callback.message, "Создание тренировки отменено.", reply_markup=kb.as_markup())
    await callback.answer()

# Показываем меню выбора блоков
async def _show_block_selection(message, state: FSMContext):
    data = await state.get_data()
    name = data.get('name', 'Без названия')
    selected = data.get('selected_blocks', {})
    text = f"🔧 **Структура тренировки:** {name}\n\nВыберите блок и добавьте упражнения:\n\n"
    blocks = [('warmup', '🔥 Разминка'), ('nervousprep', '⚡ Подготовка НС'), ('main', '💪 Основная'), ('cooldown', '🧘 Заминка')]
    for k, label in blocks:
        status = "✅" if k in selected else "⭕"
        cnt = len(selected.get(k, {}).get('exercises', [])) if k in selected else 0
        text += f"{status} {label} — {cnt} упр.\n"
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Разминка", callback_data="create_add_warmup")
    kb.button(text="➕ Подготовка НС", callback_data="create_add_nervousprep")
    kb.button(text="➕ Основная", callback_data="create_add_main")
    kb.button(text="➕ Заминка", callback_data="create_add_cooldown")
    kb.button(text="✅ Готово — сохранить тренировку", callback_data="create_finish")
    kb.button(text="❌ Отменить", callback_data="create_cancel")
    kb.adjust(2)
    await _safe_edit_or_send(message, text, reply_markup=kb.as_markup(), parse_mode="Markdown")
    await state.set_state(CreateWorkoutStates.selecting_blocks)

# Обработка текстового ввода (все состояния создания/редактирования)
async def process_workout_text_input(message: Message, state: FSMContext):
    current = await state.get_state()
    # НАЗВАНИЕ
    if current in (CreateWorkoutStates.waiting_workout_name, CreateWorkoutStates.waiting_workout_name.state, "waiting_workout_name", "waiting_name"):
        name = message.text.strip()
        if len(name) < 3:
            await message.answer("Название слишком короткое (мин. 3 символа).")
            return
        await state.update_data(name=name)
        kb = InlineKeyboardBuilder()
        kb.button(text="⏭ Пропустить описание", callback_data="create_skip_description")
        kb.button(text="❌ Отменить", callback_data="create_cancel")
        kb.adjust(2)
        await message.answer(f"✅ Название сохранено: *{name}*\n\nВведите описание или нажмите «Пропустить»", reply_markup=kb.as_markup(), parse_mode="Markdown")
        await state.set_state(CreateWorkoutStates.waiting_workout_description)
        return

    # ОПИСАНИЕ
    if current in (CreateWorkoutStates.waiting_workout_description, CreateWorkoutStates.waiting_workout_description.state, "waiting_workout_description", "waiting_description"):
        desc = message.text.strip()
        await state.update_data(description=desc)
        await _show_block_selection(message, state)
        return

    # Блок — описание блока
    if current in (CreateWorkoutStates.adding_block_description, CreateWorkoutStates.adding_block_description.state, "adding_block_description"):
        desc = message.text.strip()
        d = await state.get_data()
        cur_block = d.get('current_block')
        sel = d.get('selected_blocks', {})
        sel.setdefault(cur_block, {"description": "", "exercises": []})
        sel[cur_block]['description'] = desc
        await state.update_data(selected_blocks=sel)
        await message.answer("Описание блока сохранено.")
        await _show_block_selection(message, state)
        return

    # Поиск упражнений — текстовый ввод (используем ту же логику как в exercises)
    if current == "searching_exercise_for_block":
        q = message.text.strip().lower()
        async with db_manager.pool.acquire() as conn:
            exs = await conn.fetch("""
                SELECT id, name, category, muscle_group
                FROM exercises
                WHERE lower(name) LIKE $1 OR lower(category) LIKE $1 OR lower(muscle_group) LIKE $1
                ORDER BY name
                LIMIT 20
            """, f"%{q}%")
        if not exs:
            await message.answer("По запросу ничего не найдено.")
            return
        kb = InlineKeyboardBuilder()
        for e in exs:
            cat = e.get('category') or "Без категории"
            kb.button(text=f"💪 {e['name']} ({cat})", callback_data=f"create_add_ex_{e['id']}")
        kb.button(text="🔍 Новый поиск", callback_data="create_search_ex")
        kb.button(text="🔙 К блокам", callback_data="create_back_to_blocks")
        kb.adjust(1)
        await message.answer(f"🔎 Найдено: {len(exs)}", reply_markup=kb.as_markup())
        return

    # RPE / weight flow or editing flows could be added here
    # fallback
    await message.answer("Я не ожидал этот ввод в текущем контексте. Попробуйте использовать меню.")
    return

# Пропустить описание (legacy compatible)
@workouts_router.callback_query(F.data == "create_skip_description")
async def create_skip_description(callback: CallbackQuery, state: FSMContext):
    await state.update_data(description="")
    await _show_block_selection(callback.message, state)
    await callback.answer()




# Добавление блока - переход в меню блока
@workouts_router.callback_query(F.data.in_(["create_add_warmup", "create_add_nervousprep", "create_add_main", "create_add_cooldown"]))
async def create_add_block(callback: CallbackQuery, state: FSMContext):
    mapping = {
        "create_add_warmup": "warmup",
        "create_add_nervousprep": "nervousprep",
        "create_add_main": "main",
        "create_add_cooldown": "cooldown"
    }
    phase = mapping.get(callback.data)
    if not phase:
        await callback.answer()
        return
    await state.update_data(current_block=phase)
    kb = InlineKeyboardBuilder()
    kb.button(text="📝 Добавить описание блока", callback_data="create_add_block_desc")
    kb.button(text="🔍 Найти упражнение", callback_data="create_search_ex")
    kb.button(text="✏️ Добавить упражнение вручную (текстом)", callback_data="manual_add_exercise")
    kb.button(text="🔙 К выбору блоков", callback_data="create_back_to_blocks")
    kb.adjust(1)
    names = {'warmup': 'Разминка', 'nervousprep': 'Подготовка НС', 'main': 'Основная', 'cooldown': 'Заминка'}
    await _safe_edit_or_send(callback.message, f"📋 **{names.get(phase)}**\n\nВыберите действие:", reply_markup=kb.as_markup(), parse_mode="Markdown")
    await callback.answer()

@workouts_router.callback_query(F.data == "create_back_to_blocks")
async def create_back_to_blocks(callback: CallbackQuery, state: FSMContext):
    await _show_block_selection(callback.message, state)
    await callback.answer()

@workouts_router.callback_query(F.data == "create_add_block_desc")
async def create_add_block_desc(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("📝 Введите описание для блока:")
    await state.set_state(CreateWorkoutStates.adding_block_description)
    await callback.answer()

# Поиск упражнений — попросить ввести текст
@workouts_router.callback_query(F.data == "create_search_ex")
async def create_search_ex(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("🔍 Введите текст для поиска упражнений (например: присед, жим):")
    await state.set_state("searching_exercise_for_block")
    await callback.answer()

# Добавление упражнения из результатов поиска
@workouts_router.callback_query(F.data.startswith("create_add_ex_"))
async def create_add_ex(callback: CallbackQuery, state: FSMContext):
    ex_id = _parse_int_suffix(callback.data)
    if ex_id is None:
        await callback.answer("Некорректный ID упражнения", show_alert=True)
        return
    # Получаем упражнение
    async with db_manager.pool.acquire() as conn:
        row = await conn.fetchrow("SELECT id, name FROM exercises WHERE id = $1", ex_id)
    if not row:
        await callback.answer("Упражнение не найдено", show_alert=True)
        return

    # Сохраняем в state временно (по умолчанию без параметров)
    data = await state.get_data()
    cur = data.get('current_block', 'main')
    sel = data.get('selected_blocks', {})
    sel.setdefault(cur, {"description": "", "exercises": []})
    # по идее тут нужно запросить параметры: sets/reps/%1RM/rest
    # мы предлагаем выбор: ввести параметры или добавить как простой пункт
    await state.update_data(pending_exercise={"id": row['id'], "name": row['name'], "block": cur})
    kb = InlineKeyboardBuilder()
    kb.button(text="⚙️ Указать параметры (подходы/повторы/%1ПМ)", callback_data="create_configure_pending_ex")
    kb.button(text="➕ Добавить просто (без параметров)", callback_data="create_confirm_add_pending_ex")
    kb.button(text="🔙 К результатам поиска", callback_data="create_search_ex")
    kb.adjust(1)
    await callback.message.edit_text(f"Выбрано: *{row['name']}*\n\nДобавить с параметрами или просто?", reply_markup=kb.as_markup(), parse_mode="Markdown")
    await callback.answer()

# Редактирование параметров для только что выбранного упражнения
@workouts_router.callback_query(F.data == "create_configure_pending_ex")
async def create_configure_pending_ex(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    pending = data.get('pending_exercise')
    if not pending:
        await callback.answer("Контекст потерян", show_alert=True)
        return
    # начинаем диалог: запрос подходов
    await state.update_data(config_step="sets")
    await callback.message.edit_text("Введите количество подходов (целое число), или 'пропустить' чтобы добавить без параметров:")
    await state.set_state("configuring_pending_ex")
    await callback.answer()

# подтвердить добавление без параметров
@workouts_router.callback_query(F.data == "create_confirm_add_pending_ex")
async def create_confirm_add_pending_ex(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    pending = data.get('pending_exercise')
    if not pending:
        await callback.answer("Контекст потерян", show_alert=True)
        return
    cur = pending['block']
    sel = data.get('selected_blocks', {})
    sel.setdefault(cur, {"description": "", "exercises": []})
    sel[cur]['exercises'].append({
        "id": pending['id'],
        "name": pending['name'],
        "sets": None,
        "reps_min": None,
        "reps_max": None,
        "one_rm_percent": None,
        "rest_seconds": None
    })
    # чистим pending
    await state.update_data(selected_blocks=sel)
    await state.update_data(pending_exercise=None)
    await callback.message.edit_text(f"✅ Упражнение *{pending['name']}* добавлено в блок.", parse_mode="Markdown")
    await _show_block_selection(callback.message, state)
    await callback.answer()

# Обработка текстового ввода параметров для pending exercise
@workouts_router.message()
async def configuring_pending_ex_input(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state != "configuring_pending_ex":
        return  # не наш контекст
    text = message.text.strip().lower()
    data = await state.get_data()
    pending = data.get('pending_exercise')
    if not pending:
        await message.answer("Контекст потерян.")
        await state.clear()
        return
    step = data.get('config_step')
    # шаг: sets -> reps -> percent -> rest -> confirm
    if step == "sets":
        if text in ("пропустить", "skip", "-"):
            # добавить без параметров
            sel = data.get('selected_blocks', {})
            cur = pending['block']
            sel.setdefault(cur, {"description": "", "exercises": []})
            sel[cur]['exercises'].append({
                "id": pending['id'],
                "name": pending['name'],
                "sets": None,
                "reps_min": None,
                "reps_max": None,
                "one_rm_percent": None,
                "rest_seconds": None
            })
            await state.update_data(selected_blocks=sel)
            await state.update_data(pending_exercise=None)
            await message.answer("Добавлено без параметров.")
            await _show_block_selection(message, state)
            return
        try:
            sets = int(text)
            await state.update_data(config_sets=sets, config_step="reps")
            await message.answer("Введите количество повторов (одиночное число или диапазон через '-': например '8' или '8-12'):")
            return
        except ValueError:
            await message.answer("Введите целое число для подходов или 'пропустить'.")
            return
    if step == "reps":
        # парсим reps
        if "-" in text:
            try:
                a, b = text.split("-", 1)
                rmin = int(a.strip())
                rmax = int(b.strip())
            except Exception:
                await message.answer("Неверный формат диапазона. Пример: 8-12")
                return
        else:
            try:
                rmin = rmax = int(text)
            except Exception:
                await message.answer("Введите число повторов или диапазон 8-12.")
                return
        await state.update_data(config_reps_min=rmin, config_reps_max=rmax, config_step="percent")
        await message.answer("Укажите % от 1ПМ (например 70) или напишите 'нет' чтобы пропустить:")
        return
    if step == "percent":
        if text in ("нет", "no", "пропустить", "skip", "-"):
            await state.update_data(config_one_rm_percent=None, config_step="rest")
            await message.answer("Укажите отдых между подходами в секундах (например 90) или 'пропустить':")
            return
        try:
            perc = int(text)
            if not (0 < perc <= 200):
                raise ValueError
            await state.update_data(config_one_rm_percent=perc, config_step="rest")
            await message.answer("Укажите отдых между подходами в секундах (например 90) или 'пропустить':")
            return
        except Exception:
            await message.answer("Введите целое число процентов, например 70, или 'нет'.")
            return
    if step == "rest":
        if text in ("пропустить", "skip", "-"):
            rest = None
        else:
            try:
                rest = int(text)
            except Exception:
                await message.answer("Введите число секунд или 'пропустить'.")
                return
        # собираем и добавляем
        sel = data.get('selected_blocks', {})
        cur = pending['block']
        sel.setdefault(cur, {"description": "", "exercises": []})
        entry = {
            "id": pending['id'],
            "name": pending['name'],
            "sets": data.get('config_sets'),
            "reps_min": data.get('config_reps_min'),
            "reps_max": data.get('config_reps_max'),
            "one_rm_percent": data.get('config_one_rm_percent'),
            "rest_seconds": rest
        }
        # если указан percent, проверим есть ли 1RM у пользователя для этого упражнения
        if entry.get('one_rm_percent'):
            user = await db_manager.get_user_by_telegram_id(message.from_user.id)
            async with db_manager.pool.acquire() as conn:
                orm = await conn.fetchrow("SELECT * FROM one_rep_max WHERE user_id = $1 AND exercise_id = $2", user['id'], pending['id'])
            if not orm:
                # предложим пройти тест (зависит от модуля tests)
                kb = InlineKeyboardBuilder()
                kb.button(text="Пройти тест на 1ПМ", callback_data=f"start_1rm_test_for_{pending['id']}")
                kb.button(text="Добавить без %", callback_data="create_confirm_add_pending_ex")
                kb.button(text="🔙 К блокам", callback_data="create_back_to_blocks")
                kb.adjust(1)
                await message.answer("1ПМ для этого упражнения не найден — хотите пройти тест?", reply_markup=kb.as_markup())
                return
        sel[cur]['exercises'].append(entry)
        await state.update_data(selected_blocks=sel)
        await state.update_data(pending_exercise=None)
        # чистим временные конфиги
        for k in ["config_step", "config_sets", "config_reps_min", "config_reps_max", "config_one_rm_percent"]:
            if k in data:
                await state.update_data({k: None})
        await message.answer(f"✅ Упражнение {entry['name']} добавлено в {cur}.")
        await _show_block_selection(message, state)
        return

# Обработчик кнопки запуска теста 1РМ (ссылка в тестовый модуль)
@workouts_router.callback_query(F.data.startswith("start_1rm_test_for_"))
async def start_1rm_test_for(callback: CallbackQuery, state: FSMContext):
    ex_id = _parse_int_suffix(callback.data)
    if ex_id is None:
        await callback.answer("Некорректно", show_alert=True)
        return
    # перенаправляем пользователя на модуль тестов — предполагается, что он есть
    # ставим состояние, чтобы после теста вернуться: сохраняем контекст
    data = await state.get_data()
    await state.update_data(await_state_return={"after": "add_pending_after_1rm", "exercise_id": ex_id, "context": data})
    # предполагаем, что в handlers.tests есть функция start_1rm_test_from_handlers
    try:
        from handlers import tests as tests_module
        # если есть готовая функция для запуска 1rm теста — вызываем её (если нет, просто сообщаем)
        if hasattr(tests_module, "start_1rm_test_from_handlers"):
            await tests_module.start_1rm_test_from_handlers(callback, ex_id)
            await callback.answer()
            return
    except Exception:
        logger.info("Модуль tests не предоставляет start_1rm_test_from_handlers, отправим инструкцию")
    await callback.message.edit_text("Пожалуйста пройдите тест 1ПМ вручную (/start_1rm_test), затем вернитесь и добавьте упражнение.")
    await callback.answer()

# Подтвердить завершение создания — сохранить в БД
@workouts_router.callback_query(F.data == "create_finish")
async def create_finish(callback: CallbackQuery, state: FSMContext):
    try:
        data = await state.get_data()
        name = data.get('name')
        if not name:
            await callback.answer("Нет названия тренировки", show_alert=True)
            return
        selected = data.get('selected_blocks', {})
        total_exs = sum(len(b.get('exercises', [])) for b in selected.values())
        if total_exs == 0:
            await callback.answer("Добавьте хотя бы одно упражнение!", show_alert=True)
            return
        user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
        async with db_manager.pool.acquire() as conn:
            wid = await conn.fetchval("""
                INSERT INTO workouts (name, description, created_by, created_at, is_active)
                VALUES ($1,$2,$3, now(), true) RETURNING id
            """, name, data.get('description', ''))
            order = 0
            for phase, block in selected.items():
                for ex in block.get('exercises', []):
                    order += 1
                    await conn.execute("""
                        INSERT INTO workout_exercises 
                        (workout_id, exercise_id, phase, order_in_phase, sets, reps_min, reps_max, one_rm_percent, rest_seconds, notes)
                        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
                    """, wid, ex['id'], phase, order, ex.get('sets'), ex.get('reps_min'), ex.get('reps_max'), ex.get('one_rm_percent'), ex.get('rest_seconds'), ex.get('notes'))
            unique = await conn.fetchval("SELECT unique_id FROM workouts WHERE id = $1", wid)
        await callback.message.edit_text(f"🎉 Тренировка создана! Код: `{unique}`\nУпражнений: {total_exs}", parse_mode="Markdown")
        await state.clear()
        await callback.answer()
    except Exception as e:
        logger.exception("create_finish error: %s", e)
        await callback.answer("Ошибка при сохранении", show_alert=True)

# ----------------- START/FINISH FLOW (player) -----------------
@workouts_router.callback_query(F.data.startswith("start_workout_"))
async def start_workout(callback: CallbackQuery):
    wid = _parse_int_suffix(callback.data)
    if wid is None:
        await callback.answer("Некорректный ID", show_alert=True)
        return
    async with db_manager.pool.acquire() as conn:
        w = await conn.fetchrow("SELECT name FROM workouts WHERE id = $1", wid)
    if not w:
        await callback.answer("Тренировка не найдена", show_alert=True)
        return
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Завершил тренировку", callback_data=f"finish_workout_{wid}")
    kb.button(text="📋 Детали", callback_data=f"view_workout_{wid}")
    kb.adjust(1)
    await _safe_edit_or_send(callback.message, f"▶️ Начинаем: **{w['name']}**\n\nПосле выполнения нажмите «Завершил тренировку»", reply_markup=kb.as_markup(), parse_mode="Markdown")
    await callback.answer()

@workouts_router.callback_query(F.data.startswith("finish_workout_"))
async def finish_workout(callback: CallbackQuery, state: FSMContext):
    wid = _parse_int_suffix(callback.data)
    if wid is None:
        await callback.answer()
        return
    await state.update_data(finishing_workout_id=wid)
    await callback.message.edit_text("✅ Оцени тренировку по шкале 1-10 (RPE):")
    await state.set_state("waiting_rpe")
    await callback.answer()

# Обработка текста после завершения (RPE -> weight)
# (этот общечатовый обработчик уже может быть подключён в handlers.__init__ -> handle_all_text_messages)
# но на всякий случай оставляем отдельный handler ниже, если включён в маршрутизацию общего message handler.

# ----------------- EDIT / DELETE -----------------
@workouts_router.callback_query(F.data.startswith("edit_workout_"))
async def edit_workout(callback: CallbackQuery, state: FSMContext):
    wid = _parse_int_suffix(callback.data)
    if wid is None:
        await callback.answer("Некорректный ID", show_alert=True)
        return
    async with db_manager.pool.acquire() as conn:
        w = await conn.fetchrow("SELECT id, name, description, created_by FROM workouts WHERE id = $1", wid)
    if not w:
        await callback.answer("Не найдено", show_alert=True)
        return
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    if w['created_by'] != user['id']:
        await callback.answer("Только автор может редактировать", show_alert=True)
        return
    kb = InlineKeyboardBuilder()
    kb.button(text="✏️ Переименовать", callback_data=f"rename_workout_{wid}")
    kb.button(text="📝 Изменить описание", callback_data=f"change_desc_workout_{wid}")
    kb.button(text="🗑️ Удалить", callback_data=f"delete_workout_{wid}")
    kb.button(text="🔙 К тренировке", callback_data=f"view_workout_{wid}")
    kb.adjust(1)
    await _safe_edit_or_send(callback.message, f"✏️ Редактирование: {w['name']}", reply_markup=kb.as_markup())
    await callback.answer()

@workouts_router.callback_query(F.data.startswith("delete_workout_"))
async def delete_workout(callback: CallbackQuery):
    wid = _parse_int_suffix(callback.data)
    if wid is None:
        await callback.answer("Некорректный ID", show_alert=True)
        return
    try:
        async with db_manager.pool.acquire() as conn:
            await conn.execute("UPDATE workouts SET is_active = false WHERE id = $1", wid)
        await callback.message.edit_text("✅ Тренировка удалена.")
        await callback.answer()
    except Exception as e:
        logger.exception("delete_workout error: %s", e)
        await callback.answer("Ошибка", show_alert=True)

# ----------------- REGISTER -----------------
def register_workout_handlers(dp):
    print("✅ workouts_router успешно подключён!")
   # dp.include_router(workouts_router)

    # Регистрация обработчиков callback'ов (у тебя они уже есть выше)
    dp.callback_query.register(workouts_menu, F.data == "workouts_menu")
    dp.callback_query.register(create_workout_start, F.data == "create_workout")
    dp.callback_query.register(create_cancel, F.data == "cancel_workout_creation")
    dp.callback_query.register(create_skip_description, F.data == "skip_workout_description")

    # ...и т.д. (твои остальные callback-хендлеры)

    # === Обработка текстового ввода при создании тренировки ===
    dp.message.register(
    process_workout_text_input,
    StateFilter(
        CreateWorkoutStates.waiting_workout_name,
        CreateWorkoutStates.waiting_workout_description,
        CreateWorkoutStates.adding_block_description,
        CreateWorkoutStates.manual_exercise_input
    ),
    F.text
)

    logger.info("🏋️ Обработчики тренировок зарегистрированы")


__all__ = ["workouts_router", "register_workout_handlers", "process_workout_text_input"]
