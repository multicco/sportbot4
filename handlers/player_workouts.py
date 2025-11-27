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

@player_workouts_router.callback_query(F.data.startswith("start_workout_"))
async def start_workout(callback: CallbackQuery, state: FSMContext):
    """Начать тренировку — работает и для подопечных, и для тренера (тест)"""
    try:
        workout_id = int(callback.data.split("_")[-1])
        user_tg_id = callback.from_user.id

        logger.info(f"Старт тренировки {workout_id} пользователем {user_tg_id}")

        # Получаем пользователя и его роль
        user = await db_manager.get_user_by_telegram_id(user_tg_id)
        if not user:
            await callback.answer("Пользователь не найден", show_alert=True)
            return

        user_role = user.get('role', 'player')
        is_trainer = user_role in ['admin', 'trainer', 'coach']

        # --------------------- ПРОВЕРКА ДОСТУПА ---------------------
        can_start = False
        workout_name = "Тренировка"

        async with db_manager.pool.acquire() as conn:
            # 1. Если тренер — разрешаем начать любую тренировку (для теста/демо)
            if is_trainer:
                workout = await conn.fetchrow(
                    "SELECT name FROM workouts WHERE id = $1 AND COALESCE(is_active, TRUE)",
                    workout_id
                )
                if workout:
                    can_start = True
                    workout_name = workout['name']

            # 2. Если подопечный — проверяем назначение
            else:
                assigned = await conn.fetchrow("""
                    SELECT w.name 
                    FROM workout_individual_students wis
                    JOIN workouts w ON w.id = wis.workout_id
                    JOIN individual_students s ON s.id = wis.student_id
                    WHERE wis.workout_id = $1 
                      AND s.telegram_id = $2 
                      AND wis.is_active = TRUE
                      AND s.is_active = TRUE
                """, workout_id, user_tg_id)

                if assigned:
                    can_start = True
                    workout_name = assigned['name']

        if not can_start:
            await callback.answer("Эта тренировка вам не назначена", show_alert=True)
            return

        # --------------------- ОБНОВЛЕНИЕ СТАТУСА ---------------------
        success = await teams.teams_db.update_player_workout_status(
            telegram_id=user_tg_id,
            workout_id=workout_id,
            status='in_progress'
        )

        if not success:
            logger.error(f"Не удалось обновить статус тренировки {workout_id} для {user_tg_id}")
            await callback.answer("Не удалось начать тренировку", show_alert=True)
            return

        # --------------------- КРАСИВОЕ СООБЩЕНИЕ ---------------------
        kb = InlineKeyboardBuilder()
        kb.button(text="Завершить тренировку", callback_data=f"finish_workout_{workout_id}")
        kb.button(text="Мои тренировки", callback_data="assigned_workouts")
        kb.button(text="Главное меню", callback_data="main_menu")
        kb.adjust(1)

        trainer_text = "\n\nРежим тренера — тренировка начата для теста" if is_trainer else ""

        await callback.message.edit_text(
            f"**ТРЕНИРОВКА НАЧАТА!**\n\n"
            f"**{workout_name}**\n\n"
            f"Жги железо, брат!\n"
            f"Когда закончишь — жми «Завершить тренировку»\n"
            f"{trainer_text}\n"
            f"_Не забудь оценить RPE после завершения_",
            reply_markup=kb.as_markup(),
            parse_mode="Markdown"
        )

        await callback.answer("Тренировка начата!")

        logger.info(f"Тренировка {workout_id} успешно начата (роль: {user_role})")

    except Exception as e:
        logger.exception(f"Критическая ошибка в start_workout: {e}")
        await callback.answer("Ошибка при старте тренировки", show_alert=True)

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




def get_player_workouts_router():
    """Экспорт роутера"""
    return player_workouts_router
