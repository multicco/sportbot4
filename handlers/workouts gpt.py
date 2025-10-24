from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import db_manager
from states.workout_states import CreateWorkoutStates

workouts_router = Router()

# === СОЗДАНИЕ НОВОЙ ТРЕНИРОВКИ ===
@workouts_router.callback_query(F.data == "create_workout")
async def start_create_workout(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🏋️ **Создание новой тренировки**\n\nВведите название вашей тренировки:",
        parse_mode="Markdown"
    )
    await state.set_state(CreateWorkoutStates.waiting_name)
    await callback.answer()


# === ПОИСК ТРЕНИРОВКИ ПО КОДУ ===
@workouts_router.callback_query(F.data == "find_workout")
async def start_find_workout(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🔍 **Введите код тренировки**, чтобы найти её.\n\n_Код можно получить от тренера или друга._",
        parse_mode="Markdown"
    )
    await state.set_state("waiting_workout_code")
    await callback.answer()


# === ОБРАБОТКА ВВОДА КОДА ТРЕНИРОВКИ ===
async def process_find_workout_input(message: Message, state: FSMContext):
    code = message.text.strip()

    async with db_manager.pool.acquire() as conn:
        workout = await conn.fetchrow(
            "SELECT * FROM workouts WHERE unique_id = $1 OR id::text = $1",
            code
        )

    if not workout:
        await message.answer("❌ Тренировка с таким кодом не найдена. Попробуйте снова.")
        return

    async with db_manager.pool.acquire() as conn:
        exercises = await conn.fetch(
            """
            SELECT e.name, we.phase, we.sets, we.reps_min, we.reps_max, we.one_rm_percent, we.rest_seconds
            FROM workout_exercises we
            JOIN exercises e ON we.exercise_id = e.id
            WHERE we.workout_id = $1
            ORDER BY we.phase, we.order_in_phase
            """,
            workout["id"]
        )

    text = (
        f"🏋️ **{workout['name']}**\n"
        f"📋 Описание: {workout['description'] or '—'}\n\n"
        f"💡 Код: `{workout['unique_id']}`\n\n"
    )

    if exercises:
        current_phase = None
        for ex in exercises:
            phase = ex["phase"]
            if phase != current_phase:
                phase_names = {
                    "warmup": "🔥 Разминка",
                    "nervous_prep": "⚡ Подготовка НС",
                    "main": "💪 Основная часть",
                    "cooldown": "🧘 Заминка"
                }
                text += f"\n**{phase_names.get(phase, phase.capitalize())}**:\n"
                current_phase = phase
            text += (
                f"• {ex['name']} — {ex['sets']}×{ex['reps_min']}-{ex['reps_max']} повт.  ⏱️ отдых {ex['rest_seconds']}с"
            )
            if ex["one_rm_percent"]:
                text += f" ({ex['one_rm_percent']}% 1ПМ)"
            text += "\n"
    else:
        text += "❌ Упражнения не добавлены.\n"

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🏋️ Создать свою тренировку", callback_data="create_workout")
    keyboard.button(text="🔙 В меню тренировок", callback_data="workouts_menu")
    keyboard.adjust(1)

    await message.answer(text, reply_markup=keyboard.as_markup(), parse_mode="Markdown")
    await state.clear()


# === ОБРАБОТКА ТЕКСТОВОГО ВВОДА ===
async def process_workout_text_input(message: Message, state: FSMContext):
    current_state = await state.get_state()

    # === Ввод названия тренировки ===
    if current_state == CreateWorkoutStates.waiting_name.state:
        workout_name = message.text.strip()
        if not workout_name or len(workout_name) < 3:
            await message.answer("❌ Название слишком короткое. Минимум 3 символа.")
            return
        await state.update_data(name=workout_name)
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="📝 Добавить описание", callback_data="add_workout_description")
        keyboard.button(text="⏭️ Пропустить описание", callback_data="skip_description")
        keyboard.adjust(1)
        await message.answer(
            f"✅ **Название тренировки:** {workout_name}\n\nХотите добавить описание?",
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )
        await state.set_state(CreateWorkoutStates.waiting_description)
        return

    # === Ввод описания тренировки ===
    if current_state == CreateWorkoutStates.waiting_description.state:
        description = message.text.strip()
        await state.update_data(description=description)
        await message.answer("✅ Описание сохранено. Теперь вы можете добавить упражнения или блоки.")
        return

    # === Ввод кода тренировки ===
    if current_state == "waiting_workout_code":
        await process_find_workout_input(message, state)
        return

    await message.answer("ℹ️ Пожалуйста, используйте кнопки меню для навигации.")


def register_workout_handlers(dp):
    dp.include_router(workouts_router)


__all__ = ["workouts_router", "process_workout_text_input", "register_workout_handlers"]
