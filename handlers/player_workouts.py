# handlers/player_workouts.pymsdb.

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
#from handlers.teams import  teams_db
player_workouts_router = Router(name="player_workouts")
from handlers import teams 
logger.info("Импорт teams_db в player_workouts.py: %s", teams )
from handlers.one_rm import get_user_1rm_for_exercise
from utils.formatters import format_exercise_info

from handlers.one_rm import handle_test1rm_from_workout
from database import db_manager


# ----------  РЕКОРД СКОРОСТИ (лучшее = НАИМЕНЬШЕЕ время) ----------
async def get_user_speed_max(user_id: int, exercise_id: int) -> float | None:
    """Лучший результат скорости = минимальное время среди всех тестов."""
    try:
        async with db_manager.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT MIN(result_seconds) AS best
                FROM user_speed_records
                WHERE user_id = $1 AND exercise_id = $2
            """, user_id, exercise_id)
        return float(row["best"]) if row and row["best"] is not None else None
    except Exception as e:
        logger.error(f"Ошибка в get_user_speed_max: {e}")
        return None

# ----------  РЕКОРД ВЫНОСЛИВОСТИ (лучшее = НАИБОЛЬШЕЕ время) ----------
async def get_user_endurance_max(user_id: int, exercise_id: int) -> float | None:
    """Лучший результат выносливости = максимальное время удержания."""
    try:
        async with db_manager.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT MAX(result_seconds) AS best
                FROM user_endurance_records
                WHERE user_id = $1 AND exercise_id = $2
            """, user_id, exercise_id)
        return float(row["best"]) if row and row["best"] is not None else None
    except Exception:
        return None

#добавляем новый функционал  2 02
# @player_workouts_router.message(Command("myworkouts"))
# @player_workouts_router.callback_query(F.data.in_(["assigned_workouts", "my_workouts"]))
# async def show_my_workouts(update: Message | CallbackQuery, state: FSMContext):
#     """Показать тренировки игрока"""
#     await state.clear()
    
#     if isinstance(update, CallbackQuery):
#         telegram_id = update.from_user.id
#         message = update.message
#         is_callback = True
#     else:
#         telegram_id = update.from_user.id
#         message = update
#         is_callback = False
    
#     # Проверка инициализации teams_db
#     if teams.teams_db is None:
#         logger.error("teams.teams_db не инициализирована в show_my_workouts")
#         text = (
#             "<b>❌ Ошибка</b>\n\n"
#             "База данных недоступна. Попробуйте позже."
#         )
#         keyboard = InlineKeyboardBuilder()
#         keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
        
#         if is_callback:
#             await message.edit_text(text, reply_markup=keyboard.as_markup(), parse_mode="HTML")
#             await update.answer()
#         else:
#             await message.answer(text, reply_markup=keyboard.as_markup(), parse_mode="HTML")
#         return
    
#     # Получаем тренировки игрока
#     try:
#         workouts = await teams.teams_db.get_player_workouts(telegram_id)
#     except Exception as e:
#         logger.error(f"Ошибка при получении тренировок для telegram_id {telegram_id}: {e}", exc_info=True)
#         text = (
#             "<b>❌ Ошибка</b>\n\n"
#             "Не удалось загрузить тренировки. Попробуйте позже."
#         )
#         keyboard = InlineKeyboardBuilder()
#         keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
        
#         if is_callback:
#             await message.edit_text(text, reply_markup=keyboard.as_markup(), parse_mode="HTML")
#             await update.answer()
#         else:
#             await message.answer(text, reply_markup=keyboard.as_markup(), parse_mode="HTML")
#         return
    
#     if not workouts:
#         keyboard = InlineKeyboardBuilder()
#         keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
        
#         text = (
#             "<b>📭 У вас пока нет тренировок</b>\n\n"
#             "Тренер назначит тренировки, и они появятся здесь."
#         )
        
#         if is_callback:
#             await message.edit_text(text, reply_markup=keyboard.as_markup(), parse_mode="HTML")
#             await update.answer()
#         else:
#             await message.answer(text, reply_markup=keyboard.as_markup(), parse_mode="HTML")
#         return
    
#     # Группируем по статусам
#     new_workouts = [w for w in workouts if w['status'] == 'pending']
#     in_progress = [w for w in workouts if w['status'] == 'in_progress']
#     completed = [w for w in workouts if w['status'] == 'completed']
    
#     text = "<b>💪 Мои тренировки</b>\n\n"
    
#     keyboard = InlineKeyboardBuilder()
    
#     # Новые тренировки
#     if new_workouts:
#         text += f"<b>🔴 Новые ({len(new_workouts)}):</b>\n"
#         for w in new_workouts:
#             deadline_text = ""
#             if w['deadline']:
#                 deadline_text = f" ⏰ До {w['deadline'].strftime('%d.%m')}"
            
#             text += f"  • {w['workout_name']} ({w['team_name']}){deadline_text}\n"
#             keyboard.button(
#                 text=f"💪 {w['workout_name']}",
#                 callback_data=f"start_workout_{w['workout_id']}"
#             )
#         text += "\n"
    
#     # В процессе
#     if in_progress:
#         text += f"<b>⏳ В процессе ({len(in_progress)}):</b>\n"
#         for w in in_progress:
#             text += f"  • {w['workout_name']} ({w['team_name']})\n"
#             keyboard.button(
#                 text=f"▶️ Продолжить: {w['workout_name']}",
#                 callback_data=f"continue_workout_{w['workout_id']}"
#             )
#         text += "\n"
    
#     # Выполненные (последние 5)
#     if completed:
#         text += f"<b>✅ Выполнено ({len(completed)}):</b>\n"
#         for w in completed[:5]:
#             rpe_text = f" (RPE: {w['rpe']:.1f})" if w['rpe'] else ""
#             completed_date = w['completed_at'].strftime('%d.%m') if w['completed_at'] else ""
#             text += f"  • {w['workout_name']}{rpe_text} - {completed_date}\n"
    
#     keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
#     keyboard.adjust(1)
    
#     if is_callback:
#         await message.edit_text(text, reply_markup=keyboard.as_markup(), parse_mode="HTML")
#         await update.answer()
#     else:
#         await message.answer(text, reply_markup=keyboard.as_markup(), parse_mode="HTML")

@player_workouts_router.message(Command("myworkouts"))
@player_workouts_router.callback_query(F.data.in_(["assigned_workouts", "my_workouts"]))
async def show_my_workouts(update: Message | CallbackQuery, state: FSMContext):
    """Показать АКТИВНЫЕ тренировки игрока (без выполненных)"""
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
    
    # Получаем только АКТИВНЫЕ тренировки (не archived/completed)
    try:
        workouts = await teams.teams_db.get_player_workouts(telegram_id)
    except Exception as e:
        logger.error(f"Ошибка при получении тренировок: {e}", exc_info=True)
        text = "<b>❌ Ошибка</b>\n\nНе удалось загрузить тренировки."
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
        
        if is_callback:
            await message.edit_text(text, reply_markup=keyboard.as_markup(), parse_mode="HTML")
            await update.answer()
        else:
            await message.answer(text, reply_markup=keyboard.as_markup(), parse_mode="HTML")
        return
    
    # Фильтруем только активные (pending, in_progress) — completed/archived убираем
    active_workouts = [w for w in workouts if w['status'] in ['pending', 'in_progress']]
    
    # Группируем
    new_workouts = [w for w in active_workouts if w['status'] == 'pending']
    in_progress = [w for w in active_workouts if w['status'] == 'in_progress']
    
    # Формируем текст
    text = "<b>💪 Мои тренировки</b>\n\n"
    keyboard = InlineKeyboardBuilder()
    
    if not active_workouts:
        text += "📭 У вас пока нет активных тренировок.\n\nТренер назначит новые."
        keyboard.button(text="📜 История тренировок", callback_data="workout_history")
        keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
        keyboard.adjust(1)
        
        if is_callback:
            await message.edit_text(text, reply_markup=keyboard.as_markup(), parse_mode="HTML")
            await update.answer()
        else:
            await message.answer(text, reply_markup=keyboard.as_markup(), parse_mode="HTML")
        return
    
    # Новые тренировки
    if new_workouts:
        text += f"<b>🔴 Новые ({len(new_workouts)}):</b>\n"
        for w in new_workouts:
            deadline_text = ""
            if w['deadline']:
                deadline_text = f" ⏰ До {w['deadline'].strftime('%d.%m')}"
            text += f"  • {w['workout_name']}{deadline_text}\n"
            keyboard.button(
                text=f"💪 {w['workout_name']}",
                callback_data=f"start_workout_{w['workout_id']}"
            )
        text += "\n"
    
    # В процессе
    if in_progress:
        text += f"<b>⏳ В процессе ({len(in_progress)}):</b>\n"
        for w in in_progress:
            text += f"  • {w['workout_name']}\n"
            keyboard.button(
                text=f"▶️ Продолжить: {w['workout_name']}",
                callback_data=f"continue_workout_{w['workout_id']}"
            )
        text += "\n"
    
    # Кнопки внизу
    keyboard.button(text="📜 История тренировок", callback_data="workout_history")
    keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
    keyboard.adjust(1)
    
    if is_callback:
        await message.edit_text(text, reply_markup=keyboard.as_markup(), parse_mode="HTML")
        await update.answer()
    else:
        await message.answer(text, reply_markup=keyboard.as_markup(), parse_mode="HTML")


@player_workouts_router.callback_query(F.data.startswith("start_workout_"))
async def start_workout(callback: CallbackQuery, state: FSMContext):
    try:
        workout_id = int(callback.data.split("_")[-1])
        user_tg_id = callback.from_user.id

        user = await db_manager.get_user_by_telegram_id(user_tg_id)
        if not user:
            await callback.answer("Пользователь не найден", show_alert=True)
            return

        is_trainer = user['role'] in ['admin', 'trainer', 'coach']

        # --------------------- ДЛЯ ТРЕНЕРА — ПРОПУСКАЕМ ВСЁ, СРАЗУ ПУСКАЕМ ---------------------
        if is_trainer:
            # Тренер может запускать любую тренировку — просто создаём сессию
            async with db_manager.pool.acquire() as conn:
                workout = await conn.fetchrow("SELECT name FROM workouts WHERE id = $1", workout_id)
                if not workout:
                    await callback.answer("Тренировка не найдена", show_alert=True)
                    return

                # Создаём сессию для тренера (если ещё нет)
                session = await conn.fetchrow("""
                    SELECT id FROM workout_sessions 
                    WHERE user_id = $1 AND workout_id = $2
                """, user['id'], workout_id)

                if not session:
                    await conn.execute("""
                        INSERT INTO workout_sessions (user_id, workout_id, status, started_at)
                        VALUES ($1, $2, 'in_progress', NOW())
                    """, user['id'], workout_id)

            # Сразу открываем новое меню
            await show_workout_overview(callback, state, workout_id)
            await callback.answer("Тренировка начата (режим тренера)")
            return

        # --------------------- ДЛЯ ПОДОПЕЧНОГО — СТАРАЯ ПРОВЕРКА ---------------------
        async with db_manager.pool.acquire() as conn:
            assigned = await conn.fetchrow("""
                SELECT w.name 
                FROM workout_individual_students wis
                JOIN workouts w ON w.id = wis.workout_id
                JOIN individual_students s ON s.id = wis.student_id
                WHERE wis.workout_id = $1 AND s.telegram_id = $2 AND wis.is_active = TRUE
            """, workout_id, user_tg_id)

            # 2. Командное назначение (если не нашли индивидуальное)
            if not assigned:
                assigned = await conn.fetchrow("""
                    SELECT w.name
                    FROM workout_team_player_assignments wpa
                    JOIN workout_teams wt ON wt.id = wpa.workout_team_id
                    JOIN team_players tp ON tp.id = wpa.team_player_id
                    JOIN workouts w ON w.id = wt.workout_id
                    WHERE wt.workout_id = $1
                    AND tp.telegram_id = $2
                    AND wpa.status = 'pending'
                    AND wt.is_active = TRUE
                """, workout_id, user_tg_id)


              # ❗ Если не найдено НИЧЕГО — выходим
            if not assigned:
                await callback.answer("Эта тренировка вам не назначена", show_alert=True)
                return   

        # Обновляем статус через твой метод (для подопечных)
        success = await teams.teams_db.update_player_workout_status(
            telegram_id=user_tg_id,
            workout_id=workout_id,
            status='in_progress'
        )

        if not success:
            await callback.answer("Не удалось начать тренировку", show_alert=True)
            return

        await show_workout_overview(callback, state, workout_id)
        await callback.answer("Тренировка начата!")

    except Exception as e:
        logger.exception(f"Ошибка в start_workout: {e}")
        await callback.answer("Ошибка", show_alert=True)


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
    """Обработать оценку RPE и архивировать тренировку"""
    data = await state.get_data()
    workout_id = data.get('workout_id')
    
    if callback.data == "rpe_skip":
        rpe = None
        rpe_text = "не указана"
    else:
        rpe = float(callback.data.split("_")[-1])
        rpe_text = f"{rpe}/10"
    
    # Обновляем RPE в сессии
    async with db_manager.pool.acquire() as conn:
        await conn.execute("""
            UPDATE workout_sessions 
            SET rpe = $1, 
                status = 'completed',
                completed_at = NOW()
            WHERE user_id = (SELECT id FROM users WHERE telegram_id = $2)
              AND workout_id = $3
              AND status = 'in_progress'
        """, rpe, callback.from_user.id, workout_id)
    
    # Архивируем назначение (убираем из активных)
    success = await teams.teams_db.update_player_workout_status(
        telegram_id=callback.from_user.id,
        workout_id=workout_id,
        status='archived',
        rpe=rpe
    )
    
    await state.clear()
    
    if success:
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="📜 История тренировок", callback_data="workout_history")
        keyboard.button(text="💪 Мои тренировки", callback_data="assigned_workouts")
        keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
        keyboard.adjust(1)
        
        await callback.message.edit_text(
            f"🎉 <b>Тренировка завершена!</b>\n\n"
            f"✅ Статус: Выполнено\n"
            f"📊 RPE: {rpe_text}\n\n"
            f"Тренировка перемещена в историю.\n"
            f"Тренер может назначить её снова.",
            reply_markup=keyboard.as_markup(),
            parse_mode="HTML"
        )
        await callback.answer("✅ Сохранено в историю!")
    else:
        await callback.answer("❌ Ошибка сохранения", show_alert=True)



# @player_workouts_router.callback_query(F.data == "my_workouts")
# async def my_workouts(callback: CallbackQuery):
#     """Показать назначенные подопечному тренировки"""
#     try:
#         logger.info(f"=== my_workouts START user {callback.from_user.id} ===")
        
#         # ЛОГИРОВАНИЕ 1: Получение юзера
#         user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
#         logger.info(f"✓ User found: {user}")
        
#         if not user:
#             logger.error(f"✗ User NOT found for telegram_id {callback.from_user.id}")
#             await callback.answer("❌ Пользователь не найден", show_alert=True)
#             return
        
#         logger.info(f"✓ User ID: {user.get('id')}")
#         user_id = user['id']
        
#         # ЛОГИРОВАНИЕ 2: Подключение к БД
#         async with db_manager.pool.acquire() as conn:
#             logger.info("✓ DB connection acquired")
            
#             # Сначала найти student_id по user_id (или telegram_id)
#             student = await conn.fetchrow(
#                 """
#                 SELECT id FROM individual_students 
#                 WHERE telegram_id = $1 AND is_active = TRUE
#                 """,
#                 callback.from_user.id
#             )
            
#             if not student:
#                 logger.info(f"⚠️ No individual_student found for telegram_id {callback.from_user.id}")
#                 text = ("🏋️ **Мои тренировки**\n\n"
#                         "У вас пока нет назначенных тренировок.\n\n"
#                         "Обратитесь к тренеру для назначения тренировки!")
#                 keyboard = InlineKeyboardBuilder()
#                 keyboard.button(text="🔙 Главное меню", callback_data="mainmenu")
                
#                 await callback.message.edit_text(
#                     text,
#                     reply_markup=keyboard.as_markup(),
#                     parse_mode="Markdown"
#                 )
#                 return
            
#             student_id = student['id']
#             logger.info(f"✓ Student ID: {student_id}")
            
#             # ЛОГИРОВАНИЕ 3: Запрос НАЗНАЧЕННЫХ тренировок
#             workouts = await conn.fetch(
#                 """
#                 SELECT 
#                     w.id,
#                     w.name,
#                     w.description,
#                     w.unique_id,
#                     w.created_at,
#                     COUNT(we.id) as exercise_count,
#                     wis.assigned_at,
#                     wis.deadline
#                 FROM workouts w
#                 LEFT JOIN workout_exercises we ON w.id = we.workout_id
#                 INNER JOIN workout_individual_students wis ON w.id = wis.workout_id
#                 WHERE wis.student_id = $1
#                 AND wis.is_active = TRUE
#                 AND w.is_active = TRUE
#                 GROUP BY w.id, wis.id
#                 ORDER BY wis.assigned_at DESC
#                 LIMIT 10
#                 """,
#                 student_id
#             )
            
#             logger.info(f"✓ Query executed, found: {len(workouts) if workouts else 0} workouts")
            
#             if workouts:
#                 logger.info(f"✓ First workout keys: {list(workouts[0].keys())}")
                
#                 text = f"💪 **Мои назначенные тренировки ({len(workouts)}):**\n\n"
#                 keyboard = InlineKeyboardBuilder()
                
#                 for i, workout in enumerate(workouts):
#                     logger.info(f"✓ Processing workout {i}: {workout.get('name')}")
                    
#                     exercise_count = workout['exercise_count'] or 0
#                     deadline = workout.get('deadline')
#                     deadline_text = f"⏰ {deadline.strftime('%d.%m')}" if deadline else ""
                    
#                     button_text = f"📋 {workout['name']}"
#                     if exercise_count > 0:
#                         button_text += f" ({exercise_count} упр.)"
                    
#                     keyboard.button(
#                         text=button_text,
#                         callback_data=f"view_workout_{workout['id']}"
#                     )
                    
#                     text += f"**{workout['name']}**\n"
#                     text += f"📋 Упражнений: {exercise_count}\n"
#                     if deadline_text:
#                         text += f"{deadline_text}\n"
#                     text += f"🆔 Код: `{workout['unique_id']}`\n\n"
                
#                 keyboard.adjust(1)
#                 keyboard.button(text="🔙 Главное меню", callback_data="mainmenu")
                
#                 logger.info("✓ About to edit message")
#             else:
#                 logger.info("⚠️ No assigned workouts found")
#                 text = ("💪 **Мои тренировки**\n\n"
#                         "У вас пока нет назначенных тренировок.\n\n"
#                         "Обратитесь к тренеру для назначения тренировки!")
#                 keyboard = InlineKeyboardBuilder()
#                 keyboard.button(text="🔙 Главное меню", callback_data="mainmenu")
            
#             logger.info("✓ Editing message...")
#             await callback.message.edit_text(
#                 text,
#                 reply_markup=keyboard.as_markup(),
#                 parse_mode="Markdown"
#             )
#             logger.info("✓ Message edited successfully")
            
#             await callback.answer()
#             logger.info("=== my_workouts END (SUCCESS) ===")
            
#     except Exception as e:
#         logger.error(f"=== ERROR in my_workouts ===", exc_info=True)
#         logger.error(f"Error type: {type(e).__name__}")
#         logger.error(f"Error message: {str(e)}")
#         import traceback
#         logger.error(f"Traceback:\n{traceback.format_exc()}")
        
#         await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)






# ===================================================================
# КРАСИВАЯ ТРЕНИРОВКА 2025: блоки + %1ПМ с весом + галочки + прогресс-бар
# ===================================================================

def get_block_emoji(name: str) -> str:
    n = name.lower()
    if any(x in n for x in ["разминка", "warm"]):    return "🔥 Разминка"
    if any(x in n for x in ["заминка", "cool"]):     return "🧘 Заминка" 
    if any(x in n for x in ["пнс", "ns", "нервн"]):  return "⚡ Подготовка НС"
    if "основн" in n or "main" in n:                 return "💪 Основная часть"
    return "🏋️ Тренировка"

async def get_or_create_session(user_id: int, workout_id: int) -> int:
    """Возвращает session_id. Создаёт, если нет."""
    async with db_manager.pool.acquire() as conn:
        sess = await conn.fetchrow("""
            SELECT id FROM workout_sessions WHERE user_id = $1 AND workout_id = $2
        """, user_id, workout_id)
        if sess:
            # После редактирования состава тренировки строки прогресса могут
            # остаться без workout_exercise_id (мы отвязываем их от удалённых
            # строк workout_exercises). Перепривязываем/дополняем по актуальному составу.
            stale = await conn.fetchval("""
                SELECT COUNT(*) FROM workout_session_exercises
                WHERE session_id = $1 AND workout_exercise_id IS NULL
            """, sess['id'])
            if stale:
                await conn.execute("""
                    DELETE FROM workout_session_exercises
                    WHERE session_id = $1 AND workout_exercise_id IS NULL
                """, sess['id'])
                await fill_session_exercises_from_blocks(sess['id'], workout_id)
            return sess['id']
        
        new_id = await conn.fetchval("""
            INSERT INTO workout_sessions (user_id, workout_id, status, started_at)
            VALUES ($1, $2, 'in_progress', NOW()) RETURNING id
        """, user_id, workout_id)
        
        await fill_session_exercises_from_blocks(new_id, workout_id)
        return new_id

async def fill_session_exercises_from_blocks(session_id: int, workout_id: int):
    async with db_manager.pool.acquire() as conn:
        exercises = await conn.fetch("""
            SELECT 
                we.id          AS block_ex_id,
                we.exercise_id,
                COALESCE(we.sets, 1) AS sets_total
            FROM workout_exercises we
            WHERE we.workout_id = $1
            ORDER BY we.phase, we.order_in_phase
        """, workout_id)

        async with conn.transaction():
            for ex in exercises:
                await conn.execute("""
                    INSERT INTO workout_session_exercises 
                    (session_id, workout_exercise_id, exercise_id, sets_total, status)
                    VALUES ($1, $2, $3, $4, 'pending')
                    ON CONFLICT DO NOTHING
                """,
                    session_id,
                    ex["block_ex_id"],
                    ex["exercise_id"],
                    ex["sets_total"],
                )

async def get_session_progress(session_id: int) -> tuple[int, int, int]:
    async with db_manager.pool.acquire() as conn:
        r = await conn.fetchrow("""
            SELECT 
                COALESCE(SUM(COALESCE(sets_completed, 0)), 0) AS done_sets,
                COALESCE(SUM(COALESCE(sets_total, 1)), 0) AS total_sets
            FROM workout_session_exercises
            WHERE session_id = $1
        """, session_id)

        done = r['done_sets']
        total = r['total_sets'] or 1
        percent = int(done / total * 100)
        return done, total, percent


async def is_exercise_completed(session_id: int, block_ex_id: int) -> bool:
    async with db_manager.pool.acquire() as conn:
        r = await conn.fetchrow("""
            SELECT sets_completed, sets_total 
            FROM workout_session_exercises 
            WHERE session_id = $1 AND workout_exercise_id = $2
        """, session_id, block_ex_id)
        return r and r['sets_completed'] >= r['sets_total']

async def mark_exercise_completed(session_id: int, block_ex_id: int):
    async with db_manager.pool.acquire() as conn:
        await conn.execute("""
            UPDATE workout_session_exercises
            SET sets_completed = sets_total, 
                completed_at = NOW(), 
                status = 'completed'
            WHERE session_id = $1 AND workout_exercise_id = $2
        """, session_id, block_ex_id)

async def get_user_quantity_max(user_id: int, exercise_id: int) -> int | None:
    """Возвращает максимальное количество повторений из теста quantity"""
    try:
        async with db_manager.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT max_reps
                FROM user_tests
                WHERE user_id = $1 AND exercise_id = $2 AND test_type = 'quantity'
                ORDER BY tested_at DESC
                LIMIT 1
            """, user_id, exercise_id)
        return int(row["max_reps"]) if row else None
    except Exception as e:
        logger.error(f"Ошибка в get_user_quantity_max: {e}")
        return None

async def show_workout_overview(
    cb_or_msg: CallbackQuery | Message,
    state: FSMContext,
    workout_id: int
):
    """Максимально красивая карточка тренировки с разделителями-блоками и персональными расчётами."""
    try:
        message = cb_or_msg.message if isinstance(cb_or_msg, CallbackQuery) else cb_or_msg

        user_tg_id = cb_or_msg.from_user.id
        user       = await db_manager.get_user_by_telegram_id(user_tg_id)
        if not user:
            await message.answer("❗ Пользователь не найден")
            return
        user_id, role = user["id"], user.get("role", "player")
        is_trainer    = role in ["admin", "trainer", "coach"]

        # сессия + прогресс
        session_id = await get_or_create_session(user_id, workout_id)
        await state.update_data(current_session_id=session_id, current_workout_id=workout_id)

        # данные тренировки
        async with db_manager.pool.acquire() as conn:
            workout = await conn.fetchrow("""
                SELECT w.*, u.first_name || ' ' || u.last_name AS author_name
                FROM workouts w
                LEFT JOIN users u ON u.id = w.created_by
                WHERE w.id = $1
            """, workout_id)

            if not workout:
                await message.answer("❗ Тренировка не найдена")
                return

            exercises = await conn.fetch("""
                SELECT 
                    we.id            AS workout_exercise_id,
                    we.exercise_id,
                    we.phase,
                    we.sets, we.reps_min, we.reps_max,
                    we.one_rm_percent, we.rest_seconds,
                    we.notes,
                    e.name           AS exercise_name,
                    e.test_type
                FROM workout_exercises we
                LEFT JOIN exercises e ON e.id = we.exercise_id
                WHERE we.workout_id = $1
                ORDER BY we.phase, we.order_in_phase
            """, workout_id)

        # группировка по фазам
        from collections import defaultdict
        blocks = defaultdict(list)
        for ex in exercises:
            blocks[ex["phase"]].append(ex)

        # прогресс
        done_sets, total_sets, percent = await get_session_progress(session_id)

        # ==========  ШАПКА  ==========
        lines = [f"🏋️‍♂️ <b>{workout['name']}</b>"]
        if workout.get("description"):
            lines.append(f"<i>{workout['description']}</i>")
        lines.append(f"👤 Автор: {workout.get('author_name', 'Тренера')}")

        if total_sets:
            bar = "🟩" * (percent // 10) + "⬜" * (10 - percent // 10)
            lines.append(f"{bar}  <b>{done_sets}/{total_sets}</b> подходов · {percent}%")
        if is_trainer:
            lines.append("🔧 <i>Режим тренера</i>")

        text = "\n".join(lines)
        kb   = InlineKeyboardBuilder()

        # ==========  БЛОКИ  ==========
        phase_names = {
            "warmup":      "🔥 РАЗМИНКА",
            "nervousprep": "⚡ ПОДГОТОВКА НС",
            "main":        "💪 ОСНОВНАЯ ЧАСТЬ",
            "cooldown":    "🧘 ЗАМИНКА"
        }

        def center(txt: str, w: int = 32) -> str:
            return txt.center(w)[:w]

        phase_order = ["warmup", "nervousprep", "main", "cooldown"]
        for phase in phase_order:
            phase_exercises = blocks.get(phase)
            if not phase_exercises:
                continue

            # разделитель-блок
            divider = center(f"〰️ {phase_names.get(phase, phase.title())} 〰️")
            kb.button(text=divider, callback_data=f"ignore_block_{phase}")

            # упражнения
            for ex in phase_exercises:
                block_ex_id = ex["workout_exercise_id"]
                display_name = ex["exercise_name"] or ex["notes"] or "Упражнение"
                if len(display_name) > 25:
                    display_name = display_name[:22] + "..."

                params = ""
                if ex["sets"]:
                    reps = f"{ex['reps_min']}" if ex["reps_min"] else ""
                    if ex["reps_max"] and ex["reps_max"] != ex["reps_min"]:
                        reps += f"-{ex['reps_max']}"
                    params = f" {ex['sets']}×{reps}".strip()

                # === персональный % (вес или время) — используем RAW время для скорости ===
                if ex["one_rm_percent"] is not None:
                    percent = float(ex["one_rm_percent"])

                    if ex["test_type"] == "speed":
                        # лучшее = минимальное время среди всех тестов
                        best_raw = None
                        if ex["exercise_id"]:
                            best_raw = await get_user_speed_max(user_id, ex["exercise_id"])

                        if best_raw:
                            target = best_raw * (100 / percent)
                            params += f"  @{percent:.0f}% (≈{target:.2f} с)"
                        else:
                            params += f"  @{percent:.0f}% (тест не пройден)"

                    elif ex["test_type"] == "endurance":
                        best = await get_user_endurance_max(user_id, ex["exercise_id"])
                        if best:
                            target = best * (percent / 100)
                            params += f"  @{percent:.0f}% (≈{target:.1f} с)"
                        else:
                            params += f"  @{percent:.0f}% (тест не пройден)"

                    elif ex["test_type"] == "quantity":
                        best = await get_user_quantity_max(user_id, ex["exercise_id"])
                        if best:
                            target = round(best * (percent / 100))
                            params += f"  @{percent:.0f}% (≈{target} раз)"
                        else:
                            params += f"  @{percent:.0f}% (тест не пройден)"

                    else:
                        # Силовое (strength или всё остальное)
                        orm = await get_user_1rm_for_exercise(user_id, ex["exercise_id"])
                        if orm:
                            weight = round(orm * percent / 100, 1)
                            params += f"  @{percent:.0f}% (≈{weight} кг)"
                        else:
                            params += f"  @{percent:.0f}% (тест не пройден)"

                if ex["rest_seconds"]:
                    params += f"  отд.{ex['rest_seconds']}с"

                raw_text = f"{display_name}{params}"
                btn_text = raw_text.ljust(32)[:32]
                kb.button(
                    text=btn_text[:64],
                    callback_data=f"exdet_{ex['exercise_id'] or 0}_{workout_id}_{session_id}_{block_ex_id}"
                )

        # ==========  НИЖНИЕ КНОПКИ  ==========
        kb.button(text="🏁 Завершить", callback_data=f"finish_workout_{workout_id}")
        kb.button(text="📋 Мои тренировки", callback_data="my_workouts")
        kb.button(text="🏠 Главное меню", callback_data="main_menu")
        kb.adjust(1)

        # отправка
        if isinstance(cb_or_msg, CallbackQuery):
            await message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="HTML")
            await cb_or_msg.answer()
        else:
            await message.answer(text, reply_markup=kb.as_markup(), parse_mode="HTML")

    except Exception as e:
        logger.exception("❗ show_workout_overview error: %s", e)
        await (cb_or_msg.answer if isinstance(cb_or_msg, CallbackQuery) else message.answer)(
            "❗ Ошибка загрузки тренировки", show_alert=True
        )

        # ==========  НИЖНИЕ КНОПКИ  ==========
        kb.button(text="🏁 Завершить", callback_data=f"finish_workout_{workout_id}")
        kb.button(text="📋 Мои тренировки", callback_data="my_workouts")
        kb.button(text="🏠 Главное меню", callback_data="main_menu")
        kb.adjust(1)

        # отправка
        if isinstance(cb_or_msg, CallbackQuery):
            await message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="HTML")
            await cb_or_msg.answer()
        else:
            await message.answer(text, reply_markup=kb.as_markup(), parse_mode="HTML")

    except Exception as e:
        logger.exception("❗ show_workout_overview error: %s", e)
        await (cb_or_msg.answer if isinstance(cb_or_msg, CallbackQuery) else message.answer)(
             "❗ Ошибка загрузки тренировки", show_alert=True)


@player_workouts_router.callback_query(F.data.regexp(r"^back_\d+$"))
async def back_to_workout(callback: CallbackQuery, state: FSMContext):
    """Вернуться из карточки упражнения в меню тренировки"""
    wid = int(callback.data.split("_")[1])
    await show_workout_overview(callback, state, wid)
    await callback.answer()

# ОБРАБОТЧИК ДЛЯ НЕКЛИКАБЕЛЬНЫХ РАЗДЕЛИТЕЛЕЙ
@player_workouts_router.callback_query(F.data.startswith("ignore_block_"))
async def ignore_block_separator(callback: CallbackQuery):
    """Обработчик для некликабельных разделителей блоков"""
    await callback.answer()  # Просто закрываем уведомление, ничего не делаем





#

# @player_workouts_router.callback_query(F.data.startswith("exdet_"))
# async def exercise_detail(callback: CallbackQuery, state: FSMContext):
#     """Красивое окно упражнения: параметры, персональные расчёты, прогресс, возврат."""
#     try:
#         _, ex_id_str, wid_str, sess_id_str, block_ex_id_str = callback.data.split("_")
#         ex_id, wid, sess_id, block_ex_id = map(int, (ex_id_str, wid_str, sess_id_str, block_ex_id_str))

#         user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
#         if not user:
#             await callback.answer("❗ Пользователь не найден", show_alert=True)
#             return
#         user_id = user["id"]

#         # ‑‑‑‑‑‑‑ данные упражнения ‑‑‑‑‑‑‑
#         async with db_manager.pool.acquire() as conn:
#             ex_row = await conn.fetchrow("""
#                 SELECT we.exercise_id, we.sets, we.reps_min, we.reps_max,
#                        we.one_rm_percent, we.rest_seconds, we.notes,
#                        e.name, e.description, e.test_type, e.category
#                 FROM workout_exercises we
#                 LEFT JOIN exercises e ON e.id = we.exercise_id
#                 WHERE we.id = $1
#             """, block_ex_id)

#         if not ex_row:
#             await callback.answer("❗ Упражнение не найдено", show_alert=True)
#             return

#         is_manual = ex_row["exercise_id"] is None
#         name = ex_row["name"] or ex_row["notes"] or "Упражнение"
#         emoji = {"strength": "💪", "speed": "🏃", "endurance": "⏱️"}.get(ex_row["test_type"], "🏋️")

#         # ‑‑‑‑‑‑‑ 1. Шапка ‑‑‑‑‑‑‑
#         lines = [f"{emoji} <b>{name}</b>"]
#         if ex_row["description"]:
#             lines.append(f"<i>{ex_row['description']}</i>")

#         # ‑‑‑‑‑‑‑ 2. Базовые параметры ‑‑‑‑‑‑‑
#         params = []
#         if ex_row["sets"]:
#             reps = f"{ex_row['reps_min']}" if ex_row['reps_min'] else ""
#             if ex_row["reps_max"] and ex_row["reps_max"] != ex_row["reps_min"]:
#                 reps += f"-{ex_row['reps_max']}"
#             params.append(f"{ex_row['sets']}×{reps}".strip())
#         if ex_row["rest_seconds"]:
#             params.append(f"отдых {ex_row['rest_seconds']} с")

#         if params:
#             lines.append(" • ".join(params))

#                 # ‑‑‑‑‑‑‑ 3. Персональные расчёты ‑‑‑‑‑‑‑ (с правильной логикой для speed/endurance)
#         if not is_manual and ex_row["one_rm_percent"] is not None:
#             percent = float(ex_row["one_rm_percent"])  # Decimal → float


#             if ex_row["test_type"] == "speed":
#                 best_func = get_user_speed_max if ex_row["test_type"] == "speed" else get_user_endurance_max
#                 best = await best_func(user_id, ex_row["exercise_id"])
#                 if best:
#                     target = best * (100 / percent)  # Скорость: ниже % → больше секунд (медленнее, правильно!)
#                     lines.append(f"🏃 <b>Цель: {target:.2f} с</b>\n   ({percent:.0f}% интенсивности от рекорда {best:.2f} с)")
#                 else:
#                     lines.append(f"🏃 <b>Цель: {percent:.0f}% интенсивности</b>\n   (пройдите тест)")

#             elif ex_row["test_type"] == "endurance":
#                 best = await get_user_endurance_max(user_id, ex_row["exercise_id"])
#                 if best:
#                     target = best * (percent / 100)  # Выносливость: ниже % → меньше секунд
#                     lines.append(f"⏱️ <b>Цель: {target:.1f} с</b>\n   ({percent:.0f}% интенсивности от рекорда {best:.1f} с)")
#                 else:
#                     lines.append(f"⏱️ <b>Цель: {percent:.0f}% интенсивности</b>\n   (пройдите тест)")

#             else:
#                 # Силовое
#                 orm = await get_user_1rm_for_exercise(user_id, ex_row["exercise_id"])
#                 if orm:
#                     weight = round(orm * percent / 100, 1)
#                     lines.append(f"💪 <b>Ваш вес: {weight} кг</b>\n   ({percent:.0f}% от 1ПМ {orm} кг)")
#                 else:
#                     lines.append(f"💪 <b>Вес: {percent:.0f}% от 1ПМ</b>\n   (тест не пройден)")

#         elif ex_row["test_type"] == "quantity":
#                     best = await get_user_quantity_max(user_id, ex_row["exercise_id"])
#                     if best:
#                         target = round(best * (percent / 100))
#                         lines.append(f"🔢 <b>Цель: {target} повторений</b>\n   ({percent:.0f}% от рекорда {best} раз)")
#                     else:
#                         lines.append(f"🔢 <b>Цель: {percent:.0f}% от максимума</b>\n   (пройдите тест на количество)")



#         # Формируем итоговый текст
#         text = "\n".join(lines)

#         # ‑‑‑‑‑‑‑ 4. Клавиатура ‑‑‑‑‑‑‑
#         completed = await is_exercise_completed(sess_id, block_ex_id)
#         kb = InlineKeyboardBuilder()

#         # основная кнопка
#         kb.button(
#             text=f"{'✅' if completed else '⬜'} Отметить выполненным",
#             callback_data="done" if completed else f"markdone_{sess_id}_{block_ex_id}_{wid}"
#         )

#         # кнопка теста
#         if not is_manual and ex_row["test_type"] and ex_row["test_type"] != "none":
#             if ex_row["test_type"] == "speed":
#                 best = await get_user_speed_max(user_id, ex_row["exercise_id"])
#                 btn_text = f"🏃 Обновить рекорд: {best:.2f} с" if best else "🏃 Пройти тест"
#             elif ex_row["test_type"] == "endurance":
#                 best = await get_user_endurance_max(user_id, ex_row["exercise_id"])
#                 btn_text = f"⏱️ Обновить рекорд: {best:.2f} с" if best else "⏱️ Пройти тест"
#             else:
#                 orm = await get_user_1rm_for_exercise(user_id, ex_row["exercise_id"])
#                 btn_text = f"💪 Обновить 1ПМ: {orm} кг" if orm else "💪 Пройти тест 1ПМ"
#             kb.button(text=btn_text, callback_data=f"test1rm_{ex_row['exercise_id']}_{wid}")

#         kb.button(text="🔙 Назад к тренировке", callback_data=f"back_{wid}")
#         kb.adjust(1)

#         await callback.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="HTML")
#         await callback.answer()

#     except Exception as e:
#         logger.exception("❗ exercise_detail error: %s", e)
#         await callback.answer("Ошибка при загрузке упражнения", show_alert=True)
# Отметить выполненным
@player_workouts_router.callback_query(F.data.startswith("markdone_"))
async def mark_done(callback: CallbackQuery, state: FSMContext):
    _, sess_id, block_ex_id, wid = callback.data.split("_")
    await db_manager.pool.execute("""
        UPDATE workout_session_exercises SET sets_completed = sets_total, completed_at = NOW(), status = 'completed'
        WHERE session_id = $1 AND workout_exercise_id = $2
    """, int(sess_id), int(block_ex_id))
    await callback.answer("Отмечено!", show_alert=True)
    await show_workout_overview(callback, state, int(wid))


# Назад в тренировку
@player_workouts_router.callback_query(F.data == "back_from_exercise")
async def back_from_exercise_details(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    workout_id = data.get("current_workout_id")
    if workout_id:
        await show_workout_overview(callback, state, workout_id)
    else:
        await callback.message.edit_text("Ошибка возврата")
    await callback.answer()

@player_workouts_router.callback_query(F.data.startswith("exdet_"))
async def exercise_detail(callback: CallbackQuery, state: FSMContext):
    """Полная карточка упражнения с описанием, техникой и заметками тренера."""
    try:
        _, ex_id_str, wid_str, sess_id_str, block_ex_id_str = callback.data.split("_")
        ex_id, wid, sess_id, block_ex_id = map(int, (ex_id_str, wid_str, sess_id_str, block_ex_id_str))

        user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer("❗ Пользователь не найден", show_alert=True)
            return
        user_id = user["id"]

        # Получаем ПОЛНЫЕ данные: и из workout_exercises (заметки тренера), и из exercises (описание)
        async with db_manager.pool.acquire() as conn:
            ex_row = await conn.fetchrow("""
                SELECT 
                    we.exercise_id, we.sets, we.reps_min, we.reps_max,
                    we.one_rm_percent, we.rest_seconds, we.notes as trainer_notes,
                    e.name, e.description, e.test_type, e.category,
                    e.instructions, e.video_url, e.muscle_group, 
                    e.equipment, e.difficulty_level,
                    u.first_name as author_name
                FROM workout_exercises we
                LEFT JOIN exercises e ON e.id = we.exercise_id
                LEFT JOIN users u ON e.created_by = u.id
                WHERE we.id = $1
            """, block_ex_id)

        if not ex_row:
            await callback.answer("❗ Упражнение не найдено", show_alert=True)
            return

        is_manual = ex_row["exercise_id"] is None
        name = ex_row["name"] or ex_row["trainer_notes"] or "Упражнение"
        
        # Эмодзи по типу
        emoji_map = {"strength": "🏋️", "speed": "🏃", "endurance": "⏱️", "quantity": "🔢"}
        emoji = emoji_map.get(ex_row["test_type"], "💪")

        lines = []
        
        # 1. Название и категория
        lines.append(f"{emoji} <b>{name}</b>")
        if not is_manual and ex_row["category"]:
            lines.append(f"<i>Категория: {ex_row['category']}</i>")

        # 2. ПОЛНОЕ ОПИСАНИЕ из карточки упражнения (как в exercises.py)
        if ex_row["description"]:
            lines.append(f"\n📝 <b>Описание:</b>\n{ex_row['description']}")
        
        if ex_row["instructions"]:
            lines.append(f"\n⚙️ <b>Техника выполнения:</b>\n{ex_row['instructions']}")
        
        if ex_row["muscle_group"]:
            lines.append(f"\n💪 <b>Группа мышц:</b> {ex_row['muscle_group']}")
            
        if ex_row["equipment"] and ex_row["equipment"] != "Собственный вес":
            lines.append(f"🛠 <b>Оборудование:</b> {ex_row['equipment']}")

        # 3. ЗАМЕТКИ ТРЕНЕРА (специфичны именно для этой тренировки!)
        if ex_row["trainer_notes"]:
            lines.append(f"\n💡 <b>Указания тренера для этой тренировки:</b>\n<i>{ex_row['trainer_notes']}</i>")

        # 4. Параметры тренировки (sets/reps)
        params = []
        if ex_row["sets"]:
            reps = f"{ex_row['reps_min']}" if ex_row['reps_min'] else ""
            if ex_row["reps_max"] and ex_row["reps_max"] != ex_row["reps_min"]:
                reps += f"-{ex_row['reps_max']}"
            params.append(f"<b>Подходы:</b> {ex_row['sets']}×{reps}".strip())
        if ex_row["rest_seconds"]:
            params.append(f"<b>Отдых:</b> {ex_row['rest_seconds']} сек")

        if params:
            lines.append(f"\n🏋️ <b>Параметры в тренировке:</b>")
            lines.append(" • ".join(params))

        # 5. ПЕРСОНАЛЬНЫЕ РАСЧЁТЫ (сохраняем логику из оригинала)
        if not is_manual and ex_row["one_rm_percent"] is not None:
            percent = float(ex_row["one_rm_percent"])

            if ex_row["test_type"] == "speed":
                best = await get_user_speed_max(user_id, ex_row["exercise_id"])
                if best:
                    target = best * (100 / percent)
                    lines.append(f"\n🏃 <b>Цель по скорости:</b> {target:.2f} сек")
                    lines.append(f"<i>({percent:.0f}% от вашего рекорда {best:.2f} сек)</i>")
                else:
                    lines.append(f"\n🏃 <b>Цель:</b> {percent:.0f}% интенсивности")

            elif ex_row["test_type"] == "endurance":
                best = await get_user_endurance_max(user_id, ex_row["exercise_id"])
                if best:
                    target = best * (percent / 100)
                    lines.append(f"\n⏱️ <b>Цель по времени:</b> {target:.1f} сек")
                    lines.append(f"<i>({percent:.0f}% от вашего рекорда {best:.1f} сек)</i>")
                else:
                    lines.append(f"\n⏱️ <b>Цель:</b> {percent:.0f}% интенсивности")

            elif ex_row["test_type"] == "quantity":
                best = await get_user_quantity_max(user_id, ex_row["exercise_id"])
                if best:
                    target = round(best * (percent / 100))
                    lines.append(f"\n🔢 <b>Цель:</b> {target} повторений")
                    lines.append(f"<i>({percent:.0f}% от вашего максимума {best} раз)</i>")
                else:
                    lines.append(f"\n🔢 <b>Цель:</b> {percent:.0f}% от максимума")

            else:  # strength
                orm = await get_user_1rm_for_exercise(user_id, ex_row["exercise_id"])
                if orm:
                    weight = round(orm * percent / 100, 1)
                    lines.append(f"\n💪 <b>Рабочий вес:</b> {weight} кг")
                    lines.append(f"<i>({percent:.0f}% от 1ПМ {orm} кг)</i>")
                else:
                    lines.append(f"\n💪 <b>Вес:</b> {percent:.0f}% от 1ПМ (тест не пройден)")

        # 6. Дополнительно
        if ex_row["video_url"]:
            lines.append(f"\n🎥 <a href='{ex_row['video_url']}'>Видео-инструкция</a>")
        
        if ex_row["author_name"]:
            lines.append(f"\n👤 <i>Автор упражнения: {ex_row['author_name']}</i>")

        text = "\n".join(lines)

        # Клавиатура
        completed = await is_exercise_completed(sess_id, block_ex_id)
        kb = InlineKeyboardBuilder()

        # Кнопка выполнения
        if completed:
            kb.button(
                text="🟢 Выполнено",
                callback_data=f"back_{wid}"
            )
        else:
            kb.button(
                text="⬜ Отметить выполненным",
                callback_data=f"markdone_{sess_id}_{block_ex_id}_{wid}"
    )


        # Кнопка теста
        if not is_manual and ex_row["test_type"] and ex_row["test_type"] != "none":
            if ex_row["test_type"] == "speed":
                best = await get_user_speed_max(user_id, ex_row["exercise_id"])
                btn_text = f"🏃 Обновить рекорд: {best:.2f} с" if best else "🏃 Пройти тест скорости"
            elif ex_row["test_type"] == "endurance":
                best = await get_user_endurance_max(user_id, ex_row["exercise_id"])
                btn_text = f"⏱️ Обновить рекорд: {best:.1f} с" if best else "⏱️ Пройти тест выносливости"
            elif ex_row["test_type"] == "quantity":
                best = await get_user_quantity_max(user_id, ex_row["exercise_id"])
                btn_text = f"🔢 Обновить рекорд: {best} раз" if best else "🔢 Пройти тест"
            else:
                orm = await get_user_1rm_for_exercise(user_id, ex_row["exercise_id"])
                btn_text = f"💪 Обновить 1ПМ: {orm} кг" if orm else "💪 Пройти тест 1ПМ"
            
            kb.button(text=btn_text, callback_data=f"test1rm_{ex_row['exercise_id']}_{wid}")

        kb.button(text="🔙 Назад к тренировке", callback_data=f"back_{wid}")
        kb.adjust(1)

        await callback.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="HTML")
        await callback.answer()

    except Exception as e:
        logger.exception("❗ exercise_detail error: %s", e)
        await callback.answer("Ошибка при загрузке упражнения", show_alert=True)

# @player_workouts_router.callback_query(F.data.startswith("exdet_"))
# async def exercise_detail(callback: CallbackQuery, state: FSMContext):
#     """Полная карточка упражнения с описанием, техникой и заметками тренера."""
#     try:
#         parts = callback.data.split("_")
#         if len(parts) != 5:
#             logger.error(f"BAD exdet callback: {callback.data}")
#             await callback.answer("⚠️ Устаревшая кнопка. Вернитесь в тренировку.", show_alert=True)
#             return

#         _, ex_id_str, wid_str, sess_id_str, block_ex_id_str = parts
#         ex_id, wid, sess_id, block_ex_id = map(int, (ex_id_str, wid_str, sess_id_str, block_ex_id_str))

#         user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
#         if not user:
#             await callback.answer("❗ Пользователь не найден", show_alert=True)
#             return
#         user_id = user["id"]

#         # --- данные упражнения ---
#         async with db_manager.pool.acquire() as conn:
#             ex_row = await conn.fetchrow("""
#                 SELECT 
#                     we.exercise_id,
#                     we.sets,
#                     we.reps_min,
#                     we.reps_max,
#                     we.one_rm_percent,
#                     we.rest_seconds,
#                     we.notes AS trainer_notes,
#                     e.name,
#                     e.description,
#                     e.test_type,
#                     e.category,
#                     e.instructions,
#                     e.video_url,
#                     e.muscle_group,
#                     e.equipment,
#                     e.difficulty_level,
#                     u.first_name AS author_name
#                 FROM workout_exercises we
#                 LEFT JOIN exercises e ON e.id = we.exercise_id
#                 LEFT JOIN users u ON e.created_by = u.id
#                 WHERE we.id = $1
#             """, block_ex_id)

#         if not ex_row:
#             await callback.answer("❗ Упражнение не найдено", show_alert=True)
#             return

#         is_manual = ex_row["exercise_id"] is None
#         name = ex_row["name"] or ex_row["trainer_notes"] or "Упражнение"

#         emoji_map = {
#             "strength": "🏋️",
#             "speed": "🏃",
#             "endurance": "⏱️",
#             "quantity": "🔢"
#         }
#         emoji = emoji_map.get(ex_row["test_type"], "💪")

#         lines: list[str] = []

#         # 1. Заголовок
#         lines.append(f"{emoji} <b>{name}</b>")
#         if not is_manual and ex_row["category"]:
#             lines.append(f"<i>Категория: {ex_row['category']}</i>")

#         # 2. Описание
#         if ex_row["description"]:
#             lines.append(f"\n📝 <b>Описание:</b>\n{ex_row['description']}")

#         if ex_row["instructions"]:
#             lines.append(f"\n⚙️ <b>Техника выполнения:</b>\n{ex_row['instructions']}")

#         if ex_row["muscle_group"]:
#             lines.append(f"\n💪 <b>Группа мышц:</b> {ex_row['muscle_group']}")

#         if ex_row["equipment"] and ex_row["equipment"] != "Собственный вес":
#             lines.append(f"🛠 <b>Оборудование:</b> {ex_row['equipment']}")

#         # 3. Заметки тренера
#         if ex_row["trainer_notes"]:
#             lines.append(
#                 f"\n💡 <b>Указания тренера:</b>\n<i>{ex_row['trainer_notes']}</i>"
#             )

#         # 4. Параметры тренировки
#         params = []
#         if ex_row["sets"]:
#             reps = f"{ex_row['reps_min']}" if ex_row["reps_min"] else ""
#             if ex_row["reps_max"] and ex_row["reps_max"] != ex_row["reps_min"]:
#                 reps += f"-{ex_row['reps_max']}"
#             params.append(f"<b>Подходы:</b> {ex_row['sets']}×{reps}".strip())

#         if ex_row["rest_seconds"]:
#             params.append(f"<b>Отдых:</b> {ex_row['rest_seconds']} сек")

#         if params:
#             lines.append("\n🏋️ <b>Параметры в тренировке:</b>")
#             lines.append(" • ".join(params))

#         # 5. Персональные расчёты
#         if not is_manual and ex_row["one_rm_percent"] is not None:
#             percent = float(ex_row["one_rm_percent"])

#             if ex_row["test_type"] == "speed":
#                 best = await get_user_speed_max(user_id, ex_row["exercise_id"])
#                 if best:
#                     target = best * (100 / percent)
#                     lines.append(f"\n🏃 <b>Цель:</b> {target:.2f} сек")
#                     lines.append(f"<i>{percent:.0f}% от рекорда {best:.2f} сек</i>")
#                 else:
#                     lines.append(f"\n🏃 <b>Цель:</b> {percent:.0f}% интенсивности")

#             elif ex_row["test_type"] == "endurance":
#                 best = await get_user_endurance_max(user_id, ex_row["exercise_id"])
#                 if best:
#                     target = best * (percent / 100)
#                     lines.append(f"\n⏱ <b>Цель:</b> {target:.1f} сек")
#                     lines.append(f"<i>{percent:.0f}% от рекорда {best:.1f} сек</i>")
#                 else:
#                     lines.append(f"\n⏱ <b>Цель:</b> {percent:.0f}% интенсивности")

#             elif ex_row["test_type"] == "quantity":
#                 best = await get_user_quantity_max(user_id, ex_row["exercise_id"])
#                 if best:
#                     target = round(best * (percent / 100))
#                     lines.append(f"\n🔢 <b>Цель:</b> {target} повторений")
#                     lines.append(f"<i>{percent:.0f}% от максимума {best}</i>")
#                 else:
#                     lines.append(f"\n🔢 <b>Цель:</b> {percent:.0f}% от максимума")

#             else:  # strength
#                 orm = await get_user_1rm_for_exercise(user_id, ex_row["exercise_id"])
#                 if orm:
#                     weight = round(orm * percent / 100, 1)
#                     lines.append(f"\n💪 <b>Рабочий вес:</b> {weight} кг")
#                     lines.append(f"<i>{percent:.0f}% от 1ПМ {orm} кг</i>")
#                 else:
#                     lines.append(f"\n💪 <b>Вес:</b> {percent:.0f}% от 1ПМ")

#         # 6. Дополнительно
#         if ex_row["video_url"]:
#             lines.append(f"\n🎥 <a href='{ex_row['video_url']}'>Видео-инструкция</a>")

#         if ex_row["author_name"]:
#             lines.append(f"\n👤 <i>Автор упражнения: {ex_row['author_name']}</i>")

#         text = "\n".join(lines)

#         # --- КЛАВИАТУРА ---
#         completed = await is_exercise_completed(sess_id, block_ex_id)
#         kb = InlineKeyboardBuilder()

#         if completed:
#             kb.button(text="🟢 Выполнено", callback_data=f"back_{wid}")
#         else:
#             kb.button(
#                 text="⬜ Отметить выполненным",
#                 callback_data=f"markdone_{sess_id}_{block_ex_id}_{wid}"
#             )

#         if not is_manual and ex_row["test_type"] and ex_row["test_type"] != "none":
#             kb.button(
#                 text="🧪 Пройти / обновить тест",
#                 callback_data=f"test1rm_{ex_row['exercise_id']}_{wid}"
#             )

#         kb.button(text="🔙 Назад к тренировке", callback_data=f"back_{wid}")
#         kb.adjust(1)

#         await callback.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="HTML")
#         await callback.answer()

#     except Exception as e:
#         logger.exception("❗ exercise_detail error")
#         await callback.answer("Ошибка при загрузке упражнения", show_alert=True)


# Отменить выполнение упражнения
@player_workouts_router.callback_query(F.data.startswith("markundone_"))
async def mark_undone(callback: CallbackQuery, state: FSMContext):
    """Отменить отметку о выполнении упражнения."""
    try:
        _, sess_id, block_ex_id, wid = callback.data.split("_")
        sess_id = int(sess_id)
        block_ex_id = int(block_ex_id)
        wid = int(wid)
        
        # Обновляем в БД: отменяем выполнение
        await db_manager.pool.execute("""
            UPDATE workout_session_exercises 
            SET sets_completed = 0, 
                completed_at = NULL, 
                status = 'pending'
            WHERE session_id = $1 AND workout_exercise_id = $2
        """, sess_id, block_ex_id)
        
        await callback.answer("✅ Отметка отменена!", show_alert=True)
        
        # Возвращаемся к деталям упражнения
        await exercise_detail(callback, state)
        
    except Exception as e:
        logger.exception("❗ mark_undone error: %s", e)
        await callback.answer("Ошибка при отмене", show_alert=True)


# Отметить выполненным
@player_workouts_router.callback_query(F.data.startswith("markdone_"))
async def mark_done(callback: CallbackQuery, state: FSMContext):
    """Отметить упражнение как выполненное."""
    try:
        _, sess_id, block_ex_id, wid = callback.data.split("_")
        sess_id = int(sess_id)
        block_ex_id = int(block_ex_id)
        wid = int(wid)
        
        # Получаем количество подходов для этого упражнения
        async with db_manager.pool.acquire() as conn:
            result = await conn.fetchval("""
                SELECT we.sets 
                FROM workout_exercises we
                WHERE we.id = $1
            """, block_ex_id)
        
        sets_count = result or 1
        
        # Обновляем в БД
        await db_manager.pool.execute("""
            UPDATE workout_session_exercises 
            SET sets_completed = $1, 
                completed_at = NOW(), 
                status = 'completed'
            WHERE session_id = $2 AND workout_exercise_id = $3
        """, sets_count, sess_id, block_ex_id)
        
        await callback.answer("✅ Упражнение отмечено как выполненное!", show_alert=True)
        
        # Возвращаемся к деталям упражнения
        await exercise_detail(callback, state)
        
    except Exception as e:
        logger.exception("❗ mark_done error: %s", e)
        await callback.answer("Ошибка при отметке", show_alert=True)


# ==============================================================
# СТАРТ ТРЕНИРОВКИ (РАБОТАЕТ ДЛЯ ВСЕХ)
# ==============================================================

@player_workouts_router.callback_query(F.data.startswith("start_workout_"))
async def start_workout(callback: CallbackQuery, state: FSMContext):
    """Начать тренировку. Работает для тренеров, индивидуальных подопечных и игроков команд."""
    try:
        workout_id = int(callback.data.split("_")[-1])
        user_tg_id = callback.from_user.id

        logger.info(f"Старт тренировки {workout_id} пользователем {user_tg_id}")



            # ---------- отладочный блок ----------
        async with db_manager.pool.acquire() as conn:
            dbg_team = await conn.fetchrow("""
                SELECT wpa.id AS assign_id,
                    wpa.status,
                    tp.telegram_id,
                    wt.workout_id
                FROM workout_team_player_assignments wpa
                JOIN workout_teams wt ON wt.id = wpa.workout_team_id
                JOIN team_players tp ON tp.id = wpa.team_player_id
                WHERE wt.workout_id = $1
                AND tp.telegram_id = $2
            """, workout_id, user_tg_id)
            logger.info("DBG team assign: %s", dict(dbg_team) if dbg_team else "NO TEAM ROW")
        # ---------- конец отладки ----------


        user = await db_manager.get_user_by_telegram_id(user_tg_id)
        if not user:
            await callback.answer("Пользователь не найден", show_alert=True)
            return

        user_role = user.get('role', 'player')
        is_trainer = user_role in ['admin', 'trainer', 'coach']

        can_start = False
        workout_name = "Тренировка"

        async with db_manager.pool.acquire() as conn:
            # ТРЕНЕРУ разрешаем запустить любую тренировку (режим теста)
            if is_trainer:
                row = await conn.fetchrow(
                    "SELECT name FROM workouts WHERE id = $1", workout_id
                )
                if row:
                    can_start = True
                    workout_name = row['name']
            else:
                # 1. Индивидуальное назначение
                row = await conn.fetchrow("""
                    SELECT w.name
                    FROM workout_individual_students wis
                    JOIN workouts w ON w.id = wis.workout_id
                    JOIN individual_students s ON s.id = wis.student_id
                    WHERE wis.workout_id = $1
                      AND s.telegram_id = $2
                      AND wis.is_active = TRUE
                """, workout_id, user_tg_id)

                # 2. Командное назначение (если не нашли индивидуальное)
                if not row:
                    row = await conn.fetchrow("""
                        SELECT w.name
                        FROM workout_team_player_assignments wpa
                        JOIN workout_teams wt ON wt.id = wpa.workout_team_id
                        JOIN team_players tp ON tp.id = wpa.team_player_id
                        JOIN workouts w ON w.id = wt.workout_id
                        WHERE wt.workout_id = $1
                          AND tp.telegram_id = $2
                          AND wpa.status = 'pending'
                          AND wt.is_active = TRUE
                    """, workout_id, user_tg_id)

                if row:
                    can_start = True
                    workout_name = row['name']

        if not can_start:
            logger.info(
                f"Отказ: workout_id={workout_id}, user_tg_id={user_tg_id}, is_trainer={is_trainer}"
            )
            await callback.answer("Эта тренировка вам не назначена", show_alert=True)
            return

        # Обновляем статус назначения на «в процессе»
        success = await teams.teams_db.update_player_workout_status(
            telegram_id=user_tg_id,
            workout_id=workout_id,
            status='in_progress'
        )
        if not success:
            logger.error(
                f"Не удалось обновить статус тренировки {workout_id} для {user_tg_id}"
            )
            await callback.answer("Не удалось начать тренировку", show_alert=True)
            return

        # Переходим в меню самой тренировки
        await show_workout_overview(callback, state, workout_id)
        await callback.answer("Тренировка начата!")

    except Exception as e:
        logger.exception(f"Критическая ошибка в start_workout: {e}")
        await callback.answer("Ошибка при старте тренировки", show_alert=True)


@player_workouts_router.callback_query(F.data == "my_team")
async def player_my_team(callback: CallbackQuery):
    user_tg_id = callback.from_user.id

    async with db_manager.pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT t.id, t.name, t.description, t.sport_type, t.max_players, t.access_code
            FROM teams t
            JOIN team_players tp ON tp.team_id = t.id
            WHERE tp.telegram_id = $1 AND tp.is_active = TRUE
            LIMIT 1
        """, user_tg_id)

        if not row:
            await callback.answer("Вы не состоите ни в одной команде", show_alert=True)
            return

        kb = InlineKeyboardBuilder()
        kb.button(text="📋 Тренировки команды", callback_data=f"team_workouts_player_{row['id']}")
        kb.button(text="🔙 Главное меню", callback_data="main_menu")
        kb.adjust(1)

        text = (
            f"🏆 **{row['name']}**\n"
            f"📝 {row['description'] or 'Без описания'}\n"
            f"🏃 Вид спорта: {row['sport_type']}\n"
            f"👥 Игроков: до {row['max_players']}\n"
            f"🆔 Код: `{row['access_code']}`"
        )
        await callback.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="Markdown")
        await callback.answer()



@player_workouts_router.callback_query(F.data.startswith("team_workouts_player_"))
async def show_team_workouts_player(callback: CallbackQuery):
    team_id = int(callback.data.split("_")[-1])
    user_tg_id = callback.from_user.id

    # Получаем информацию о пользователе для проверки роли
    user = await db_manager.get_user_by_telegram_id(user_tg_id)
    if not user:
        await callback.answer("Пользователь не найден", show_alert=True)
        return

    is_trainer = user.get('role') in ['admin', 'trainer', 'coach']

    async with db_manager.pool.acquire() as conn:
        workouts = await conn.fetch("""
            SELECT
                wt.id,
                w.name AS workout_name,
                w.description,
                w.difficulty_level,
                w.estimated_duration_minutes,
                wt.assigned_at,
                wt.deadline,
                wt.notes,
                COUNT(wpa.id) FILTER (WHERE wpa.status = 'completed') AS completed,
                COUNT(wpa.id) FILTER (WHERE wpa.status = 'in_progress') AS in_progress,
                COUNT(wpa.id) AS total_players
            FROM workout_teams wt
            JOIN workouts w ON w.id = wt.workout_id
            LEFT JOIN workout_team_player_assignments wpa ON wpa.workout_team_id = wt.id
            JOIN team_players tp ON tp.team_id = wt.team_id AND tp.telegram_id = $2
            WHERE wt.team_id = $1 AND wt.is_active = TRUE
            GROUP BY wt.id, w.name, w.description, w.difficulty_level,
                     w.estimated_duration_minutes, wt.assigned_at,
                     wt.deadline, wt.notes
            ORDER BY wt.assigned_at DESC
        """, team_id, user_tg_id)

    if not workouts:
        await callback.answer("📭 Для вашей команды пока нет тренировок", show_alert=True)
        return

    kb = InlineKeyboardBuilder()
    text = f"📋 **Тренировки вашей команды ({len(workouts)}):**\n\n"

    for w in workouts:
        progress = f"{w['completed']}/{w['total_players']}"
        deadline = w['deadline'].strftime('%d.%m') if w['deadline'] else ''
        text += f"💪 **{w['workout_name']}**\n📊 Выполнили: {progress}\n⏰ До: {deadline}\n\n"
        
        # Игроку сразу кнопка «Начать»
        kb.button(text=f"▶️ {w['workout_name']}", callback_data=f"start_workout_{w['workout_id']}")

    # # Только для тренеров показываем кнопку "Назначить тренировку"
    # if is_trainer:
    #     kb.button(text="➕ Назначить тренировку", callback_data=f"assign_workout_{team_id}")

    kb.button(text="🔙 К команде", callback_data="my_team")
    kb.adjust(1)
    await callback.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="Markdown")
    await callback.answer()




@player_workouts_router.callback_query(F.data.startswith("continue_workout_"))
async def continue_workout(callback: CallbackQuery, state: FSMContext):
    """Продолжить тренировку"""
    try:
        workout_id = int(callback.data.split("_")[-1])
        await show_workout_overview(callback, state, workout_id)
        await callback.answer("Продолжаем! 💪")
    except Exception as e:
        logger.exception(f"❌ Ошибка в continue_workout: {e}")
        await callback.answer("Ошибка", show_alert=True)


@player_workouts_router.callback_query(F.data == "workout_history")
@player_workouts_router.message(Command("history"))
async def show_workout_history(update: Message | CallbackQuery, state: FSMContext):
    """Показать историю выполненных тренировок с RPE"""
    await state.clear()
    
    if isinstance(update, CallbackQuery):
        telegram_id = update.from_user.id
        message = update.message
        is_callback = True
    else:
        telegram_id = update.from_user.id
        message = update
        is_callback = False
    
    try:
        async with db_manager.pool.acquire() as conn:
            # Получаем завершённые тренировки из сессий
            history = await conn.fetch("""
                SELECT 
                    w.name as workout_name,
                    w.id as workout_id,
                    ws.completed_at,
                    ws.rpe,
                    ws.started_at,
                    COUNT(wse.id) FILTER (WHERE wse.status = 'completed') as exercises_done,
                    COUNT(wse.id) as total_exercises
                FROM workout_sessions ws
                JOIN workouts w ON w.id = ws.workout_id
                LEFT JOIN workout_session_exercises wse ON wse.session_id = ws.id
                WHERE ws.user_id = (SELECT id FROM users WHERE telegram_id = $1)
                  AND ws.status = 'completed'
                GROUP BY w.name, w.id, ws.completed_at, ws.rpe, ws.started_at
                ORDER BY ws.completed_at DESC
                LIMIT 20
            """, telegram_id)
    except Exception as e:
        logger.error(f"Ошибка загрузки истории: {e}")
        text = "<b>❌ Ошибка</b>\n\nНе удалось загрузить историю."
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="🔙 Назад", callback_data="my_workouts")
        
        if is_callback:
            await message.edit_text(text, reply_markup=keyboard.as_markup(), parse_mode="HTML")
            await update.answer()
        else:
            await message.answer(text, reply_markup=keyboard.as_markup(), parse_mode="HTML")
        return
    
    text = "<b>📜 История тренировок</b>\n\n"
    keyboard = InlineKeyboardBuilder()
    
    if not history:
        text += "📝 Вы ещё не выполнили ни одной тренировки.\n\n"
        text += "Завершённые тренировки будут появляться здесь."
        keyboard.button(text="💪 Мои тренировки", callback_data="my_workouts")
        keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
        keyboard.adjust(1)
    else:
        text += f"Всего выполнено: <b>{len(history)}</b>\n\n"
        
        for i, h in enumerate(history[:10]):  # Показываем последние 10
            date_str = h['completed_at'].strftime('%d.%m.%Y') if h['completed_at'] else '—'
            
            # Эмодзи по RPE
            rpe = h['rpe']
            if rpe:
                if rpe <= 3:
                    rpe_emoji = "🟢"
                elif rpe <= 6:
                    rpe_emoji = "🟡"
                elif rpe <= 8:
                    rpe_emoji = "🟠"
                else:
                    rpe_emoji = "🔴"
                rpe_text = f"{rpe_emoji} RPE: {rpe:.0f}/10"
            else:
                rpe_text = "⚪ RPE: не указан"
            
            # Прогресс
            progress = f"{h['exercises_done']}/{h['total_exercises']}"
            
            text += f"<b>{i+1}. {h['workout_name']}</b>\n"
            text += f"   📅 {date_str} | {rpe_text}\n"
            text += f"   ✅ Упражнений: {progress}\n\n"
        
        if len(history) > 10:
            text += f"<i>... и ещё {len(history) - 10} тренировок</i>\n\n"
        
        keyboard.button(text="💪 Мои тренировки", callback_data="my_workouts")
        keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
        keyboard.adjust(1)
    
    if is_callback:
        await message.edit_text(text, reply_markup=keyboard.as_markup(), parse_mode="HTML")
        await update.answer()
    else:
        await message.answer(text, reply_markup=keyboard.as_markup(), parse_mode="HTML")


@player_workouts_router.callback_query(F.data.startswith("markdone_"))
async def mark_exercise_done_handler(callback: CallbackQuery, state: FSMContext):
    _, session_id, block_ex_id, workout_id = callback.data.split("_")
    await mark_exercise_completed(int(session_id), int(block_ex_id))
    await callback.answer("✅ Выполнено!", show_alert=True)
    await show_workout_overview(callback, state, int(workout_id))
    
def get_player_workouts_router():
    """Экспорт роутера"""
    return player_workouts_router
