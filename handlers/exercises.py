# handlers/workouts.py
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
workouts_router = Router()


# -----------------------
#  HELPERS
# -----------------------
async def _safe_edit_or_send(message_obj, text: str, **kwargs):
    """
    Попробовать edit_text, если не получилось — отправить новое сообщение.
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
    return {"name": name, "description": "", "exercises": []}


# -----------------------
#  DEBUG: ловим ВСЕ callback (временно можно убрать)
# -----------------------
@workouts_router.callback_query()  # catch-all для колбеков — удобно отлаживать
async def _debug_all_callbacks(callback: CallbackQuery):
    logger.debug("🔸 Получен callback: %s (from %s)", callback.data, callback.from_user.id)
    # не отвечаем автоматически — даём возможность нормальным хендлерам обработать
    # но если ни один хендлер сработает, то update будет помечен как not handled в логах aiogram


@workouts_router.message()  # debug для любых сообщений (показывается только если router подключён)
async def _debug_all_messages(message: Message, state: FSMContext):
    current_state = await state.get_state()
    logger.debug("💬 DEBUG MESSAGE: text='%s' state=%s user=%s", message.text, current_state, message.from_user.id)
    # не отвечаем автоматически


# === ПОИСК УПРАЖНЕНИЙ ===
@exercises_router.callback_query(F.data == "search_exercise")
async def search_exercise_menu(callback: CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.button(text="По названию", callback_data="search_by_name")
    kb.button(text="По категории", callback_data="search_by_category")
    kb.button(text="По группе мышц", callback_data="search_by_muscle")
    kb.button(text="Главное меню", callback_data="main_menu")
    kb.adjust(1)
    await callback.message.edit_text(
        "**Поиск упражнений**\n\nВыберите способ:",
        reply_markup=kb.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()

# -----------------------
#  MENU: главная точка входа в меню тренировок
# -----------------------
@workouts_router.callback_query(F.data == "workouts_menu")
async def workouts_menu(callback: CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.button(text="🏋️ Мои тренировки", callback_data="workouts_my")
    kb.button(text="🔍 Найти тренировку", callback_data="workouts_find")
    kb.button(text="➕ Создать тренировку", callback_data="create_workout")
    kb.button(text="📊 Моя статистика", callback_data="workout_statistics")
    kb.button(text="🔙 Главное меню", callback_data="main_menu")
    kb.adjust(2)
    await callback.message.edit_text("🏋️ **Меню тренировок**\n\nВыберите действие:", reply_markup=kb.as_markup(), parse_mode="Markdown")
    await callback.answer()


# -----------------------
#  МОИ ТРЕНИРОВКИ (краткий список)
# -----------------------
@workouts_router.callback_query(F.data == "workouts_my")
async def my_workouts(callback: CallbackQuery):
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


# -----------------------
#  Просмотр тренировки
# -----------------------
def _format_time(seconds: Optional[int]) -> str:
    if not seconds:
        return ""
    m, s = divmod(seconds, 60)
    if m > 0:
        return f"{m}м {s}с" if s else f"{m}м"
    return f"{s}с"


@workouts_router.callback_query(F.data.startswith("view_workout_"))
async def view_workout_details(callback: CallbackQuery):
    try:
        workout_id = int(callback.data.split("_")[-1])
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
        kb.button(text="▶️ Начиная тренировку", callback_data=f"start_workout_{workout_id}")
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




# -----------------------
#  СОЗДАНИЕ ТРЕНИРОВКИ
# -----------------------
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
async def cancel_workout_creation(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardBuilder()
    kb.button(text="🔙 В меню тренировок", callback_data="workouts_menu")
    kb.adjust(1)
    await _safe_edit_or_send(callback.message, "❌ Создание тренировки отменено.", reply_markup=kb.as_markup())
    await callback.answer()


# message handler: ввод названия тренировки
@workouts_router.message(StateFilter(CreateWorkoutStates.waiting_workout_name))
async def handle_workout_name(message: Message, state: FSMContext):
    name = (message.text or "").strip()
    if not name or len(name) < 3:
        await message.answer("Название слишком короткое — минимум 3 символа.")
        return
    await state.update_data(name=name)
    kb = InlineKeyboardBuilder()
    kb.button(text="Пропустить описание", callback_data="skip_workout_description")
    kb.button(text="Добавить описание", callback_data="add_workout_description")
    kb.adjust(1)
    await message.answer(f"✅ Название сохранено: *{name}*\n\nДобавьте описание или пропустите.", reply_markup=kb.as_markup(), parse_mode="Markdown")
    await state.set_state(CreateWorkoutStates.waiting_workout_description)


# callback: нажали "Пропустить описание"
@workouts_router.callback_query(F.data == "skip_workout_description")
async def skip_workout_description(callback: CallbackQuery, state: FSMContext):
    await state.update_data(description="")
    await callback.answer("Описание пропущено")
    await show_block_selection_menu(callback.message, state)


# callback: открыть ввод описания
@workouts_router.callback_query(F.data == "add_workout_description")
async def add_workout_description(callback: CallbackQuery):
    await callback.message.edit_text("📝 Введите описание тренировки (необязательно):", parse_mode="Markdown")
    # Перевод на состояние ожидания текста — handled через текущее состояние ожидания описания
    await callback.answer()


# message handler: ввод описания
@workouts_router.message(StateFilter(CreateWorkoutStates.waiting_workout_description))
async def handle_workout_description(message: Message, state: FSMContext):
    desc = (message.text or "").strip()
    await state.update_data(description=desc)
    await message.answer("Описание сохранено.")
    await show_block_selection_menu(message, state)


# Отображение меню выбора блоков
async def show_block_selection_menu(message_obj, state: FSMContext):
    data = await state.get_data()
    name = data.get("name", "<без названия>")
    selected = data.get("selected_blocks", {})

    text = f"🏗 **Конструктор тренировки: {name}**\n\nВыберите блокы для тренировки:\n\n"
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


# callback: добавление блока (разные блоки приходят как add_block_<key>)
@workouts_router.callback_query(F.data.startswith("add_block_"))
async def add_block(callback: CallbackQuery, state: FSMContext):
    key = callback.data.split("_", 2)[2]
    # сохраняем текущий блок в state
    await state.update_data(current_block=key)
    # показываем меню добавления описания → затем упражнения
    kb = InlineKeyboardBuilder()
    kb.button(text="Добавить описание блока", callback_data="add_block_description")
    kb.button(text="Пропустить описание блока", callback_data="skip_block_description")
    kb.button(text="🔙 Назад", callback_data="back_to_constructor")
    kb.adjust(1)
    await callback.message.edit_text(f"✍️ Блок: *{key}*", reply_markup=kb.as_markup(), parse_mode="Markdown")
    await state.set_state(CreateWorkoutStates.adding_block_description)
    await callback.answer()


@workouts_router.callback_query(F.data == "back_to_constructor")
async def back_to_constructor(callback: CallbackQuery, state: FSMContext):
    # просто возвращаем в меню конструирования
    await show_block_selection_menu(callback.message, state)
    await callback.answer()


@workouts_router.callback_query(F.data == "add_block_description")
async def prompt_block_description(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("📝 Введите описание для этого блока (необязательно):", parse_mode="Markdown")
    await state.set_state(CreateWorkoutStates.adding_block_description)
    await callback.answer()


@workouts_router.callback_query(F.data == "skip_block_description")
async def skip_block_description(callback: CallbackQuery, state: FSMContext):
    # добавим пустую запись для блока, если её ещё нет
    data = await state.get_data()
    sel = data.get("selected_blocks", {})
    current = data.get("current_block")
    if current:
        sel.setdefault(current, _new_block_struct())
        await state.update_data(selected_blocks=sel)
    await callback.answer("Описание блока пропущено")
    # перейти к добавлению упражнений
    await show_block_exercises_menu(callback.message, state)


# message handler: ввод описания блока
@workouts_router.message(StateFilter(CreateWorkoutStates.adding_block_description))
async def handle_block_description(message: Message, state: FSMContext):
    desc = (message.text or "").strip()
    data = await state.get_data()
    current = data.get("current_block")
    sel = data.get("selected_blocks", {})
    if not current:
        await message.answer("Не найден текущий блок. Вернитесь в конструктор.")
        return
    # обновляем
    sel.setdefault(current, _new_block_struct())
    sel[current]["description"] = desc
    await state.update_data(selected_blocks=sel)
    await message.answer("Описание блока сохранено.")
    # перейти к выбору упражнений для блока
    await show_block_exercises_menu(message, state)


# Показать меню упражнений для текущего блока
async def show_block_exercises_menu(message_obj, state: FSMContext):
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


# callback: manual add -> переводим FSM в manual_exercise_input
@workouts_router.callback_query(F.data == "manual_add_exercise")
async def manual_add_exercise(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("📝 Введите упражнение вручную (напр.: Присед 3x10 70% 90с):", parse_mode="Markdown")
    # переводим в специальное состояние
    await state.set_state(CreateWorkoutStates.manual_exercise_input)
    await callback.answer()


# message handler: принимает ручной ввод упражнения
@workouts_router.message(StateFilter(CreateWorkoutStates.manual_exercise_input))
async def handle_manual_exercise_input(message: Message, state: FSMContext):
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
    # остаёмся в режиме добавления упражнений (или переводим в adding_exercises)
    await state.set_state(CreateWorkoutStates.adding_exercises)


@workouts_router.callback_query(F.data == "back_to_block_exercises")
async def back_to_block_exercises(callback: CallbackQuery, state: FSMContext):
    await show_block_exercises_menu(callback.message, state)
    await callback.answer()


@workouts_router.callback_query(F.data == "finish_current_block")
async def finish_current_block(callback: CallbackQuery, state: FSMContext):
    # просто возвращаем в конструктор блоков
    await callback.answer("Блок сохранён")
    await show_block_selection_menu(callback.message, state)


# callback: поиск упражнений — попытаемся делегировать в handlers.exercises, если он есть
@workouts_router.callback_query(F.data == "search_exercise_for_block")
async def search_exercise_for_block(callback: CallbackQuery, state: FSMContext):
    # если есть модуль handlers.exercises и там функция searchexerciseforblock, вызовем её
    try:
        from handlers import exercises as exercises_handler  # local import
        if hasattr(exercises_handler, "searchexerciseforblock"):
            await exercises_handler.searchexerciseforblock(callback, state)
            return
    except Exception:
        logger.debug("Модуль handlers.exercises отсутствует или вызов не удался", exc_info=True)

    # fallback: показать простые подсказки
    kb = InlineKeyboardBuilder()
    kb.button(text="🔍 Поиск (не реализовано)", callback_data="noop")
    kb.button(text="📝 Добавить вручную", callback_data="manual_add_exercise")
    kb.button(text="🔙 К упражнениям блока", callback_data="back_to_block_exercises")
    kb.adjust(1)
    await callback.message.edit_text("🔍 Поиск упражнений временно недоступен. Выберите действие:", reply_markup=kb.as_markup(), parse_mode="Markdown")
    await callback.answer()


# Save workout to DB — только вызывается при завершении
@workouts_router.callback_query(F.data == "finish_workout_creation")
async def finish_workout_creation(callback: CallbackQuery, state: FSMContext):
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
                INSERT INTO workouts (name, description, created_by, visibility, difficulty_level, estimated_duration_minutes, created_at)
                VALUES ($1, $2, $3, 'private', 'intermediate', $4, now())
                RETURNING id
                """,
                name, description, user["id"], max(5, total_exercises * 5),
            )

            # optionally compute unique_id (if table creates it via trigger, skip)
            unique_id = await conn.fetchval("SELECT unique_id FROM workouts WHERE id = $1", workout_id)

            order = 0
            for phase, block in selected_blocks.items():
                for ex in block["exercises"]:
                    order += 1
                    await conn.execute(
                        """
                        INSERT INTO workout_exercises (
                            workout_id, exercise_id, phase, order_in_phase, sets, reps_min, reps_max, one_rm_percent, rest_seconds, notes
                        ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
                        """,
                        workout_id,
                        ex.get("id"),
                        phase,
                        order,
                        ex.get("sets"),
                        ex.get("reps_min"),
                        ex.get("reps_max"),
                        ex.get("one_rm_percent"),
                        ex.get("rest_seconds"),
                        ex.get("notes"),
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
@workouts_router.callback_query(F.data.startswith("start_workout_"))
async def start_workout_session(callback: CallbackQuery):
    await callback.answer("Функция старта тренировки (в разработке).")


@workouts_router.callback_query(F.data.startswith("copy_workout_code_"))
async def copy_workout_code(callback: CallbackQuery):
    await callback.answer("Код скопирован в буфер (симуляция).")


# -----------------------
#  REGISTRATION (call from handlers.__init__ or main)
# -----------------------
def register_workout_handlers(dp):
    """
    Must be called once (from handlers.__init__ or main.py).
    It will attach `workouts_router` to the dispatcher.
    """
    try:
        dp.include_router(workouts_router)
        logger.info("✅ workouts_router подключён!")
    except RuntimeError as e:
        # уже подключён (если код запускается несколько раз в dev) — безопасно игнорируем
        logger.warning("workouts_router уже был подключён: %s", e)


from aiogram import Router
import logging

logger = logging.getLogger(__name__)

exercises_router = Router()

def register_exercise_handlers(dp):
    """
    Регистрирует router упражнений.
    """
    try:
        dp.include_router(exercises_router)
        logger.info("✅ exercises_router подключён!")
    except RuntimeError as e:
        logger.warning(f"⚠️ exercises_router уже был подключён: {e}")