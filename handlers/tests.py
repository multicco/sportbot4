# ===== ИСПРАВЛЕННЫЙ handlers/tests.py БЕЗ КНОПКИ ТРЕНИРОВОК =====

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
        text += f"👨‍🏫 **Тренерская панель:**\n"
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
    # ✅ ИСПРАВЛЕНИЕ: Проверяем тип данных
    if isinstance(test_data, str):
        return {
            'valid': False,
            'errors': [f"Получена строка вместо словаря: '{test_data}'"],
            'data': {}
        }
    
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
    
    return result


def parse_strength_test_input(text: str) -> Dict[str, Any]:
    """
    ИСПРАВЛЕННЫЙ парсинг ввода пользователя
    """
    try:
        original_text = text
        text = text.strip().lower()

        # Убираем единицы измерения
        text = re.sub(r'(кг|kg)', ' ', text)
        text = re.sub(r'(раз|повт)', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()

        # Ищем числа
        numbers = re.findall(r'\d+\.?\d*', text)

        if len(numbers) >= 2:
            return {
                'weight': float(numbers[0]),
                'reps': int(float(numbers[1])),
                'original_text': original_text,
                'parsed_successfully': True
            }
        elif len(numbers) == 1:
            return {
                'error': 'found_one_number',
                'number': float(numbers[0]),
                'original_text': original_text,
                'parsed_successfully': False
            }
        else:
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

# ===== ОБЩИЕ ЗАГЛУШКИ =====
async def team_analytics(callback: CallbackQuery):
    """Временная заглушка"""
    await callback.answer("🚧 В разработке - аналитика команды")

async def public_test_sets(callback: CallbackQuery):
    """Временная заглушка"""
    await callback.answer("🚧 В разработке - публичные тесты")

async def my_achievements(callback: CallbackQuery):
    """Временная заглушка"""
    await callback.answer("🚧 В разработке - достижения")

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
            text = f"❌ Упражнения по запросу '{search_term}' не найдены\n\n" \
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
        statedata = await state.get_data()
        exercise_data = statedata.get('exercise', {})
        exercise_name = exercise_data.get('name', 'Упражнение')  # ✅
        exercise_id = statedata.get('exercise_id')  # ✅

        if not exercise_id:
            await message.answer("❌ Ошибка: упражнение не выбрано")
            await state.clear()
            return

        # ✅ ШАГ 1: Сначала ПАРСИМ строку в словарь
        parsed_result = parse_strength_test_input(message.text)

        # ✅ ШАГ 2: Проверяем успешность парсинга
        if not parsed_result.get('parsed_successfully', False):
            # Обработка ошибок парсинга
            error_type = parsed_result.get('error', 'unknown')

            if error_type == 'found_one_number':
                await message.answer(
                    f"❌ Найдено только одно число\n\n"
                    f"Введите **вес и повторения**:\n"
                    f"Например: `80 10`",
                    parse_mode="Markdown"
                )
            else:
                await message.answer(
                    f"❌ Неверный формат\n\n"
                    f"Введите: `вес повторения`\n"
                    f"Например: `80 10`",
                    parse_mode="Markdown"
                )
            return

        # ✅ ШАГ 3: Создаем СЛОВАРЬ с данными
        test_data = {
            'weight': parsed_result['weight'],
            'reps': parsed_result['reps'],
            'exercise_id': exercise_id,
            'exercise_name': exercise_name
        }

        # ✅ ШАГ 4: Теперь валидируем СЛОВАРЬ (а не строку!)
        validation = validate_test_data(test_data, 'strength')

        if not validation['valid']:
            error_text = "❌ **Ошибки в данных:**\n\n"
            for error in validation['errors']:
                error_text += f"• {error}\n"

            await message.answer(error_text, parse_mode="Markdown")
            return

        # ✅ ШАГ 5: Получаем валидные данные и делаем расчет
        valid_data = validation['data']
        weight = valid_data['weight']
        reps = valid_data['reps']

        # Расчет 1ПМ
        def calculate_1rm(w: float, r: int):
            if r == 1:
                return {'brzycki': w, 'epley': w, 'lander': w, 'average': w}

            brzycki = w / (1.0278 - 0.0278 * r)
            epley = w * (1 + r / 30.0)
            lander = (100 * w) / (101.3 - 2.67123 * r)
            average = (brzycki + epley + lander) / 3.0

            return {
                'brzycki': round(brzycki, 1),
                'epley': round(epley, 1),
                'lander': round(lander, 1),
                'average': round(average, 1)
            }

        results = calculate_1rm(weight, reps)

        # Сохранение в БД
        from database import db_manager
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

        # Показ результата
        text = f"🎉 **Результат силового теста**\n\n"
        text += f"💪 **Упражнение:** {exercise_name}\n"
        text += f"📊 **Результат:** {weight} кг × {reps} повт.\n\n"

        text += f"**📈 1ПМ по формулам:**\n"
        text += f"• **Brzycki:** {results['brzycki']} кг\n"
        text += f"• **Epley:** {results['epley']} кг\n"
        text += f"• **Lander:** {results['lander']} кг\n\n"

        text += f"🎯 **Ваш 1ПМ: {results['average']} кг**\n"
        text += f"_(среднее по 3 формулам)_"

        from aiogram.utils.keyboard import InlineKeyboardBuilder
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="💪 Новый тест", callback_data="new_strength_test")
        keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
        keyboard.adjust(2)

        await message.answer(text, reply_markup=keyboard.as_markup(), parse_mode="Markdown")
        await state.clear()

    except Exception as e:
        logger.error(f"Ошибка в process_strength_test_data: {e}")
        await message.answer("❌ Произошла ошибка при обработке теста")
        await state.clear()

async def process_endurance_test_data(message: Message, state: FSMContext):
    """Обработка данных теста выносливости"""
    test_data = message.text.strip()
    data = await state.get_data()
    exercise = data['exercise']
    user = await db_manager.get_user_by_telegram_id(message.from_user.id)
    
    validation = validate_test_data(test_data, 'endurance')
    if not validation['valid']:
        await message.answer(f"❌ Ошибки: {', '.join(validation['errors'])}")
        return
    
    try:
        async with db_manager.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO test_results 
                (user_id, exercise_id, test_type, result_value, result_unit, duration_seconds)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, user['id'], data['exercise_id'], 'endurance', 
                 validation['seconds'], 'сек', validation['seconds'])
        
        text = f"✅ **Тест выносливости завершен!**\n\n"
        text += f"⏱️ **Упражнение:** {exercise['name']}\n"
        text += f"💪 **Результат:** {validation['formatted_time']}\n"
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
            await conn.execute("""
                INSERT INTO test_results 
                (user_id, exercise_id, test_type, result_value, result_unit, time_seconds, distance)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, user['id'], data['exercise_id'], 'speed', 
                 validation['time'], 'сек', validation['time'], validation['distance'])
        
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
                INSERT INTO test_results 
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
                FROM test_results tr
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
    """Показать прогресс по тестам"""
    await callback.answer("🚧 В разработке - анализ прогресса по тестам")

async def test_records(callback: CallbackQuery):
    """Показать рекорды пользователя"""
    await callback.answer("🚧 В разработке - личные рекорды")

# ===== ФУНКЦИЯ ДЛЯ ТРЕНИРОВОК =====
async def get_user_test_result_for_workout(user_id: int, exercise_id: int):
    """Получить последний результат теста пользователя для упражнения"""
    try:
        async with db_manager.pool.acquire() as conn:
            result = await conn.fetchrow("""
                SELECT * FROM test_results 
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
    
    # ОБЩИЕ ЗАГЛУШКИ
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