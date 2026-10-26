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

# @player_workouts_router.callback_query(F.data.startswith("start_workout_"))
# async def start_workout(callback: CallbackQuery, state: FSMContext):
#     """Начать тренировку — работает и для подопечных, и для тренера (тест)"""
#     try:
#         workout_id = int(callback.data.split("_")[-1])
#         user_tg_id = callback.from_user.id

#         logger.info(f"Старт тренировки {workout_id} пользователем {user_tg_id}")

#         # Получаем пользователя и его роль
#         user = await db_manager.get_user_by_telegram_id(user_tg_id)
#         if not user:
#             await callback.answer("Пользователь не найден", show_alert=True)
#             return

#         user_role = user.get('role', 'player')
#         is_trainer = user_role in ['admin', 'trainer', 'coach']

#         # --------------------- ПРОВЕРКА ДОСТУПА ---------------------
#         can_start = False
#         workout_name = "Тренировка"

#         async with db_manager.pool.acquire() as conn:
#             # 1. Если тренер — разрешаем начать любую тренировку (для теста/демо)
#             if is_trainer:
#                 workout = await conn.fetchrow(
#                     "SELECT name FROM workouts WHERE id = $1 AND COALESCE(is_active, TRUE)",
#                     workout_id
#                 )
#                 if workout:
#                     can_start = True
#                     workout_name = workout['name']

#             # 2. Если подопечный — проверяем назначение
#             else:
#                 assigned = await conn.fetchrow("""
#                     SELECT w.name 
#                     FROM workout_individual_students wis
#                     JOIN workouts w ON w.id = wis.workout_id
#                     JOIN individual_students s ON s.id = wis.student_id
#                     WHERE wis.workout_id = $1 
#                       AND s.telegram_id = $2 
#                       AND wis.is_active = TRUE
#                       AND s.is_active = TRUE
#                 """, workout_id, user_tg_id)

#                 if assigned:
#                     can_start = True
#                     workout_name = assigned['name']

#         if not can_start:
#             await callback.answer("Эта тренировка вам не назначена", show_alert=True)
#             return

#         # --------------------- ОБНОВЛЕНИЕ СТАТУСА ---------------------
#         success = await teams.teams_db.update_player_workout_status(
#             telegram_id=user_tg_id,
#             workout_id=workout_id,
#             status='in_progress'
#         )

#         if not success:
#             logger.error(f"Не удалось обновить статус тренировки {workout_id} для {user_tg_id}")
#             await callback.answer("Не удалось начать тренировку", show_alert=True)
#             return

#         # --------------------- КРАСИВОЕ СООБЩЕНИЕ ---------------------
#         kb = InlineKeyboardBuilder()
#         kb.button(text="Завершить тренировку", callback_data=f"finish_workout_{workout_id}")
#         kb.button(text="Мои тренировки", callback_data="assigned_workouts")
#         kb.button(text="Главное меню", callback_data="main_menu")
#         kb.adjust(1)

#         trainer_text = "\n\nРежим тренера — тренировка начата для теста" if is_trainer else ""

#         await callback.message.edit_text(
#             f"**ТРЕНИРОВКА НАЧАТА!**\n\n"
#             f"**{workout_name}**\n\n"
#             f"Жги железо, брат!\n"
#             f"Когда закончишь — жми «Завершить тренировку»\n"
#             f"{trainer_text}\n"
#             f"_Не забудь оценить RPE после завершения_",
#             reply_markup=kb.as_markup(),
#             parse_mode="Markdown"
#         )

#         await callback.answer("Тренировка начата!")

#         logger.info(f"Тренировка {workout_id} успешно начата (роль: {user_role})")

#     except Exception as e:
#         logger.exception(f"Критическая ошибка в start_workout: {e}")
#         await callback.answer("Ошибка при старте тренировки", show_alert=True)

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



# @player_workouts_router.callback_query(F.data.startswith('viewplayerworkout_'))
# async def view_player_workout_callback(callback: CallbackQuery, state: FSMContext):
#     """Показать детали тренировки игроку/подопечному"""
#     try:
#         workout_id = int(callback.data.split('_')[1])
        
#         # Получить тренировку с упражнениями
#         workout_data = await teams.teams_db.get_workout_with_exercises(workout_id)
        
#         if not workout_data:
#             await callback.answer("❌ Тренировка не найдена", show_alert=True)
#             return
        
#         workout = workout_data['workout']
#         blocks = workout_data['blocks']
        
#         # Формируем текст
#         text = f"💪 <b>{workout['name']}</b>\n\n"
        
#         if workout.get('description'):
#             text += f"📝 {workout['description']}\n\n"
        
#         if not blocks:
#             text += "❌ В этой тренировке нет упражнений"
#         else:
#             text += f"📊 <b>Блоков:</b> {len(blocks)}\n\n"
            
#             for i, block_data in enumerate(blocks, 1):
#                 block = block_data['block']
#                 exercises = block_data['exercises']
                
#                 text += f"<b>Блок {i}: {block['name']}</b>\n"
                
#                 if block.get('description'):
#                     text += f"<i>{block['description']}</i>\n"
                
#                 if not exercises:
#                     text += "  (пусто)\n\n"
#                 else:
#                     for j, ex in enumerate(exercises, 1):
#                         text += f"\n  {j}. <b>{ex['exercise_name']}</b>\n"
                        
#                         if ex.get('exercise_description'):
#                             # Обрезаем описание если длинное
#                             desc = ex['exercise_description']
#                             if len(desc) > 100:
#                                 desc = desc[:100] + "..."
#                             text += f"     📖 {desc}\n"
                        
#                         # Параметры
#                         params = []
#                         if ex.get('sets'):
#                             params.append(f"Подходы: {ex['sets']}")
#                         if ex.get('reps'):
#                             params.append(f"Повторения: {ex['reps']}")
#                         if ex.get('weight'):
#                             params.append(f"Вес: {ex['weight']} кг")
#                         if ex.get('duration'):
#                             params.append(f"Длительность: {ex['duration']} сек")
#                         if ex.get('rest_time'):
#                             params.append(f"Отдых: {ex['rest_time']} сек")
                        
#                         if params:
#                             text += f"     🔹 {' | '.join(params)}\n"
                        
#                         if ex.get('video_url'):
#                             text += f"     🎥 <a href='{ex['video_url']}'>Видео</a>\n"
                    
#                     text += "\n"
        
#         # Кнопки
#         keyboard = InlineKeyboardBuilder()
#         keyboard.button(text="▶️ Начать тренировку", callback_data=f"startworkout_{workout_id}")
#         keyboard.button(text="🔙 К списку", callback_data="assigned_workouts")
#         keyboard.adjust(1)
        
#         await callback.message.edit_text(
#             text, 
#             reply_markup=keyboard.as_markup(), 
#             parse_mode="HTML"
#         )
#         await callback.answer()
        
#     except Exception as e:
#         logger.exception(f"🔴 Ошибка при просмотре тренировки: {e}")
#         await callback.answer("❌ Ошибка при загрузке тренировки", show_alert=True)

from database import db_manager
# @player_workouts_router.callback_query(F.data.startswith('view_workout_'))
# async def view_player_workout_callback(callback: CallbackQuery, state: FSMContext):
#     """Показать детали назначенной тренировки — работает и для подопечных, и для тренеров"""
#     try:
#         workout_id = int(callback.data.split('_')[-1])
#         user_tg_id = callback.from_user.id
        
#         logger.info(f"=== view_player_workout START workout_id={workout_id} user={user_tg_id} ===")
        
#         # Получить пользователя
#         user = await db_manager.get_user_by_telegram_id(user_tg_id)
#         if not user:
#             await callback.answer("Пользователь не найден", show_alert=True)
#             return

#         # ЕСЛИ ЭТО ТРЕНЕР ИЛИ АДМИН — ПРОПУСКАЕМ ВСЮ ПРОВЕРКУ НА СТУДЕНТА
#         is_trainer = user.get('role') in ['admin', 'trainer', 'coach']

#         if not is_trainer:
#             # Только для игроков — проверяем, что он подопечный и тренировка назначена
#             async with db_manager.pool.acquire() as conn:
#                 student = await conn.fetchrow(
#                     """
#                     SELECT id FROM individual_students 
#                     WHERE telegram_id = $1 AND is_active = TRUE
#                     """,
#                     user_tg_id
#                 )
                
#                 if not student:
#                     logger.error(f"Student not found for telegram_id {user_tg_id}")
#                     await callback.answer("У вас нет доступа к этой тренировке", show_alert=True)
#                     return
                
#                 student_id = student['id']
                
#                 workout_assigned = await conn.fetchrow(
#                     """
#                     SELECT wis.* FROM workout_individual_students wis
#                     WHERE wis.workout_id = $1 
#                     AND wis.student_id = $2
#                     AND wis.is_active = TRUE
#                     """,
#                     workout_id,
#                     student_id
#                 )
                
#                 if not workout_assigned:
#                     logger.error(f"Workout {workout_id} not assigned to student {student_id}")
#                     await callback.answer("У вас нет доступа к этой тренировке", show_alert=True)
#                     return
            
#             logger.info("Access granted (player)")
#         else:
#             logger.info("Access granted (trainer/admin) — пропуск проверки студента")

#         # Загружаем тренировку — единый вызов для всех
#         workout_data = await teams.teams_db.get_workout_with_exercises(workout_id)
        
#         if not workout_data:
#             logger.error(f"Workout {workout_id} not found")
#             await callback.answer("Тренировка не найдена", show_alert=True)
#             return
        
#         workout = workout_data['workout']
#         blocks = workout_data['blocks']
        
#         # Формируем текст — полностью твой оригинальный, красивый
#         text = f"<b>{workout['name']}</b>\n\n"
        
#         if workout.get('description'):
#             text += f"{workout['description']}\n\n"
        
#         if not blocks:
#             text += "В этой тренировке нет упражнений"
#         else:
#             text += f"<b>Блоков:</b> {len(blocks)}\n\n"
            
#             for i, block_data in enumerate(blocks, 1):
#                 block = block_data['block']
#                 exercises = block_data['exercises']
                
#                 text += f"<b>Блок {i}: {block['name']}</b>\n"
                
#                 if block.get('description'):
#                     text += f"<i>{block['description']}</i>\n"
                
#                 if exercises:
#                     for j, ex in enumerate(exercises, 1):
#                         text += f"\n  {j}. <b>{ex['exercise_name']}</b>\n"
                        
#                         if ex.get('exercise_description'):
#                             desc = ex['exercise_description']
#                             if len(desc) > 100:
#                                 desc = desc[:100] + "..."
#                             text += f"     {desc}\n"
                        
#                         params = []
#                         if ex.get('sets'):
#                             params.append(f"Подходы: {ex['sets']}")
#                         if ex.get('reps'):
#                             params.append(f"Повторения: {ex['reps']}")
#                         if ex.get('weight'):
#                             params.append(f"Вес: {ex['weight']} кг")
#                         if ex.get('duration'):
#                             params.append(f"Длительность: {ex['duration']} сек")
#                         if ex.get('rest_time'):
#                             params.append(f"Отдых: {ex['rest_time']} сек")
                        
#                         if params:
#                             text += f"     {' | '.join(params)}\n"
                        
#                         if ex.get('video_url'):
#                             text += f"     <a href='{ex['video_url']}'>Видео</a>\n"
                    
#                     text += "\n"
        
#         # Кнопки — разные для подопечного и тренера
#         keyboard = InlineKeyboardBuilder()
        
#         if is_trainer:
#             keyboard.button(text="К шаблонам", callback_data="my_templates")
#         else:
#             keyboard.button(text="Начать тренировку", callback_data=f"start_workout_{workout_id}")
#             keyboard.button(text="К списку", callback_data="my_workouts")
        
#         keyboard.adjust(1)
        
#         await callback.message.edit_text(
#             text, 
#             reply_markup=keyboard.as_markup(), 
#             parse_mode="HTML"
#         )
#         await callback.answer()
#         logger.info("=== view_player_workout END (SUCCESS) ===")
        
#     except Exception as e:
#         logger.exception(f"Ошибка: {e}")
#         await callback.answer("Ошибка при загрузке тренировки", show_alert=True)








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
    success = await teams.teams_db.update_player_workout_status(
        telegram_id=callback.from_user.id,
        workout_id=workout_id,
        status='completed',
        rpe=rpe
    )
    
    await state.clear()
    
    if success:
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="📋 Мои тренировки", callback_data="assigned_workouts")
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



@player_workouts_router.callback_query(F.data == "my_workouts")
async def my_workouts(callback: CallbackQuery):
    """Показать назначенные подопечному тренировки"""
    try:
        logger.info(f"=== my_workouts START user {callback.from_user.id} ===")
        
        # ЛОГИРОВАНИЕ 1: Получение юзера
        user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
        logger.info(f"✓ User found: {user}")
        
        if not user:
            logger.error(f"✗ User NOT found for telegram_id {callback.from_user.id}")
            await callback.answer("❌ Пользователь не найден", show_alert=True)
            return
        
        logger.info(f"✓ User ID: {user.get('id')}")
        user_id = user['id']
        
        # ЛОГИРОВАНИЕ 2: Подключение к БД
        async with db_manager.pool.acquire() as conn:
            logger.info("✓ DB connection acquired")
            
            # Сначала найти student_id по user_id (или telegram_id)
            student = await conn.fetchrow(
                """
                SELECT id FROM individual_students 
                WHERE telegram_id = $1 AND is_active = TRUE
                """,
                callback.from_user.id
            )
            
            if not student:
                logger.info(f"⚠️ No individual_student found for telegram_id {callback.from_user.id}")
                text = ("🏋️ **Мои тренировки**\n\n"
                        "У вас пока нет назначенных тренировок.\n\n"
                        "Обратитесь к тренеру для назначения тренировки!")
                keyboard = InlineKeyboardBuilder()
                keyboard.button(text="🔙 Главное меню", callback_data="mainmenu")
                
                await callback.message.edit_text(
                    text,
                    reply_markup=keyboard.as_markup(),
                    parse_mode="Markdown"
                )
                return
            
            student_id = student['id']
            logger.info(f"✓ Student ID: {student_id}")
            
            # ЛОГИРОВАНИЕ 3: Запрос НАЗНАЧЕННЫХ тренировок
            workouts = await conn.fetch(
                """
                SELECT 
                    w.id,
                    w.name,
                    w.description,
                    w.unique_id,
                    w.created_at,
                    COUNT(we.id) as exercise_count,
                    wis.assigned_at,
                    wis.deadline
                FROM workouts w
                LEFT JOIN workout_exercises we ON w.id = we.workout_id
                INNER JOIN workout_individual_students wis ON w.id = wis.workout_id
                WHERE wis.student_id = $1
                AND wis.is_active = TRUE
                AND w.is_active = TRUE
                GROUP BY w.id, wis.id
                ORDER BY wis.assigned_at DESC
                LIMIT 10
                """,
                student_id
            )
            
            logger.info(f"✓ Query executed, found: {len(workouts) if workouts else 0} workouts")
            
            if workouts:
                logger.info(f"✓ First workout keys: {list(workouts[0].keys())}")
                
                text = f"💪 **Мои назначенные тренировки ({len(workouts)}):**\n\n"
                keyboard = InlineKeyboardBuilder()
                
                for i, workout in enumerate(workouts):
                    logger.info(f"✓ Processing workout {i}: {workout.get('name')}")
                    
                    exercise_count = workout['exercise_count'] or 0
                    deadline = workout.get('deadline')
                    deadline_text = f"⏰ {deadline.strftime('%d.%m')}" if deadline else ""
                    
                    button_text = f"📋 {workout['name']}"
                    if exercise_count > 0:
                        button_text += f" ({exercise_count} упр.)"
                    
                    keyboard.button(
                        text=button_text,
                        callback_data=f"view_workout_{workout['id']}"
                    )
                    
                    text += f"**{workout['name']}**\n"
                    text += f"📋 Упражнений: {exercise_count}\n"
                    if deadline_text:
                        text += f"{deadline_text}\n"
                    text += f"🆔 Код: `{workout['unique_id']}`\n\n"
                
                keyboard.adjust(1)
                keyboard.button(text="🔙 Главное меню", callback_data="mainmenu")
                
                logger.info("✓ About to edit message")
            else:
                logger.info("⚠️ No assigned workouts found")
                text = ("💪 **Мои тренировки**\n\n"
                        "У вас пока нет назначенных тренировок.\n\n"
                        "Обратитесь к тренеру для назначения тренировки!")
                keyboard = InlineKeyboardBuilder()
                keyboard.button(text="🔙 Главное меню", callback_data="mainmenu")
            
            logger.info("✓ Editing message...")
            await callback.message.edit_text(
                text,
                reply_markup=keyboard.as_markup(),
                parse_mode="Markdown"
            )
            logger.info("✓ Message edited successfully")
            
            await callback.answer()
            logger.info("=== my_workouts END (SUCCESS) ===")
            
    except Exception as e:
        logger.error(f"=== ERROR in my_workouts ===", exc_info=True)
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        import traceback
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)



# ===================================================================
# КРАСИВАЯ ТРЕНИРОВКА 2025: блоки + %1ПМ с весом + галочки + прогресс-бар
# Работает с твоим one_rm.py и всеми существующими функциями
# ===================================================================

from aiogram import F
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext

from utils.formatters import format_exercise_info
from handlers.one_rm import get_user_1rm_for_exercise
import logging

logger = logging.getLogger(__name__)

# ==============================================================
# ВСПОМОГАШКИ
# ==============================================================

def get_block_emoji(name: str) -> str:
    n = name.lower()
    if any(x in n for x in ["разминка", "warm"]):    return "Разминка"
    if any(x in n for x in ["заминка", "cool"]):     return "Заминка"
    if any(x in n for x in ["пнс", "ns", "нервн"]):   return "Подготовка НС"
    if "основн" in n or "main" in n:                 return "Основная часть"
    return "Тренировка"


# ==============================================================
# ОСНОВНЫЕ ФУНКЦИИ
# ==============================================================

async def get_or_create_session(player_workout_id: int):
    """Возвращает session_id. Создаёт, если нет."""
    async with db_manager.pool.acquire() as conn:
        sess = await conn.fetchrow(
            "SELECT id FROM player_workout_sessions WHERE player_workout_id = $1",
            player_workout_id
        )
        if sess:
            return sess['id']

        # создаём сессию + все упражнения
        async with conn.transaction():
            sess_id = (await conn.fetchrow(
                "INSERT INTO player_workout_sessions (player_workout_id) VALUES ($1) RETURNING id",
                player_workout_id
            ))['id']

            exercises = await conn.fetch("""
                SELECT wbe.id as block_ex_id, wbe.exercise_id
                FROM workout_block_exercises wbe
                JOIN workout_blocks wb ON wbe.block_id = wb.id
                WHERE wb.workout_id = (SELECT workout_id FROM player_workouts WHERE id = $1)
            """, player_workout_id)

            for ex in exercises:
                await conn.execute("""
                    INSERT INTO workout_session_exercises (session_id, block_exercise_id, exercise_id)
                    VALUES ($1, $2, $3)
                """, sess_id, ex['block_ex_id'], ex['exercise_id'])

        return sess_id


async def get_session_progress(session_id: int):
    async with db_manager.pool.acquire() as conn:
        r = await conn.fetchrow("""
            SELECT 
                COUNT(*) FILTER (WHERE is_completed) as done,
                COUNT(*) as total
            FROM workout_session_exercises WHERE session_id = $1
        """, session_id)
        done = r['done']
        total = r['total'] or 1
        percent = int(done / total * 100)
        return done, total, percent


# ==============================================================
# ГЛАВНОЕ МЕНЮ ТРЕНИРОВКИ
# ==============================================================

async def show_workout_overview(cb_or_msg: CallbackQuery | Message, state: FSMContext, workout_id: int):
    user_tg_id = cb_or_msg.from_user.id
    user = await db_manager.get_user_by_telegram_id(user_tg_id)
    user_id = user['id']
    is_trainer = user['role'] in ['admin', 'trainer', 'coach']

    # player_workout_id
    pw = await db_manager.pool.fetchrow(
        "SELECT id FROM player_workouts WHERE workout_id = $1 AND player_id = $2",
        workout_id, user_id
    )
    if not pw:
        await cb_or_msg.message.edit_text("Ошибка доступа к тренировке")
        return
    player_workout_id = pw['id']

    session_id = await get_or_create_session(player_workout_id)

    data = await teams.teams_db.get_workout_with_exercises(workout_id)
    if not data: return

    done, total, percent = await get_session_progress(session_id)

    # Прогресс-бар
    bar = "🟩" * (percent // 10) + "⬜" * (10 - percent // 10)

    text = f"**ТРЕНИРОВКА**\n\n**{data['workout']['name']}**\n\n"
    text += f"**Прогресс** {done}/{total}  ·  {percent}%\n{bar}\n\n"
    if is_trainer:
        text += "Режим тренера — тест\n\n"

    kb = InlineKeyboardBuilder()

    for block_data in sorted(data['blocks'], key=lambda x: x['block'].get('block_order', 0)):
        block = block_data['block']
        exercises = block_data['exercises']
        if not exercises: continue

        text += f"{get_block_emoji(block['name'])} **{block['name']}**\n\n"

        for ex in exercises:
            ex_id = ex['exercise_id']
            block_ex_id = ex['id']                     # workout_block_exercises.id

            # галочка?
            completed = await db_manager.pool.fetchval("""
                SELECT is_completed FROM workout_session_exercises
                WHERE session_id = $1 AND block_exercise_id = $2
            """, session_id, block_ex_id)
            check = "✅ " if completed else "⬜ "

            # параметры
            params = []
            if ex.get('sets'):
                reps = f"{ex.get('reps_min') or ex['reps']}"
                if ex.get('reps_max'): reps += f"-{ex['reps_max']}"
                params.append(f"{ex['sets']}×{reps}")

            if ex.get('one_rm_percent'):
                orm = await get_user_1rm_for_exercise(user_id, ex_id)
                if orm:
                    weight = round(orm * ex['one_rm_percent'] / 100, 1)
                    params.append(f"@{ex['one_rm_percent']}% (≈{weight}кг)")
                else:
                    params.append(f"@{ex['one_rm_percent']}%")

            if ex.get('rest_seconds'):
                params.append(f"отдых {ex['rest_seconds']}с")

            btn_text = f"{check}{ex['exercise_name']}"
            if params: btn_text += f": {' '.join(params)}"

            kb.button(
                text=btn_text,
                callback_data=f"exdet_{ex_id}_{workout_id}_{session_id}_{block_ex_id}"
            )
        text += "\n"

    kb.button(text="Завершить тренировку", callback_data=f"finish_{workout_id}")
    kb.button(text="Мои тренировки", callback_data="assigned_workouts")
    kb.button(text="Главное меню", callback_data="main_menu")
    kb.adjust(1)

    if isinstance(cb_or_msg, CallbackQuery):
        await cb_or_msg.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="Markdown")
        await cb_or_msg.answer()
    else:
        await cb_or_msg.answer(text, reply_markup=kb.as_markup(), parse_mode="Markdown")

    await state.update_data(current_session_id=session_id, current_workout_id=workout_id)


# ==============================================================
# КАРТОЧКА УПРАЖНЕНИЯ + ГАЛОЧКА + 1ПМ
# ==============================================================

@player_workouts_router.callback_query(F.data.startswith("exdet_"))
async def exercise_detail(callback: CallbackQuery, state: FSMContext):
    _, ex_id, wid, sess_id, block_ex_id = callback.data.split("_")
    ex_id, wid, sess_id, block_ex_id = int(ex_id), int(wid), int(sess_id), int(block_ex_id)

    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    user_id = user['id']

    exercise = await db_manager.pool.fetchrow("""
        SELECT e.*, u.first_name as author_name 
        FROM exercises e
        LEFT JOIN users u ON e.created_by = u.id
        WHERE e.id = $1
    """, ex_id)

    text = format_exercise_info(dict(exercise))

    # 1ПМ
    orm = await get_user_1rm_for_exercise(user_id, ex_id)
    if orm:
        text += f"\n\n**Ваш 1ПМ:** {orm} кг"

    kb = InlineKeyboardBuilder()

    # галочка выполненного
    done = await db_manager.pool.fetchval("""
        SELECT is_completed FROM workout_session_exercises
        WHERE session_id = $1 AND block_exercise_id = $2
    """, sess_id, block_ex_id)
    kb.button(
        text="✅ Выполнено" if done else "Отметить выполненным",
        callback_data="done" if done else f"markdone_{sess_id}_{block_ex_id}_{wid}"
    )

    # тест 1ПМ
    if exercise['test_type'] and exercise['test_type'] != 'none':
        btn_1rm = f"1ПМ: {orm} кг (обновить)" if orm else "Пройти тест 1ПМ"
        kb.button(text=btn_1rm, callback_data=f"test1rm_{ex_id}_{wid}")

    kb.button(text="Назад к тренировке", callback_data=f"back_{wid}")
    kb.button(text="Завершить тренировку", callback_data=f"finish_{wid}")
    kb.adjust(1)

    await callback.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="Markdown")
    await callback.answer()


# Отметить выполненным
@player_workouts_router.callback_query(F.data.startswith("markdone_"))
async def mark_done(callback: CallbackQuery, state: FSMContext):
    _, sess_id, block_ex_id, wid = callback.data.split("_")
    await db_manager.pool.execute("""
        UPDATE workout_session_exercises SET is_completed = TRUE, completed_at = NOW()
        WHERE session_id = $1 AND block_exercise_id = $2
    """, int(sess_id), int(block_ex_id))
    await callback.answer("Отмечено!", show_alert=True)
    await show_workout_overview(callback, state, int(wid))


# Назад в тренировку
@player_workouts_router.callback_query(F.data.startswith("back_"))
async def back_to_overview(callback: CallbackQuery, state: FSMContext):
    wid = int(callback.data.split("_")[1])
    await show_workout_overview(callback, state, wid)


# Запуск теста 1ПМ из тренировки
@player_workouts_router.callback_query(F.data.startswith("test1rm_"))
async def start_1rm_from_workout(callback: CallbackQuery, state: FSMContext):
    _, ex_id, wid = callback.data.split("_")
    ex_id, wid = int(ex_id), int(wid)

    exercise = await db_manager.pool.fetchrow("SELECT name FROM exercises WHERE id = $1", ex_id)

    await state.update_data(
        return_after_1rm_test=wid,
        exercise_id=ex_id,
        exercise_name=exercise['name']
    )
    await state.set_state("waiting_1rm_data")

    await callback.message.edit_text(
        f"**Тест 1ПМ: {exercise['name']}**\n\n"
        "Введите: `вес повторения`\n"
        "Пример: `80 5`",
        parse_mode="Markdown"
    )
    await callback.answer()


# ==============================================================
# ВАЖНО: ВСТАВЬ ЭТО В КОНЕЦ ФУНКЦИИ process_1rm_data в one_rm.py
# ==============================================================
# (ищи строку await state.clear() и вставь перед ней)

        # # ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
        # data = await state.get_data()
        # return_to = data.get("return_after_1rm_test")
        # if return_to:
        #     from handlers.player_workouts import show_workout_overview
        #     await message.answer("1ПМ обновлён — возвращаемся в тренировку!")
        #     await show_workout_overview(message, state, return_to)
        #     await state.clear()
        #     return
        # # ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←



def get_player_workouts_router():
    """Экспорт роутера"""
    return player_workouts_router