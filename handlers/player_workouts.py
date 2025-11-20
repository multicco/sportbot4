# handlers/player_workouts.py

import logging
from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from states.workout_assignment_states import WorkoutPlayerStates
logger = logging.getLogger(__name__)
player_workouts_router = Router(name="player_workouts")
from handlers import teams 
logger.info("Импорт teams_db в player_workouts.py: %s", teams )

from states.player_rpe_state import PlayerRPEState   


# @player_workouts_router.message()          # ловит ВСЕ текстовые сообщения
# async def debug(message: Message, state: FSMContext):
#     st = await state.get_state()
#     await message.answer(f"state={st}\nтекст={message.text}")


@player_workouts_router.message(Command("myworkouts"))
@player_workouts_router.callback_query(F.data == "assigned_workouts")
async def show_my_workouts(update: Message | CallbackQuery, state: FSMContext):
    """Показать тренировки игрока"""
    await state.clear()
    
    if isinstance(update, CallbackQuery):
        telegram_id = update.from_user.id
        message = update.message
        is_callback = True
    else:
        telegram_id = update.from_user.id
        message = update
        is_callback = False
    
    # Проверка инициализации teams_db
    if teams.teams_db is None:
        logger.error("teams.teams_db не инициализирована в show_my_workouts")
        text = (
            "<b>❌ Ошибка</b>\n\n"
            "База данных недоступна. Попробуйте позже."
        )
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
        
        if is_callback:
            await message.edit_text(text, reply_markup=keyboard.as_markup(), parse_mode="HTML")
            await update.answer()
        else:
            await message.answer(text, reply_markup=keyboard.as_markup(), parse_mode="HTML")
        return
    
    # Получаем тренировки игрока
    try:
        workouts = await teams.teams_db.get_player_workouts(telegram_id)
    except Exception as e:
        logger.error(f"Ошибка при получении тренировок для telegram_id {telegram_id}: {e}", exc_info=True)
        text = (
            "<b>❌ Ошибка</b>\n\n"
            "Не удалось загрузить тренировки. Попробуйте позже."
        )
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
        
        if is_callback:
            await message.edit_text(text, reply_markup=keyboard.as_markup(), parse_mode="HTML")
            await update.answer()
        else:
            await message.answer(text, reply_markup=keyboard.as_markup(), parse_mode="HTML")
        return
    
    if not workouts:
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
        
        text = (
            "<b>📭 У вас пока нет тренировок</b>\n\n"
            "Тренер назначит тренировки, и они появятся здесь."
        )
        
        if is_callback:
            await message.edit_text(text, reply_markup=keyboard.as_markup(), parse_mode="HTML")
            await update.answer()
        else:
            await message.answer(text, reply_markup=keyboard.as_markup(), parse_mode="HTML")
        return
    
    # Группируем по статусам
    new_workouts = [w for w in workouts if w['status'] == 'pending']
    in_progress = [w for w in workouts if w['status'] == 'in_progress']
    completed = [w for w in workouts if w['status'] == 'completed']
    
    text = "<b>💪 Мои тренировки</b>\n\n"
    
    keyboard = InlineKeyboardBuilder()
    
    # Новые тренировки
    if new_workouts:
        text += f"<b>🔴 Новые ({len(new_workouts)}):</b>\n"
        for w in new_workouts:
            deadline_text = ""
            if w['deadline']:
                deadline_text = f" ⏰ До {w['deadline'].strftime('%d.%m')}"
            
            text += f"  • {w['workout_name']} ({w['team_name']}){deadline_text}\n"
            keyboard.button(
                text=f"💪 {w['workout_name']}",
                callback_data=f"start_workout_{w['workout_id']}"
            )
        text += "\n"
    
    # В процессе
    if in_progress:
        text += f"<b>⏳ В процессе ({len(in_progress)}):</b>\n"
        for w in in_progress:
            text += f"  • {w['workout_name']} ({w['team_name']})\n"
            keyboard.button(
                text=f"▶️ Продолжить: {w['workout_name']}",
                callback_data=f"continue_workout_{w['workout_id']}"
            )
        text += "\n"
    
    # Выполненные (последние 5)
    if completed:
        text += f"<b>✅ Выполнено ({len(completed)}):</b>\n"
        for w in completed[:5]:
            rpe_text = f" (RPE: {w['rpe']:.1f})" if w['rpe'] else ""
            completed_date = w['completed_at'].strftime('%d.%m') if w['completed_at'] else ""
            text += f"  • {w['workout_name']}{rpe_text} - {completed_date}\n"
    
    keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
    keyboard.adjust(1)
    
    if is_callback:
        await message.edit_text(text, reply_markup=keyboard.as_markup(), parse_mode="HTML")
        await update.answer()
    else:
        await message.answer(text, reply_markup=keyboard.as_markup(), parse_mode="HTML")


@player_workouts_router.callback_query(F.data.startswith("start_workout_"))
async def start_workout(callback: CallbackQuery, state: FSMContext):
    """Начать тренировку"""
    workout_id = int(callback.data.split("_")[-1])
    
    # Обновляем статус
    success = await teams.teams_db.update_player_workout_status(
        telegram_id=callback.from_user.id,
        workout_id=workout_id,
        status='in_progress'
    )
    
    if not success:
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="✅ Завершить тренировку", callback_data=f"player_finish_workout_{workout_id}")
    keyboard.button(text="📋 Мои тренировки", callback_data="assigned_workouts")
    keyboard.adjust(1)
    
    await callback.message.edit_text(
        f"💪 **Тренировка начата!**\n\n"
        f"Удачной тренировки! Когда закончите, нажмите \"Завершить\".\n\n"
        f"💡 *Не забудьте оценить интенсивность тренировки по шкале RPE после завершения*",
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer("✅ Тренировка начата!")

@player_workouts_router.callback_query(F.data.startswith("player_finish_workout_"))
async def finish_workout(callback: CallbackQuery, state: FSMContext):
    workout_id = int(callback.data.split("_")[-1])
    
    await state.clear()  # ← ЭТО ФИКС: очищаем любое старое состояние перед новым!
    
    await state.set_state(PlayerRPEState.waiting)
    await state.update_data(workout_id=workout_id)
    
    await callback.message.edit_text(
        "📊 **Оцените интенсивность тренировки**\n\n"
        "Введите число от **1 до 10**:\n"
        "1 – легко, 10 – максимум\n\n"
        "💡 *Напишите цифру в чат*",
        parse_mode="Markdown"
    )
    await callback.answer()

@player_workouts_router.message(PlayerRPEState.waiting)
async def process_rpe_text(message: Message, state: FSMContext):
    text = message.text.strip().replace(",", ".")

    # Проверяем корректность формата RPE
    try:
        rpe = float(text)
        if not 1 <= rpe <= 10:
            raise ValueError
        rpe = round(rpe, 1)
    except:
        await state.clear()
        await message.answer("❌ Введите число от 1 до 10. Пример: 7 или 8.5")
        return

    data = await state.get_data()
    workout_id = data.get("workout_id")

    if not workout_id:
        await message.answer("Ошибка: потерялся ID тренировки. Начните заново.")
        await state.clear()
        return

    success = await teams.teams_db.update_player_workout_status(
        telegram_id=message.from_user.id,
        workout_id=workout_id,
        status='completed',
        rpe=rpe
    )

    await state.clear()

    if success:
        await message.answer(
            f"🎉 **Тренировка завершена!**\n\n"
            f"📊 RPE: {rpe:.1f}/10\n"
            f"Отличная работа! 💪",
            parse_mode="Markdown"
        )
    else:
        await message.answer("❌ Не удалось сохранить результат. Обратитесь к администратору.")


def get_player_workouts_router():
    """Экспорт роутера"""
    return player_workouts_router