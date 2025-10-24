
# МОДУЛЬ АНАЛИТИКИ RPE И ИСТОРИИ ТРЕНИРОВОК

from aiogram import Router
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import F
from datetime import datetime, timedelta
from typing import Dict, List
import statistics

rpe_analytics_router = Router()

@rpe_analytics_router.callback_query(F.data == "my_workout_history")
async def show_workout_history(callback: CallbackQuery):
    """Показать историю тренировок пользователя"""
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)

    # Получаем историю тренировок
    sessions = await get_user_workout_sessions(user['id'], limit=20)

    if not sessions:
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="🏁 Начать первую тренировку", callback_data="enhanced_training_menu")
        keyboard.button(text="🔙 Назад", callback_data="enhanced_training_menu")
        keyboard.adjust(1)

        await callback.message.edit_text(
            "📊 **История тренировок**\n\n"
            "У вас пока нет выполненных тренировок.\n"
            "Начните свою первую тренировку!",
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )
        return

    # Группируем по статусу
    completed = [s for s in sessions if s['status'] == 'completed']
    in_progress = [s for s in sessions if s['status'] == 'in_progress']
    abandoned = [s for s in sessions if s['status'] == 'abandoned']

    keyboard = InlineKeyboardBuilder()

    # Показываем последние 10 тренировок
    for session in sessions[:10]:
        status_emoji = {
            'completed': '✅',
            'in_progress': '🔄', 
            'abandoned': '⏹️'
        }.get(session['status'], '❓')

        date_str = session['started_at'].strftime('%d.%m')
        time_str = session['started_at'].strftime('%H:%M')

        rpe_text = f" RPE:{session['rpe']}" if session['rpe'] else ""
        duration_text = f" {session['total_duration_minutes']}мин" if session['total_duration_minutes'] else ""

        keyboard.button(
            text=f"{status_emoji} {session['workout_name']} - {date_str} {time_str}{rpe_text}{duration_text}",
            callback_data=f"view_session_{session['id']}"
        )

    keyboard.adjust(1)

    # Дополнительные функции
    keyboard.row(InlineKeyboardButton(text="📈 Аналитика RPE", callback_data="rpe_analytics"))
    keyboard.row(InlineKeyboardButton(text="📊 Статистика", callback_data="workout_statistics"))
    keyboard.row(InlineKeyboardButton(text="🔙 К тренировкам", callback_data="enhanced_training_menu"))

    text = f"📊 **История тренировок**\n\n"
    text += f"✅ **Завершенных:** {len(completed)}\n"
    text += f"🔄 **В процессе:** {len(in_progress)}\n"
    text += f"⏹️ **Прерванных:** {len(abandoned)}\n\n"

    if completed:
        # Средние показатели
        avg_rpe = statistics.mean([s['rpe'] for s in completed if s['rpe']])
        avg_duration = statistics.mean([s['total_duration_minutes'] for s in completed if s['total_duration_minutes']])

        text += f"📈 **Средние показатели:**\n"
        text += f"• RPE: {avg_rpe:.1f}/10\n"
        text += f"• Длительность: {avg_duration:.0f} минут\n\n"

    text += f"**Последние тренировки:**"

    await callback.message.edit_text(
        text,
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()

@rpe_analytics_router.callback_query(F.data.startswith("view_session_"))
async def view_session_details(callback: CallbackQuery):
    """Просмотр деталей сессии тренировки"""
    session_id = int(callback.data.split("_")[2])

    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    session = await get_session_details(session_id, user['id'])

    if not session:
        await callback.answer("❌ Сессия не найдена", show_alert=True)
        return

    # Статус эмодзи
    status_info = {
        'completed': {'emoji': '✅', 'name': 'Завершена'},
        'in_progress': {'emoji': '🔄', 'name': 'В процессе'},
        'abandoned': {'emoji': '⏹️', 'name': 'Прервана'}
    }

    status = status_info.get(session['status'], {'emoji': '❓', 'name': 'Неизвестно'})

    text = f"📋 **Детали тренировки**\n\n"
    text += f"📝 **Название:** {session['workout_name']}\n"
    text += f"🆔 **ID тренировки:** {session.get('workout_unique_id', 'N/A')}\n"
    text += f"📅 **Дата:** {session['started_at'].strftime('%d.%m.%Y')}\n"
    text += f"⏰ **Начало:** {session['started_at'].strftime('%H:%M')}\n"

    if session['completed_at']:
        text += f"🏁 **Завершение:** {session['completed_at'].strftime('%H:%M')}\n"

    text += f"🔄 **Статус:** {status['emoji']} {status['name']}\n"

    if session['total_duration_minutes']:
        hours = session['total_duration_minutes'] // 60
        minutes = session['total_duration_minutes'] % 60
        if hours > 0:
            text += f"⏱️ **Продолжительность:** {hours}ч {minutes}мин\n"
        else:
            text += f"⏱️ **Продолжительность:** {minutes} минут\n"

    if session['rpe']:
        rpe_info = RPE_SCALE.get(session['rpe'], {'emoji': '❓', 'name': 'Неизвестно'})
        text += f"📊 **RPE:** {rpe_info['emoji']} {session['rpe']}/10 - {rpe_info['name']}\n"

    if session['session_notes']:
        text += f"\n📝 **Заметки:**\n_{session['session_notes']}_\n"

    # Статистика упражнений
    exercises_stats = await get_session_exercises_stats(session_id)
    if exercises_stats:
        text += f"\n🏋️ **Выполнено упражнений:** {exercises_stats['completed_exercises']}\n"
        text += f"📊 **Всего подходов:** {exercises_stats['total_sets']}\n"

        if exercises_stats['total_weight']:
            text += f"⚖️ **Общий тоннаж:** {exercises_stats['total_weight']:.0f} кг\n"

    keyboard = InlineKeyboardBuilder()

    if session['status'] == 'in_progress':
        keyboard.button(text="▶️ Продолжить тренировку", callback_data=f"resume_session_{session_id}")

    keyboard.button(text="📊 Детали упражнений", callback_data=f"session_exercises_{session_id}")
    keyboard.button(text="🔙 К истории", callback_data="my_workout_history")
    keyboard.adjust(1)

    await callback.message.edit_text(
        text,
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()

@rpe_analytics_router.callback_query(F.data == "rpe_analytics")
async def show_rpe_analytics(callback: CallbackQuery):
    """Показать аналитику RPE"""
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)

    # Получаем данные RPE за разные периоды
    rpe_7_days = await get_rpe_analytics(user['id'], days=7)
    rpe_30_days = await get_rpe_analytics(user['id'], days=30)
    rpe_all_time = await get_rpe_analytics(user['id'], days=9999)

    text = f"📈 **Аналитика RPE**\n\n"

    if not rpe_all_time['sessions']:
        text += "❌ Недостаточно данных для анализа.\nВыполните несколько тренировок с оценкой RPE."

        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="🔙 К истории", callback_data="my_workout_history")

        await callback.message.edit_text(text, reply_markup=keyboard.as_markup(), parse_mode="Markdown")
        return

    # 7 дней
    if rpe_7_days['sessions'] > 0:
        text += f"📅 **За последние 7 дней:**\n"
        text += f"• Тренировок: {rpe_7_days['sessions']}\n"
        text += f"• Средний RPE: {rpe_7_days['avg_rpe']:.1f}/10\n"
        text += f"• Макс RPE: {rpe_7_days['max_rpe']}/10\n\n"

    # 30 дней  
    if rpe_30_days['sessions'] > 0:
        text += f"📅 **За последние 30 дней:**\n"
        text += f"• Тренировок: {rpe_30_days['sessions']}\n"
        text += f"• Средний RPE: {rpe_30_days['avg_rpe']:.1f}/10\n"
        text += f"• Макс RPE: {rpe_30_days['max_rpe']}/10\n\n"

    # Все время
    text += f"📈 **За все время:**\n"
    text += f"• Всего тренировок: {rpe_all_time['sessions']}\n"
    text += f"• Средний RPE: {rpe_all_time['avg_rpe']:.1f}/10\n"
    text += f"• Диапазон: {rpe_all_time['min_rpe']}-{rpe_all_time['max_rpe']}/10\n\n"

    # Распределение по уровням RPE
    rpe_distribution = await get_rpe_distribution(user['id'])
    if rpe_distribution:
        text += f"📊 **Распределение по уровням интенсивности:**\n"
        for rpe_level, count in sorted(rpe_distribution.items()):
            rpe_info = RPE_SCALE.get(rpe_level, {'emoji': '❓', 'name': f'RPE {rpe_level}'})
            percentage = (count / rpe_all_time['sessions']) * 100
            text += f"{rpe_info['emoji']} **{rpe_level}** ({rpe_info['name']}): {count} раз ({percentage:.0f}%)\n"

    # Рекомендации
    if rpe_30_days['avg_rpe'] > 8:
        text += f"\n💡 **Рекомендация:** Ваш средний RPE довольно высок ({rpe_30_days['avg_rpe']:.1f}). Рассмотрите включение более легких тренировок для восстановления."
    elif rpe_30_days['avg_rpe'] < 5:
        text += f"\n💡 **Рекомендация:** Ваш средний RPE невысок ({rpe_30_days['avg_rpe']:.1f}). Возможно, стоит увеличить интенсивность для лучшего прогресса."
    else:
        text += f"\n✅ **Хорошо!** Ваш средний RPE в оптимальном диапазоне ({rpe_30_days['avg_rpe']:.1f})."

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="📈 Детальная статистика", callback_data="detailed_rpe_stats")
    keyboard.button(text="📊 График RPE", callback_data="rpe_chart")
    keyboard.button(text="🔙 К истории", callback_data="my_workout_history")
    keyboard.adjust(1)

    await callback.message.edit_text(
        text,
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()

@rpe_analytics_router.callback_query(F.data == "workout_statistics")
async def show_workout_statistics(callback: CallbackQuery):
    """Показать общую статистику тренировок"""
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)

    stats = await get_comprehensive_workout_stats(user['id'])

    if not stats['total_sessions']:
        await callback.message.edit_text(
            "📊 **Статистика тренировок**\n\n"
            "У вас пока нет данных для статистики.\n"
            "Выполните несколько тренировок!"
        )
        return

    text = f"📊 **Статистика тренировок**\n\n"

    # Общие показатели
    text += f"🏋️ **Общие показатели:**\n"
    text += f"• Всего тренировок: {stats['total_sessions']}\n"
    text += f"• Завершенных: {stats['completed_sessions']} ({stats['completion_rate']:.0f}%)\n"
    text += f"• В среднем в неделю: {stats['avg_sessions_per_week']:.1f}\n\n"

    # Время тренировок
    if stats['avg_duration']:
        text += f"⏱️ **Время тренировок:**\n"
        text += f"• Средняя длительность: {stats['avg_duration']:.0f} минут\n"
        text += f"• Самая короткая: {stats['min_duration']} минут\n"
        text += f"• Самая длинная: {stats['max_duration']} минут\n"
        text += f"• Общее время: {stats['total_duration_hours']:.1f} часов\n\n"

    # RPE статистика
    if stats['avg_rpe']:
        text += f"📈 **Интенсивность (RPE):**\n"
        text += f"• Средний RPE: {stats['avg_rpe']:.1f}/10\n"
        text += f"• Диапазон: {stats['min_rpe']}-{stats['max_rpe']}/10\n\n"

    # Любимые тренировки
    if stats['favorite_workouts']:
        text += f"⭐ **Популярные тренировки:**\n"
        for workout in stats['favorite_workouts'][:3]:
            text += f"• {workout['name']}: {workout['count']} раз\n"
        text += f"\n"

    # Активность по дням недели
    if stats['activity_by_weekday']:
        text += f"📅 **Активность по дням недели:**\n"
        weekdays = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        for day, count in stats['activity_by_weekday'].items():
            percentage = (count / stats['completed_sessions']) * 100 if stats['completed_sessions'] > 0 else 0
            text += f"• {weekdays[day]}: {count} тренировок ({percentage:.0f}%)\n"

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="📈 Аналитика RPE", callback_data="rpe_analytics")
    keyboard.button(text="📅 По месяцам", callback_data="monthly_stats")
    keyboard.button(text="🔙 К истории", callback_data="my_workout_history")
    keyboard.adjust(1)

    await callback.message.edit_text(
        text,
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()

# Функции для работы с базой данных
async def get_user_workout_sessions(user_id: int, limit: int = 20) -> List[Dict]:
    """Получить сессии тренировок пользователя"""
    async with db_manager.pool.acquire() as conn:
        sql = """
        SELECT ws.*, w.name as workout_name, w.unique_id as workout_unique_id
        FROM workout_sessions ws
        JOIN workouts w ON ws.workout_id = w.id
        WHERE ws.user_id = $1
        ORDER BY ws.started_at DESC
        LIMIT $2
        """
        rows = await conn.fetch(sql, user_id, limit)
        return [dict(row) for row in rows]

async def get_session_details(session_id: int, user_id: int) -> Dict:
    """Получить детали сессии"""
    async with db_manager.pool.acquire() as conn:
        sql = """
        SELECT ws.*, w.name as workout_name, w.unique_id as workout_unique_id
        FROM workout_sessions ws
        JOIN workouts w ON ws.workout_id = w.id
        WHERE ws.id = $1 AND ws.user_id = $2
        """
        row = await conn.fetchrow(sql, session_id, user_id)
        return dict(row) if row else None

async def get_session_exercises_stats(session_id: int) -> Dict:
    """Получить статистику упражнений сессии"""
    async with db_manager.pool.acquire() as conn:
        sql = """
        SELECT 
            COUNT(*) as completed_exercises,
            SUM(completed_sets) as total_sets,
            SUM(CASE 
                WHEN actual_weights IS NOT NULL 
                THEN (SELECT SUM(weight) FROM unnest(actual_weights) as weight)
                ELSE 0 
            END) as total_weight
        FROM workout_session_exercises
        WHERE session_id = $1 AND completed_at IS NOT NULL
        """
        row = await conn.fetchrow(sql, session_id)
        return dict(row) if row else {}

async def get_rpe_analytics(user_id: int, days: int) -> Dict:
    """Получить аналитику RPE за период"""
    async with db_manager.pool.acquire() as conn:
        sql = """
        SELECT 
            COUNT(*) as sessions,
            AVG(rpe) as avg_rpe,
            MIN(rpe) as min_rpe,
            MAX(rpe) as max_rpe
        FROM workout_sessions
        WHERE user_id = $1 
        AND status = 'completed' 
        AND rpe IS NOT NULL
        AND started_at >= CURRENT_DATE - INTERVAL '%s days' % $2
        """
        row = await conn.fetchrow(sql, user_id, days)

        if row and row['sessions']:
            return {
                'sessions': row['sessions'],
                'avg_rpe': float(row['avg_rpe']),
                'min_rpe': row['min_rpe'],
                'max_rpe': row['max_rpe']
            }
        else:
            return {'sessions': 0, 'avg_rpe': 0, 'min_rpe': 0, 'max_rpe': 0}

async def get_rpe_distribution(user_id: int) -> Dict[int, int]:
    """Получить распределение RPE по уровням"""
    async with db_manager.pool.acquire() as conn:
        sql = """
        SELECT rpe, COUNT(*) as count
        FROM workout_sessions
        WHERE user_id = $1 AND status = 'completed' AND rpe IS NOT NULL
        GROUP BY rpe
        ORDER BY rpe
        """
        rows = await conn.fetch(sql, user_id)
        return {row['rpe']: row['count'] for row in rows}

async def get_comprehensive_workout_stats(user_id: int) -> Dict:
    """Получить комплексную статистику тренировок"""
    async with db_manager.pool.acquire() as conn:
        # Основная статистика
        basic_stats = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total_sessions,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_sessions,
                AVG(CASE WHEN status = 'completed' THEN total_duration_minutes END) as avg_duration,
                MIN(CASE WHEN status = 'completed' THEN total_duration_minutes END) as min_duration,
                MAX(CASE WHEN status = 'completed' THEN total_duration_minutes END) as max_duration,
                SUM(CASE WHEN status = 'completed' THEN total_duration_minutes ELSE 0 END) / 60.0 as total_duration_hours,
                AVG(CASE WHEN status = 'completed' THEN rpe END) as avg_rpe,
                MIN(CASE WHEN status = 'completed' THEN rpe END) as min_rpe,
                MAX(CASE WHEN status = 'completed' THEN rpe END) as max_rpe,
                MIN(started_at) as first_workout,
                MAX(started_at) as last_workout
            FROM workout_sessions 
            WHERE user_id = $1
        """, user_id)

        if not basic_stats or basic_stats['total_sessions'] == 0:
            return {'total_sessions': 0}

        stats = dict(basic_stats)

        # Процент завершения
        stats['completion_rate'] = (stats['completed_sessions'] / stats['total_sessions']) * 100

        # Средние тренировки в неделю
        if stats['first_workout'] and stats['last_workout']:
            days_diff = (stats['last_workout'] - stats['first_workout']).days + 1
            weeks = days_diff / 7
            stats['avg_sessions_per_week'] = stats['completed_sessions'] / max(weeks, 1)
        else:
            stats['avg_sessions_per_week'] = 0

        # Любимые тренировки
        favorite_workouts = await conn.fetch("""
            SELECT w.name, COUNT(*) as count
            FROM workout_sessions ws
            JOIN workouts w ON ws.workout_id = w.id
            WHERE ws.user_id = $1 AND ws.status = 'completed'
            GROUP BY w.id, w.name
            ORDER BY count DESC
            LIMIT 5
        """, user_id)

        stats['favorite_workouts'] = [dict(row) for row in favorite_workouts]

        # Активность по дням недели (0 = понедельник)
        weekday_stats = await conn.fetch("""
            SELECT EXTRACT(DOW FROM started_at) as weekday, COUNT(*) as count
            FROM workout_sessions
            WHERE user_id = $1 AND status = 'completed'
            GROUP BY EXTRACT(DOW FROM started_at)
            ORDER BY weekday
        """, user_id)

        # Преобразуем Sunday(0) -> Monday(0)
        activity_by_weekday = {}
        for row in weekday_stats:
            dow = int(row['weekday'])
            # Postgres: 0=Sunday, 1=Monday ... 6=Saturday
            # Нам нужно: 0=Monday, 1=Tuesday ... 6=Sunday
            adjusted_dow = (dow + 6) % 7
            activity_by_weekday[adjusted_dow] = row['count']

        stats['activity_by_weekday'] = activity_by_weekday

        return stats
