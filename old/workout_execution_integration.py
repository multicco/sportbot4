
# ПОЛНАЯ ИНТЕГРАЦИЯ СИСТЕМЫ ВЫПОЛНЕНИЯ ТРЕНИРОВОК С RPE

from aiogram import Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Импорты всех модулей системы выполнения
from workout_execution_module import workout_execution_router, WorkoutExecutionStates, RPE_SCALE
from rpe_analytics_module import rpe_analytics_router

# Объединенный роутер для всей системы выполнения тренировок
workout_execution_system_router = Router()

# Включаем все подроутеры
workout_execution_system_router.include_router(workout_execution_router)
workout_execution_system_router.include_router(rpe_analytics_router)

# Обновленное меню тренировок с функциями выполнения
def get_workout_execution_menu(user_role: str) -> InlineKeyboardMarkup:
    """Меню системы выполнения тренировок"""
    keyboard = InlineKeyboardBuilder()

    # Основные функции для всех пользователей
    keyboard.button(text="📋 Мои тренировки", callback_data="my_enhanced_workouts")
    keyboard.button(text="📊 История тренировок", callback_data="my_workout_history")

    # Создание тренировок
    keyboard.button(text="➕ Создать тренировку", callback_data="create_enhanced_workout")
    keyboard.button(text="🔍 Найти тренировку", callback_data="search_workout_by_id")
    keyboard.adjust(2)

    # Аналитика и статистика
    keyboard.row(InlineKeyboardButton(text="📈 Аналитика RPE", callback_data="rpe_analytics"))
    keyboard.row(InlineKeyboardButton(text="📊 Статистика тренировок", callback_data="workout_statistics"))
    keyboard.row(InlineKeyboardButton(text="🌍 Публичные тренировки", callback_data="browse_public_workouts"))

    # Дополнительно для тренеров
    if user_role in ['coach', 'admin']:
        keyboard.row(InlineKeyboardButton(text="👥 Управление командой", callback_data="team_management"))

    keyboard.row(InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu"))

    return keyboard.as_markup()

@workout_execution_system_router.callback_query(F.data == "workout_execution_menu")
async def show_workout_execution_menu(callback: CallbackQuery):
    """Показать главное меню системы выполнения тренировок"""
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    role = user['role'] if user else 'player'

    # Получаем краткую статистику пользователя
    quick_stats = await get_user_quick_stats(user['id'])

    menu_text = "🏋️ **Система тренировок**\n\n"

    if quick_stats['total_sessions'] > 0:
        menu_text += f"📊 **Ваша статистика:**\n"
        menu_text += f"• Тренировок завершено: {quick_stats['completed_sessions']}\n"
        if quick_stats['avg_rpe']:
            menu_text += f"• Средний RPE: {quick_stats['avg_rpe']:.1f}/10\n"
        if quick_stats['last_workout']:
            days_ago = (datetime.now().date() - quick_stats['last_workout'].date()).days
            if days_ago == 0:
                menu_text += f"• Последняя тренировка: сегодня\n"
            elif days_ago == 1:
                menu_text += f"• Последняя тренировка: вчера\n"
            else:
                menu_text += f"• Последняя тренировка: {days_ago} дней назад\n"
        menu_text += f"\n"

    menu_text += f"**Возможности системы:**\n"
    menu_text += f"🏁 Пошаговое выполнение тренировок\n"
    menu_text += f"📊 Оценка интенсивности по шкале RPE (1-10)\n"
    menu_text += f"📈 Детальная аналитика и статистика\n"
    menu_text += f"⏱️ Отслеживание времени и прогресса\n"
    menu_text += f"🌍 Обмен тренировками с сообществом\n\n"

    menu_text += f"Выберите действие:"

    await callback.message.edit_text(
        menu_text,
        reply_markup=get_workout_execution_menu(role),
        parse_mode="Markdown"
    )
    await callback.answer()

# Дополнительные обработчики для интеграции
@workout_execution_system_router.callback_query(F.data.startswith("view_player_workout_"))
async def view_player_workout_enhanced(callback: CallbackQuery):
    """Улучшенный просмотр тренировки игроком с возможностью выполнения"""
    workout_id = int(callback.data.split("_")[3])

    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    workout = await get_workout_details(workout_id)

    if not workout or not await check_workout_access(user['id'], workout):
        await callback.answer("❌ Тренировка не найдена или нет доступа", show_alert=True)
        return

    # Получаем историю выполнения этой тренировки
    execution_history = await get_workout_execution_history(user['id'], workout_id)

    # Формируем текст с деталями тренировки
    text = f"🏋️ **{workout['name']}**\n\n"

    if workout['description']:
        text += f"📄 {workout['description']}\n\n"

    if workout.get('unique_id'):
        text += f"🆔 **ID:** {workout['unique_id']}\n"

    # История выполнения
    if execution_history:
        last_session = execution_history[0]
        text += f"\n📊 **История выполнения:**\n"
        text += f"• Выполнялась {len(execution_history)} раз\n"
        text += f"• Последний раз: {last_session['started_at'].strftime('%d.%m.%Y')}\n"
        if last_session['rpe']:
            rpe_info = RPE_SCALE.get(last_session['rpe'], {'emoji': '❓', 'name': 'Неизвестно'})
            text += f"• Последний RPE: {rpe_info['emoji']} {last_session['rpe']}/10\n"

    # Показываем структуру тренировки
    text += f"\n**Структура тренировки:**\n"
    exercises_by_phase = workout['exercises_by_phase']

    for phase_key, phase_info in WORKOUT_PHASES.items():
        phase_exercises = exercises_by_phase.get(phase_key, [])

        if phase_exercises:
            text += f"\n{phase_info['emoji']} **{phase_info['name']}** ({len(phase_exercises)} упр.)\n"

            for i, ex in enumerate(phase_exercises[:3], 1):  # Показываем первые 3
                reps_display = f"{ex['reps_min']}-{ex['reps_max']}" if ex['reps_min'] != ex['reps_max'] else str(ex['reps_min'])

                # Рассчитываем вес для пользователя
                weight_display = ""
                if ex['one_rm_percent']:
                    calc_weight = await calculate_weight_from_1rm(user['id'], ex['exercise_id'], ex['one_rm_percent'])
                    if calc_weight:
                        weight_display = f" - **{calc_weight:.1f}кг**"
                    else:
                        weight_display = f" - {ex['one_rm_percent']}% от 1ПМ"
                elif ex['fixed_weight'] and ex['fixed_weight'] > 0:
                    weight_display = f" - **{ex['fixed_weight']}кг**"

                text += f"{i}. {ex['exercise_name']} - {ex['sets']}x{reps_display}{weight_display}\n"

            if len(phase_exercises) > 3:
                text += f"... и еще {len(phase_exercises) - 3} упражнений\n"

    # Создаем клавиатуру
    keyboard = InlineKeyboardBuilder()

    # Основная кнопка начала тренировки
    keyboard.row(InlineKeyboardButton(text="🚀 НАЧАТЬ ТРЕНИРОВКУ", callback_data=f"start_workout_{workout_id}"))

    # Дополнительные действия
    keyboard.button(text="📊 История выполнения", callback_data=f"workout_execution_history_{workout_id}")
    keyboard.button(text="📋 Копировать тренировку", callback_data=f"copy_found_workout_{workout_id}")
    keyboard.adjust(2)

    keyboard.row(InlineKeyboardButton(text="🔙 К моим тренировкам", callback_data="my_enhanced_workouts"))

    await callback.message.edit_text(
        text,
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()

@workout_execution_system_router.callback_query(F.data.startswith("workout_execution_history_"))
async def show_workout_execution_history(callback: CallbackQuery):
    """Показать историю выполнения конкретной тренировки"""
    workout_id = int(callback.data.split("_")[3])

    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)

    # Получаем историю выполнения
    history = await get_workout_execution_history(user['id'], workout_id, limit=10)
    workout = await get_workout_details(workout_id)

    if not history:
        await callback.message.edit_text(
            f"📊 **История выполнения**\n\n"
            f"Вы еще не выполняли эту тренировку.\n"
            f"Начните первую тренировку!"
        )
        return

    text = f"📊 **История выполнения**\n"
    text += f"🏋️ **Тренировка:** {workout['name']}\n\n"

    text += f"**Статистика:**\n"
    completed_sessions = [s for s in history if s['status'] == 'completed']

    if completed_sessions:
        avg_duration = statistics.mean([s['total_duration_minutes'] for s in completed_sessions if s['total_duration_minutes']])
        avg_rpe = statistics.mean([s['rpe'] for s in completed_sessions if s['rpe']])

        text += f"• Выполнено: {len(completed_sessions)} раз\n"
        text += f"• Средняя длительность: {avg_duration:.0f} минут\n"
        text += f"• Средний RPE: {avg_rpe:.1f}/10\n\n"

    text += f"**Последние сессии:**\n"

    for i, session in enumerate(history[:7], 1):
        date_str = session['started_at'].strftime('%d.%m')
        time_str = session['started_at'].strftime('%H:%M')

        status_emoji = {
            'completed': '✅',
            'in_progress': '🔄',
            'abandoned': '⏹️'
        }.get(session['status'], '❓')

        duration_text = f" ({session['total_duration_minutes']}мин)" if session['total_duration_minutes'] else ""
        rpe_text = f" RPE:{session['rpe']}" if session['rpe'] else ""

        text += f"{i}. {status_emoji} {date_str} {time_str}{duration_text}{rpe_text}\n"

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🚀 Выполнить снова", callback_data=f"start_workout_{workout_id}")
    keyboard.button(text="🔙 К тренировке", callback_data=f"view_player_workout_{workout_id}")
    keyboard.adjust(1)

    await callback.message.edit_text(
        text,
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()

# Функции для работы с БД
async def get_user_quick_stats(user_id: int) -> Dict:
    """Получить быструю статистику пользователя"""
    async with db_manager.pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total_sessions,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_sessions,
                AVG(CASE WHEN status = 'completed' THEN rpe END) as avg_rpe,
                MAX(CASE WHEN status = 'completed' THEN completed_at END) as last_workout
            FROM workout_sessions 
            WHERE user_id = $1
        """, user_id)

        if row:
            return {
                'total_sessions': row['total_sessions'],
                'completed_sessions': row['completed_sessions'], 
                'avg_rpe': float(row['avg_rpe']) if row['avg_rpe'] else None,
                'last_workout': row['last_workout']
            }
        else:
            return {
                'total_sessions': 0,
                'completed_sessions': 0,
                'avg_rpe': None,
                'last_workout': None
            }

async def get_workout_execution_history(user_id: int, workout_id: int, limit: int = 10) -> List[Dict]:
    """Получить историю выполнения конкретной тренировки"""
    async with db_manager.pool.acquire() as conn:
        sql = """
        SELECT *
        FROM workout_sessions
        WHERE user_id = $1 AND workout_id = $2
        ORDER BY started_at DESC
        LIMIT $3
        """
        rows = await conn.fetch(sql, user_id, workout_id, limit)
        return [dict(row) for row in rows]

# Middleware для аналитики RPE
class RPEAnalyticsMiddleware:
    """Middleware для сбора аналитики RPE"""

    async def __call__(self, handler, event, data):
        result = await handler(event, data)

        # Логируем завершение тренировок с RPE
        if hasattr(event, 'data') and event.data.startswith('select_rpe_'):
            user_id = event.from_user.id
            rpe = int(event.data.split('_')[2])

            # Можно добавить дополнительную аналитику
            logger.info(f"User {user_id} completed workout with RPE {rpe}")

            # Уведомления тренеру при экстремальных RPE
            await notify_coach_about_extreme_rpe(user_id, rpe)

        return result

async def notify_coach_about_extreme_rpe(user_id: int, rpe: int):
    """Уведомить тренера о экстремальном RPE"""
    if rpe >= 9:  # Очень высокий RPE
        # Найти тренера пользователя
        coach = await get_user_coach(user_id)
        if coach:
            user = await db_manager.get_user_by_id(user_id)
            message = f"⚠️ Внимание! Игрок {user['first_name']} закончил тренировку с RPE {rpe}/10 (очень высокая интенсивность). Возможно, стоит скорректировать нагрузку."
            # Отправить уведомление тренеру
            # await send_notification_to_coach(coach['telegram_id'], message)

async def get_user_coach(user_id: int):
    """Получить тренера пользователя"""
    async with db_manager.pool.acquire() as conn:
        sql = """
        SELECT u.* FROM users u
        JOIN team_members tm ON u.id = tm.user_id
        JOIN teams t ON tm.team_id = t.id
        WHERE t.created_by = u.id AND tm.user_id = $1 AND tm.is_active = true
        """
        row = await conn.fetchrow(sql, user_id)
        return dict(row) if row else None

# Функция инициализации системы выполнения тренировок
async def init_workout_execution_system():
    """Инициализация системы выполнения тренировок"""

    # Создаем необходимые индексы если их нет
    async with db_manager.pool.acquire() as conn:
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_workout_sessions_user_status ON workout_sessions(user_id, status)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_workout_sessions_workout_user ON workout_sessions(workout_id, user_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_workout_sessions_rpe ON workout_sessions(rpe) WHERE rpe IS NOT NULL")

    logger.info("Workout execution system initialized")

# Главная функция интеграции
async def setup_workout_execution_system(dp):
    """Настройка системы выполнения тренировок"""

    # Добавляем роутер
    dp.include_router(workout_execution_system_router)

    # Добавляем middleware
    dp.callback_query.middleware(RPEAnalyticsMiddleware())

    # Инициализируем систему
    await init_workout_execution_system()

    logger.info("🏋️ Workout execution system with RPE analytics is ready!")
