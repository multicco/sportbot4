# handlers/workouts.py
# -*- coding: utf-8 -*-
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
logger = logging.getLogger(__name__)
import asyncio

from aiogram import Bot, F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command, StateFilter
from aiogram.enums import ParseMode
from utils.helpers import _safe_edit_or_send
from utils.nav import add_nav_buttons
from database import db_manager
from states.workout_states import CreateWorkoutStates

logger = logging.getLogger(__name__)
workouts_router = Router()
#from handlers.exercises import search_exercise_menu
#........................nazaz.....................

# =====================================================================
# ✨ ДОЛГОВРЕМЕННОЕ ХРАНИЛИЩЕ ЧЕРНОВИКОВ ТРЕНИРОВКИ (не сгорает при
# выходе в главное меню, сбросе FSM, неизвестном состоянии и рестарте
# бота — данные живут в PostgreSQL).
# =====================================================================
WORKOUT_DRAFT_KEY = "workout_draft"   # ключ в FSM-данных (активный черновик)


async def _ensure_workout_drafts_table() -> None:
    """Создать таблицу черновиков (идемпотентно)."""
    async with db_manager.pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS workout_drafts (
                user_id     BIGINT PRIMARY KEY,
                state       TEXT,
                data        TEXT,
                updated_at  TIMESTAMPTZ DEFAULT NOW()
            )
        """)


async def _save_workout_draft(state: FSMContext, telegram_id: int) -> None:
    """Сохранить текущий FSM-черновик тренировки в БД."""
    try:
        data = await state.get_data()
        draft = data.get(WORKOUT_DRAFT_KEY)
        if not isinstance(draft, dict):
            return
        current = await state.get_state()
        import json as _json
        async with db_manager.pool.acquire() as conn:
            await _ensure_workout_drafts_table()
            await conn.execute(
                """
                INSERT INTO workout_drafts (user_id, state, data, updated_at)
                VALUES ($1, $2, $3, NOW())
                ON CONFLICT (user_id)
                DO UPDATE SET state = EXCLUDED.state,
                              data = EXCLUDED.data,
                              updated_at = NOW()
                """,
                telegram_id, current, _json.dumps(draft, ensure_ascii=False, default=str),
            )
    except Exception:
        logger.debug("Не удалось сохранить черновик тренировки", exc_info=True)


async def _load_workout_draft(telegram_id: int) -> Optional[Dict[str, Any]]:
    """Загрузить черновик из БД. Возвращает {'state': str|None, 'draft': dict} или None."""
    try:
        import json as _json
        async with db_manager.pool.acquire() as conn:
            await _ensure_workout_drafts_table()
            row = await conn.fetchrow(
                "SELECT state, data FROM workout_drafts WHERE user_id = $1",
                telegram_id,
            )
        if not row or not row["data"]:
            return None
        draft = _json.loads(row["data"])
        if not isinstance(draft, dict):
            return None
        return {"state": row["state"], "draft": draft}
    except Exception:
        logger.debug("Не удалось загрузить черновик тренировки", exc_info=True)
        return None


async def _delete_workout_draft(telegram_id: int) -> None:
    try:
        async with db_manager.pool.acquire() as conn:
            await _ensure_workout_drafts_table()
            await conn.execute("DELETE FROM workout_drafts WHERE user_id = $1", telegram_id)
    except Exception:
        logger.debug("Не удалось удалить черновик тренировки", exc_info=True)


def _draft_is_active(draft: Dict[str, Any]) -> bool:
    """Черновик «живой», если есть название и/или упражнения в блоках."""
    if not isinstance(draft, dict):
        return False
    if draft.get("editing_workout_id"):
        return True
    if (draft.get("name") or "").strip():
        return True
    selected = draft.get("selected_blocks") or {}
    return any(b.get("exercises") for b in selected.values() if isinstance(b, dict))


async def _sync_workout_draft(state: FSMContext, **updates) -> None:
    """Обновить FSM-данные И зеркало-черновик одним вызовом.

    Все шаги конструктора тренировки должны использовать ЭТУ функцию
    вместо state.update_data(...) — тогда черновик автоматически
    сохраняется в БД после каждого шага (значения None тоже попадают в
    черновик, чтобы очистка временных ключей не «оживляла» их при
    восстановлении).
    """
    await state.update_data(**updates)
    data = await state.get_data()
    draft = dict(data.get(WORKOUT_DRAFT_KEY) or {})
    for key in ("name", "description", "selected_blocks", "current_block",
                "searching_in_block", "editing_workout_id", "pending_exercise",
                "config_step", "config_sets", "config_reps_min", "config_reps_max",
                "config_one_rm_percent", "selected_exercise_id",
                "selected_exercise_name", "selected_exercise_1rm",
                "selected_exercise_defaults"):
        if key in updates:
            draft[key] = updates[key]
    await state.update_data({WORKOUT_DRAFT_KEY: draft})


async def _sync_and_save_draft(state: FSMContext, message_or_cb, **updates) -> None:
    """_sync_workout_draft + немедленный снимок в БД (по telegram_id из события)."""
    await _sync_workout_draft(state, **updates)
    tg_id = getattr(getattr(message_or_cb, "from_user", None), "id", None)
    if tg_id is None:
        tg_id = getattr(message_or_cb, "id", None)  # Message
    if tg_id:
        await _save_workout_draft(state, tg_id)


async def _restore_workout_draft(message_or_cb, state: FSMContext, telegram_id: int) -> bool:
    """Восстановить активный черновик (из FSM, иначе из БД) и перерисовать экран.

    Возвращает True, если восстановление выполнено.
    """
    data = await state.get_data()
    draft = data.get(WORKOUT_DRAFT_KEY)
    current = await state.get_state()

    if not (isinstance(draft, dict) and _draft_is_active(draft)):
        loaded = await _load_workout_draft(telegram_id)
        if loaded and _draft_is_active(loaded["draft"]):
            draft = loaded["draft"]
            current = loaded["state"]
            new_data = dict(await state.get_data())
            new_data[WORKOUT_DRAFT_KEY] = draft
            new_data.update({k: v for k, v in draft.items() if k != "nav_back"})
            await state.set_data(new_data)
            if current:
                await state.set_state(current)
        else:
            return False

    # Если состояние потеряно, но черновик есть — восстановим на самый
    # логичный экран по содержимому черновика.
    if not current:
        if draft.get("selected_blocks") is not None or draft.get("name"):
            await state.set_state(CreateWorkoutStates.selecting_blocks)
            current = CreateWorkoutStates.selecting_blocks.state
        else:
            await state.set_state(CreateWorkoutStates.waiting_workout_name)
            current = CreateWorkoutStates.waiting_workout_name.state

    text_obj = getattr(message_or_cb, "text", None)
    msg = getattr(message_or_cb, "message", message_or_cb)

    # Черновики других модулей (упражнения/тесты), случайно попавшие под
    # /train — не восстанавливаем здесь.
    if "CreateWorkoutStates" not in str(current):
        return False

    if current == CreateWorkoutStates.waiting_workout_name.state:
        kb = InlineKeyboardBuilder()
        kb.button(text="❌ Отменить", callback_data="create_cancel")
        add_nav_buttons(kb, back=False, to_menu=True, adjust_per_row=1)
        await _safe_edit_or_send(
            msg,
            "🏋️ <b>Создание тренировки</b>\n\n"
            "▶️ Черновик восстановлен. Введите название тренировки:",
            reply_markup=kb.as_markup(), parse_mode="HTML",
        )
    elif current == CreateWorkoutStates.waiting_workout_description.state:
        kb = InlineKeyboardBuilder()
        kb.button(text="Пропустить описание", callback_data="create_skip_description")
        kb.button(text="Отменить", callback_data="create_cancel")
        add_nav_buttons(kb, back=False, to_menu=True, adjust_per_row=1)
        await _safe_edit_or_send(
            msg,
            f"▶️ Продолжаем: <code>{(draft.get('name') or '').strip()}</code>\n\n"
            "Введите описание или нажмите «Пропустить»:",
            reply_markup=kb.as_markup(), parse_mode="HTML",
        )
    elif current in (CreateWorkoutStates.selecting_blocks.state,
                     CreateWorkoutStates.adding_block_description.state):
        await _show_block_selection(msg, state)
    elif current in (CreateWorkoutStates.adding_exercises.state,
                     CreateWorkoutStates.selecting_exercises.state,
                     CreateWorkoutStates.manual_exercise_input.state):
        await _show_exercises_for_block(msg, state)
    elif current == CreateWorkoutStates.configuring_exercise.state:
        ex_name = draft.get("selected_exercise_name")
        if ex_name:
            defaults = draft.get("selected_exercise_defaults") or {}
            d_sets = defaults.get("sets", 3)
            d_reps = defaults.get("reps", 8)
            kb = InlineKeyboardBuilder()
            kb.button(
                text=f"✅ {d_sets}x{d_reps} (по умолчанию)",
                callback_data=f"create_ex_quick_{draft.get('selected_exercise_id')}_{d_sets}_{d_reps}_75_120",
            )
            kb.button(text="🔙 Выбрать другое", callback_data="create_search_ex")
            add_nav_buttons(kb, back=True, to_menu=True, adjust_per_row=1)
            await _safe_edit_or_send(
                msg,
                f"▶️ <b>{ex_name}</b> — введите параметры "
                "(формат: <code>подходы повторения % отдых</code>, например <code>3 8</code>) "
                "или используйте кнопку.",
                reply_markup=kb.as_markup(), parse_mode="HTML",
            )
        else:
            pending = draft.get("pending_exercise")
            if isinstance(pending, dict) and pending:
                await _sync_workout_draft(state, pending_exercise=pending, config_step="sets")
                await _safe_edit_or_send(
                    msg,
                    f"▶️ Продолжаем настройку: <b>{pending.get('name', '')}</b>\n\n"
                    "Введите количество подходов (целое число), или «пропустить»:",
                    parse_mode="HTML",
                )
            else:
                await _show_block_selection(msg, state)
    elif current == CreateWorkoutStates.searching_exercise_for_block.state:
        await _show_exercises_for_block(msg, state)
    else:
        # Любой иной экран тренировок → безопасный возврат к блокам
        await _show_block_selection(msg, state)
    return True


@workouts_router.message(Command("train"))
async def cmd_train(message: Message, state: FSMContext, bot: Bot):
    """Универсальная команда: вернуться в раздел тренировок.

    - Активный черновик создания тренировки НЕ сбрасывается: если вы были
      в конструкторе — вернёмся ровно туда же (даже после перезапуска бота).
    - Иначе показываем меню тренировок (как по кнопке 🏋️).
    """
    restored = False
    try:
        restored = await _restore_workout_draft(message, state, message.from_user.id)
    except Exception:
        logger.exception("cmd_train: ошибка восстановления черновика")

    if restored:
        await message.answer("↩️ Вернул вас к незавершённой тренировке. "
                             "Команда /train делает это в любой момент.")
        return

    # Сбрасываем только состояние тренировок, не трогая FSM других модулей
    current = await state.get_state()
    if current and isinstance(current, str) and current.startswith("CreateWorkoutStates"):
        await state.set_state(None)

    role = await get_user_role(message.from_user.id)
    kb = InlineKeyboardBuilder()
    kb.button(text="🔍 Найти тренировку", callback_data="find_workout")
    if role in ("admin", "trainer", "coach"):
        kb.button(text="📁 Мои шаблоны", callback_data="my_templates")
        kb.button(text="➕ Создать тренировку", callback_data="create_workout")
        kb.button(text="📊 Статистика", callback_data="workout_statistics")
    else:
        kb.button(text="🏋️ Мои тренировки", callback_data="my_workouts")
        kb.button(text="🏅 Мои достижения", callback_data="my_achievements")
    kb.button(text="🏠 Главное меню", callback_data="main_menu")
    kb.adjust(1)

    # Проверить сохранённый черновик в БД — предложить продолжить
    loaded = await _load_workout_draft(message.from_user.id)
    if loaded and _draft_is_active(loaded["draft"]):
        name = (loaded["draft"].get("name") or "без названия").strip()
        kb2 = InlineKeyboardBuilder()
        kb2.button(text=f"▶️ Продолжить тренировку «{name[:30]}»", callback_data="resume_workout_draft")
        for row in kb.as_markup().inline_keyboard:
            for btn in row:
                kb2.button(text=btn.text, callback_data=btn.callback_data)
        kb2.adjust(1)
        kb = kb2

    await message.answer(
        "🏋️ <b>Меню тренировок</b>\n\nВыберите действие "
        "(или напишите /train в любой момент, чтобы вернуться сюда):",
        reply_markup=kb.as_markup(), parse_mode="HTML",
    )


@workouts_router.callback_query(F.data == "resume_workout_draft")
async def resume_workout_draft_cb(callback: CallbackQuery, state: FSMContext):
    """Кнопка «Продолжить тренировку» из меню /train."""
    loaded = await _load_workout_draft(callback.from_user.id)
    if not loaded or not _draft_is_active(loaded["draft"]):
        await callback.answer("Черновик не найден", show_alert=True)
        return
    new_data = dict(await state.get_data())
    new_data[WORKOUT_DRAFT_KEY] = loaded["draft"]
    new_data.update({k: v for k, v in loaded["draft"].items() if k != "nav_back"})
    await state.set_data(new_data)
    if loaded["state"]:
        await state.set_state(loaded["state"])
    await callback.answer()
    ok = await _restore_workout_draft(callback, state, callback.from_user.id)
    if not ok:
        await _show_block_selection(callback.message, state)

@workouts_router.callback_query(F.data == "back_to_constructor")
async def back_to_constructor(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CreateWorkoutStates.adding_exercises)
    await _show_block_selection(callback.message, state)
    await callback.answer()


# ----------------- HELPERS -----------------
async def _get_user_one_rm(telegram_id: int, exercise_id: int) -> Optional[float]:
    """Получить 1ПМ пользователя по упражнению из последних результатов тестов.

    В таблице exercises нет колонки one_rm_kg — вес берётся из user_tests
    (последний результат с test_weight для силовых упражнений).
    """
    try:
        user = await db_manager.get_user_by_telegram_id(telegram_id)
        if not user:
            return None
        async with db_manager.pool.acquire() as conn:
            val = await conn.fetchval(
                """
                SELECT test_weight FROM user_tests
                WHERE user_id = $1 AND exercise_id = $2
                  AND test_weight IS NOT NULL
                ORDER BY tested_at DESC
                LIMIT 1
                """,
                user["id"], exercise_id,
            )
        return float(val) if val else None
    except Exception:
        logging.getLogger(__name__).debug("Не удалось получить 1ПМ", exc_info=True)
        return None


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



# ==================== ОПЦИОНАЛЬНО: ДОБАВИТЬ ФИЛЬТР ПО РОЛЯМ В ГЛАВНОЕ МЕНЮ =====
@workouts_router.callback_query(F.data == "workouts_menu")
async def workouts_menu(callback: CallbackQuery):
    try:
        user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
        role = user.get('role', 'player') if user else 'player'

        kb = InlineKeyboardBuilder()

        # Общие кнопки
        kb.button(text="Найти тренировку", callback_data="find_workout")

        if role in ['admin', 'trainer', 'coach']:
            # Тренеры и админы — работают с шаблонами
            kb.button(text="Мои шаблоны", callback_data="my_templates")      # ← НОВАЯ КНОПКА
            kb.button(text="Создать тренировку", callback_data="create_workout")
            kb.button(text="Статистика", callback_data="workout_statistics")
        else:
            # Игроки — видят только свои назначенные
            kb.button(text="Мои тренировки", callback_data="my_workouts")    # ← ОСТАЁТСЯ ТОЛЬКО ДЛЯ ИГРОКОВ
            kb.button(text="Мои достижения", callback_data="my_achievements")

        kb.button(text="Главное меню", callback_data="main_menu")
        kb.adjust(1)  # или 2, как тебе нравится
        add_nav_buttons(kb, back=True, to_menu=False, adjust_per_row=1)

        text = "<b>Меню тренировок</b>\n\n"
        if role in ['admin', 'trainer', 'coach']:
            text += "Вы — тренер. Здесь ваши шаблоны и инструменты создания."
        else:
            text += "Вы — подопечный. Здесь ваши назначенные тренировки."

        await _safe_edit_or_send(callback.message, text, reply_markup=kb.as_markup(), parse_mode="HTML")
        await callback.answer()

    except Exception as e:
        logger.exception("Ошибка в workouts_menu")
        await callback.answer("Ошибка", show_alert=True)

async def _add_manual_exercise_to_block(state: FSMContext, text: str) -> str:
    """Добавляет ручное упражнение в текущий блок. Возвращает имя блока."""
    data = await state.get_data()
    cur_block = data.get("current_block", "main")
    selected = data.get("selected_blocks", {})
    selected.setdefault(cur_block, {"description": "", "exercises": []})

    # Ручное упражнение — запись без exercise_id, весь текст в notes
    first_line = text.splitlines()[0].strip()
    display_name = first_line[:40] + ("…" if len(first_line) > 40 else "")
    selected[cur_block]["exercises"].append({
        "id": None,            # нет связи с таблицей exercises
        "name": display_name,  # короткое имя для списков блоков
        "sets": None,
        "reps_min": None,
        "reps_max": None,
        "one_rm_percent": None,
        "rest_seconds": None,
        "notes": text,         # произвольный текст тренера
    })

    await _sync_workout_draft(state, selected_blocks=selected)
    return cur_block


@workouts_router.callback_query(F.data == "manual_add_exercise")

async def add_exercise_manually(callback: CallbackQuery, state: FSMContext):
    """Ручное добавление упражнения — кнопка работает!"""

    # Узнаём, в каком блоке сейчас находимся (это важно!)
    data = await state.get_data()
    current_block = data.get("current_block", "main")

    kb = InlineKeyboardBuilder()
    kb.button(text="🔙 К блокам", callback_data="create_back_to_blocks")
    kb.button(text="❌ Отменить", callback_data="create_cancel")
    add_nav_buttons(kb, back=True, to_menu=True)  # ⬅️ Назад + 🏋️ Меню тренировки
    await _safe_edit_or_send(
        callback.message,
        "Введите упражнение вручную:\n\n"
        f"Блок: *{_pretty_block_name(current_block)}*\n\n"
        "Примеры:\n"
        "• Жим лёжа 4×8-10, 75%, отдых 2 мин\n"
        "• Бёрпи 3 круга по 20 сек\n"
        "• Растяжка спины — 3 минуты\n\n"
        "_Отправьте упражнение сообщением или нажмите кнопку._",
        reply_markup=kb.as_markup(),
        parse_mode="Markdown",
    )

    await state.set_state(CreateWorkoutStates.manual_exercise_input)
    await callback.answer()




# ==================== ЗАЩИТА: ПРОВЕРКА ДОСТУПА ПЕРЕД ПРОСМОТРОМ ====================

async def check_workout_access(user_id: int, telegram_id: int, workout_id: int) -> bool:
    """
    Корректная проверка доступа:
    - админ → всё
    - автор → доступ
    - тренер → свои + подопечных
    - игрок → назначения из workout_individual_students
    """
    try:
        # Получаем пользователя по telegram_id
        user = await db_manager.get_user_by_telegram_id(telegram_id)
        if not user:
            return False
        
        role = user.get('role', 'player')

        # Админ видит всё
        if role == 'admin':
            return True

        async with db_manager.pool.acquire() as conn:

            # Узнаем, кто создал тренировку
            creator = await conn.fetchval(
                "SELECT created_by FROM workouts WHERE id=$1",
                workout_id
            )
            if not creator:
                return False

            # Автор тренировки → доступ
            if creator == user['id']:  # <-- ИСПРАВЛЕНО
                return True

            # Тренер → видит тренировки подопечных
            if role in ['trainer', 'coach']:
                is_trainee = await conn.fetchval("""
                    SELECT COUNT(*) 
                    FROM user_trainee_assignments
                    WHERE trainer_id=$1 AND trainee_id=$2
                """, user['id'], creator)
                if is_trainee:
                    return True

            # Игрок → проверяем назначение тренировки
            student = await conn.fetchrow("""
                SELECT id FROM individual_students
                WHERE telegram_id=$1 AND is_active=TRUE
            """, telegram_id)

            if not student:
                return False

            assigned = await conn.fetchval("""
                SELECT COUNT(*)
                FROM workout_individual_students
                WHERE workout_id=$1 AND student_id=$2 AND is_active=TRUE
            """, workout_id, student['id'])

            return assigned > 0

    except Exception as e:
        logger.exception(f"Ошибка проверки доступа: {e}")
        return False



@workouts_router.callback_query(F.data.startswith("view_workout_"))
async def view_workout_details(callback: CallbackQuery):
    """Показать карточку тренировки с блоками в правильном порядке"""
    # 1. Парсинг ID
    try:
        workout_id = _parse_id_with_prefix(callback.data, "view_workout_")
    except ValueError:
        await callback.answer("Некорректный ID", show_alert=True)
        return

    # 2. Проверка доступа
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    can_access = await check_workout_access(user['id'], callback.from_user.id, workout_id)
    if not can_access:
        await callback.answer("У вас нет доступа к этой тренировке", show_alert=True)
        return

    # 3. Загрузка данных
    try:
        async with db_manager.pool.acquire() as conn:
            workout = await conn.fetchrow("""
                SELECT w.*, 
                       u.first_name AS creator_name, 
                       u.last_name  AS creator_lastname
                FROM workouts w
                LEFT JOIN users u ON w.created_by = u.id
                WHERE w.id = $1 AND COALESCE(w.is_active, true)
            """, workout_id)

            if not workout:
                await callback.answer("Тренировка не найдена", show_alert=True)
                return

            exercises = await conn.fetch("""
                SELECT 
                    we.id,
                    we.workout_id,
                    we.exercise_id,
                    we.phase,
                    we.order_in_phase,
                    we.sets,
                    we.reps_min,
                    we.reps_max,
                    we.one_rm_percent,
                    we.rest_seconds,
                    we.notes,
                    COALESCE(e.name, we.notes) AS display_name,
                    e.muscle_group,
                    e.category
                FROM workout_exercises we
                LEFT JOIN exercises e ON e.id = we.exercise_id
                WHERE we.workout_id = $1
                ORDER BY we.order_in_phase
            """, workout_id)

    except Exception as e:
        logger.exception("view_workout_details db error: %s", e)
        await callback.answer("Ошибка БД", show_alert=True)
        return

    # 4. Формирование текста
    text = f"**{workout['name']}**\n\n"

    if workout.get('description'):
        text += f"_{workout['description']}_\n\n"

    text += (
        f"Автор: {workout.get('creator_name') or ''} {workout.get('creator_lastname') or ''}\n"
        f"Время: ~{workout.get('estimated_duration_minutes') or 0} мин\n"
        f"Код: `{workout.get('unique_id')}`\n\n"
    )

    # 5. Вывод упражнений в строгом порядке фаз
    if exercises:
        phase_map = {
            'warmup': 'Разминка',
            'nervousprep': 'Подготовка НС',
            'main': 'Основная',
            'cooldown': 'Заминка'
        }
        phase_order = ["warmup", "nervousprep", "main", "cooldown"]
        blocks = {ph: [] for ph in phase_order}

        for ex in exercises:
            blocks[ex['phase']].append(ex)

        for phase in phase_order:
            phase_exercises = blocks[phase]
            if not phase_exercises:
                continue
            text += f"\n**{phase_map.get(phase, phase)}:**\n"

            for ex in phase_exercises:
                name = ex['display_name'] or "Без названия"
                sets = ex.get('sets') or "-"
                if ex.get('reps_min') is None:
                    reps = "-"
                elif ex.get('reps_max') is not None and ex['reps_min'] != ex['reps_max']:
                    reps = f"{ex['reps_min']}-{ex['reps_max']}"
                else:
                    reps = f"{ex['reps_min']}"

                line = f"• **{name}** — {sets}×{reps}"
                if ex.get('one_rm_percent'):
                    line += f" ({ex['one_rm_percent']}% 1ПМ)"

                if ex.get('rest_seconds'):
                    rs = ex['rest_seconds']
                    line += f" | отдых {rs//60}м{rs%60}с" if rs >= 60 else f" | отдых {rs}с"

                text += line + "\n"
    else:
        text += "Упражнений пока нет.\n"

    # 6. Кнопки
    kb = InlineKeyboardBuilder()
    kb.button(text="Начать тренировку", callback_data=f"start_workout_{workout_id}")
    kb.button(text="Редактировать", callback_data=f"edit_workout_{workout_id}")
    kb.button(text="Удалить", callback_data=f"delete_workout_{workout_id}")
    kb.button(text="В мои", callback_data="my_workouts")
    kb.adjust(2)

    # 7. Отправка
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
    # Начинаем новый черновик (он будет сохраняться в БД на каждом шаге)
    await state.update_data({WORKOUT_DRAFT_KEY: {}})
    await _sync_workout_draft(state)
    await _save_workout_draft(state, callback.from_user.id)
    await state.set_state(CreateWorkoutStates.waiting_workout_name)
    await callback.answer()

@workouts_router.callback_query(F.data == "create_cancel")
async def create_cancel(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    draft = data.get(WORKOUT_DRAFT_KEY) or {}
    edit_wid = data.get("editing_workout_id") or draft.get("editing_workout_id")
    await state.clear()
    # Черновик отменяем явно (только при создании; при редактировании
    # изменений в БД не было — просто убираем снимок)
    if not edit_wid and _draft_is_active(draft):
        await _delete_workout_draft(callback.from_user.id)
    elif edit_wid:
        await _delete_workout_draft(callback.from_user.id)
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
    # 🔒 Сохраняем/обновляем долговременный черновик — тренировка не
    # «сгорит», даже если пользователь уйдёт в главное меню или бот
    # перезапустится. Вернуться можно кнопкой «Меню тренировки» или /train.
    try:
        await _sync_workout_draft(state, name=name, selected_blocks=selected)
        tg_id = getattr(getattr(message, "from_user", None), "id", None)
        if tg_id:
            await _save_workout_draft(state, tg_id)
    except Exception:
        logger.debug("Не удалось сохранить черновик (block selection)", exc_info=True)
    edit_mode = bool(data.get('editing_workout_id'))
    header = "🔧 **Редактирование структуры тренировки:**" if edit_mode else "🔧 **Структура тренировки:**"
    text = f"{header} {name}\n\nВыберите блок и добавьте упражнения:\n\n"
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
    kb.button(text="🗑 Очистить все блоки", callback_data="create_clear_blocks")
    finish_text = "✅ Сохранить изменения" if edit_mode else "✅ Готово — сохранить тренировку"
    kb.button(text=finish_text, callback_data="create_finish")
    cancel_text = "❌ Отменить редактирование" if edit_mode else "❌ Отменить"
    kb.button(text=cancel_text, callback_data="create_cancel")
    add_nav_buttons(kb, back=True, to_menu=True)  # ⬅️ Назад + 🏋️ Меню тренировки
    await _safe_edit_or_send(message, text, reply_markup=kb.as_markup(), parse_mode="Markdown")
    await state.set_state(CreateWorkoutStates.selecting_blocks)


@workouts_router.callback_query(F.data == "create_clear_blocks")
async def create_clear_blocks(callback: CallbackQuery, state: FSMContext):
    """Очищает все блоки текущей тренировки (при создании и при редактировании состава)."""
    data = await state.get_data()
    if not data.get('editing_workout_id') and not data.get('selected_blocks'):
        await callback.answer("Блоки уже пусты", show_alert=True)
        return
    await _sync_workout_draft(state, selected_blocks={}, current_block=None)
    await _show_block_selection(callback.message, state)
    await callback.answer("Все блоки очищены")


# handlers/workouts.py - ТОЛЬКО ОБРАБОТЧИКИ ДЛЯ ПОИСКА (вставить в конец файла перед "# ====" или другими комментариями)

# =====================================================
# ✓ ИСПРАВЛЕНИЕ: НОВЫЕ ОБРАБОТЧИКИ ПОИСКА ТРЕНИРОВКИ
# =====================================================

# Добавить в workouts.py эти функции:

@workouts_router.callback_query(F.data == "find_workout")
async def find_workout(callback: CallbackQuery, state: FSMContext):
    """Меню поиска тренировки - выбор способа поиска"""
    logger.info(f"find_workout menu для user {callback.from_user.id}")
    
    kb = InlineKeyboardBuilder()
    kb.button(text="🔍 Поиск по коду", callback_data="search_by_code")
    kb.button(text="📝 Поиск по названию", callback_data="search_by_name")
    kb.button(text="🔙 В меню", callback_data="workouts_menu")
    kb.adjust(1)
    
    await _safe_edit_or_send(
        callback.message,
        "🔍 **Поиск тренировки**\n\nВыберите способ поиска:",
        reply_markup=kb.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()


@workouts_router.callback_query(F.data == "search_by_code")
async def search_by_code_start(callback: CallbackQuery, state: FSMContext):
    """Начало поиска по коду тренировки"""
    kb = InlineKeyboardBuilder()
    kb.button(text="❌ Отменить", callback_data="find_workout")
    kb.adjust(1)
    
    await _safe_edit_or_send(
        callback.message,
        "📝 Введите код тренировки (например: ABC123):",
        reply_markup=kb.as_markup()
    )
    await state.set_state(CreateWorkoutStates.searching_by_code)
    await callback.answer()


@workouts_router.callback_query(F.data == "search_by_name")
async def search_by_name_start(callback: CallbackQuery, state: FSMContext):
    """Начало поиска по названию тренировки"""
    kb = InlineKeyboardBuilder()
    kb.button(text="❌ Отменить", callback_data="find_workout")
    kb.adjust(1)
    
    await _safe_edit_or_send(
        callback.message,
        "📝 Введите название или часть названия тренировки:",
        reply_markup=kb.as_markup()
    )
    await state.set_state(CreateWorkoutStates.searching_by_name)
    await callback.answer()


async def get_user_role(telegram_id: int) -> str:
    """Получить роль пользователя по telegram_id"""
    try:
        user = await db_manager.get_user_by_telegram_id(telegram_id)
        if user:
            return user.get('role', 'player')
    except Exception as e:
        logger.exception(f"Ошибка получения роли: {e}")
    return 'player'


async def can_access_workout(user_id: int, telegram_id: int, workout_id: int) -> bool:
    """
    ✓ ФУНКЦИЯ ПРОВЕРКИ ДОСТУПА К ТРЕНИРОВКЕ
    
    Правила доступа:
    - АДМИН: видит всё
    - АВТОР: видит свои
    - ТРЕНЕР: видит свои + тренировки своих подопечных
    - ИГРОК: видит только свои
    """
    role = await get_user_role(telegram_id)
    
    if role == 'admin':
        return True
    
    async with db_manager.pool.acquire() as conn:
        workout = await conn.fetchrow(
            "SELECT created_by FROM workouts WHERE id = $1",
            workout_id
        )
        
        if not workout:
            return False
        
        # Если это твоя тренировка
        if workout['created_by'] == user_id:
            return True
        
        # Если ты тренер - проверяем, является ли это твоим игроком
        if role == 'trainer':
            is_trainee = await conn.fetchval("""
                SELECT COUNT(*) FROM user_trainee_assignments
                WHERE trainer_id = $1 AND trainee_id = $2
            """, user_id, workout['created_by'])
            return is_trainee > 0
    
    return False


@workouts_router.message(StateFilter(CreateWorkoutStates.searching_by_code))
async def handle_code_search(message: Message, state: FSMContext):
    """Обработка поиска по коду тренировки"""
    code = message.text.strip().upper()
    
    if len(code) < 3:
        await message.answer("❌ Код должен быть минимум 3 символа")
        return
    
    try:
        user = await db_manager.get_user_by_telegram_id(message.from_user.id)
        if not user:
            await message.answer("❌ Пользователь не найден в БД")
            await state.clear()
            return
        
        async with db_manager.pool.acquire() as conn:
            workout = await conn.fetchrow("""
                SELECT w.id, w.name, w.unique_id, w.description,
                       u.first_name, u.last_name,
                       (SELECT COUNT(*) FROM workout_exercises WHERE workout_id = w.id) as exercise_count
                FROM workouts w
                LEFT JOIN users u ON w.created_by = u.id
                WHERE w.unique_id = $1 AND coalesce(w.is_active, true) = true
            """, code)
            
            if not workout:
                kb = InlineKeyboardBuilder()
                kb.button(text="🔄 Новый поиск", callback_data="search_by_code")
                kb.button(text="🔙 В меню", callback_data="find_workout")
                kb.adjust(1)
                
                await message.answer(
                    "❌ Тренировка с таким кодом не найдена",
                    reply_markup=kb.as_markup()
                )
                await state.clear()
                return
            
            # ✓ ПРОВЕРЯЕМ ДОСТУП перед показом
            can_access = await can_access_workout(user['id'], message.from_user.id, workout['id'])
            
            if not can_access:
                kb = InlineKeyboardBuilder()
                kb.button(text="🔄 Новый поиск", callback_data="search_by_code")
                kb.button(text="🔙 В меню", callback_data="find_workout")
                kb.adjust(1)
                
                await message.answer(
                    "🚫 У вас нет доступа к этой тренировке",
                    reply_markup=kb.as_markup()
                )
                await state.clear()
                return
            
            # Показываем найденную тренировку
            text = f"🏷 **{workout['name']}**\n\n"
            if workout.get('description'):
                text += f"📝 _{workout['description']}_\n\n"
            text += f"👤 Автор: {workout.get('first_name') or ''} {workout.get('last_name') or ''}\n"
            text += f"💡 Код: `{workout['unique_id']}`\n"
            text += f"📊 Упражнений: {workout['exercise_count']}\n"
            
            kb = InlineKeyboardBuilder()
            kb.button(text="👁️ Просмотр", callback_data=f"view_workout_{workout['id']}")
            kb.button(text="➕ Добавить", callback_data=f"add_to_my_{workout['id']}")
            kb.button(text="🔄 Новый поиск", callback_data="search_by_code")
            kb.adjust(1)
            
            await message.answer(text, reply_markup=kb.as_markup(), parse_mode="Markdown")
            await state.clear()
            logger.info(f"✅ Поиск по коду: найдена тренировка {workout['id']}")
    
    except Exception as e:
        logger.exception(f"Ошибка поиска по коду: {e}")
        await message.answer("❌ Ошибка при поиске тренировки")
        await state.clear()


@workouts_router.message(StateFilter(CreateWorkoutStates.searching_by_name))
async def handle_name_search(message: Message, state: FSMContext):
    """Обработка поиска по названию тренировки"""
    search_text = f"%{message.text.strip()}%"
    
    try:
        user = await db_manager.get_user_by_telegram_id(message.from_user.id)
        if not user:
            await message.answer("❌ Пользователь не найден в БД")
            await state.clear()
            return
        
        async with db_manager.pool.acquire() as conn:
            workouts = await conn.fetch("""
                SELECT w.id, w.name, w.unique_id, w.description,
                       u.first_name, u.last_name,
                       (SELECT COUNT(*) FROM workout_exercises WHERE workout_id = w.id) as exercise_count
                FROM workouts w
                LEFT JOIN users u ON w.created_by = u.id
                WHERE (w.name ILIKE $1 OR w.description ILIKE $1)
                AND coalesce(w.is_active, true) = true
                ORDER BY w.created_at DESC
                LIMIT 10
            """, search_text)
            
            if not workouts:
                kb = InlineKeyboardBuilder()
                kb.button(text="🔄 Новый поиск", callback_data="search_by_name")
                kb.button(text="🔙 В меню", callback_data="find_workout")
                kb.adjust(1)
                
                await message.answer(
                    "❌ Тренировки не найдены",
                    reply_markup=kb.as_markup()
                )
                await state.clear()
                return
            
            text = f"🔍 **Найдено {len(workouts)} тренировок:**\n\n"
            
            kb = InlineKeyboardBuilder()
            accessible_count = 0
            
            for w in workouts:
                # ✓ ПРОВЕРЯЕМ ДОСТУП к каждой
                can_access = await can_access_workout(user['id'], message.from_user.id, w['id'])
                
                icon = "✅" if can_access else "🔒"
                text += f"{icon} **{w['name']}** ({w['exercise_count']} упр.)\n"
                text += f"   Код: `{w['unique_id']}`\n"
                
                if can_access:
                    kb.button(text=w['name'][:30], callback_data=f"view_workout_{w['id']}")
                    accessible_count += 1
            
            text += f"\n✅ Доступно: {accessible_count} из {len(workouts)}"
            
            kb.button(text="🔄 Новый поиск", callback_data="search_by_name")
            kb.button(text="🔙 В меню", callback_data="find_workout")
            kb.adjust(1)
            
            await message.answer(text, reply_markup=kb.as_markup(), parse_mode="Markdown")
            await state.clear()
            logger.info(f"✅ Поиск по названию: найдено {accessible_count} доступных из {len(workouts)}")
    
    except Exception as e:
        logger.exception(f"Ошибка поиска по названию: {e}")
        await message.answer("❌ Ошибка при поиске тренировки")
        await state.clear()




@workouts_router.callback_query(F.data == "my_templates")
async def show_my_templates(callback: CallbackQuery):
    """Показать созданные шаблоны тренировок — для тренеров и админов"""
    try:
        logger.info(f"=== show_my_templates START user {callback.from_user.id} ===")
        
        user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer("❌ Пользователь не найден", show_alert=True)
            return
        
        role = user.get('role', 'player')
        if role not in ['trainer', 'coach', 'admin']:
            await callback.answer("🚫 Доступ только для тренеров", show_alert=True)
            return
        
        user_id = user['id']
        
        async with db_manager.pool.acquire() as conn:
            if role == 'admin':
                rows = await conn.fetch("""
                    SELECT w.id, w.name, w.unique_id,
                           (SELECT COUNT(*) FROM workout_exercises we WHERE we.workout_id = w.id) as exercise_count,
                           w.estimated_duration_minutes,
                           u.first_name AS creator_first, u.last_name AS creator_last
                    FROM workouts w
                    LEFT JOIN users u ON w.created_by = u.id
                    WHERE COALESCE(w.is_active, TRUE) = TRUE
                    ORDER BY w.created_at DESC
                    LIMIT 50
                """)
            else:  # trainer/coach
                rows = await conn.fetch("""
                    SELECT DISTINCT w.id, w.name, w.unique_id,
                           (SELECT COUNT(*) FROM workout_exercises we WHERE we.workout_id = w.id) as exercise_count,
                           w.estimated_duration_minutes,
                           u.first_name AS creator_first, u.last_name AS creator_last
                    FROM workouts w
                    LEFT JOIN users u ON w.created_by = u.id
                    WHERE w.created_by = $1 OR w.created_by IN (
                        SELECT trainee_id FROM user_trainee_assignments WHERE trainer_id = $1
                    )
                    AND COALESCE(w.is_active, TRUE) = TRUE
                    ORDER BY w.created_at DESC
                    LIMIT 50
                """, user_id)
        
        if not rows:
            text = "<b>📭 У вас пока нет шаблонов тренировок</b>\n\nСоздайте первую в меню!"
            kb = InlineKeyboardBuilder()
            kb.button(text="➕ Создать", callback_data="create_workout")
            kb.button(text="🏠 Главное меню", callback_data="main_menu")
            kb.adjust(1)
        else:
            text = f"<b>📚 Мои шаблоны тренировок ({len(rows)}):</b>\n\n"
            kb = InlineKeyboardBuilder()
            for r in rows:
                cnt = r['exercise_count'] or 0
                creator = f"{r['creator_first']} {r['creator_last'] or ''}".strip() or "Неизвестно"
                text += f"• <b>{r['name']}</b> ({cnt} упр.) — от {creator}\nКод: <code>{r['unique_id']}</code>\n\n"
                kb.button(text=f"{r['name']} ({cnt})", callback_data=f"view_workout_{r['id']}")
            kb.button(text="➕ Создать", callback_data="create_workout")
            kb.button(text="🏠 Главное меню", callback_data="main_menu")
            kb.adjust(1)
        
        await _safe_edit_or_send(callback.message, text, reply_markup=kb.as_markup(), parse_mode="HTML")
        await callback.answer()
        logger.info("=== show_my_templates END (SUCCESS) ===")
    
    except Exception as e:
        logger.error("=== ERROR in show_my_templates ===", exc_info=True)
        await callback.answer("❌ Ошибка загрузки шаблонов", show_alert=True)




@workouts_router.callback_query(F.data.in_(["create_add_warmup", "create_add_nervousprep", "create_add_main", "create_add_cooldown"]))
async def create_add_block(callback: CallbackQuery, state: FSMContext):
    """Добавить блок и СРАЗУ показать упражнения (без описания!)"""
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
    
    await _sync_workout_draft(state, current_block=phase)
    
    # Создаём блок с пустым описанием
    data = await state.get_data()
    selected = data.get('selected_blocks', {})
    selected.setdefault(phase, {"description": "", "exercises": []})
    
    await _sync_workout_draft(state, selected_blocks=selected)
    
    # ✅ СРАЗУ К УПРАЖНЕНИЯМ БЕЗ ПРОМЕЖУТОЧНОГО МЕНЮ!
    await _show_exercises_for_block(callback.message, state)
    await callback.answer()


async def _show_exercises_for_block(message, state: FSMContext):
    data = await state.get_data()
    cur = data.get('current_block', 'main')
    # 🔒 Долговременный черновик: каждое открытие экрана блока фиксируем в БД
    try:
        await _sync_workout_draft(
            state,
            current_block=cur,
            selected_blocks=data.get('selected_blocks', {}),
            name=data.get('name'),
        )
        tg_id = getattr(getattr(message, "from_user", None), "id", None)
        if tg_id:
            await _save_workout_draft(state, tg_id)
    except Exception:
        logger.debug("Не удалось сохранить черновик (exercises screen)", exc_info=True)
    phase_map = {'warmup': '🔥 Разминка', 'nervousprep': '⚡ Подготовка НС', 'main': '💪 Основная', 'cooldown': '🧘 Заминка'}
    sel = data.get('selected_blocks', {})
    block = sel.get(cur, {"description": "", "exercises": []})
    text = f"📋 **Блок: {phase_map.get(cur)}**\n\nОписание: {block['description'] or 'Нет'}\n\nУпражнения:\n"
    if block['exercises']:
        for ex in block['exercises']:
            text += f"• {ex['name']}\n"
    else:
        text += "Пока пусто.\n"
    kb = InlineKeyboardBuilder()
    kb.button(text="🔍 Поиск упражнения", callback_data="workout_start_ex_search")
    kb.button(text="📝 Добавить вручную", callback_data="manual_add_exercise")
    # Кнопки удаления для каждого упражнения (по индексу в блоке) — работают и при создании, и при редактировании состава
    for idx, ex in enumerate(block['exercises']):
        short_name = (ex['name'] or '?')[:24]
        kb.button(
            text=f"🗑 Удалить: {short_name}",
            callback_data=f"block_remove_ex_{cur}_{idx}",
        )
    kb.button(text="🔙 К блокам", callback_data="create_back_to_blocks")
    add_nav_buttons(kb, back=True, to_menu=True)  # ⬅️ Назад + 🏋️ Меню тренировки
    await _safe_edit_or_send(message, text, reply_markup=kb.as_markup(), parse_mode="Markdown")
    await state.set_state(CreateWorkoutStates.adding_exercises)


@workouts_router.callback_query(F.data.startswith("block_remove_ex_"))
async def block_remove_exercise(callback: CallbackQuery, state: FSMContext):
    """Удаляет упражнение из блока тренировки (в конструкторе/редакторе состава)."""
    try:
        parts = callback.data.split("_")
        # block_remove_ex_<phase>_<index>
        idx = int(parts[-1])
        phase = "_".join(parts[3:-1])  # на случай фаз с '_' в названии
        data = await state.get_data()
        selected = data.get("selected_blocks", {})
        block = selected.get(phase)
        if not block or not block.get("exercises"):
            await callback.answer("Блок не найден или пуст", show_alert=True)
            return
        if idx < 0 or idx >= len(block["exercises"]):
            await callback.answer("Упражнение уже удалено, список обновлён", show_alert=True)
            await _show_exercises_for_block(callback.message, state)
            return
        removed = block["exercises"].pop(idx)
        await _sync_workout_draft(state, selected_blocks=selected, current_block=phase)
        await _show_exercises_for_block(callback.message, state)
        await callback.answer(f"🗑 Удалено: {removed.get('name', '?')}")
    except Exception as e:
        logger.exception("block_remove_exercise error: %s", e)
        await callback.answer("Ошибка при удалении", show_alert=True)

@workouts_router.callback_query(F.data.startswith("workout_add_ex_"))
async def workout_add_exercise(callback: CallbackQuery, state: FSMContext):
    ex_id = int(callback.data.split("_")[-1])
    data = await state.get_data()
    block = data.get("searching_in_block")
    if not block:
        await callback.answer("Контекст потерян.", show_alert=True)
        return

    async with db_manager.pool.acquire() as conn:
        ex = await conn.fetchrow("SELECT name FROM exercises WHERE id = $1", ex_id)
    if not ex:
        await callback.answer("Упражнение не найдено.", show_alert=True)
        return

    selected = data.get("selected_blocks", {})
    selected.setdefault(block, {"description": "", "exercises": []})
    selected[block]["exercises"].append({
        "id": ex_id,
        "name": ex["name"],
        "sets": None, "reps_min": None, "reps_max": None,
        "one_rm_percent": None, "rest_seconds": None
    })
    await _sync_workout_draft(state, selected_blocks=selected)

    # Сразу перерисовываем экран блока (без промежуточного edit_text,
    # который зря «съедал» id сообщения и вызывал message is not modified)
    await _show_exercises_for_block(callback.message, state)
    await callback.answer()

# === ПОИСК УПРАЖНЕНИЙ ЧЕРЕЗ ГЛАВНОЕ МЕНЮ ===
@workouts_router.callback_query(F.data == "workout_start_ex_search")
async def workout_start_ex_search(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    block = data.get("current_block")
    logger.info("workout_start_ex_search: current_block = %s", block)
    if not block:
        await callback.answer("Ошибка: блок не выбран.", show_alert=True)
        return

    # Сохраняем, куда добавить
    await _sync_workout_draft(state, searching_in_block=block)
    await state.set_state(CreateWorkoutStates.searching_exercise_for_block)

    # Открываем ТО ЖЕ МЕНЮ, что и в главном меню
    
    from handlers import exercises
    await exercises.search_exercise_menu(callback, state)

@workouts_router.callback_query(F.data == "create_back_to_blocks")
async def create_back_to_blocks(callback: CallbackQuery, state: FSMContext):
    await _show_block_selection(callback.message, state)
    await callback.answer()

@workouts_router.callback_query(F.data == "workout_start_search")
async def workout_start_search(callback: CallbackQuery, state: FSMContext):
    # Сохраняем, что мы ищем в блоке
    data = await state.get_data()
    block = data.get("current_block")
    if not block:
        await callback.answer("Ошибка: блок не выбран.", show_alert=True)
        return

    await _sync_workout_draft(state, searching_in_block=block)
    await state.set_state(CreateWorkoutStates.searching_exercise_for_block)

    # Показываем ТО ЖЕ МЕНЮ, что и в главном меню!
    
    from handlers import exercises
    await exercises.search_exercise_menu(callback, state)

    await callback.answer()

# @workouts_router.callback_query(F.data == "create_search_ex")
# async def create_search_ex(callback: CallbackQuery, state: FSMContext):
#     # Сохраняем, что мы ищем в блоке
#     data = await state.get_data()
#     block = data.get("current_block")
#     if not block:
#         await callback.answer("Ошибка: блок не выбран.", show_alert=True)
#         return

#     await _sync_workout_draft(state, searching_in_block=block)
#     await state.set_state(CreateWorkoutStates.searching_exercise_for_block)

#     # Показываем тот же текст, что и в главном меню
#     await _safe_edit_or_send(callback.message, "Введите название упражнения для поиска:")
#     await callback.answer()


@workouts_router.callback_query(F.data == "create_search_ex")
async def create_search_ex(callback: CallbackQuery, state: FSMContext):
    """
    Запуск того же меню поиска упражнений, что и в главном меню,
    но в контексте текущего блока тренировки.
    """
    data = await state.get_data()
    block = data.get("current_block")
    if not block:
        await callback.answer("Ошибка: блок не выбран.", show_alert=True)
        return

    # сохраняем, в какой блок добавляем
    await _sync_workout_draft(state, searching_in_block=block)
    await state.set_state(CreateWorkoutStates.searching_exercise_for_block)

    # открываем то же меню поиска, что и из главного меню
    from handlers import exercises
    await exercises.search_exercise_menu(callback, state)

    await callback.answer()




# ИСПРАВЛЕНИЕ: Показать меню параметров перед добавлением упражнения
def _pretty_block_name(phase: str) -> str:
    names = {
        "warmup": "Разминка",
        "nervousprep": "Подготовка НС",
        "main": "Основная",
        "cooldown": "Заминка"
    }
    return names.get(phase, "Основная")



# В файле workouts.py замените функцию create_add_ex на эту:

@workouts_router.callback_query(F.data.startswith("create_add_ex_"))
async def create_add_ex(callback: CallbackQuery, state: FSMContext):
    ex_id = _parse_int_suffix(callback.data)
    if ex_id is None:
        await callback.answer("Некорректный ID", show_alert=True)
        return

    data = await state.get_data()
    current_block = data.get("searching_in_block")
    if not current_block:
        await callback.answer("Ошибка: блок не выбран.", show_alert=True)
        return

    try:
        async with db_manager.pool.acquire() as conn:
            # В таблице exercises нет колонок default_sets/default_reps/one_rm_kg —
            # выбираем только существующие поля, дефолты константные.
            row = await conn.fetchrow(
                "SELECT id, name, muscle_group, category FROM exercises WHERE id = $1",
                ex_id
            )
        if not row:
            await callback.answer("Упражнение не найдено", show_alert=True)
            return
        one_rm_kg = await _get_user_one_rm(callback.from_user.id, ex_id)

        # Сохраняем ВСЕ нужные данные
        await _sync_workout_draft(
            state,
            selected_exercise_id=ex_id,
            selected_exercise_name=row['name'],
            selected_exercise_1rm=one_rm_kg,
            selected_exercise_defaults={
                'sets': 3,
                'reps': 8,
                'percent': 75,
                'rest': 120,
            },
            current_block=current_block  # ← КРИТИЧНО!
        )
        
        # Показываем информацию об упражнении и запрашиваем параметры
        one_rm_info = ""
        if one_rm_kg:
            one_rm_info = f"\n\n💡 **1ПМ известен: {one_rm_kg} кг**\nПосле ввода % будет показан точный вес"
        
        defaults = 3
        default_reps = 8
        
        text = f"""
🏋️ **{row['name']}**
💪 {row.get('muscle_group', 'Неизвестно')} | {row.get('category', 'Без категории')}

📝 **Введите параметры упражнения:**

**Формат:** подходы повторения % отдых

📌 **Примеры:**
  • `{defaults} {default_reps}` → {defaults}x{default_reps} по умолчанию
  • `4 10` → 4 подхода по 10 повторений
  • `4 10 75` → 4x10 при 75% от 1ПМ
  • `4 10 75 120` → полный формат + 120с отдыха

❓ **Значения по умолчанию:**
  • Подходы: {defaults}
  • Повторения: {default_reps}
  • % от 1ПМ: 75%
  • Отдых: 120 сек{one_rm_info}

_Или нажмите кнопку для значений по умолчанию:_
"""
        
        kb = InlineKeyboardBuilder()
        kb.button(
            text=f"✅ {defaults}x{default_reps} 75% 120s (по умолчанию)",
            callback_data=f"create_ex_quick_{ex_id}_{defaults}_{default_reps}_75_120"
        )
        kb.button(text="🔙 Выбрать другое", callback_data="create_search_ex")
        kb.adjust(1)
        
        await _safe_edit_or_send(callback.message, text, reply_markup=kb.as_markup(), parse_mode="Markdown")
        
        # Устанавливаем состояние для ввода параметров
        await state.set_state(CreateWorkoutStates.configuring_exercise)
        await callback.answer()
    
    except Exception as e:
        logger.exception("Ошибка в create_add_ex: %s", e)
        await callback.answer("❌ Ошибка при загрузке упражнения", show_alert=True)


# ========== БЫСТРОЕ ДОБАВЛЕНИЕ СО ЗНАЧЕНИЯМИ ПО УМОЛЧАНИЮ ==========

@workouts_router.callback_query(F.data.startswith("create_ex_quick_"))
async def create_ex_quick(callback: CallbackQuery, state: FSMContext):
    """Добавляет упражнение со значениями по умолчанию (кнопка)."""
    parts = callback.data.split("_")
    try:
        ex_id = int(parts[3])
        sets = int(parts[4])
        reps = int(parts[5])
        percent = int(parts[6])
        rest = int(parts[7])
    except (ValueError, IndexError):
        await callback.answer("❌ Ошибка при парсинге параметров", show_alert=True)
        return
    
    await _finalize_exercise_for_create(callback.message, state, sets, reps, percent, rest)
    await callback.answer()


# ========== ВВОД ПАРАМЕТРОВ В ОДНУ СТРОКУ ==========

@workouts_router.message(StateFilter(CreateWorkoutStates.configuring_exercise))
async def handle_create_exercise_params_input(message: Message, state: FSMContext):
    logger.info("handle_create_exercise_params_input: START")
    """
    Обрабатывает ввод параметров упражнения в формате: "4 10 75 120"
    """
    text = (message.text or "").strip()
    
    # Парсим параметры
    parts = text.split()
    
    if len(parts) < 1 or len(parts) > 4:
        await message.answer(
            "❌ **Неверный формат!**\n\n"
            "Используйте: `подходы повторения % отдых`\n"
            "Примеры:\n"
            "  • `4` → 4 подхода\n"
            "  • `4 10` → 4x10\n"
            "  • `4 10 75` → 4x10 75%\n"
            "  • `4 10 75 120` → 4x10 75% 120с\n"
            "  • `4 10 - 120` → 4x10 без % 120с",
            parse_mode="Markdown"
        )
        return
    
    # Парсим с валидацией
    try:
        sets = int(parts[0]) if len(parts) >= 1 else None
        reps = int(parts[1]) if len(parts) >= 2 else None
        
        # ИСПРАВЛЕНИЕ: обрабатываем "-" как None
        percent_str = parts[2] if len(parts) >= 3 else None
        percent = int(percent_str) if percent_str and percent_str != "-" else None
        
        rest = int(parts[3]) if len(parts) >= 4 else None
        
        # Валидируем диапазоны (percent может быть None)
        if sets and not (1 <= sets <= 20):
            raise ValueError("Подходы: 1-20")
        if reps and not (1 <= reps <= 100):
            raise ValueError("Повторения: 1-100")
        if percent is not None and not (1 <= percent <= 200):  # ИСПРАВЛЕНИЕ: is not None
            raise ValueError("% от 1ПМ: 1-200")
        if rest and not (0 <= rest <= 600):
            raise ValueError("Отдых: 0-600 сек")
    
    except ValueError as e:
        if str(e).startswith("Подходы") or str(e).startswith("Повторения") or str(e).startswith("% от 1ПМ") or str(e).startswith("Отдых"):
            await message.answer(f"❌ {str(e)}")
        else:
            await message.answer("❌ Неверные числа. Проверьте формат: `3 10 - 90`")
        return
    
    # Используем значения по умолчанию для пропущенных параметров
    data = await state.get_data()
    # defaults может быть None (например, после очистки ключа в _finalize_exercise_for_create)
    defaults = data.get("selected_exercise_defaults") or {}

    sets = sets or defaults.get('sets', 3)
    reps = reps or defaults.get('reps', 8)
    percent = percent if percent is not None else defaults.get('percent', 75)
    rest = rest or defaults.get('rest', 120)
    
    # Финализируем упражнение
    await _finalize_exercise_for_create(message, state, sets, reps, percent, rest)


# ========== ФИНАЛИЗАЦИЯ (СОХРАНЕНИЕ В БЛОК) ==========

async def _finalize_exercise_for_create(message, state: FSMContext, sets: int, reps: int,
                                       percent: int, rest: int):
    """
    Сохраняет упражнение с параметрами в текущий блок.
    """
    data = await state.get_data()
    current_block = data.get("current_block")
    exercise_id = data.get("selected_exercise_id")
    exercise_name = data.get("selected_exercise_name")
    one_rm_kg = data.get("selected_exercise_1rm")
    
    if not current_block or not exercise_id:
        await message.answer("❌ Ошибка: блок или упражнение не выбраны")
        return
    
    # Вычисляем вес если известен 1ПМ
    weight_kg = None
    if one_rm_kg and percent:
        weight_kg = round(one_rm_kg * percent / 100, 1)
    
    # Создаём запись упражнения
    exercise_entry = {
        "id": exercise_id,
        "name": exercise_name,
        "sets": sets,
        "reps_min": reps,
        "reps_max": reps,
        "one_rm_percent": percent,
        "rest_seconds": rest,
        "weight_kg": weight_kg,
        "notes": None,
    }
    
    # Добавляем в блок
    selected_blocks = data.get("selected_blocks", {})
    selected_blocks.setdefault(current_block, {"description": "", "exercises": []})
    selected_blocks[current_block]["exercises"].append(exercise_entry)
    
    await _sync_workout_draft(state, selected_blocks=selected_blocks)
    
    # Чистим временные данные
    for key in ["selected_exercise_id", "selected_exercise_name", "selected_exercise_1rm", "selected_exercise_defaults"]:
        await _sync_workout_draft(state, **{key: None})
    
    # Формируем итоговое сообщение
    weight_info = ""
    if weight_kg:
        weight_info = f"\n  💪 Вес: **{weight_kg} кг** (при {percent}% от {one_rm_kg}кг 1ПМ)"
    elif percent:
        weight_info = f"\n  📊 {percent}% от 1ПМ"
    
    rest_info = f"\n  ⏱ Отдых: {rest} сек" if rest else ""
    
    text = f"""
✅ **{exercise_name}** добавлено в блок!

📋 **Параметры:**
  • **{sets}x{reps}** подходы x повторения{weight_info}{rest_info}

Что дальше?
"""
    
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Добавить ещё упражнение", callback_data="create_search_ex")
    kb.button(text="✅ Завершить блок", callback_data="create_back_to_blocks")
    kb.button(text="🔙 К блокам", callback_data="create_back_to_blocks")
    add_nav_buttons(kb, back=True, to_menu=True)  # ⬅️ Назад + 🏋️ Меню тренировки

    await message.answer(text, reply_markup=kb.as_markup(), parse_mode="Markdown")
    
    
    for key in ["selected_exercise_id", "selected_exercise_name", "selected_exercise_1rm", "selected_exercise_defaults"]:
        await _sync_workout_draft(state, **{key: None})

    # Оставляем current_block, selected_blocks и т.д.
    # Переводим FSM в режим добавления/выбора упражнений в блоке
    await state.set_state(CreateWorkoutStates.adding_exercises)


# Редактирование параметров для только что выбранного упражнения
@workouts_router.callback_query(F.data == "create_configure_pending_ex")
async def create_configure_pending_ex(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    pending = data.get('pending_exercise')
    if not pending:
        await callback.answer("Контекст потерян", show_alert=True)
        return
    # начинаем диалог: запрос подходов
    await _sync_workout_draft(state, config_step="sets")
    await _safe_edit_or_send(callback.message, "Введите количество подходов (целое число), или 'пропустить' чтобы добавить без параметров:")
    await state.set_state(CreateWorkoutStates.configuring_exercise)
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
    await _sync_workout_draft(state, selected_blocks=sel)
    await _sync_workout_draft(state, pending_exercise=None)
    await _show_block_selection(callback.message, state)
    await callback.answer()


# Обработка текстового ввода параметров для pending exercise
async def configuring_pending_ex_input(message: Message, state: FSMContext):
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
            await _sync_workout_draft(state, selected_blocks=sel)
            await _sync_workout_draft(state, pending_exercise=None)
            await message.answer("Добавлено без параметров.")
            await _show_block_selection(message, state)
            return
        try:
            sets = int(text)
            await _sync_workout_draft(state, config_sets=sets, config_step="reps")
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
        await _sync_workout_draft(state, config_reps_min=rmin, config_reps_max=rmax, config_step="percent")
        await message.answer("Укажите % от 1ПМ (например 70) или напишите 'нет' чтобы пропустить:")
        return
    if step == "percent":
        if text in ("нет", "no", "пропустить", "skip", "-"):
            await _sync_workout_draft(state, config_one_rm_percent=None, config_step="rest")
            await message.answer("Укажите отдых между подходами в секундах (например 90) или 'пропустить':")
            return
        try:
            perc = int(text)
            if not (0 < perc <= 200):
                raise ValueError
            await _sync_workout_draft(state, config_one_rm_percent=perc, config_step="rest")
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
        
        if entry.get('one_rm_percent'):
            user = await db_manager.get_user_by_telegram_id(message.from_user.id)

            async with db_manager.pool.acquire() as conn:
                orm = await conn.fetchrow(
                    """
                    SELECT formula_average, calculation_method, tested_at
                    FROM one_rep_max
                    WHERE user_id = $1
                    AND exercise_id = $2
                    AND is_active = true
                    ORDER BY tested_at DESC
                    LIMIT 1
                    """,
                    user['id'], pending['id']
                )

            if not orm:
                # предложим пройти тест (зависит от модуля tests)
                kb = InlineKeyboardBuilder()
                kb.button(text="Пройти тест на 1ПМ", callback_data=f"start_1rm_test_for_{pending['id']}")
                kb.button(text="Добавить без %", callback_data="create_confirm_add_pending_ex")
                kb.button(text="🔙 К блокам", callback_data="create_back_to_blocks")
                kb.adjust(1)
                await message.answer(
                    "1ПМ для этого упражнения не найден — хотите пройти тест?",
                    reply_markup=kb.as_markup()
                )
                return
            else:
                one_rm_value = orm["formula_average"]
                method = orm["calculation_method"]
                tested_at = orm["tested_at"]
                logger.info(
                    f"✅ Найден 1ПМ={one_rm_value} (метод={method}, дата={tested_at}) "
                    f"для user_id={user['id']}, exercise_id={pending['id']}"
                )

        # добавляем упражнение в текущий блок
        sel[cur]['exercises'].append(entry)
        await _sync_workout_draft(state, selected_blocks=sel)
        await _sync_workout_draft(state, pending_exercise=None)

        # чистим временные конфиги
        for k in [
            "config_step",
            "config_sets",
            "config_reps_min",
            "config_reps_max",
            "config_one_rm_percent",
        ]:
            await _sync_workout_draft(state, **{k: None})

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
        from . import tests as tests_module
        # если есть готовая функция для запуска 1rm теста — вызываем её (если нет, просто сообщаем)
        if hasattr(tests_module, "start_1rm_test_from_handlers"):
            await tests_module.start_1rm_test_from_handlers(callback, ex_id)
            await callback.answer()
            return
    except Exception:
        logger.info("Модуль tests не предоставляет start_1rm_test_from_handlers, отправим инструкцию")
    await _safe_edit_or_send(callback.message, "Пожалуйста пройдите тест 1ПМ вручную (/start_1rm_test), затем вернитесь и добавьте упражнение.")
    await callback.answer()



@workouts_router.callback_query(F.data == "create_finish")
async def create_finish(callback: CallbackQuery, state: FSMContext):
    """✨ Финал: сохраняем тренировку в БД (создание ИЛИ редактирование существующей)"""
    try:
        data = await state.get_data()
        name = data.get("name")
        if not name or not name.strip():
            await callback.answer("❗ Название не может быть пустым", show_alert=True)
            return

        selected = data.get("selected_blocks", {})
        total_exs = sum(len(b.get("exercises", [])) for b in selected.values())
        if total_exs == 0:
            await callback.answer("❗ Добавьте хотя бы одно упражнение", show_alert=True)
            return

        user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer("❗ Пользователь не найден в БД", show_alert=True)
            return

        edit_wid = data.get("editing_workout_id")

        async with db_manager.pool.acquire() as conn:
            if edit_wid:
                # === РЕЖИМ РЕДАКТИРОВАНИЯ: проверяем права и обновляем шапку ===
                w = await conn.fetchrow(
                    "SELECT id, created_by FROM workouts WHERE id = $1", edit_wid
                )
                if not w:
                    await callback.answer("❌ Тренировка не найдена", show_alert=True)
                    return
                role = (user or {}).get('role', 'player')
                if w['created_by'] != user['id'] and role != 'admin':
                    await callback.answer("Редактировать может только автор или админ", show_alert=True)
                    return
                wid = edit_wid
                await conn.execute(
                    "UPDATE workouts SET name = $1, description = $2 WHERE id = $3",
                    name.strip(),
                    (data.get("description") or "").strip(),
                    wid,
                )
                # Перезаписываем состав: сначала отвязываем строки прогресса
                # учеников (workout_session_exercises ссылается на workout_exercises FK),
                # затем удаляем старые строки и вставляем новые.
                await conn.execute(
                    """
                    UPDATE workout_session_exercises wse
                       SET workout_exercise_id = NULL
                      FROM workout_sessions ws
                     WHERE wse.session_id = ws.id
                       AND ws.workout_id = $1
                       AND wse.workout_exercise_id IS NOT NULL
                    """,
                    wid,
                )
                await conn.execute("DELETE FROM workout_exercises WHERE workout_id = $1", wid)
            else:
                # === РЕЖИМ СОЗДАНИЯ ===
                wid = await conn.fetchval(
                    """
                    INSERT INTO workouts (name, description, created_by, created_at, is_active, estimated_duration_minutes)
                    VALUES ($1, $2, $3, NOW(), TRUE, 0)
                    RETURNING id
                    """,
                    name.strip(),
                    (data.get("description") or "").strip(),
                    user["id"],
                )

            # Вставляем упражнения (общий код для создания и редактирования)
            order = 0
            for phase, block in selected.items():
                for ex in block.get("exercises", []):
                    order += 1

                    exercise_id = ex.get("id")          # NULL для ручных
                    sets        = ex.get("sets")
                    reps_min    = ex.get("reps_min")
                    reps_max    = ex.get("reps_max")
                    one_rm_pct  = ex.get("one_rm_percent")
                    rest_sec    = ex.get("rest_seconds")
                    notes       = ex.get("notes")

                    # для ручных подставляем 0, чтобы NOT NULL не ругались
                    if exercise_id is None:
                        sets     = sets or 0
                        reps_min = reps_min or 0
                        reps_max = reps_max or 0
                        rest_sec = rest_sec or 0
                        one_rm_pct = None

                    await conn.execute(
                        """
                        INSERT INTO workout_exercises
                        (workout_id, exercise_id, phase, order_in_phase,
                         sets, reps_min, reps_max, one_rm_percent, rest_seconds, notes)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                        """,
                        wid, exercise_id, phase, order,
                        sets, reps_min, reps_max, one_rm_pct, rest_sec, notes,
                    )

            # Уникальный код
            unique = await conn.fetchval(
                "SELECT unique_id FROM workouts WHERE id = $1", wid
            )

        # Красивое завершение
        if edit_wid:
            await _safe_edit_or_send(callback.message, 
                f"🎉 <b>Тренировка обновлена!</b>\n\n"
                f"📋 Название: <code>{name}</code>\n"
                f"🔢 Упражнений: {total_exs}\n"
                f"📌 Код для подопечных: <code>{unique}</code>",
                parse_mode="HTML",
            )
        else:
            await _safe_edit_or_send(callback.message, 
                f"🎉 <b>Тренировка создана!</b>\n\n"
                f"📋 Название: <code>{name}</code>\n"
                f"🔢 Упражнений: {total_exs}\n"
                f"📌 Код для подопечных: <code>{unique}</code>",
                parse_mode="HTML",
            )
        # Тренировка сохранена в БД — черновик больше не нужен
        await _delete_workout_draft(callback.from_user.id)
        await state.clear()

    except Exception as e:
        logger.exception("create_finish error: %s", e)
        await callback.answer("❌ Ошибка при сохранении", show_alert=True)
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
    await _safe_edit_or_send(callback.message, "✅ Оцени тренировку по шкале 1-10 (RPE):")
    await state.set_state(CreateWorkoutStates.waiting_rpe)
    await callback.answer()


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
    role = (user or {}).get('role', 'player')
    if not user or (w['created_by'] != user['id'] and role != 'admin'):
        await callback.answer("Редактировать может только автор или админ", show_alert=True)
        return
    kb = InlineKeyboardBuilder()
    kb.button(text="✏️ Переименовать", callback_data=f"rename_workout_{wid}")
    kb.button(text="📝 Изменить описание", callback_data=f"change_desc_workout_{wid}")
    kb.button(text="🛠 Редактировать состав (упражнения)", callback_data=f"edit_composition_{wid}")
    kb.button(text="🗑️ Удалить", callback_data=f"delete_workout_{wid}")
    kb.button(text="🔙 К тренировке", callback_data=f"view_workout_{wid}")
    kb.adjust(1)
    await _safe_edit_or_send(callback.message, f"✏️ Редактирование: {w['name']}", reply_markup=kb.as_markup())
    await callback.answer()


@workouts_router.callback_query(F.data.startswith("rename_workout_"))
async def rename_workout(callback: CallbackQuery, state: FSMContext):
    wid = _parse_int_suffix(callback.data)
    if wid is None:
        await callback.answer("Некорректный ID", show_alert=True)
        return
    await _sync_workout_draft(state, editing_workout_id=wid)
    kb = InlineKeyboardBuilder()
    kb.button(text="❌ Отменить", callback_data=f"view_workout_{wid}")
    kb.adjust(1)
    await _safe_edit_or_send(
        callback.message,
        "✏️ Введите новое название тренировки:",
        reply_markup=kb.as_markup(),
    )
    await state.set_state(CreateWorkoutStates.renaming_workout)
    await callback.answer()


@workouts_router.callback_query(F.data.startswith("change_desc_workout_"))
async def change_desc_workout(callback: CallbackQuery, state: FSMContext):
    wid = _parse_int_suffix(callback.data)
    if wid is None:
        await callback.answer("Некорректный ID", show_alert=True)
        return
    await _sync_workout_draft(state, editing_workout_id=wid)
    kb = InlineKeyboardBuilder()
    kb.button(text="❌ Отменить", callback_data=f"view_workout_{wid}")
    kb.adjust(1)
    await _safe_edit_or_send(
        callback.message,
        "📝 Введите новое описание тренировки:",
        reply_markup=kb.as_markup(),
    )
    await state.set_state(CreateWorkoutStates.changing_workout_description)
    await callback.answer()


# ----------------- FULL COMPOSITION EDIT -----------------
@workouts_router.callback_query(F.data.startswith("edit_composition_"))
async def edit_composition(callback: CallbackQuery, state: FSMContext):
    """Загружает существующую тренировку в FSM-конструктор для полного редактирования состава."""
    wid = _parse_int_suffix(callback.data)
    if wid is None:
        await callback.answer("Некорректный ID", show_alert=True)
        return
    try:
        async with db_manager.pool.acquire() as conn:
            w = await conn.fetchrow(
                "SELECT id, name, description, created_by FROM workouts WHERE id = $1", wid
            )
            if not w:
                await callback.answer("Тренировка не найдена", show_alert=True)
                return
            user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
            role = (user or {}).get('role', 'player')
            if not user or (w['created_by'] != user['id'] and role != 'admin'):
                await callback.answer("Редактировать может только автор или админ", show_alert=True)
                return

            rows = await conn.fetch(
                """
                SELECT we.id, we.exercise_id, we.phase, we.order_in_phase,
                       we.sets, we.reps_min, we.reps_max,
                       we.one_rm_percent, we.rest_seconds, we.notes,
                       e.name AS ex_name
                FROM workout_exercises we
                LEFT JOIN exercises e ON e.id = we.exercise_id
                WHERE we.workout_id = $1
                ORDER BY we.order_in_phase, we.id
                """,
                wid,
            )

        selected: Dict[str, Dict[str, Any]] = {}
        for r in rows:
            phase = r['phase'] if r['phase'] in ("warmup", "nervousprep", "main", "cooldown") else "main"
            block = selected.setdefault(phase, {"description": "", "exercises": []})
            block["exercises"].append({
                "id": r['exercise_id'],          # None для ручных упражнений
                "db_row_id": r['id'],
                "name": r['ex_name'] or (r['notes'] if r['exercise_id'] is None else None),
                "sets": r['sets'],
                "reps_min": r['reps_min'],
                "reps_max": r['reps_max'],
                "one_rm_percent": float(r['one_rm_percent']) if r['one_rm_percent'] is not None else None,
                "rest_seconds": r['rest_seconds'],
                "notes": r['notes'],
            })

        await _sync_workout_draft(
            state,
            editing_workout_id=wid,
            name=w['name'],
            description=w['description'] or "",
            selected_blocks=selected,
            pending_exercise=None,
            current_block=None,
        )
        await _show_block_selection(callback.message, state)
        await callback.answer("Режим редактирования состава")
    except Exception as e:
        logger.exception("edit_composition error: %s", e)
        await callback.answer("Ошибка при загрузке тренировки", show_alert=True)

@workouts_router.callback_query(F.data.startswith("delete_workout_"))
async def delete_workout(callback: CallbackQuery):
    wid = _parse_int_suffix(callback.data)
    if wid is None:
        await callback.answer("Некорректный ID", show_alert=True)
        return
    try:
        async with db_manager.pool.acquire() as conn:
            await conn.execute("UPDATE workouts SET is_active = false WHERE id = $1", wid)
        await _safe_edit_or_send(callback.message, "✅ Тренировка удалена.")
        await callback.answer()
    except Exception as e:
        logger.exception("delete_workout error: %s", e)
        await callback.answer("Ошибка", show_alert=True)


# Пропустить описание (legacy compatible)
@workouts_router.callback_query(F.data == "create_skip_description")
async def create_skip_description(callback: CallbackQuery, state: FSMContext):
    await _sync_workout_draft(state, description="")
    await _show_block_selection(callback.message, state)
    await callback.answer()


# Обработка текстового ввода (все состояния создания/редактирования)
# Эта функция вызывается из handle_all_text_messages в __init__.py
async def process_workout_text_input(message: Message, state: FSMContext):
    current = await state.get_state()
    data = await state.get_data()

    # -------------------------------------------------
    # 1. НАЗВАНИЕ ТРЕНИРОВКИ
    # -------------------------------------------------
    if current == CreateWorkoutStates.waiting_workout_name:
        name = message.text.strip()
        if len(name) < 3:
            await message.answer("Название слишком короткое (мин. 3 символа).")
            return
        # Если это редактирование существующей тренировки — сразу обновляем name
        edit_wid = data.get('editing_workout_id')
        if edit_wid:
            async with db_manager.pool.acquire() as conn:
                await conn.execute("UPDATE workouts SET name = $1 WHERE id = $2", name, edit_wid)
            await _sync_workout_draft(state, name=name)
            kb = InlineKeyboardBuilder()
            kb.button(text="🛠 К редактированию состава", callback_data=f"edit_composition_{edit_wid}")
            kb.button(text="📋 К тренировке", callback_data=f"view_workout_{edit_wid}")
            kb.adjust(1)
            await message.answer(
                f"✅ Название обновлено на: *{name}*",
                reply_markup=kb.as_markup(),
                parse_mode="Markdown",
            )
            await state.clear()
            return
        await _sync_workout_draft(state, name=name)
        kb = InlineKeyboardBuilder()
        kb.button(text="Пропустить описание", callback_data="create_skip_description")
        kb.button(text="Отменить", callback_data="create_cancel")
        kb.adjust(2)
        await message.answer(
            f"Название сохранено: *{name}*\n\nВведите описание или нажмите «Пропустить»",
            reply_markup=kb.as_markup(),
            parse_mode="Markdown"
        )
        await state.set_state(CreateWorkoutStates.waiting_workout_description)
        return

    # -------------------------------------------------
    # 1b. ПЕРЕИМЕНОВАНИЕ СУЩЕСТВУЮЩЕЙ ТРЕНИРОВКИ
    # -------------------------------------------------
    if current == CreateWorkoutStates.renaming_workout:
        new_name = message.text.strip()
        if len(new_name) < 3:
            await message.answer("❌ Название слишком короткое (мин. 3 символа).")
            return
        wid = data.get('editing_workout_id')
        if not wid:
            await message.answer("❌ Контекст потерян, начните заново.")
            await state.clear()
            return
        try:
            async with db_manager.pool.acquire() as conn:
                await conn.execute("UPDATE workouts SET name = $1 WHERE id = $2", new_name, wid)
            kb = InlineKeyboardBuilder()
            kb.button(text="📋 К тренировке", callback_data=f"view_workout_{wid}")
            kb.button(text="🏋️ Мои тренировки", callback_data="my_workouts")
            kb.adjust(1)
            await message.answer(
                f"✅ Название обновлено на: *{new_name}*",
                reply_markup=kb.as_markup(),
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.exception("rename_workout text handler error: %s", e)
            await message.answer("❌ Ошибка при сохранении названия.")
        await state.clear()
        return

    # -------------------------------------------------
    # 1c. ИЗМЕНЕНИЕ ОПИСАНИЯ СУЩЕСТВУЮЩЕЙ ТРЕНИРОВКИ
    # -------------------------------------------------
    if current == CreateWorkoutStates.changing_workout_description:
        new_desc = message.text.strip()
        wid = data.get('editing_workout_id')
        if not wid:
            await message.answer("❌ Контекст потерян, начните заново.")
            await state.clear()
            return
        try:
            async with db_manager.pool.acquire() as conn:
                await conn.execute("UPDATE workouts SET description = $1 WHERE id = $2", new_desc, wid)
            kb = InlineKeyboardBuilder()
            kb.button(text="📋 К тренировке", callback_data=f"view_workout_{wid}")
            kb.button(text="🏋️ Мои тренировки", callback_data="my_workouts")
            kb.adjust(1)
            await message.answer(
                "✅ Описание обновлено.",
                reply_markup=kb.as_markup(),
            )
        except Exception as e:
            logger.exception("change_desc_workout text handler error: %s", e)
            await message.answer("❌ Ошибка при сохранении описания.")
        await state.clear()
        return

    # -------------------------------------------------
    # 2. ОПИСАНИЕ ТРЕНИРОВКИ
    # -------------------------------------------------
    if current == CreateWorkoutStates.waiting_workout_description:
        await _sync_workout_draft(state, description=message.text.strip())
        await _show_block_selection(message, state)
        return

    # -------------------------------------------------
    # 3. ОПИСАНИЕ БЛОКА
    # -------------------------------------------------
    if current == CreateWorkoutStates.adding_block_description:
        desc = message.text.strip()
        cur_block = data.get('current_block')
        sel = data.get('selected_blocks', {})
        sel.setdefault(cur_block, {"description": "", "exercises": []})
        sel[cur_block]['description'] = desc
        await _sync_workout_draft(state, selected_blocks=sel)
        await message.answer("Описание блока сохранено.")
        await _show_block_selection(message, state)
        return

    # -------------------------------------------------
    # 4. ПОИСК УПРАЖНЕНИЯ В БЛОКЕ
    # -------------------------------------------------
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
            kb.button(text=f"{e['name']} ({cat})", callback_data=f"create_add_ex_{e['id']}")
        kb.button(text="Поиск упражнения", callback_data="workout_start_search")
        kb.button(text="К блокам", callback_data="create_back_to_blocks")
        kb.adjust(1)
        await message.answer(f"Найдено: {len(exs)}", reply_markup=kb.as_markup())
        return

    # -------------------------------------------------
    # 5. КОНФИГУРАЦИЯ ПАРАМЕТРОВ УПРАЖНЕНИЯ (configuring_exercise)
    # -------------------------------------------------
    if current == CreateWorkoutStates.configuring_exercise:
        text = message.text.strip().lower()
        pending = data.get('pending_exercise')
        if not pending:
            await message.answer("Контекст потерян. Начните заново.")
            await state.clear()
            return

        step = data.get('config_step')

        # === ПОДХОДЫ (sets) ===
        if step == "sets":
            if text in ("пропустить", "skip", "-", "нет"):
                await _add_exercise_without_params(state, pending, message)
                return
            try:
                sets = int(text)
                if sets <= 0:
                    raise ValueError
                await _sync_workout_draft(state, config_sets=sets, config_step="reps")
                await message.answer("Введите количество повторов (например: 8 или 8-12):")
                return
            except ValueError:
                await message.answer("Введите целое число (например: 3) или «пропустить».")
                return

        # === ПОВТОРЫ (reps) ===
        if step == "reps":
            if "-" in text:
                try:
                    a, b = text.split("-", 1)
                    rmin = int(a.strip())
                    rmax = int(b.strip())
                    if rmin <= 0 or rmax < rmin:
                        raise ValueError
                except Exception:
                    await message.answer("Неверный диапазон. Пример: 8-12")
                    return
            else:
                try:
                    rmin = rmax = int(text)
                    if rmin <= 0:
                        raise ValueError
                except Exception:
                    await message.answer("Введите число повторов (например: 10) или диапазон 8-12.")
                    return
            await _sync_workout_draft(state, config_reps_min=rmin, config_reps_max=rmax, config_step="percent")
            await message.answer("Укажите % от 1ПМ (например: 70) или напишите «нет»:")
            return

        # === % ОТ 1ПМ (percent) ===
        if step == "percent":
            if text in ("нет", "no", "пропустить", "skip", "-"):
                await _sync_workout_draft(state, config_one_rm_percent=None, config_step="rest")
                await message.answer("Отдых между подходами в секундах (например: 90) или «пропустить»:")
                return
            try:
                perc = int(text)
                if not (1 <= perc <= 200):
                    raise ValueError
                await _sync_workout_draft(state, config_one_rm_percent=perc, config_step="rest")
                await message.answer("Отдых между подходами в секундах (например: 90) или «пропустить»:")
                return
            except Exception:
                await message.answer("Введите число от 1 до 200 или «нет».")
                return

        # === ОТДЫХ (rest) ===
        if step == "rest":
            if text in ("пропустить", "skip", "-", "нет"):
                rest = None
            else:
                try:
                    rest = int(text)
                    if rest < 0:
                        raise ValueError
                except Exception:
                    await message.answer("Введите число секунд (например: 90) или «пропустить».")
                    return

            # === ПРОВЕРКА 1ПМ ===
            if data.get('config_one_rm_percent'):
                user = await db_manager.get_user_by_telegram_id(message.from_user.id)
                async with db_manager.pool.acquire() as conn:
                    orm = await conn.fetchrow(
                        "SELECT value FROM one_rep_max WHERE user_id = $1 AND exercise_id = $2",
                        user['id'], pending['id']
                    )
                if not orm:
                    kb = InlineKeyboardBuilder()
                    kb.button(text="Пройти тест 1ПМ", callback_data=f"start_1rm_test_for_{pending['id']}")
                    kb.button(text="Добавить без %", callback_data="create_confirm_add_pending_ex")
                    kb.button(text="К блокам", callback_data="create_back_to_blocks")
                    kb.adjust(1)
                    await message.answer(
                        "1ПМ для этого упражнения не найден — хотите пройти тест?",
                        reply_markup=kb.as_markup()
                    )
                    return

            # === ДОБАВЛЕНИЕ С ПАРАМЕТРАМИ ===
            await add_exercise_with_params_start(state, pending, rest, message)
            return

 

    # -------------------------------------------------
    # 4b. РУЧНОЙ ВВОД УПРАЖНЕНИЙ (текстом)
    # Работает и в состоянии manual_exercise_input, и в adding_exercises
    # (после «Добавить ещё» / возврата к блокам пользователь может просто
    # писать упражнения текстом — каждое сообщение добавляется в текущий блок).
    # -------------------------------------------------
    if current in (CreateWorkoutStates.manual_exercise_input,
                   CreateWorkoutStates.adding_exercises):
        text = (message.text or "").strip()
        if not text:
            await message.answer(
                "Пришлите упражнение текстом, например:\n"
                "«Жим лёжа 4×8-10, 75%, отдых 2 мин»"
            )
            return

        # текущий блок (если нет — считаем main)
        cur_block = data.get("current_block", "main")
        selected = data.get("selected_blocks", {})
        selected.setdefault(cur_block, {"description": "", "exercises": []})

        # добавляем «ручное упражнение» как отдельную запись БЕЗ exercise_id
        selected[cur_block]["exercises"].append({
            "id": None,                # важно: нет связи с exercises
            "name": None,              # имя не нужно, весь текст в notes
            "sets": None,
            "reps_min": None,
            "reps_max": None,
            "one_rm_percent": None,
            "rest_seconds": None,
            "notes": text,             # весь произвольный текст тренера
        })

        await _sync_workout_draft(state, selected_blocks=selected, current_block=cur_block)

        block_exs = selected[cur_block]["exercises"]
        added_count = sum(
            1 for ex in block_exs
            if ex.get("id") is None and ex.get("notes")
        )
        hint = (
            "Можно добавить ещё упражнение текстом или выбрать действие кнопкой:"
            if added_count > 1 else
            "Так держать! Добавляйте следующее упражнение текстом или выберите действие кнопкой:"
        )
        await message.answer(
            f"✅ Добавлено в блок «{_pretty_block_name(cur_block)}»: {text}\n\n{hint}"
        )

        kb = InlineKeyboardBuilder()
        kb.button(text="📝 Добавить ещё вручную", callback_data="manual_add_exercise")
        kb.button(text="🔍 Поиск упражнения", callback_data="workout_start_ex_search")
        kb.button(text="🔙 К блокам", callback_data="create_back_to_blocks")
        kb.adjust(1)

        await message.answer("Что дальше?", reply_markup=kb.as_markup())
        await state.set_state(CreateWorkoutStates.adding_exercises)
        return


    # -------------------------------------------------
    # 7. RPE ПОСЛЕ ЗАВЕРШЕНИЯ ТРЕНИРОВКИ
    # -------------------------------------------------
    if current == CreateWorkoutStates.waiting_rpe:
        try:
            rpe = int(message.text.strip())
            if not 1 <= rpe <= 10:
                raise ValueError
            wid = data.get("finishing_workout_id")
            async with db_manager.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO workout_completions (workout_id, user_id, rpe, completed_at)
                    VALUES ($1, (SELECT id FROM users WHERE telegram_id = $2), $3, now())
                    """,
                    wid, message.from_user.id, rpe
                )
            await message.answer(f"RPE {rpe} сохранено! Тренировка завершена.")
            await state.clear()
        except Exception:
            await message.answer("Введите число от 1 до 10.")
        return

    # -------------------------------------------------
    # FALLBACK
    # -------------------------------------------------
    await message.answer("Я не ожидал этот ввод. Используйте кнопки.")


# ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
# ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←

# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===

async def _add_exercise_without_params(state: FSMContext, pending: dict, message: Message):
    data = await state.get_data()
    cur = pending['block']
    sel = data.get('selected_blocks', {})
    sel.setdefault(cur, {"description": "", "exercises": []})
    sel[cur]['exercises'].append({
        "id": pending['id'],
        "name": pending['name'],
        "sets": None, "reps_min": None, "reps_max": None,
        "one_rm_percent": None, "rest_seconds": None
    })
    await _sync_workout_draft(state, selected_blocks=sel, pending_exercise=None)
    for key in ["config_step", "config_sets", "config_reps_min", "config_reps_max", "config_one_rm_percent"]:
        await _sync_workout_draft(state, **{key: None})
    await message.answer(f"Упражнение *{pending['name']}* добавлено без параметров.", parse_mode="Markdown")
    await _show_block_selection(message, state)
@workouts_router.callback_query(F.data.startswith("use_in_workout_"))
async def use_in_workout_with_params(callback: CallbackQuery, state: FSMContext):
    """Использовать упражнение в тренировке при создании"""
    
    ex_id = int(callback.data.split("_")[-1])
    data = await state.get_data()
    
    # Берём блок (он ТОЧНО есть, потому что кнопка появилась только если есть current_block)
    block = data.get("current_block")
    
    if not block:
        await callback.answer("Ошибка: блок не выбран.", show_alert=True)
        return
    
    try:
        async with db_manager.pool.acquire() as conn:
            # Колонок default_sets/default_reps_min/one_rm_kg в exercises нет —
            # берём только существующие поля.
            ex = await conn.fetchrow(
                "SELECT name, test_type FROM exercises WHERE id = $1",
                ex_id
            )
        
        if not ex:
            await callback.answer("Упражнение не найдено.", show_alert=True)
            return
        one_rm_kg = await _get_user_one_rm(callback.from_user.id, ex_id)
        
        # Сохраняем данные упражнения
        await _sync_workout_draft(
            state,
            selected_exercise_id=ex_id,
            selected_exercise_name=ex["name"],
            selected_exercise_1rm=one_rm_kg,
            selected_exercise_defaults={
                'sets': 3,
                'reps': 8,
                'percent': 75,
                'rest': 120,
            },
            current_block=block
        )
        
        # Показываем форму параметров
        defaults = 3
        default_reps = 8
        
        text = f"""
🏋️ **{ex['name']}**

📝 **Введите параметры упражнения:**

**Формат:** подходы повторения % отдых

📌 **Примеры:**
• `{defaults} {default_reps}` → {defaults}x{default_reps}
• `4 10 75 120` → 4x10 при 75% + 120с отдыха

_Или нажмите кнопку для значений по умолчанию:_
"""
        
        kb = InlineKeyboardBuilder()
        kb.button(
            text=f"✅ {defaults}x{default_reps} (по умолчанию)",
            callback_data=f"create_ex_quick_{ex_id}_{defaults}_{default_reps}_75_120"
        )
        kb.button(text="🔙 Выбрать другое", callback_data="create_search_ex")
        kb.adjust(1)
        
        await _safe_edit_or_send(callback.message, text, reply_markup=kb.as_markup(), parse_mode="Markdown")
        await state.set_state(CreateWorkoutStates.configuring_exercise)
        
    except Exception as e:
        logger.error(f"ERROR: {e}", exc_info=True)
        await callback.answer("❌ Ошибка", show_alert=True)
    
    await callback.answer()



from handlers import teams  # Добавь этот импорт в начало файла, если его нет




# ------------------  КАРДИО-ВВОД  ------------------
@workouts_router.message(StateFilter(CreateWorkoutStates.configuring_exercise_cardio))
async def handle_cardio_params_input(message: Message, state: FSMContext):
    text = message.text.strip()
    data = await state.get_data()
    ex_id   = data.get("selected_exercise_id")
    ex_name = data.get("selected_exercise_name")
    block   = data.get("current_block")

    if not all([ex_id, ex_name, block]):
        await message.answer("Контекст потерян. Начните заново.")
        await state.clear()
        return

    parts = text.split()
    if len(parts) != 4:
        await message.answer("❗ Нужно ровно 4 значения: `подходы повторы %отлучшеговремени отдых_сек`")
        return

    try:
        sets = int(parts[0])
        reps = int(parts[1])
        percent = parts[2]
        rest = int(parts[3])
        if sets <= 0 or reps <= 0 or rest < 0:
            raise ValueError

        speed_percent = None if percent == "-" else int(percent)
        if speed_percent is not None and not (1 <= speed_percent <= 200):
            raise ValueError
    except ValueError:
        await message.answer("❗ Неверные числа. Пример: `3 1 90 60` или `3 1 - 60`")
        return

    # сохраняем в блок
    entry = {
        "id": ex_id,
        "name": ex_name,
        "sets": sets,
        "reps_min": reps,
        "reps_max": reps,
        "one_rm_percent": speed_percent,  # ← новое поле
        "rest_seconds": rest,
        "notes": None,
    }
    selected = data.get("selected_blocks", {})
    selected.setdefault(block, {"description": "", "exercises": []})
    selected[block]["exercises"].append(entry)
    await _sync_workout_draft(state, selected_blocks=selected)

    # чистим временные ключи
    for k in (
        "selected_exercise_id",
        "selected_exercise_name",
        "selected_exercise_1rm",
        "pending_ex_id",
        "pending_ex_name",
        "pending_ex_block",
        "pending_one_rm",
        "pending_one_rm_method",
        "pending_one_rm_tested_at",
        "exercise_test_type",
    ):
        await state.update_data({k: None})

    await message.answer(
        f"**{ex_name}** добавлено: {sets}×{reps}, "
        f"{speed_percent or '—'}% от лучшего времени, отдых {rest} сек"
    )
    await _show_exercises_for_block(message, state)
    await state.set_state(CreateWorkoutStates.adding_exercises)
#----------------- REGISTER -----------------
def register_workout_handlers(dp):
    #dp.include_router(workouts_router)
    logger.info("🏋️ Обработчики тренировок зарегистрированы")


__all__ = ["workouts_router", "register_workout_handlers", "process_workout_text_input"]