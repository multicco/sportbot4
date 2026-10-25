# ===== ОБРАБОТЧИКИ 1ПМ, ВЫНОСЛИВОСТИ И СКОРОСТИ =====

from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
import logging
from database import db_manager
from keyboards.main_keyboards_old import get_coming_soon_keyboard
from utils.validators import validate_1rm_data, validate_endurance_data, validate_speed_data
from utils.formatters import format_1rm_results

logger = logging.getLogger(__name__)

# ------------------  FSM-стейты  ------------------
WAITING_1RM_DATA       = "waiting_1rm_data"
WAITING_ENDURANCE_DATA = "waiting_endurance_data"
WAITING_SPEED_DATA     = "waiting_speed_data"
from states.workout_states import CreateWorkoutStates
from aiogram.filters import StateFilter
# ------------------  РЕГИСТРАЦИЯ  ------------------
def register_one_rm_handlers(dp):
    """Регистрация всех тестовых обработчиков"""
    # 1ПМ
    dp.callback_query.register(new_1rm_test, F.data == "new_1rm_test")
    dp.callback_query.register(select_1rm_exercise, F.data.startswith("1rm_"))
    dp.callback_query.register(handle_test1rm_from_workout, F.data.startswith("test1rm_"))
    dp.callback_query.register(show_my_1rm_results, F.data == "my_1rm_results")
    dp.callback_query.register(show_1rm_stats, F.data == "1rm_stats")

    # выносливость
    dp.callback_query.register(new_endurance_test, F.data == "new_endurance_test")
    dp.callback_query.register(select_endurance_exercise, F.data.startswith("endurance_"))

    # скорость
    dp.callback_query.register(new_speed_test, F.data == "new_speed_test")
    dp.callback_query.register(select_speed_exercise, F.data.startswith("speed_"))

    # универсальный вход
    dp.callback_query.register(start_any_test, F.data.startswith("start_test_"))

# ----------  ТЕКСТОВЫЕ ВВОДЫ  ----------
# ВАЖНО: текстовые вводы этих тестов обрабатывает единый диспетчер
# handlers.handle_all_text_messages (general_router). Здесь регистрировать
# message-хендлеры по строковым стейтам нельзя — aiogram требует объект State,
# а ошибка ImportError/TypeError при регистрации ломала весь модуль one_rm,
# из-за чего секунды (тест планки) «никуда не уходили».

# ----------  ОБРАБОТКА КОЛИЧЕСТВЕННОГО ТЕСТА  ----------
async def process_quantity_data(message: Message, state: FSMContext):
    """Обработка ввода для quantity-теста"""
    try:
        reps = int(message.text.strip())
        if reps <= 0 or reps > 10000:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите целое число повторений (1-10000)")
        return

    data        = await state.get_data()
    ex_id       = data.get("exercise_id")
    ex_name     = data.get("exercise_name")
    user        = await db_manager.get_user_by_telegram_id(message.from_user.id)

    async with db_manager.pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO user_tests
            (user_id, exercise_id, test_type, result_value, result_unit, max_reps, tested_at)
            VALUES ($1, $2, $3, $4, $5, $6, NOW())
        """, user["id"], int(ex_id), "quantity", reps, "раз", reps)

    kb = InlineKeyboardBuilder()
    kb.button(text="💪 Новый тест", callback_data="new_test_menu")
    kb.button(text="📊 Мои результаты", callback_data="my_tests")
    kb.button(text="🏠 Главное меню", callback_data="main_menu")
    await message.answer(
        f"🔢 **Результат:** {reps} повторений\n✅ Сохранено!",
        reply_markup=kb.as_markup(), parse_mode="Markdown"
    )
    await state.clear()
# ==============================================================================
#  1ПМ
# ==============================================================================
async def new_1rm_test(callback: CallbackQuery):
    """Список силовых упражнений для теста 1ПМ"""
    try:
        async with db_manager.pool.acquire() as conn:
            exercises = await conn.fetch("""
                SELECT id, name, category, muscle_group
                FROM exercises 
                WHERE category = 'Силовые'
                ORDER BY name
                LIMIT 15
            """)
        if not exercises:
            await callback.message.edit_text("❌ Силовые упражнения не найдены.")
            return

        kb = InlineKeyboardBuilder()
        for ex in exercises:
            kb.button(text=f"💪 {ex['name']}", callback_data=f"1rm_{ex['id']}")
        kb.button(text="🔙 Назад", callback_data="one_rm_menu")
        kb.adjust(1)

        await callback.message.edit_text(
            "💪 **Выберите упражнение для теста 1ПМ:**",
            reply_markup=kb.as_markup(), parse_mode="Markdown"
        )
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    await callback.answer()

async def select_1rm_exercise(callback: CallbackQuery, state: FSMContext):
    """Выбор упражнения и переход к вводу данных с учётом типа теста"""
    ex_id = int(callback.data.split("_")[1])
    ex    = await db_manager.pool.fetchrow(
        "SELECT id, name, test_type FROM exercises WHERE id=$1", ex_id
    )
    if not ex:
        await callback.answer("Упражнение не найдено", show_alert=True)
        return

    await state.update_data(exercise_id=ex_id, exercise_name=ex["name"])

    test_type = ex["test_type"] or "strength"   # на всякий случай

    # ----------  ВЕТВЛЕНИЕ ПО ТИПУ ТЕСТА  ----------
    if test_type == "endurance":
        await callback.message.edit_text(
            f"⏱ **Тест выносливости: {ex['name']}**\n\n"
            "Введите результат в секундах (например: `120`) или в формате `1:30`:",
            parse_mode="Markdown"
        )
        await state.set_state("waiting_endurance_data")
        await callback.answer()
        return

    if test_type == "speed":
        await callback.message.edit_text(
            f"🏃 **Тест скорости: {ex['name']}**\n\n"
            "Введите результат в секундах (например: `8.5`)",
            parse_mode="Markdown"
        )
        await state.set_state("waiting_speed_data")
        await callback.answer()
        return

    if test_type == "quantity":
        await callback.message.edit_text(
            f"🔢 **Количественный тест: {ex['name']}**\n\n"
            "Введите максимальное количество повторений (например: `45`):",
            parse_mode="Markdown"
        )
        await state.set_state("waiting_quantity_data")
        await callback.answer()
        return

    # ----------  ДЛЯ СИЛОВЫХ (и всего остального) – 1ПМ  ----------
    await callback.message.edit_text(
        f"💪 **Тест 1ПМ: {ex['name']}**\n\n"
        "Введите `вес повторения` (например: `80 5`):",
        parse_mode="Markdown"
    )
    await state.set_state(WAITING_1RM_DATA)
    await callback.answer()

async def show_my_1rm_results(callback: CallbackQuery):
    """История 1ПМ пользователя"""
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    try:
        async with db_manager.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT e.name, orm.weight, orm.tested_at, orm.reps, orm.test_weight
                FROM one_rep_max orm
                JOIN exercises e ON orm.exercise_id = e.id
                WHERE orm.user_id = $1
                ORDER BY orm.tested_at DESC
                LIMIT 10
            """, user['id'])
        if rows:
            text = "📊 **Ваши результаты 1ПМ:**\n\n"
            for r in rows:
                dt = r['tested_at'].strftime('%d.%m.%Y')
                text += f"💪 **{r['name']}**\n🏋️ 1ПМ: **{r['weight']} кг**\n📝 Тест: {r['test_weight']}кг × {r['reps']} раз\n📅 {dt}\n\n"
        else:
            text = "📊 У вас пока нет результатов 1ПМ."
        kb = InlineKeyboardBuilder().button(text="💪 Новый тест", callback_data="new_1rm_test").button(text="🔙 К тестам", callback_data="one_rm_menu")
        await callback.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="Markdown")
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    await callback.answer()

async def show_1rm_stats(callback: CallbackQuery):
    await callback.message.edit_text(
        "🚧 Статистика 1ПМ в разработке.",
        reply_markup=get_coming_soon_keyboard(), parse_mode="Markdown"
    )
    await callback.answer()

# ==============================================================================
#  УНИВЕРСАЛЬНЫЙ ВХОД
# ==============================================================================
async def start_any_test(callback: CallbackQuery, state: FSMContext):
    """Определяет тип упражнения и ветвит на нужный тест"""
    _, ex_id_str, w_id_str = callback.data.split("_")
    ex_id, w_id = int(ex_id_str), int(w_id_str)

    ex = await db_manager.pool.fetchrow("SELECT name, test_type FROM exercises WHERE id=$1", ex_id)
    if not ex:
        await callback.answer("Упражнение не найдено", show_alert=True)
        return

    await state.update_data(exercise_id=ex_id, exercise_name=ex["name"])
    if w_id:
        await state.update_data(return_after_test=w_id)   # универсальный ключ возврата

    if ex["test_type"] == "strength":
        await _start_1rm_test(callback, state)
    elif ex["test_type"] == "endurance":
        await _start_endurance_test(callback, state)
    elif ex["test_type"] == "speed":
        await _start_speed_test(callback, state)
    else:
        await callback.answer("Для этого упражнения тест не предусмотрен", show_alert=True)

# ------------------  вспомогательные «старты»  ------------------
async def _start_1rm_test(cb: CallbackQuery, state: FSMContext):
    name = (await state.get_data())["exercise_name"]
    await cb.message.edit_text(
        f"💪 **Тест 1ПМ: {name}**\n\n"
        "Введите `вес повторения` (например: `80 5`):",
        parse_mode="Markdown"
    )
    await state.set_state(WAITING_1RM_DATA)
    await cb.answer()

async def _start_endurance_test(cb: CallbackQuery, state: FSMContext):
    name = (await state.get_data())["exercise_name"]
    await cb.message.edit_text(
        f"⏱ **Тест выносливости: {name}**\n\n"
        "Введите результат в секундах (например: `120`):",
        parse_mode="Markdown"
    )
    await state.set_state(WAITING_ENDURANCE_DATA)
    await cb.answer()

async def _start_speed_test(cb: CallbackQuery, state: FSMContext):
    name = (await state.get_data())["exercise_name"]
    await cb.message.edit_text(
        f"🏃 **Тест скорости: {name}**\n\n"
        "Введите результат в секундах (например: `8.5`):",
        parse_mode="Markdown"
    )
    await state.set_state(WAITING_SPEED_DATA)
    await cb.answer()

# ==============================================================================
#  1ПМ: расчёт и сохранение
# ==============================================================================
def calculate_1rm(weight, reps):
    w, r = float(weight), int(reps)
    if r == 1:
        return {'brzycki': w, 'epley': w, 'alternative': w, 'average': w}
    brzycki   = w / (1.0278 - 0.0278 * r)
    epley     = w * (1 + r / 30.0)
    alternative = w * (1 + 0.025 * r)
    average   = (brzycki + epley + alternative) / 3.0
    return {k: round(v, 1) for k, v in {
        'brzycki': brzycki, 'epley': epley, 'alternative': alternative, 'average': average
    }.items()}

async def process_1rm_data(message: Message, state: FSMContext):
    parts = message.text.split()
    valid = validate_1rm_data(parts[0] if len(parts) > 0 else "",
                              parts[1] if len(parts) > 1 else "")
    if not valid['valid']:
        await message.answer(valid['error'])
        return

    weight, reps = valid['weight'], valid['reps']
    results = calculate_1rm(weight, reps)
    data    = await state.get_data()
    name    = data.get('exercise_name', 'Упражнение')
    user    = await db_manager.get_user_by_telegram_id(message.from_user.id)

    try:
        async with db_manager.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO one_rep_max (user_id, exercise_id, weight, reps, test_weight,
                                       formula_brzycki, formula_epley, formula_alternative, formula_average)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """, user['id'], int(data['exercise_id']), results['average'],
               reps, weight, results['brzycki'], results['epley'],
               results['alternative'], results['average'])

        text = format_1rm_results(name, weight, reps, results)
        kb   = (InlineKeyboardBuilder()
                .button(text="💪 Новый тест", callback_data="new_1rm_test")
                .button(text="📊 Мои результаты", callback_data="my_1rm_results")
                .button(text="🏠 Главное меню", callback_data="main_menu")
                .adjust(1))
        await message.answer(text, reply_markup=kb.as_markup(), parse_mode="Markdown")

        ret = data.get("return_after_test")
        if ret:
            from handlers.player_workouts import show_workout_overview
            await message.answer("1ПМ обновлён — возвращаемся в тренировку!")
            await show_workout_overview(message, state, int(ret))
            await state.clear()
            return

        # ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
        # ВОЗВРАТ В ТРЕНИРОВКУ ПОСЛЕ 1ПМ
        # ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
        data = await state.get_data()
        return_to = data.get("return_after_1rm_test")
        if return_to:
            from handlers.player_workouts import show_workout_overview
            await message.answer("1ПМ обновлён — возвращаемся в тренировку!")
            await show_workout_overview(message, state, return_to)
            await state.clear()
            return
        # ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←

        

        await state.clear()

    except Exception as e:
        await message.answer(f"❌ Ошибка сохранения: {e}")

# ==============================================================================
#  ВЫНОСЛИВОСТЬ
# ==============================================================================
async def new_endurance_test(callback: CallbackQuery):
    try:
        async with db_manager.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, name FROM exercises WHERE test_type='endurance' ORDER BY name LIMIT 15
            """)
        if not rows:
            await callback.message.edit_text("❌ Упражнений на выносливость не найдено.")
            return
        kb = InlineKeyboardBuilder()
        for r in rows:
            kb.button(text=f"⏱ {r['name']}", callback_data=f"endurance_{r['id']}")
        kb.button(text="🔙 Назад", callback_data="one_rm_menu")
        kb.adjust(1)
        await callback.message.edit_text(
            "⏱ **Выберите упражнение для теста выносливости:**",
            reply_markup=kb.as_markup(), parse_mode="Markdown"
        )
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    await callback.answer()

async def select_endurance_exercise(callback: CallbackQuery, state: FSMContext):
    ex_id = int(callback.data.split("_")[1])
    ex    = await db_manager.pool.fetchrow("SELECT name FROM exercises WHERE id=$1", ex_id)
    if not ex:
        await callback.answer("Упражнение не найдено", show_alert=True)
        return
    await state.update_data(exercise_id=ex_id, exercise_name=ex["name"])
    await callback.message.edit_text(
        f"⏱ **Тест выносливости: {ex['name']}**\n\n"
        "Введите результат в секундах (например: `120`):",
        parse_mode="Markdown"
    )
    await state.set_state(WAITING_ENDURANCE_DATA)
    await callback.answer()

def calc_endurance_max(sec: float):
    s = float(sec)
    return {
        "a": round(s * 1.05, 1),
        "b": round(s * 1.10, 1),
        "c": round(s * 1.15, 1),
        "avg": round(s * 1.10, 1)
    }

async def process_endurance_data(message: Message, state: FSMContext):
    try:
        sec = float(message.text.replace(",", "."))
        if sec <= 0 or sec > 86400:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите корректное время в секундах.")
        return

    data   = await state.get_data()
    ex_id  = int(data["exercise_id"])
    name   = data["exercise_name"]
    user   = await db_manager.get_user_by_telegram_id(message.from_user.id)
    results = calc_endurance_max(sec)

    async with db_manager.pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO user_endurance_records
            (user_id, exercise_id, result_seconds, model_a, model_b, model_c, average)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """, user["id"], ex_id, sec, results["a"], results["b"], results["c"], results["avg"])

    kb = (InlineKeyboardBuilder()
          .button(text="➕ Ещё тест", callback_data="new_endurance_test")
          .button(text="📊 Мои рекорды", callback_data="my_endurance_results")
          .button(text="🏠 Главное меню", callback_data="main_menu")
          .adjust(1))
    await message.answer(
        f"⏱ **Результат выносливости: {name}**\n\n"
        f"Ваше время: **{sec} с**\n"
        f"Расчётный максимум ≈ **{results['avg']} с**",
        reply_markup=kb.as_markup(), parse_mode="Markdown"
    )

    ret = data.get("return_after_test")
    if ret:
        from handlers.player_workouts import show_workout_overview
        await message.answer("Рекорд выносливости обновлён — возвращаемся в тренировку!")
        await show_workout_overview(message, state, int(ret))
        await state.clear()

# ==============================================================================
#  СКОРОСТЬ
# ==============================================================================
async def new_speed_test(callback: CallbackQuery):
    try:
        async with db_manager.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, name FROM exercises WHERE test_type='speed' ORDER BY name LIMIT 15
            """)
        if not rows:
            await callback.message.edit_text("❌ Упражнений на скорость не найдено.")
            return
        kb = InlineKeyboardBuilder()
        for r in rows:
            kb.button(text=f"🏃 {r['name']}", callback_data=f"speed_{r['id']}")
        kb.button(text="🔙 Назад", callback_data="one_rm_menu")
        kb.adjust(1)
        await callback.message.edit_text(
            "🏃 **Выберите упражнение для теста скорости:**",
            reply_markup=kb.as_markup(), parse_mode="Markdown"
        )
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    await callback.answer()

async def select_speed_exercise(callback: CallbackQuery, state: FSMContext):
    ex_id = int(callback.data.split("_")[1])
    ex    = await db_manager.pool.fetchrow("SELECT name FROM exercises WHERE id=$1", ex_id)
    if not ex:
        await callback.answer("Упражнение не найдено", show_alert=True)
        return
    await state.update_data(exercise_id=ex_id, exercise_name=ex["name"])
    await callback.message.edit_text(
        f"🏃 **Тест скорости: {ex['name']}**\n\n"
        "Введите результат в секундах (например: `8.5`):",
        parse_mode="Markdown"
    )
    await state.set_state(WAITING_SPEED_DATA)
    await callback.answer()

def calc_speed_max(sec: float):
    s = float(sec)
    return {
        "a": round(s * 0.95, 2),
        "b": round(s * 0.90, 2),
        "c": round(s * 0.85, 2),
        "avg": round(s * 0.90, 2)
    }

async def process_speed_data(message: Message, state: FSMContext):
    logger.info("process_speed_data: ENTER state=%s", await state.get_state())
    try:
        sec = float(message.text.replace(",", "."))
        if sec <= 0 or sec > 3600:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите корректное время в секундах.")
        return

    data   = await state.get_data()
    ex_id  = int(data["exercise_id"])
    name   = data["exercise_name"]
    user   = await db_manager.get_user_by_telegram_id(message.from_user.id)
    results = calc_speed_max(sec)

    async with db_manager.pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO user_speed_records
            (user_id, exercise_id, result_seconds, model_a, model_b, model_c, average)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
        """, user["id"], ex_id, sec, results["a"], results["b"], results["c"], results["avg"])

    kb = (InlineKeyboardBuilder()
          .button(text="➕ Ещё тест", callback_data="new_speed_test")
          .button(text="📊 Мои рекорды", callback_data="my_speed_results")
          .button(text="🏠 Главное меню", callback_data="main_menu")
          .adjust(1))
    await message.answer(
        f"🏃 **Результат скорости: {name}**\n\n"
        f"Ваше время: **{sec} с**\n"
        f"Расчётный максимум ≈ **{results['avg']} с**",
        reply_markup=kb.as_markup(), parse_mode="Markdown"
    )

    ret = data.get("return_after_test")
    if ret:
        from handlers.player_workouts import show_workout_overview
        await message.answer("Рекорд скорости обновлён — возвращаемся в тренировку!")
        await show_workout_overview(message, state, int(ret))
        await state.clear()

# ==============================================================================
#  ВОЗВРАТ В ТРЕНИРОВКУ (совместим со старым test1rm_)
# ==============================================================================
async def handle_test1rm_from_workout(callback: CallbackQuery, state: FSMContext):
    """Совместимость со старыми кнопками test1rm_<ex_id>_<workout_id>"""
    try:
        _, ex_id_str, wid_str = callback.data.split("_")
        ex_id, workout_id = int(ex_id_str), int(wid_str)

        ex = await db_manager.pool.fetchrow("SELECT name FROM exercises WHERE id=$1", ex_id)
        if not ex:
            await callback.answer("Упражнение не найдено", show_alert=True)
            return

        await state.update_data(
            exercise_id=ex_id,
            exercise_name=ex["name"],
            return_after_test=workout_id
        )
        # переводим в 1ПМ-сценарий
        fake = callback.model_copy(update={"data": f"1rm_{ex_id}"})
        await select_1rm_exercise(fake, state)

    except Exception as e:
        logger.error(f"handle_test1rm_from_workout: {e}")
        await callback.answer("Ошибка запуска теста 1ПМ", show_alert=True)

# ==============================================================================
#  УТИЛИТЫ
# ==============================================================================
async def get_user_1rm_for_exercise(user_id: int, exercise_id: int):
    try:
        async with db_manager.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT weight FROM one_rep_max 
                WHERE user_id=$1 AND exercise_id=$2 
                ORDER BY tested_at DESC LIMIT 1
            """, user_id, exercise_id)
        return float(row['weight']) if row else None
    except Exception:
        return None

# ------------------  ЭКСПОРТ  ------------------
__all__ = [
    'register_one_rm_handlers',
    'process_1rm_data',
    'calculate_1rm',
    'get_user_1rm_for_exercise'
]