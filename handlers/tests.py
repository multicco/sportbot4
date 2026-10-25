# ===== ИСПРАВЛЕННЫЙ handlers/tests.py С ПОЛНОЦЕННЫМИ ФУНКЦИЯМИ =====

import logging

from aiogram import F, Router

from aiogram.fsm.context import FSMContext

from aiogram.types import Message, CallbackQuery

from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import db_manager

import logging

import re

from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)

# ===== ГЛАВНОЕ МЕНЮ ТЕСТОВ =====

async def tests_menu(callback: CallbackQuery):
    """Главное меню тестов с разделением на батареи и индивидуальные"""
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    
    # СОЗДАЕМ КЛАВИАТУРУ ПРЯМО ЗДЕСЬ
    keyboard = InlineKeyboardBuilder()
    
    if user['role'] in ['coach', 'admin']:
        keyboard.button(text="📋 Батареи тестов", callback_data="coach_batteries")
        keyboard.button(text="📊 Индивидуальные тесты", callback_data="individual_tests_menu")
        keyboard.button(text="📈 Аналитика команды", callback_data="team_analytics")
        keyboard.button(text="🌐 Публичные тесты", callback_data="public_test_sets")
    else:
        keyboard.button(text="📋 Мои батареи тестов", callback_data="player_batteries")
        keyboard.button(text="🔬 Индивидуальные тесты", callback_data="individual_tests_menu")
        keyboard.button(text="🏆 Мои достижения", callback_data="my_achievements")
        keyboard.button(text="🌐 Публичные тесты", callback_data="public_test_sets")
    
    keyboard.button(text="🔙 Главное меню", callback_data="main_menu")
    keyboard.adjust(2)
    
    text = f"📊 **Система тестирования - ОБНОВЛЕНО!**\n\n"
    
    if user['role'] in ['coach', 'admin']:
        text += f"👨🏫 **Тренерская панель:**\n"
        text += f"• 📋 **Батареи тестов** - НОВАЯ СИСТЕМА!\n"
        text += f"• 📊 **Индивидуальные тесты** - как раньше\n\n"
    else:
        text += f"👤 **Панель участника:**\n"
        text += f"• 📋 **Мои батареи тестов** - НОВОЕ!\n"
        text += f"• 🔬 **Индивидуальные тесты** - как раньше\n\n"
    
    text += f"🎯 **Батареи тестов:**\n"
    text += f"Создавайте наборы упражнений по темам!\n\n"
    text += f"**Выберите раздел:**"
    
    await callback.message.edit_text(
        text,
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    
    await callback.answer()

def validate_test_data(test_data, test_type):
    """Универсальная валидация данных теста.

    Принимает либо словарь, либо сырую строку ввода пользователя
    ('90', '1:30', '12.5 30' и т.п.) — строка парсится автоматически
    в зависимости от типа теста.
    Возвращает dict: valid, errors, data + поля time/distance/seconds/reps.
    """
    if isinstance(test_data, str):
        raw = re.sub(r'(сек|sec|кг|kg|раз|повт)', ' ', test_data.lower())
        raw = raw.replace(',', '.')
        numbers = re.findall(r'\d+(?:\.\d+)?', raw)
        colon_parts = [p.strip() for p in test_data.split(':') if p.strip()]

        if test_type == 'speed':
            # Формат "время дистанция" (например "12.5 30") или "12.5сек 30м"
            if len(numbers) >= 2:
                test_data = {'time': float(numbers[0]), 'distance': float(numbers[1])}
            elif len(numbers) == 1 and len(colon_parts) != 2:
                # Только время без дистанции
                test_data = {'time': float(numbers[0]), 'distance': None}
            elif len(colon_parts) == 2 and all(p.replace('.', '').isdigit() for p in colon_parts):
                test_data = {'time': int(colon_parts[0]) * 60 + float(colon_parts[1]), 'distance': None}
            else:
                return {'valid': False, 'errors': ["Введите время и дистанцию через пробел. Пример: `12.5 30`"], 'data': {}}
        elif test_type == 'endurance':
            if len(colon_parts) == 2 and all(p.replace('.', '').isdigit() for p in colon_parts):
                test_data = {'seconds': int(colon_parts[0]) * 60 + int(float(colon_parts[1]))}
            elif len(numbers) >= 1:
                test_data = {'seconds': float(numbers[0])}
            else:
                return {'valid': False, 'errors': ["Введите время в секундах. Пример: `90` или `1:30`"], 'data': {}}
        elif test_type == 'quantity':
            if len(numbers) >= 1:
                test_data = {'reps': int(float(numbers[0]))}
            else:
                return {'valid': False, 'errors': ["Введите количество повторений числом. Пример: `25`"], 'data': {}}
        elif test_type == 'strength':
            if len(numbers) >= 2:
                test_data = {'weight': float(numbers[0]), 'reps': int(float(numbers[1]))}
            else:
                return {'valid': False, 'errors': ["Введите вес и повторения через пробел. Пример: `80 10`"], 'data': {}}
        else:
            return {'valid': False, 'errors': [f"Неизвестный тип теста: {test_type}"], 'data': {}}

    if not isinstance(test_data, dict):
        return {
            'valid': False,
            'errors': [f"Неверный тип данных: {type(test_data)}"],
            'data': {}
        }

    result = {'valid': True, 'errors': [], 'data': test_data.copy()}

    if test_type == 'strength':
        try:
            weight = float(test_data.get('weight', 0))
            reps = int(test_data.get('reps', 0))

            if weight <= 0 or weight > 1000:
                result['errors'].append("Вес должен быть от 0.1 до 1000 кг")
                result['valid'] = False

            if reps <= 0 or reps > 50:
                result['errors'].append("Повторения должны быть от 1 до 50")
                result['valid'] = False

            result['data']['weight'] = weight
            result['data']['reps'] = reps

        except (ValueError, TypeError):
            result['errors'].append("Неверный формат чисел")
            result['valid'] = False

    elif test_type == 'speed':
        try:
            time_val = float(test_data.get('time', test_data.get('time_seconds', 0)))
            distance_val = test_data.get('distance')
            distance_val = float(distance_val) if distance_val is not None else None

            if time_val <= 0 or time_val > 7200:
                result['errors'].append("Время должно быть от 0.1 до 7200 секунд")
                result['valid'] = False

            if distance_val is not None and (distance_val <= 0 or distance_val > 10000):
                result['errors'].append("Дистанция должна быть от 1 до 10000 метров")
                result['valid'] = False

            result['time'] = time_val
            result['distance'] = distance_val
            result['data']['time'] = time_val
            result['data']['distance'] = distance_val
        except (ValueError, TypeError):
            result['errors'].append("Неверный формат чисел. Пример: `12.5 30`")
            result['valid'] = False

    elif test_type == 'endurance':
        try:
            seconds_val = float(test_data.get('seconds', test_data.get('time_seconds', 0)))
            if seconds_val <= 0 or seconds_val > 86400:
                result['errors'].append("Время должно быть от 1 до 86400 секунд")
                result['valid'] = False
            result['seconds'] = seconds_val
            result['data']['seconds'] = seconds_val
        except (ValueError, TypeError):
            result['errors'].append("Неверный формат времени")
            result['valid'] = False

    elif test_type == 'quantity':
        try:
            reps_val = int(test_data.get('reps', test_data.get('max_reps', 0)))
            if reps_val <= 0 or reps_val > 10000:
                result['errors'].append("Количество повторений должно быть от 1 до 10000")
                result['valid'] = False
            result['reps'] = reps_val
            result['data']['reps'] = reps_val
        except (ValueError, TypeError):
            result['errors'].append("Неверный формат числа")
            result['valid'] = False

    return result

def parse_strength_test_input(text: str) -> Dict[str, Any]:
    """
    ИСПРАВЛЕННЫЙ парсинг ввода пользователя для силовых тестов
    """
    try:
        original_text = text.strip()
        text = original_text.lower()
        
        # Убираем единицы измерения
        text = re.sub(r'(кг|kg|kg\.)', '', text)
        text = re.sub(r'(раз|раз\.)', '', text)
        text = re.sub(r'(повт|повторений|повтор)', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Ищем ВСЕ числа в тексте
        numbers = re.findall(r'\d+\.?\d*', text)
        
        if len(numbers) >= 2:
            # Успешно - найдены вес и повторения
            return {
                'weight': float(numbers[0]),
                'reps': int(float(numbers[1])),
                'original_text': original_text,
                'parsed_successfully': True
            }
        elif len(numbers) == 1:
            # Найдено только одно число
            return {
                'error': 'found_one_number',
                'number': float(numbers[0]),
                'original_text': original_text,
                'parsed_successfully': False
            }
        else:
            # Числа не найдены
            return {
                'error': 'no_numbers_found',
                'original_text': original_text,
                'parsed_successfully': False
            }
        
    except Exception as e:
        return {
            'error': 'parse_error',
            'message': str(e),
            'original_text': text,
            'parsed_successfully': False
        }

# ===== БАТАРЕИ ТЕСТОВ - ПЕРЕНАПРАВЛЕНИЯ НА НОВЫЙ МОДУЛЬ =====

async def coach_batteries_menu(callback: CallbackQuery):
    """Перенаправление на новый модуль батарей"""
    # Импортируем из нового модуля
    from handlers.test_batteries import coach_batteries_main_menu
    await coach_batteries_main_menu(callback)

async def player_batteries_menu(callback: CallbackQuery):
    """Перенаправление на новый модуль батарей"""
    from handlers.test_batteries import player_batteries_main_menu
    await player_batteries_main_menu(callback)

# ===== ПОЛНОЦЕННЫЕ ФУНКЦИИ ВМЕСТО ЗАГЛУШЕК =====

async def team_analytics(callback: CallbackQuery):
    """ПОЛНОЦЕННАЯ аналитика команды"""
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    
    if user['role'] not in ['coach', 'admin']:
        await callback.answer("❌ Доступно только тренерам", show_alert=True)
        return
    
    try:
        async with db_manager.pool.acquire() as conn:
            # Получаем команды тренера
            teams = await conn.fetch("""
                SELECT t.id, t.name, COUNT(tm.user_id) as members_count
                FROM teams t
                LEFT JOIN team_members tm ON t.id = tm.team_id AND tm.is_active = true
                WHERE t.coach_id = $1 AND t.is_active = true
                GROUP BY t.id, t.name
                ORDER BY t.name
            """, user['id'])
            
            if not teams:
                text = f"📈 **Аналитика команды**\n\n"
                text += f"⚠️ У вас пока нет команд\n\n"
                text += f"Создайте команду, чтобы видеть аналитику участников."
                
                keyboard = InlineKeyboardBuilder()
                keyboard.button(text="👥 Создать команду", callback_data="create_team")
                keyboard.button(text="🔙 К тестам", callback_data="tests_menu")
                keyboard.adjust(1)
            else:
                text = f"📈 **Аналитика команды**\n\n"
                text += f"👨🏫 **Ваши команды:**\n\n"
                
                keyboard = InlineKeyboardBuilder()
                
                for team in teams:
                    text += f"👥 **{team['name']}**\n"
                    text += f"   Участников: {team['members_count']}\n\n"
                    
                    keyboard.button(
                        text=f"📊 {team['name']} ({team['members_count']})",
                        callback_data=f"team_stats_{team['id']}"
                    )
                
                text += f"💡 Выберите команду для детальной аналитики"
                
                keyboard.button(text="🔙 К тестам", callback_data="tests_menu")
                keyboard.adjust(1)
            
            await callback.message.edit_text(
                text,
                reply_markup=keyboard.as_markup(),
                parse_mode="Markdown"
            )
            
    except Exception as e:
        logger.error(f"Ошибка аналитики команды: {e}")
        await callback.message.edit_text("❌ Ошибка загрузки аналитики команды")
    
    await callback.answer()

async def public_test_sets(callback: CallbackQuery):
    """ПОЛНОЦЕННЫЕ публичные наборы тестов"""
    try:
        async with db_manager.pool.acquire() as conn:
            # Получаем публичные батареи тестов
            public_batteries = await conn.fetch("""
                SELECT tb.id, tb.name, tb.description, tb.exercises_count,
                       u.first_name as creator_name, tb.created_at
                FROM test_batteries tb
                JOIN users u ON tb.created_by = u.id
                WHERE tb.visibility = 'public' AND tb.is_active = true
                ORDER BY tb.created_at DESC
                LIMIT 10
            """)
            
            text = f"🌐 **Публичные наборы тестов**\n\n"
            
            if public_batteries:
                text += f"📋 **Доступные наборы ({len(public_batteries)}):**\n\n"
                
                keyboard = InlineKeyboardBuilder()
                
                for battery in public_batteries:
                    text += f"📦 **{battery['name']}**\n"
                    text += f"   👤 Автор: {battery['creator_name']}\n"
                    text += f"   🏋️ Упражнений: {battery['exercises_count']}\n"
                    text += f"   📅 {battery['created_at'].strftime('%d.%m.%Y')}\n"
                    
                    if battery['description']:
                        text += f"   💭 {battery['description'][:50]}{'...' if len(battery['description']) > 50 else ''}\n"
                    
                    text += f"\n"
                    
                    keyboard.button(
                        text=f"📋 {battery['name']}",
                        callback_data=f"view_public_battery_{battery['id']}"
                    )
                
                text += f"💡 Нажмите на набор для просмотра упражнений"
                
            else:
                text += f"⚠️ Публичных наборов пока нет\n\n"
                text += f"Тренеры могут создавать публичные наборы тестов\n"
                text += f"для обмена опытом с коллегами."
                
                keyboard = InlineKeyboardBuilder()
            
            keyboard.button(text="🔍 Поиск наборов", callback_data="search_public_batteries")
            keyboard.button(text="🔙 К тестам", callback_data="tests_menu")
            keyboard.adjust(2)
            
            await callback.message.edit_text(
                text,
                reply_markup=keyboard.as_markup(),
                parse_mode="Markdown"
            )
            
    except Exception as e:
        logger.error(f"Ошибка публичных наборов: {e}")
        await callback.message.edit_text("❌ Ошибка загрузки публичных наборов")
    
    await callback.answer()

async def my_achievements(callback: CallbackQuery):
    """ПОЛНОЦЕННАЯ система достижений"""
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    
    try:
        async with db_manager.pool.acquire() as conn:
            # Получаем статистику для достижений
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_tests,
                    COUNT(DISTINCT exercise_id) as unique_exercises,
                    MAX(formula_average) as best_1rm,
                    MIN(tested_at) as first_test_date,
                    MAX(tested_at) as last_test_date
                FROM one_rep_max 
                WHERE user_id = $1
            """, user['id'])
            
            # Считаем тесты за последний месяц
            recent_tests = await conn.fetchval("""
                SELECT COUNT(*) FROM one_rep_max 
                WHERE user_id = $1 
                AND tested_at > CURRENT_DATE - INTERVAL '30 days'
            """, user['id'])
            
            total_tests = stats['total_tests'] if stats else 0
            unique_exercises = stats['unique_exercises'] if stats else 0
            best_1rm = stats['best_1rm'] if stats else 0
            
            # Система достижений
            achievements = [
                {
                    "name": "🥇 Первый тест",
                    "desc": "Пройти первый силовой тест",
                    "unlocked": total_tests > 0,
                    "progress": min(total_tests, 1)
                },
                {
                    "name": "💪 Силач",
                    "desc": "Пройти 10 силовых тестов",
                    "unlocked": total_tests >= 10,
                    "progress": min(total_tests, 10)
                },
                {
                    "name": "🎯 Снайпер",
                    "desc": "Достичь 1ПМ свыше 100кг",
                    "unlocked": best_1rm >= 100,
                    "progress": min(best_1rm, 100) if best_1rm > 0 else 0
                },
                {
                    "name": "🔬 Исследователь",
                    "desc": "Протестировать 5 разных упражнений",
                    "unlocked": unique_exercises >= 5,
                    "progress": min(unique_exercises, 5)
                },
                {
                    "name": "⚡ Активист",
                    "desc": "Пройти 5 тестов за месяц",
                    "unlocked": recent_tests >= 5,
                    "progress": min(recent_tests, 5)
                },
                {
                    "name": "🏆 Чемпион",
                    "desc": "Достичь 1ПМ свыше 150кг",
                    "unlocked": best_1rm >= 150,
                    "progress": min(best_1rm, 150) if best_1rm > 0 else 0
                },
            ]
            
            unlocked_count = sum(1 for a in achievements if a["unlocked"])
            
            text = f"🏆 **Мои достижения**\n\n"
            text += f"**Прогресс:** {unlocked_count}/{len(achievements)} "
            text += f"({unlocked_count*100//len(achievements)}%)\n\n"
            
            for achievement in achievements:
                if achievement["unlocked"]:
                    status = "✅"
                    progress = ""
                else:
                    status = "🔒"
                    if achievement["name"] in ["💪 Силач", "🔬 Исследователь", "⚡ Активист"]:
                        target_num = 10 if "Силач" in achievement["name"] else 5
                        progress = f" ({achievement['progress']}/{target_num})"
                    elif "1ПМ" in achievement["desc"]:
                        target = int(achievement["desc"].split()[-1].replace("кг", ""))
                        current = achievement['progress']
                        progress = f" ({current:.0f}/{target}кг)" if current > 0 else f" (0/{target}кг)"
                    else:
                        progress = ""
                
                text += f"{status} **{achievement['name']}**{progress}\n"
                text += f"   _{achievement['desc']}_\n\n"
            
            if total_tests > 0:
                text += f"📊 **Ваша статистика:**\n"
                text += f"• Всего тестов: {total_tests}\n"
                text += f"• Упражнений: {unique_exercises}\n"
                if best_1rm > 0:
                    text += f"• Лучший 1ПМ: {best_1rm:.1f} кг\n"
                text += f"• За месяц: {recent_tests} тестов"
            else:
                text += f"💡 Начните проходить тесты, чтобы получать достижения!"
            
            keyboard = InlineKeyboardBuilder()
            keyboard.button(text="💪 Новый тест", callback_data="individual_tests_menu")
            keyboard.button(text="📈 Мой прогресс", callback_data="test_progress")
            keyboard.button(text="🏆 Рекорды", callback_data="test_records")
            keyboard.button(text="🔙 К тестам", callback_data="tests_menu")
            keyboard.adjust(2)
            
            await callback.message.edit_text(
                text,
                reply_markup=keyboard.as_markup(),
                parse_mode="Markdown"
            )
            
    except Exception as e:
        logger.error(f"Ошибка загрузки достижений: {e}")
        await callback.message.edit_text(f"❌ Ошибка загрузки достижений: {e}")
    
    await callback.answer()

# ===== ИНДИВИДУАЛЬНЫЕ ТЕСТЫ =====

async def individual_tests_menu(callback: CallbackQuery):
    """Меню индивидуальных тестов"""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="📊 Мои тесты", callback_data="my_tests")
    keyboard.button(text="🔬 Новый тест", callback_data="new_test_menu")
    keyboard.button(text="📈 Прогресс", callback_data="test_progress")
    keyboard.button(text="🏆 Рекорды", callback_data="test_records")
    keyboard.button(text="🔙 К тестам", callback_data="tests_menu")
    keyboard.adjust(2)
    
    text = f"🔬 **Индивидуальные тесты**\n\n"
    text += f"📊 **Ведите личные рекорды по упражнениям:**\n"
    text += f"• Отслеживайте прогресс в любом упражнении\n"
    text += f"• Система автоматически определит тип теста\n"
    text += f"• Сравнивайте результаты по времени\n\n"
    text += f"💡 **Типы тестов:**\n"
    text += f"🏋️ Силовые - расчет 1ПМ по формулам\n"
    text += f"⏱️ Выносливость - время удержания\n"
    text += f"🏃 Скорость - время на дистанцию\n"
    text += f"🔢 Количественные - максимум повторений\n\n"
    text += f"**Выберите действие:**"
    
    await callback.message.edit_text(
        text,
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    
    await callback.answer()

async def new_test_menu(callback: CallbackQuery):
    """Меню поиска упражнений для индивидуального теста"""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔍 Поиск по названию", callback_data="search_by_name")
    keyboard.button(text="📂 По категориям", callback_data="search_by_category")
    keyboard.button(text="💪 По группам мышц", callback_data="search_by_muscle")
    keyboard.button(text="🔙 К индивидуальным тестам", callback_data="individual_tests_menu")
    keyboard.adjust(1)
    
    await callback.message.edit_text(
        "🔍 **Выберите упражнение для индивидуального теста:**\n\n"
        "💡 **Любое упражнение может быть протестировано!**\n"
        "Система автоматически определит тип теста:\n\n"
        "🏋️ **Силовые упражнения** → тест с расчетом 1ПМ по формулам\n"
        "⏱️ **Упражнения на выносливость** → тест времени удержания\n"
        "🏃 **Скоростные упражнения** → тест времени на дистанцию\n"
        "🔢 **Количественные** → тест максимальных повторений\n\n"
        "**Выберите способ поиска упражнения:**",
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    
    await callback.answer()

async def search_exercise_by_name_for_test(callback: CallbackQuery, state: FSMContext):
    """Поиск упражнения по названию для теста"""
    await callback.message.edit_text(
        "🔍 **Поиск упражнения для теста**\n\n"
        "Введите название упражнения:\n"
        "_Например: жим, приседания, планка, бег_\n\n"
        "💡 **Найденные упражнения будут кликабельными для тестирования!**",
        parse_mode="Markdown"
    )
    
    await state.set_state("waiting_search_for_test")
    await callback.answer()

async def search_by_category_for_test(callback: CallbackQuery):
    """Поиск упражнений по категориям для тестирования"""
    try:
        async with db_manager.pool.acquire() as conn:
            categories = await conn.fetch("SELECT DISTINCT category FROM exercises ORDER BY category")
        
        keyboard = InlineKeyboardBuilder()
        for cat in categories:
            keyboard.button(
                text=f"📂 {cat['category']}",
                callback_data=f"test_cat_{cat['category']}"
            )
        
        keyboard.button(text="🔙 К поиску теста", callback_data="new_test_menu")
        keyboard.adjust(2)
        
        await callback.message.edit_text(
            "📂 **Выберите категорию упражнений для тестирования:**\n\n"
            "💡 **Найденные упражнения можно будет сразу протестировать!**",
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    
    await callback.answer()

async def search_by_muscle_for_test(callback: CallbackQuery):
    """Поиск упражнений по группам мышц для тестирования"""
    try:
        async with db_manager.pool.acquire() as conn:
            muscle_groups = await conn.fetch("SELECT DISTINCT muscle_group FROM exercises ORDER BY muscle_group")
        
        keyboard = InlineKeyboardBuilder()
        for mg in muscle_groups:
            keyboard.button(
                text=f"💪 {mg['muscle_group']}",
                callback_data=f"test_muscle_{mg['muscle_group']}"
            )
        
        keyboard.button(text="🔙 К поиску теста", callback_data="new_test_menu")
        keyboard.adjust(2)
        
        await callback.message.edit_text(
            "💪 **Выберите группу мышц для тестирования:**\n\n"
            "💡 **Найденные упражнения можно будет сразу протестировать!**",
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    
    await callback.answer()

async def show_test_category_exercises(callback: CallbackQuery):
    """Показать упражнения категории для тестирования"""
    category = callback.data[9:]  # Убираем "test_cat_"
    
    try:
        async with db_manager.pool.acquire() as conn:
            exercises = await conn.fetch(
                "SELECT id, name, muscle_group, test_type FROM exercises WHERE category = $1 ORDER BY name",
                category
            )
        
        if exercises:
            text = f"📂 **{category} - упражнения для тестирования:**\n\n"
            text += f"💡 **Нажмите на упражнение чтобы пройти тест:**\n\n"
            
            keyboard = InlineKeyboardBuilder()
            
            for ex in exercises:
                test_emoji = {
                    'strength': '🏋️',
                    'endurance': '⏱️',
                    'speed': '🏃',
                    'quantity': '🔢',
                    'none': '💪'
                }.get(ex['test_type'] if ex['test_type'] else 'none', '💪')
                
                keyboard.button(
                    text=f"{test_emoji} {ex['name']} • {ex['muscle_group']}",
                    callback_data=f"test_{ex['id']}"
                )
            
            keyboard.button(text="🔙 К категориям", callback_data="search_by_category")
            keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
            keyboard.adjust(1)
            
            await callback.message.edit_text(
                text,
                reply_markup=keyboard.as_markup(),
                parse_mode="Markdown"
            )
        else:
            await callback.message.edit_text(f"❌ Упражнения в категории '{category}' не найдены")
    
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    
    await callback.answer()

async def show_test_muscle_exercises(callback: CallbackQuery):
    """Показать упражнения группы мышц для тестирования"""
    muscle_group = callback.data[12:]  # Убираем "test_muscle_"
    
    try:
        async with db_manager.pool.acquire() as conn:
            exercises = await conn.fetch(
                "SELECT id, name, category, test_type FROM exercises WHERE muscle_group = $1 ORDER BY name",
                muscle_group
            )
        
        if exercises:
            text = f"💪 **{muscle_group} - упражнения для тестирования:**\n\n"
            text += f"💡 **Нажмите на упражнение чтобы пройти тест:**\n\n"
            
            keyboard = InlineKeyboardBuilder()
            
            for ex in exercises:
                test_emoji = {
                    'strength': '🏋️',
                    'endurance': '⏱️',
                    'speed': '🏃',
                    'quantity': '🔢',
                    'none': '💪'
                }.get(ex['test_type'] if ex['test_type'] else 'none', '💪')
                
                keyboard.button(
                    text=f"{test_emoji} {ex['name']} ({ex['category']})",
                    callback_data=f"test_{ex['id']}"
                )
            
            keyboard.button(text="🔙 К группам мышц", callback_data="search_by_muscle")
            keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
            keyboard.adjust(1)
            
            await callback.message.edit_text(
                text,
                reply_markup=keyboard.as_markup(),
                parse_mode="Markdown"
            )
        else:
            await callback.message.edit_text(f"❌ Упражнения для группы '{muscle_group}' не найдены")
    
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    
    await callback.answer()

async def handle_test_exercise_search(message: Message, state: FSMContext):
    """Обработка поиска упражнения по названию для теста"""
    search_term = message.text.lower()
    
    try:
        async with db_manager.pool.acquire() as conn:
            exercises = await conn.fetch("""
                SELECT id, name, category, muscle_group, test_type
                FROM exercises
                WHERE LOWER(name) LIKE $1
                OR LOWER(category) LIKE $1
                OR LOWER(muscle_group) LIKE $1
                ORDER BY name
                LIMIT 15
            """, f"%{search_term}%")
        
        if exercises:
            text = f"🔍 **Найдено упражнений для тестирования: {len(exercises)}**\n\n"
            text += f"💡 **Нажмите на упражнение чтобы сразу пройти тест:**\n\n"
            
            keyboard = InlineKeyboardBuilder()
            
            for ex in exercises:
                test_emoji = {
                    'strength': '🏋️',
                    'endurance': '⏱️',
                    'speed': '🏃',
                    'quantity': '🔢',
                    'none': '💪'
                }.get(ex['test_type'] if ex['test_type'] else 'none', '💪')
                
                keyboard.button(
                    text=f"{test_emoji} {ex['name']} • {ex['muscle_group']}",
                    callback_data=f"test_{ex['id']}"
                )
            
            keyboard.button(text="🔍 Новый поиск", callback_data="new_test_menu")
            keyboard.button(text="🔙 К индивидуальным", callback_data="individual_tests_menu")
            keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
            keyboard.adjust(1)
            
            await message.answer(
                text,
                reply_markup=keyboard.as_markup(),
                parse_mode="Markdown"
            )
        else:
            text = f"❌ Упражнения по запросу '{search_term}' не найдены\n\n"  \
                   f"Попробуйте другие ключевые слова."
            
            keyboard = InlineKeyboardBuilder()
            keyboard.button(text="🔍 Новый поиск", callback_data="new_test_menu")
            keyboard.button(text="🔙 К индивидуальным", callback_data="individual_tests_menu")
            keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
            
            await message.answer(text, reply_markup=keyboard.as_markup(), parse_mode="Markdown")
        
        await state.clear()
        
    except Exception as e:
        await message.answer(f"❌ Ошибка поиска: {e}")

# ===== ПРОХОЖДЕНИЕ ТЕСТОВ С ИСПРАВЛЕННОЙ ЛОГИКОЙ =====

async def start_exercise_test(callback: CallbackQuery, state: FSMContext):
    """Начало тестирования упражнения"""
    exercise_id = int(callback.data[5:])  # Убираем "test_"
    
    try:
        async with db_manager.pool.acquire() as conn:
            exercise = await conn.fetchrow("SELECT * FROM exercises WHERE id = $1", exercise_id)
        
        if not exercise:
            await callback.answer("❌ Упражнение не найдено!")
            return
        
        await state.update_data(exercise_id=exercise_id, exercise=dict(exercise))
        
        # Определяем тип теста
        test_type = exercise['test_type'] if exercise['test_type'] else 'strength'
        
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="❌ Отменить тест", callback_data="new_test_menu")
        
        if test_type == 'strength':
            text = f"🏋️ **Силовой тест: {exercise['name']}**\n\n"
            text += f"💪 **Группа мышц:** {exercise['muscle_group']}\n"
            text += f"📂 **Категория:** {exercise['category']}\n\n"
            text += f"📝 **Введите вес и количество повторений:**\n"
            text += f"_Например: 80 10 (80кг на 10 повторений)_\n"
            text += f"_Или: 80кг 10раз_\n\n"
            text += f"💡 **1ПМ будет рассчитан автоматически по формулам:**\n"
            text += f"• Brzycki • Epley • Lander"
            
            await state.set_state("waiting_strength_test_data")
            
        elif test_type == 'endurance':
            text = f"⏱️ **Тест выносливости: {exercise['name']}**\n\n"
            text += f"💪 **Группа мышц:** {exercise['muscle_group']}\n"
            text += f"📂 **Категория:** {exercise['category']}\n\n"
            text += f"📝 **Введите время удержания:**\n"
            text += f"_Например: 90 (секунд) или 1:30 (мин:сек)_"
            
            await state.set_state("waiting_endurance_test_data")
            
        elif test_type == 'speed':
            text = f"🏃 **Скоростной тест: {exercise['name']}**\n\n"
            text += f"💪 **Группа мышц:** {exercise['muscle_group']}\n"
            text += f"📂 **Категория:** {exercise['category']}\n\n"
            text += f"📝 **Введите время и дистанцию:**\n"
            text += f"_Например: 12.5 30 (12.5сек на 30м)_"
            
            await state.set_state("waiting_speed_test_data")
            
        elif test_type == 'quantity':
            text = f"🔢 **Количественный тест: {exercise['name']}**\n\n"
            text += f"💪 **Группа мышц:** {exercise['muscle_group']}\n"
            text += f"📂 **Категория:** {exercise['category']}\n\n"
            text += f"📝 **Введите максимальное количество повторений:**\n"
            text += f"_Например: 25 (отжиманий)_"
            
            await state.set_state("waiting_quantity_test_data")
            
        else:
            # По умолчанию силовой тест с расчетом по формулам
            text = f"💪 **Силовой тест: {exercise['name']}**\n\n"
            text += f"💪 **Группа мышц:** {exercise['muscle_group']}\n"
            text += f"📂 **Категория:** {exercise['category']}\n\n"
            text += f"📝 **Введите вес и количество повторений:**\n"
            text += f"_Например: 80 10 (80кг на 10 повторений)_"
            
            await state.set_state("waiting_strength_test_data")
        
        await callback.message.edit_text(
            text,
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    
    await callback.answer()

# ===== ОБРАБОТКА РЕЗУЛЬТАТОВ ТЕСТОВ =====

async def process_strength_test_data(message: Message, state: FSMContext):
    """ИСПРАВЛЕННАЯ логика обработки силового теста"""
    try:
        # Получаем данные из состояния
        state_data = await state.get_data()
        exercise_data = state_data.get('exercise', {})
        exercise_name = exercise_data.get('name', 'Упражнение')
        exercise_id = state_data.get('exercise_id')
        
        if not exercise_id:
            await message.answer("❌ Ошибка: упражнение не выбрано")
            await state.clear()
            return
        
        # ШАГ 1: Парсим строку
        parsed_result = parse_strength_test_input(message.text)
        
        # ШАГ 2: Проверяем результат парсинга
        if not parsed_result.get('parsed_successfully', False):
            error_type = parsed_result.get('error', 'unknown')
            
            if error_type == 'found_one_number':
                await message.answer(
                    f"❌ Найдено только одно число: {parsed_result['number']}\n\n"
                    f"Введите **вес и повторения через пробел**:\n"
                    f"• `80 10` - 80кг на 10 повторений\n"
                    f"• `60 5` - 60кг на 5 повторений",
                    parse_mode="Markdown"
                )
            else:
                await message.answer(
                    f"❌ Неверный формат\n\n"
                    f"Введите: `вес повторения`\n"
                    f"Примеры:\n"
                    f"• `80 10`\n"
                    f"• `80кг 10раз`\n"
                    f"• `80 10 раз`",
                    parse_mode="Markdown"
                )
            return
        
        # ШАГ 3: Создаем словарь с данными
        test_data = {
            'weight': parsed_result['weight'],
            'reps': parsed_result['reps'],
            'exercise_id': exercise_id,
            'exercise_name': exercise_name
        }
        
        # ШАГ 4: Валидируем словарь
        validation = validate_test_data(test_data, 'strength')
        
        if not validation['valid']:
            error_text = "❌ **Ошибки в данных:**\n\n"
            for error in validation['errors']:
                error_text += f"• {error}\n"
            await message.answer(error_text, parse_mode="Markdown")
            return
        
        # ШАГ 5: Получаем валидные данные
        valid_data = validation['data']
        weight = valid_data['weight']
        reps = valid_data['reps']
        
        # Расчет 1ПМ по 3 формулам
        if reps == 1:
            results = {'brzycki': weight, 'epley': weight, 'lander': weight, 'average': weight}
        else:
            brzycki = weight / (1.0278 - 0.0278 * reps)
            epley = weight * (1 + reps / 30.0)
            lander = (100 * weight) / (101.3 - 2.67123 * reps)
            average = (brzycki + epley + lander) / 3.0
            
            results = {
                'brzycki': round(brzycki, 1),
                'epley': round(epley, 1),
                'lander': round(lander, 1),
                'average': round(average, 1)
            }
        
        # Сохранение в БД
        user = await db_manager.get_user_by_telegram_id(message.from_user.id)
        
        async with db_manager.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO one_rep_max (
                    user_id, exercise_id, weight, reps, test_weight,
                    formula_brzycki, formula_epley, formula_alternative, formula_average
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
            user['id'], int(exercise_id), results['average'],
            reps, weight, results['brzycki'], results['epley'],
            results['lander'], results['average'])
        
        # Формируем сообщение с результатами
        text = f"🎉 **Результат теста 1ПМ**\n\n"
        text += f"💪 **Упражнение:** {exercise_name}\n"
        text += f"📊 **Ваши данные:** {weight} кг × {reps} повторений\n\n"
        text += f"**📈 Расчет по формулам:**\n"
        text += f"• Бжицкого: **{results['brzycki']} кг**\n"
        text += f"• Эпли: **{results['epley']} кг**\n"
        text += f"• Ландера: **{results['lander']} кг**\n\n"
        text += f"🎯 **Ваш 1ПМ: {results['average']} кг**\n"
        text += f"_(среднее по 3 формулам)_"
        
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="💪 Новый тест", callback_data="new_test_menu")
        keyboard.button(text="📊 Мои результаты", callback_data="my_tests")
        keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
        keyboard.adjust(2)
        
        await message.answer(text, reply_markup=keyboard.as_markup(), parse_mode="Markdown")
        await state.clear()
        
    except Exception as e:
        logger.error(f"Ошибка обработки силового теста: {e}")
        await message.answer(f"❌ Ошибка: {e}")
        await state.clear()

async def process_endurance_test_data(message: Message, state: FSMContext):
    """✅ ИСПРАВЛЕННАЯ обработка теста выносливости - ФИНАЛЬНАЯ ВЕРСИЯ"""
    try:
        # Получаем данные из состояния
        state_data = await state.get_data()
        exercise_data = state_data.get('exercise', {})
        exercise_name = exercise_data.get('name', 'Упражнение')
        exercise_id = state_data.get('exercise_id')
        battery_id = state_data.get('battery_id')  # Может быть None для индивидуальных тестов
        
        if not exercise_id:
            await message.answer("❌ Ошибка: упражнение не выбрано")
            await state.clear()
            return
        
        # Парсим время из строки "90" или "1:30"
        time_input = message.text.strip()
        parts = time_input.split(':')
        
        if len(parts) == 1:
            # "90" секунд
            try:
                seconds = int(parts[0])
            except ValueError:
                await message.answer("❌ Введите время только цифрами\nПримеры: `90` или `1:30`", parse_mode="Markdown")
                return
        elif len(parts) == 2:
            # "1:30" формат
            try:
                minutes = int(parts[0])
                secs = int(parts[1])
                seconds = minutes * 60 + secs
            except ValueError:
                await message.answer("❌ Неверный формат\nПримеры: `90` (сек) или `1:30` (мин:сек)", parse_mode="Markdown")
                return
        else:
            await message.answer("❌ Неверный формат\nПримеры: `90` (сек) или `1:30` (мин:сек)", parse_mode="Markdown")
            return
        
        # ✅ Получаем пользователя
        user = await db_manager.get_user_by_telegram_id(message.from_user.id)
        
        # ✅ Вставляем в ПРАВИЛЬНУЮ таблицу в зависимости от типа теста
        async with db_manager.pool.acquire() as conn:
            if battery_id:
                # БАТАРЕЯ ТЕСТОВ → test_battery_results
                participant = await conn.fetchrow("""
                    SELECT id FROM test_battery_participants 
                    WHERE user_id = $1 AND battery_id = $2
                """, user['id'], battery_id)
                
                if participant:
                    participant_id = participant['id']
                    await conn.execute("""
                        INSERT INTO test_battery_results 
                        (participant_id, exercise_id, battery_id, test_type, result_value, 
                         result_unit, duration_seconds, tested_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
                    """, participant_id, int(exercise_id), battery_id, 'endurance', 
                    seconds, 'сек', seconds)
                else:
                    await message.answer("❌ Вы не добавлены к этой батарее тестов")
                    await state.clear()
                    return
            else:
                # ИНДИВИДУАЛЬНЫЙ ТЕСТ → user_tests
                # Колонки: user_id, exercise_id, test_type, result_value, result_unit, 
                #          test_weight, test_reps, distance, time_seconds, duration_seconds, max_reps, notes, conditions
                await conn.execute("""
                    INSERT INTO user_tests 
                    (user_id, exercise_id, test_type, result_value, result_unit, 
                     time_seconds, duration_seconds, tested_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
                """, user['id'], int(exercise_id), 'endurance', seconds, 'сек', 
                seconds, seconds)
        
        # Форматируем время для вывода
        minutes_display = seconds // 60
        seconds_display = seconds % 60
        
        text = f"🎉 **Результат теста выносливости**\n\n"
        text += f"⏱️ **Упражнение:** {exercise_name}\n"
        text += f"📊 **Время удержания:** {minutes_display}:{seconds_display:02d}\n\n"
        text += f"💡 **Результат сохранён!**"
        
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="💪 Новый тест", callback_data="new_test_menu")
        keyboard.button(text="📊 Мои результаты", callback_data="my_tests")
        keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
        keyboard.adjust(2)
        
        await message.answer(text, reply_markup=keyboard.as_markup(), parse_mode="Markdown")
        await state.clear()
        
    except Exception as e:
        logger.error(f"Ошибка обработки теста выносливости: {e}")
        await message.answer(f"❌ Ошибка: {e}")
        await state.clear()




async def process_speed_test_data(message: Message, state: FSMContext):
    """Обработка данных скоростного теста"""
    test_data = message.text.strip()
    data = await state.get_data()
    exercise = data['exercise']
    user = await db_manager.get_user_by_telegram_id(message.from_user.id)
    
    validation = validate_test_data(test_data, 'speed')
    
    if not validation['valid']:
        await message.answer(f"❌ Ошибки: {', '.join(validation['errors'])}")
        return
    
    try:
        async with db_manager.pool.acquire() as conn:
            distance_val = validation.get('distance')
            await conn.execute("""
                INSERT INTO user_tests
                (user_id, exercise_id, test_type, result_value, result_unit, time_seconds, distance)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, user['id'], data['exercise_id'], 'speed',
                validation['time'], 'сек', validation['time'], distance_val)
        
        text = f"✅ **Скоростной тест завершен!**\n\n"
        text += f"🏃 **Упражнение:** {exercise['name']}\n"
        text += f"💪 **Результат:** {validation['time']}сек на {validation['distance']}м\n"
        text += f"📅 **Дата:** {message.date.strftime('%d.%m.%Y %H:%M')}\n\n"
        text += f"✅ **Тест сохранен в вашу историю!**"
        
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="🔬 Новый тест", callback_data="new_test_menu")
        keyboard.button(text="📊 Мои тесты", callback_data="my_tests")
        keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
        keyboard.adjust(1)
        
        await message.answer(text, reply_markup=keyboard.as_markup(), parse_mode="Markdown")
        await state.clear()
        
    except Exception as e:
        await message.answer(f"❌ Ошибка сохранения: {e}")

async def process_quantity_test_data(message: Message, state: FSMContext):
    """Обработка данных количественного теста"""
    test_data = message.text.strip()
    data = await state.get_data()
    exercise = data['exercise']
    user = await db_manager.get_user_by_telegram_id(message.from_user.id)
    
    validation = validate_test_data(test_data, 'quantity')
    
    if not validation['valid']:
        await message.answer(f"❌ Ошибки: {', '.join(validation['errors'])}")
        return
    
    try:
        async with db_manager.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO user_tests
                (user_id, exercise_id, test_type, result_value, result_unit, max_reps)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, user['id'], data['exercise_id'], 'quantity',
                validation['reps'], 'раз', validation['reps'])
        
        text = f"✅ **Количественный тест завершен!**\n\n"
        text += f"🔢 **Упражнение:** {exercise['name']}\n"
        text += f"💪 **Результат:** {validation['reps']} повторений\n"
        text += f"📅 **Дата:** {message.date.strftime('%d.%m.%Y %H:%M')}\n\n"
        text += f"✅ **Тест сохранен в вашу историю!**"
        
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="🔬 Новый тест", callback_data="new_test_menu")
        keyboard.button(text="📊 Мои тесты", callback_data="my_tests")
        keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
        keyboard.adjust(1)
        
        await message.answer(text, reply_markup=keyboard.as_markup(), parse_mode="Markdown")
        await state.clear()
        
    except Exception as e:
        await message.answer(f"❌ Ошибка сохранения: {e}")

# ===== ПРОСМОТР ТЕСТОВ =====

async def my_tests(callback: CallbackQuery):
    """Показать тесты пользователя"""
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    
    try:
        async with db_manager.pool.acquire() as conn:
            tests = await conn.fetch("""
                SELECT tr.*, e.name as exercise_name, e.muscle_group
                FROM user_tests tr
                JOIN exercises e ON tr.exercise_id = e.id
                WHERE tr.user_id = $1
                ORDER BY tr.tested_at DESC
                LIMIT 10
            """, user['id'])
        
        if tests:
            text = f"📊 **Ваши последние тесты ({len(tests)}):**\n\n"
            
            for test in tests:
                test_emoji = {
                    'strength': '🏋️',
                    'endurance': '⏱️',
                    'speed': '🏃',
                    'quantity': '🔢'
                }.get(test['test_type'], '💪')
                
                text += f"{test_emoji} **{test['exercise_name']}**\n"
                text += f"💪 {test['muscle_group']} • "
                
                if test['test_type'] == 'strength':
                    text += f"1ПМ {test['result_value']}кг"
                    if test['test_weight'] and test['test_reps']:
                        text += f" ({test['test_weight']}кг×{test['test_reps']})"
                elif test['test_type'] == 'endurance':
                    minutes = int(test['result_value'] // 60)
                    seconds = int(test['result_value'] % 60)
                    text += f"{minutes}:{seconds:02d}"
                elif test['test_type'] == 'speed':
                    text += f"{test['result_value']}сек"
                    if test['distance']:
                        text += f" на {test['distance']}м"
                elif test['test_type'] == 'quantity':
                    text += f"{int(test['result_value'])} раз"
                
                text += f" • {test['tested_at'].strftime('%d.%m')}\n\n"
        else:
            text = f"📊 **У вас пока нет тестов**\n\n"
            text += f"Пройдите первый тест, чтобы начать отслеживать прогресс!"
        
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="🔬 Новый тест", callback_data="new_test_menu")
        keyboard.button(text="📈 Прогресс", callback_data="test_progress")
        keyboard.button(text="🔙 К индивидуальным", callback_data="individual_tests_menu")
        keyboard.adjust(1)
        
        await callback.message.edit_text(
            text,
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    
    await callback.answer()

async def test_progress(callback: CallbackQuery):
    """ПОЛНОЦЕННАЯ функция прогресса тестов"""
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    
    try:
        async with db_manager.pool.acquire() as conn:
            # Получаем общую статистику
            total_tests = await conn.fetchval("""
                SELECT COUNT(*) FROM one_rep_max 
                WHERE user_id = $1
            """, user['id'])
            
            # Последние 5 тестов
            recent_tests = await conn.fetch("""
                SELECT e.name, orm.weight, orm.reps, orm.formula_average,
                       orm.tested_at, orm.test_weight
                FROM one_rep_max orm
                JOIN exercises e ON orm.exercise_id = e.id
                WHERE orm.user_id = $1
                ORDER BY orm.tested_at DESC
                LIMIT 5
            """, user['id'])
            
            # Статистика по месяцам
            monthly_stats = await conn.fetchval("""
                SELECT COUNT(*) FROM one_rep_max 
                WHERE user_id = $1 
                AND tested_at > CURRENT_DATE - INTERVAL '30 days'
            """, user['id'])
            
            # Лучший результат
            best_result = await conn.fetchrow("""
                SELECT e.name, orm.formula_average, orm.tested_at
                FROM one_rep_max orm
                JOIN exercises e ON orm.exercise_id = e.id
                WHERE orm.user_id = $1
                ORDER BY orm.formula_average DESC
                LIMIT 1
            """, user['id'])
            
            text = f"📈 **Ваш прогресс в тестах**\n\n"
            text += f"📊 **Общая статистика:**\n"
            text += f"• Всего тестов: {total_tests}\n"
            text += f"• За месяц: {monthly_stats}\n"
            
            if best_result:
                text += f"• Лучший 1ПМ: {best_result['formula_average']} кг ({best_result['name']})\n"
            
            text += f"\n"
            
            if recent_tests:
                text += f"🏃 **Последние тесты:**\n"
                for test in recent_tests[:3]:  # Показываем только 3 последних
                    test_date = test['tested_at'].strftime('%d.%m.%Y')
                    text += f"💪 **{test['name']}**\n"
                    text += f"   📊 {test['test_weight']} кг × {test['reps']} → 1ПМ: {test['formula_average']} кг\n"
                    text += f"   📅 {test_date}\n\n"
                    
                if len(recent_tests) > 3:
                    text += f"_И еще {len(recent_tests) - 3} тестов..._\n\n"
            else:
                text += f"⚠️ У вас пока нет завершенных тестов\n"
                text += f"Пройдите первый тест для отслеживания прогресса!\n\n"
            
            text += f"💡 Регулярное тестирование поможет отследить прогресс\n"
            text += f"и правильно планировать нагрузки в тренировках."
            
            keyboard = InlineKeyboardBuilder()
            if total_tests > 0:
                keyboard.button(text="🏆 Мои рекорды", callback_data="test_records")
                keyboard.button(text="📊 Детали", callback_data="detailed_progress")
            keyboard.button(text="🆕 Новый тест", callback_data="individual_tests_menu")
            keyboard.button(text="🔙 К тестам", callback_data="tests_menu")
            keyboard.adjust(2)
            
            await callback.message.edit_text(
                text,
                reply_markup=keyboard.as_markup(),
                parse_mode="Markdown"
            )
            
    except Exception as e:
        logger.error(f"Ошибка загрузки прогресса: {e}")
        await callback.message.edit_text(
            f"❌ Ошибка загрузки прогресса.\n\n"
            f"Попробуйте позже или обратитесь к администратору."
        )
    
    await callback.answer()

async def test_records(callback: CallbackQuery):
    """ПОЛНОЦЕННАЯ функция рекордов тестов"""
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    
    try:
        async with db_manager.pool.acquire() as conn:
            # Получаем лучшие результаты по каждому упражнению
            records = await conn.fetch("""
                WITH best_results AS (
                    SELECT DISTINCT ON (exercise_id)
                        exercise_id, formula_average, test_weight, reps, tested_at
                    FROM one_rep_max 
                    WHERE user_id = $1
                    ORDER BY exercise_id, formula_average DESC
                )
                SELECT e.name, e.muscle_group, br.formula_average, 
                       br.test_weight, br.reps, br.tested_at
                FROM best_results br
                JOIN exercises e ON br.exercise_id = e.id
                ORDER BY br.formula_average DESC
            """, user['id'])
            
            if records:
                text = f"🏆 **Ваши рекорды**\n\n"
                
                # Топ-3 лучших результата
                text += f"🥇 **Топ-3 лучших 1ПМ:**\n"
                for i, record in enumerate(records[:3], 1):
                    medal = ["🥇", "🥈", "🥉"][i-1]
                    text += f"{medal} **{record['name']}** ({record['muscle_group']})\n"
                    text += f"   🎯 1ПМ: **{record['formula_average']} кг**\n"
                    text += f"   📊 Тест: {record['test_weight']} кг × {record['reps']}\n"
                    text += f"   📅 {record['tested_at'].strftime('%d.%m.%Y')}\n\n"
                
                # Остальные рекорды
                if len(records) > 3:
                    text += f"📋 **Остальные рекорды:**\n"
                    for record in records[3:]:
                        text += f"💪 **{record['name']}**: {record['formula_average']} кг\n"
                        text += f"   📊 {record['test_weight']} × {record['reps']} | {record['tested_at'].strftime('%d.%m')}\n\n"
                
                text += f"🎯 **Всего упражнений с рекордами:** {len(records)}"
            else:
                text = f"🏆 **Ваши рекорды**\n\n"
                text += f"⚠️ У вас пока нет рекордов\n\n"
                text += f"Пройдите тесты чтобы установить первые рекорды!\n\n"
                text += f"💡 Рекорды помогают отслеживать прогресс\n"
                text += f"и мотивируют к новым достижениям."
            
            keyboard = InlineKeyboardBuilder()
            if records:
                keyboard.button(text="📈 Мой прогресс", callback_data="test_progress")
                keyboard.button(text="🎖️ Достижения", callback_data="my_achievements")
            keyboard.button(text="💪 Новый тест", callback_data="individual_tests_menu")
            keyboard.button(text="🔙 К тестам", callback_data="tests_menu")
            keyboard.adjust(2)
            
            await callback.message.edit_text(
                text,
                reply_markup=keyboard.as_markup(),
                parse_mode="Markdown"
            )
            
    except Exception as e:
        logger.error(f"Ошибка загрузки рекордов: {e}")
        await callback.message.edit_text(f"❌ Ошибка загрузки рекордов: {e}")
    
    await callback.answer()

# ===== ФУНКЦИЯ ДЛЯ ТРЕНИРОВОК =====

async def get_user_test_result_for_workout(user_id: int, exercise_id: int):
    """Получить последний результат теста пользователя для упражнения"""
    try:
        async with db_manager.pool.acquire() as conn:
            result = await conn.fetchrow("""
                SELECT * FROM user_tests
                WHERE user_id = $1 AND exercise_id = $2
                ORDER BY tested_at DESC LIMIT 1
            """, user_id, exercise_id)
        return result
    except:
        return None

# ===== ОБРАБОТКА ТЕКСТОВЫХ СООБЩЕНИЙ =====

async def process_test_text_input(message: Message, state: FSMContext):
    """Обработка текстовых вводов для индивидуальных тестов"""
    current_state = await state.get_state()
    
    if current_state == "waiting_search_for_test":
        await handle_test_exercise_search(message, state)
    elif current_state == "waiting_strength_test_data":
        await process_strength_test_data(message, state)
    elif current_state == "waiting_endurance_test_data":
        await process_endurance_test_data(message, state)
    elif current_state == "waiting_speed_test_data":
        await process_speed_test_data(message, state)
    elif current_state == "waiting_quantity_test_data":
        await process_quantity_test_data(message, state)
    else:
        await message.answer("❓ Используйте меню для навигации.")

# ===== РЕГИСТРАЦИЯ ОБРАБОТЧИКОВ =====

def register_test_handlers(dp):
    """Регистрация обработчиков универсальных тестов"""
    # ГЛАВНОЕ МЕНЮ ТЕСТОВ
    dp.callback_query.register(tests_menu, F.data == "tests_menu")
    
    # БАТАРЕИ ТЕСТОВ - ПЕРЕНАПРАВЛЕНИЯ
    dp.callback_query.register(coach_batteries_menu, F.data == "coach_batteries")
    dp.callback_query.register(player_batteries_menu, F.data == "player_batteries")
    
    # ПОЛНОЦЕННЫЕ ФУНКЦИИ ВМЕСТО ЗАГЛУШЕК
    dp.callback_query.register(team_analytics, F.data == "team_analytics")
    dp.callback_query.register(public_test_sets, F.data == "public_test_sets")
    dp.callback_query.register(my_achievements, F.data == "my_achievements")
    
    # ИНДИВИДУАЛЬНЫЕ ТЕСТЫ
    dp.callback_query.register(individual_tests_menu, F.data == "individual_tests_menu")
    dp.callback_query.register(new_test_menu, F.data == "new_test_menu")
    dp.callback_query.register(my_tests, F.data == "my_tests")
    dp.callback_query.register(test_progress, F.data == "test_progress")
    dp.callback_query.register(test_records, F.data == "test_records")
    
    # ПОИСК УПРАЖНЕНИЙ ДЛЯ ТЕСТОВ
    dp.callback_query.register(search_exercise_by_name_for_test, F.data == "search_by_name")
    dp.callback_query.register(search_by_category_for_test, F.data == "search_by_category")
    dp.callback_query.register(search_by_muscle_for_test, F.data == "search_by_muscle")
    
    # ПРОСМОТР УПРАЖНЕНИЙ ПО КАТЕГОРИЯМ/ГРУППАМ
    dp.callback_query.register(show_test_category_exercises, F.data.startswith("test_cat_"))
    dp.callback_query.register(show_test_muscle_exercises, F.data.startswith("test_muscle_"))
    
    # ПРОХОЖДЕНИЕ ТЕСТОВ
    dp.callback_query.register(start_exercise_test, F.data.startswith("test_"))




__all__ = [
    'register_test_handlers',
    'process_test_text_input',
    'get_user_test_result_for_workout'
]