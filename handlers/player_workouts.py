# handlers/player_workouts.py

import logging
from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from states.workout_assignment_states import WorkoutPlayerStates
#from database.teams_database import teams_database
#from handlers.teams import teams_db
logger = logging.getLogger(__name__)
from handlers.teams import  teams_db
player_workouts_router = Router(name="player_workouts")
logger.info("Импорт teams_db в player_workouts.py: %s", teams_db)


@player_workouts_router.message(Command("myworkouts"))
@player_workouts_router.callback_query(F.data == "my_workouts")
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
    if teams_db is None:
        logger.error("teams_db не инициализирована в show_my_workouts")
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
        workouts = await teams_db.get_player_workouts(telegram_id)
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
    success = await teams_db.update_player_workout_status(
        telegram_id=callback.from_user.id,
        workout_id=workout_id,
        status='in_progress'
    )
    
    if not success:
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="✅ Завершить тренировку", callback_data=f"finish_workout_{workout_id}")
    keyboard.button(text="📋 Мои тренировки", callback_data="my_workouts")
    keyboard.adjust(1)
    
    await callback.message.edit_text(
        f"💪 **Тренировка начата!**\n\n"
        f"Удачной тренировки! Когда закончите, нажмите \"Завершить\".\n\n"
        f"💡 *Не забудьте оценить интенсивность тренировки по шкале RPE после завершения*",
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer("✅ Тренировка начата!")

@player_workouts_router.callback_query(F.data.startswith("finish_workout_"))
async def finish_workout(callback: CallbackQuery, state: FSMContext):
    """Завершить тренировку и запросить RPE"""
    workout_id = int(callback.data.split("_")[-1])
    
    await state.set_state(WorkoutPlayerStates.rating_rpe)
    await state.update_data(workout_id=workout_id)
    
    keyboard = InlineKeyboardBuilder()
    for i in range(1, 11):
        emoji = "🟢" if i <= 3 else "🟡" if i <= 6 else "🟠" if i <= 8 else "🔴"
        keyboard.button(text=f"{emoji} {i}", callback_data=f"rpe_{i}")
    keyboard.button(text="⏭️ Пропустить", callback_data="rpe_skip")
    keyboard.adjust(5, 5, 1)
    
    await callback.message.edit_text(
        "📊 **Оцените интенсивность тренировки**\n\n"
        "**Шкала RPE (Rate of Perceived Exertion):**\n\n"
        "1-3 🟢 Легко\n"
        "4-6 🟡 Умеренно\n"
        "7-8 🟠 Тяжело\n"
        "9-10 🔴 Максимум\n\n"
        "Выберите оценку от 1 до 10:",
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()

@player_workouts_router.callback_query(F.data.startswith("rpe_"))
async def process_rpe_rating(callback: CallbackQuery, state: FSMContext):
    """Обработать оценку RPE"""
    data = await state.get_data()
    workout_id = data.get('workout_id')
    
    if callback.data == "rpe_skip":
        rpe = None
        rpe_text = "не указана"
    else:
        rpe = float(callback.data.split("_")[-1])
        rpe_text = f"{rpe}/10"
    
    # Обновляем статус на завершено с RPE
    success = await teams_db.update_player_workout_status(
        telegram_id=callback.from_user.id,
        workout_id=workout_id,
        status='completed',
        rpe=rpe
    )
    
    await state.clear()
    
    if success:
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="📋 Мои тренировки", callback_data="my_workouts")
        keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
        keyboard.adjust(1)
        
        await callback.message.edit_text(
            f"🎉 **Тренировка завершена!**\n\n"
            f"✅ Статус: Выполнено\n"
            f"📊 RPE: {rpe_text}\n\n"
            f"Отличная работа! 💪",
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )
        await callback.answer("✅ Тренировка завершена!")
    else:
        await callback.answer("❌ Ошибка", show_alert=True)

def get_player_workouts_router():
    """Экспорт роутера"""
    return player_workouts_router
