# ===== БАТАРЕИ ТЕСТОВ - handlers/test_batteries.py =====

from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import db_manager
from utils.validators import validate_test_data
import secrets
import string
import asyncio
from aiogram import F, Router
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import db_manager
import logging

logger = logging.getLogger(__name__)

# ===== СОСТОЯНИЯ FSM =====
from aiogram.fsm.state import State, StatesGroup

class CreateBatteryStates(StatesGroup):
    """Состояния создания батареи тестов"""
    waiting_name = State()
    waiting_description = State()
    selecting_exercises = State()

class EditBatteryStates(StatesGroup):
    """Состояния редактирования батареи тестов"""
    adding_exercises = State()

class JoinBatteryStates(StatesGroup):
    """Состояния присоединения к батарее"""
    waiting_battery_code = State()

# ===== ГЛАВНОЕ МЕНЮ ДЛЯ ТРЕНЕРОВ =====
async def coach_batteries_main_menu(callback: CallbackQuery):
    """Главное меню батарей тестов для тренера"""
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    
    if user['role'] not in ['coach', 'admin']:
        await callback.answer("❌ Только тренеры могут управлять батареями!")
        return
    
    try:
        async with db_manager.pool.acquire() as conn:
            # Статистика батарей тренера (если есть таблицы)
            try:
                stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_batteries,
                        COUNT(*) FILTER (WHERE is_active = true) as active_batteries
                    FROM test_sets WHERE created_by = $1
                """, user['id'])
            except:
                stats = {'total_batteries': 0, 'active_batteries': 0}
    
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="📋 Мои батареи", callback_data="my_batteries")
        keyboard.button(text="➕ Создать батарею", callback_data="create_battery")
        keyboard.button(text="📊 Аналитика команды", callback_data="team_analytics")
        keyboard.button(text="🔙 К тестам", callback_data="tests_menu")
        keyboard.adjust(2)
        
        text = f"📋 **Батареи тестов - Тренерская панель**\n\n"
        
        total_batteries = stats['total_batteries'] or 0
        if total_batteries > 0:
            text += f"📊 **Ваша статистика:**\n"
            text += f"• Создано батарей: **{total_batteries}**\n"
            text += f"• Активных батарей: **{stats['active_batteries'] or 0}**\n\n"
        
        text += f"💡 **Концепция батарей тестов:**\n"
        text += f"• 'Тест силы межсезон' (5-10 силовых упражнений)\n"
        text += f"• 'Диагностика скорости' (спринты, челночный бег)\n"
        text += f"• 'Оценка новичков' (комплексная батарея)\n\n"
        
        text += f"🎯 **Возможности:**\n"
        text += f"• Создание именованных батарей тестов\n"
        text += f"• Добавление 5-10 упражнений в батарею\n"
        text += f"• Редактирование батарей (даже с участниками)\n"
        text += f"• Назначение батарей команде\n"
        text += f"• Отслеживание прогресса участников\n\n"
        
        text += f"**Выберите действие:**"
        
        await callback.message.edit_text(
            text,
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    
    await callback.answer()

# ===== МОИ БАТАРЕИ ТЕСТОВ =====
async def my_batteries(callback: CallbackQuery):
    """Показать батареи тестов тренера"""
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    
    try:
        async with db_manager.pool.acquire() as conn:
            batteries = await conn.fetch("""
                SELECT 
                    ts.*,
                    COUNT(DISTINCT tse.id) as exercises_count,
                    COUNT(DISTINCT tsp.id) as participants_count
                FROM test_sets ts
                LEFT JOIN test_set_exercises tse ON ts.id = tse.test_set_id
                LEFT JOIN test_set_participants tsp ON ts.id = tsp.test_set_id
                WHERE ts.created_by = $1 AND ts.is_active = true
                GROUP BY ts.id
                ORDER BY ts.created_at DESC
                LIMIT 10
            """, user['id'])
        
        if batteries:
            text = f"📋 **Ваши батареи тестов ({len(batteries)}):**\n\n"
            
            keyboard = InlineKeyboardBuilder()
            
            for battery in batteries:
                text += f"📋 **{battery['name']}**\n"
                text += f"📊 Упражнений: {battery['exercises_count']} • 👥 Участников: {battery['participants_count']}\n"
                text += f"🔒 Код: `{battery['access_code']}`\n"
                
                if battery['description']:
                    text += f"📝 _{battery['description'][:50]}{'...' if len(battery['description']) > 50 else ''}_\n"
                
                text += f"📅 {battery['created_at'].strftime('%d.%m.%Y')}\n\n"
                
                keyboard.button(
                    text=f"📋 {battery['name'][:25]}{'...' if len(battery['name']) > 25 else ''}", 
                    callback_data=f"view_battery_{battery['id']}"
                )
            
            keyboard.button(text="➕ Создать новую", callback_data="create_battery")
            keyboard.button(text="🔙 Назад", callback_data="coach_batteries")
            keyboard.adjust(1)
            
        else:
            text = f"📋 **У вас пока нет батарей тестов**\n\n"
            text += f"Создайте первую батарею для диагностики команды!\n\n"
            text += f"💡 **Пример батарей:**\n"
            text += f"• 'Тест силы межсезон'\n"
            text += f"• 'Диагностика новичков'\n"
            text += f"• 'Контроль после травмы'"
            
            keyboard = InlineKeyboardBuilder()
            keyboard.button(text="➕ Создать батарею", callback_data="create_battery")
            keyboard.button(text="🔙 Назад", callback_data="coach_batteries")
        
        await callback.message.edit_text(
            text,
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    
    await callback.answer()

# ===== СОЗДАНИЕ БАТАРЕИ ТЕСТОВ =====
async def create_battery(callback: CallbackQuery, state: FSMContext):
    """Начало создания новой батареи тестов"""
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    
    if user['role'] not in ['coach', 'admin']:
        await callback.answer("❌ Только тренеры могут создавать батареи тестов!")
        return
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="❌ Отменить", callback_data="my_batteries")
    
    await callback.message.edit_text(
        "📋 **Создание батареи тестов**\n\n"
        "🎯 **Что такое батарея тестов?**\n"
        "Это именованный набор упражнений для диагностики\n"
        "определенного аспекта подготовки спортсменов.\n\n"
        "📋 **Примеры батарей:**\n"
        "• 'Тест силы межсезон'\n"
        "• 'Диагностика скорости'\n"
        "• 'Входная оценка новичков'\n"
        "• 'Контроль после травмы'\n\n"
        "📝 **Введите название батареи тестов:**\n"
        "_Рекомендуется до 50 символов_",
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    await state.set_state(CreateBatteryStates.waiting_name)
    await callback.answer()

async def process_battery_name(message: Message, state: FSMContext):
    """Обработка названия батареи тестов"""
    battery_name = message.text.strip()
    
    if len(battery_name) < 3:
        await message.answer("❌ Название слишком короткое. Минимум 3 символа.")
        return
        
    if len(battery_name) > 100:
        await message.answer("❌ Название слишком длинное. Максимум 100 символов.")
        return
    
    await state.update_data(name=battery_name)
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="⏭️ Пропустить описание", callback_data="skip_battery_description")
    keyboard.button(text="❌ Отменить", callback_data="cancel_battery_creation")
    
    await message.answer(
        f"✅ **Название:** {battery_name}\n\n"
        f"📝 **Введите описание батареи** (необязательно):\n"
        f"_Например: 'Диагностика силовых показателей после межсезонья'_\n\n"
        f"Или пропустите этот шаг:",
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    await state.set_state(CreateBatteryStates.waiting_description)

async def process_battery_description(message: Message, state: FSMContext):
    """Обработка описания батареи тестов"""
    description = message.text.strip()
    
    if len(description) > 500:
        await message.answer("❌ Описание слишком длинное. Максимум 500 символов.")
        return
    
    await state.update_data(description=description)
    await save_battery_to_database(message, state)

async def skip_battery_description(callback: CallbackQuery, state: FSMContext):
    """Пропуск описания и сохранение батареи"""
    await state.update_data(description="")
    await save_battery_to_database(callback.message, state)
    await callback.answer()

async def save_battery_to_database(message, state: FSMContext):
    """Сохранение батареи тестов в базу данных"""
    data = await state.get_data()
    user = await db_manager.get_user_by_telegram_id(message.from_user.id)
    
    try:
        async with db_manager.pool.acquire() as conn:
            # Сохраняем набор тестов (используем существующую таблицу test_sets)
            test_set_id = await conn.fetchval("""
                INSERT INTO test_sets (name, description, created_by, visibility)
                VALUES ($1, $2, $3, $4)
                RETURNING id
            """, data['name'], data.get('description', ''), user['id'], 'private')
            
            # Получаем сгенерированный код
            test_set = await conn.fetchrow("""
                SELECT access_code FROM test_sets WHERE id = $1
            """, test_set_id)
        
        # Формируем сообщение об успешном создании
        text = f"🎉 **Батарея тестов создана успешно!**\n\n"
        text += f"📋 **Название:** {data['name']}\n"
        text += f"👁️ **Видимость:** 🔒 Приватная\n"
        text += f"🆔 **Код доступа:** `{test_set['access_code']}`\n\n"
        
        if data.get('description'):
            text += f"📝 **Описание:** {data['description']}\n\n"
        
        text += f"🎯 **Что дальше:**\n"
        text += f"• Добавьте упражнения в батарею\n"
        text += f"• Поделитесь кодом `{test_set['access_code']}` с участниками\n"
        text += f"• Отслеживайте прогресс команды\n\n"
        text += f"💡 **Участники смогут присоединиться по коду!**"
        
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="➕ Добавить упражнения", callback_data=f"add_exercises_{test_set_id}")
        keyboard.button(text="📋 Мои батареи", callback_data="my_batteries")
        keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
        keyboard.adjust(1)
        
        await message.answer(
            text,
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )
        
        await state.clear()
        
    except Exception as e:
        await message.answer(f"❌ Ошибка создания батареи тестов: {e}")

# ===== ПРОСМОТР БАТАРЕИ =====
async def view_battery_details(callback: CallbackQuery):
    """Просмотр деталей батареи"""
    battery_id = int(callback.data.split("_")[2])  # view_battery_{id}
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    
    try:
        async with db_manager.pool.acquire() as conn:
            # Получаем информацию о батарее
            battery = await conn.fetchrow("""
                SELECT ts.*, COUNT(DISTINCT tse.id) as exercises_count,
                       COUNT(DISTINCT tsp.id) as participants_count
                FROM test_sets ts
                LEFT JOIN test_set_exercises tse ON ts.id = tse.test_set_id
                LEFT JOIN test_set_participants tsp ON ts.id = tsp.test_set_id
                WHERE ts.id = $1 AND ts.created_by = $2
                GROUP BY ts.id
            """, battery_id, user['id'])
            
            if not battery:
                await callback.answer("❌ Батарея не найдена!")
                return
            
            # Получаем упражнения в батарее
            exercises = await conn.fetch("""
                SELECT tse.id, e.name, e.muscle_group, e.test_type
                FROM test_set_exercises tse
                JOIN exercises e ON tse.exercise_id = e.id
                WHERE tse.test_set_id = $1
                ORDER BY tse.id
            """, battery_id)
        
        text = f"📋 **{battery['name']}**\n\n"
        text += f"🔒 **Код доступа:** `{battery['access_code']}`\n"
        text += f"👥 **Участников:** {battery['participants_count']}\n"
        text += f"📊 **Упражнений:** {battery['exercises_count']}\n"
        text += f"📅 **Создано:** {battery['created_at'].strftime('%d.%m.%Y')}\n\n"
        
        if battery['description']:
            text += f"📝 **Описание:** {battery['description']}\n\n"
        
        if exercises:
            text += f"🏋️ **Упражнения в батарее:**\n"
            for i, ex in enumerate(exercises, 1):
                test_emoji = {
                    'strength': '🏋️',
                    'endurance': '⏱️',
                    'speed': '🏃',
                    'quantity': '🔢',
                    'none': '💪'
                }.get(ex['test_type'] if ex['test_type'] else 'none', '💪')
                text += f"{i}. {test_emoji} {ex['name']} • {ex['muscle_group']}\n"
        else:
            text += f"📭 **Упражнений пока нет**\n"
            text += f"Добавьте упражнения, чтобы участники могли проходить тесты."
        
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="➕ Добавить упражнения", callback_data=f"add_exercises_{battery_id}")
        keyboard.button(text="🔧 Редактировать", callback_data=f"edit_battery_{battery_id}")
        keyboard.button(text="📊 Результаты участников", callback_data=f"battery_results_{battery_id}")
        keyboard.button(text="📋 Мои батареи", callback_data="my_batteries")
        keyboard.adjust(1)
        
        await callback.message.edit_text(
            text,
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    
    await callback.answer()

# ===== ДОБАВЛЕНИЕ УПРАЖНЕНИЙ В БАТАРЕЮ =====
async def add_exercises_to_battery(callback: CallbackQuery, state: FSMContext):
    """Добавление упражнений в батарею"""
    battery_id = int(callback.data.split("_")[2])  # add_exercises_{id}
    await state.update_data(editing_battery_id=battery_id)
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔍 Поиск по названию", callback_data="search_for_battery")
    keyboard.button(text="📂 По категориям", callback_data="browse_cat_for_battery")
    keyboard.button(text="💪 По группам мышц", callback_data="browse_muscle_for_battery")
    keyboard.button(text="🔙 К батарее", callback_data=f"view_battery_{battery_id}")
    keyboard.adjust(1)
    
    text = f"➕ **Добавление упражнений в батарею**\n\n"
    text += f"🎯 **Рекомендации:**\n"
    text += f"• Обычно батарея содержит 5-10 упражнений\n"
    text += f"• Выбирайте упражнения под конкретную цель\n"
    text += f"• Комбинируйте разные типы тестов\n\n"
    text += f"**Выберите способ поиска упражнений:**"
    
    await callback.message.edit_text(
        text,
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    await state.set_state(EditBatteryStates.adding_exercises)
    await callback.answer()




async def process_1rm_test_input(message: Message, state: FSMContext):
    '''ИСПРАВЛЕННАЯ обработка ввода данных для теста 1ПМ'''
    try:
        # Парсим ввод пользователя
        parts = message.text.strip().split()

        if len(parts) != 2:
            await message.answer(
                "❌ Неверный формат. Введите данные через пробел:\n"
                "`вес повторения`\n\n"
                "**Примеры:**\n"
                "• `80 5` - 80 кг на 5 повторений\n"
                "• `60 10` - 60 кг на 10 повторений",
                parse_mode="Markdown"
            )
            return

        # Конвертируем в числа
        try:
            weight = float(parts[0])
            reps = int(parts[1])
        except ValueError:
            await message.answer(
                "❌ Используйте только числа.\n"
                "Пример: `80 5`",
                parse_mode="Markdown"
            )
            return

        # Валидация данных
        if weight <= 0:
            await message.answer("❌ Вес должен быть больше 0")
            return

        if reps <= 0 or reps > 30:
            await message.answer("❌ Количество повторений должно быть от 1 до 30")
            return

        # Получаем данные из состояния FSM
        state_data = await state.get_data()
        exercise_name = state_data.get('exercise_name', 'Упражнение')
        exercise_id = state_data.get('exercise_id')

        if not exercise_id:
            await message.answer("❌ Ошибка: не выбрано упражнение")
            await state.clear()
            return

        # Расчет 1ПМ по трем формулам
        def calculate_1rm(w, r):
            '''Расчет 1ПМ по формулам Бжицкого, Эпли и альтернативной'''
            w = float(w)
            r = int(r)

            # Если уже 1 повторение, то это и есть 1ПМ
            if r == 1:
                return {
                    'brzycki': w,
                    'epley': w,
                    'alternative': w,
                    'average': w
                }

            # Формула Бжицкого: 1ПМ = вес / (1.0278 - 0.0278 × повторения)
            brzycki = w / (1.0278 - 0.0278 * r)

            # Формула Эпли: 1ПМ = вес × (1 + повторения / 30)
            epley = w * (1 + r / 30.0)

            # Альтернативная формула: 1ПМ = вес × (1 + 0.025 × повторения)  
            alternative = w * (1 + 0.025 * r)

            # Среднее по трем формулам
            average = (brzycki + epley + alternative) / 3.0

            return {
                'brzycki': round(brzycki, 1),
                'epley': round(epley, 1),
                'alternative': round(alternative, 1),
                'average': round(average, 1)
            }

        # Выполняем расчет
        results = calculate_1rm(weight, reps)

        # Сохраняем результат в базу данных
        user = await db_manager.get_user_by_telegram_id(message.from_user.id)

        if not user:
            await message.answer("❌ Пользователь не найден в базе данных")
            return

        async with db_manager.pool.acquire() as conn:
            # Сохраняем результат теста
            await conn.execute('''
                INSERT INTO one_rep_max (
                    user_id, exercise_id, weight, reps, test_weight,
                    formula_brzycki, formula_epley, formula_alternative, formula_average
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ''', 
            user['id'], int(exercise_id), results['average'], 
            reps, weight, results['brzycki'], results['epley'],
            results['alternative'], results['average'])

        # Формируем сообщение с результатами
        text = f"🎉 **Результат теста 1ПМ**\n\n"
        text += f"💪 **Упражнение:** {exercise_name}\n"
        text += f"📊 **Ваши данные:** {weight} кг × {reps} {'повторение' if reps == 1 else 'повторения' if reps < 5 else 'повторений'}\n\n"

        text += f"**📈 Расчет по формулам:**\n"
        text += f"• Бжицкого: **{results['brzycki']} кг**\n"
        text += f"• Эпли: **{results['epley']} кг**\n"
        text += f"• Альтернативная: **{results['alternative']} кг**\n\n"

        text += f"🎯 **Ваш 1ПМ: {results['average']} кг**\n"
        text += f"_(среднее арифметическое по 3 формулам)_\n\n"

        # Добавляем процентовки для тренировок
        text += f"**💡 Рекомендации для тренировок:**\n"
        text += f"• 50%: {round(results['average'] * 0.5, 1)} кг (разминка)\n"
        text += f"• 70%: {round(results['average'] * 0.7, 1)} кг (выносливость)\n"
        text += f"• 85%: {round(results['average'] * 0.85, 1)} кг (сила)\n"
        text += f"• 95%: {round(results['average'] * 0.95, 1)} кг (максимальная сила)"

        # Создаем клавиатуру
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="💪 Новый тест", callback_data="new_1rm_test")
        keyboard.button(text="📊 Мои результаты", callback_data="my_1rm_results")
        keyboard.button(text="🏋️ Создать тренировку", callback_data="create_workout")
        keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
        keyboard.adjust(2)

        await message.answer(
            text,
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )

        # Очищаем состояние FSM
        await state.clear()

        logger.info(f"Пользователь {message.from_user.id} прошел тест 1ПМ: {exercise_name}, результат: {results['average']} кг")

    except Exception as e:
        logger.error(f"Ошибка в process_1rm_test_input: {e}")
        await message.answer(
            f"❌ Произошла ошибка при обработке теста:\n{str(e)}\n\n"
            f"Попробуйте еще раз или обратитесь к администратору."
        )
        await state.clear()

async def process_test_text_input(message: Message, state: FSMContext):
    '''Обработка других типов тестовых вводов'''
    current_state = await state.get_state()

    # Обрабатываем поиск упражнений для тестов
    if current_state == "waiting_search_for_test":
        await handle_test_exercise_search(message, state)
        return

    # Другие типы тестов можно добавить здесь
    await message.answer(
        f"⚠️ Обработка состояния '{current_state}' еще не реализована.\n"
        f"Используйте меню для навигации.",
        parse_mode="Markdown"
    )
    await state.clear()

async def handle_test_exercise_search(message: Message, state: FSMContext):
    '''Поиск упражнений для тестов'''
    search_term = message.text.lower().strip()

    try:
        async with db_manager.pool.acquire() as conn:
            # Ищем упражнения подходящие для тестов (обычно силовые)
            exercises = await conn.fetch('''
                SELECT id, name, category, muscle_group 
                FROM exercises 
                WHERE (LOWER(name) LIKE $1 OR LOWER(muscle_group) LIKE $1)
                  AND category IN ('Силовые', 'Функциональные')
                ORDER BY 
                  CASE WHEN LOWER(name) LIKE $1 THEN 1 ELSE 2 END,
                  name
                LIMIT 10
            ''', f"%{search_term}%")

            if exercises:
                text = f"🔍 **Найдено упражнений: {len(exercises)}**\n\n"
                keyboard = InlineKeyboardBuilder()

                for ex in exercises:
                    keyboard.button(
                        text=f"{ex['name']} ({ex['muscle_group']})",
                        callback_data=f"test_exercise_{ex['id']}"
                    )

                keyboard.button(text="🔙 К тестам", callback_data="tests_menu")
                keyboard.adjust(1)

                await message.answer(
                    text + "Выберите упражнение для теста:",
                    reply_markup=keyboard.as_markup(),
                    parse_mode="Markdown"
                )
            else:
                keyboard = InlineKeyboardBuilder()
                keyboard.button(text="🔄 Новый поиск", callback_data="search_exercise_for_test")
                keyboard.button(text="🔙 К тестам", callback_data="tests_menu")

                await message.answer(
                    f"❌ Упражнения по запросу '{search_term}' не найдены.\n\n"
                    f"Попробуйте другие ключевые слова.",
                    reply_markup=keyboard.as_markup()
                )

        await state.clear()

    except Exception as e:
        logger.error(f"Ошибка поиска упражнений для тестов: {e}")
        await message.answer("❌ Ошибка поиска. Попробуйте еще раз.")
        await state.clear()

async def search_exercises_for_battery(callback: CallbackQuery, state: FSMContext):
    """Поиск упражнений для батареи по названию"""
    await callback.message.edit_text(
        "🔍 **Поиск упражнения для батареи**\n\n"
        "Введите название упражнения:\n"
        "_Например: жим, приседания, планка, бег_\n\n"
        "💡 **Найденные упражнения можно будет добавить в батарею**",
        parse_mode="Markdown"
    )
    await callback.answer()

async def browse_categories_for_battery(callback: CallbackQuery):
    """Просмотр категорий упражнений для батареи"""
    try:
        async with db_manager.pool.acquire() as conn:
            categories = await conn.fetch("SELECT DISTINCT category FROM exercises ORDER BY category")
        
        keyboard = InlineKeyboardBuilder()
        
        for cat in categories:
            keyboard.button(
                text=f"📂 {cat['category']}", 
                callback_data=f"battery_cat_{cat['category']}"
            )
        
        keyboard.button(text="🔙 К добавлению", callback_data="back_to_add_exercises")
        keyboard.adjust(2)
        
        await callback.message.edit_text(
            "📂 **Выберите категорию упражнений для батареи:**\n\n"
            "💡 **Выбранные упражнения будут добавлены в батарею**",
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    await callback.answer()

async def browse_muscle_groups_for_battery(callback: CallbackQuery):
    """Просмотр групп мышц для батареи"""
    try:
        async with db_manager.pool.acquire() as conn:
            muscle_groups = await conn.fetch("SELECT DISTINCT muscle_group FROM exercises ORDER BY muscle_group")
        
        keyboard = InlineKeyboardBuilder()
        
        for mg in muscle_groups:
            keyboard.button(
                text=f"💪 {mg['muscle_group']}", 
                callback_data=f"battery_muscle_{mg['muscle_group']}"
            )
        
        keyboard.button(text="🔙 К добавлению", callback_data="back_to_add_exercises")
        keyboard.adjust(2)
        
        await callback.message.edit_text(
            "💪 **Выберите группу мышц для батареи:**\n\n"
            "💡 **Выбранные упражнения будут добавлены в батарею**",
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    await callback.answer()

async def show_battery_category_exercises(callback: CallbackQuery, state: FSMContext):
    """Показать упражнения категории для добавления в батарею"""
    category = callback.data[12:]  # Убираем "battery_cat_"
    
    try:
        async with db_manager.pool.acquire() as conn:
            exercises = await conn.fetch(
                "SELECT id, name, muscle_group, test_type FROM exercises WHERE category = $1 ORDER BY name",
                category
            )
        
        if exercises:
            text = f"📂 **{category} - добавить в батарею:**\n\n"
            
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
                    text=f"➕ {test_emoji} {ex['name']}", 
                    callback_data=f"add_to_battery_{ex['id']}"
                )
            
            keyboard.button(text="🔙 К категориям", callback_data="browse_cat_for_battery")
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

async def show_battery_muscle_exercises(callback: CallbackQuery, state: FSMContext):
    """Показать упражнения группы мышц для добавления в батарею"""
    muscle_group = callback.data[15:]  # Убираем "battery_muscle_"
    
    try:
        async with db_manager.pool.acquire() as conn:
            exercises = await conn.fetch(
                "SELECT id, name, category, test_type FROM exercises WHERE muscle_group = $1 ORDER BY name",
                muscle_group
            )
        
        if exercises:
            text = f"💪 **{muscle_group} - добавить в батарею:**\n\n"
            
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
                    text=f"➕ {test_emoji} {ex['name']}", 
                    callback_data=f"add_to_battery_{ex['id']}"
                )
            
            keyboard.button(text="🔙 К группам мышц", callback_data="browse_muscle_for_battery")
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

async def add_exercise_to_battery(callback: CallbackQuery, state: FSMContext):
    """Добавление упражнения в батарею"""
    exercise_id = int(callback.data.split("_")[3])  # add_to_battery_{id}
    data = await state.get_data()
    battery_id = data.get('editing_battery_id')
    
    if not battery_id:
        await callback.answer("❌ Ошибка: батарея не выбрана")
        return
    
    try:
        async with db_manager.pool.acquire() as conn:
            # Проверяем, что упражнения еще нет в батарее
            existing = await conn.fetchrow("""
                SELECT id FROM test_set_exercises 
                WHERE test_set_id = $1 AND exercise_id = $2
            """, battery_id, exercise_id)
            
            if existing:
                await callback.answer("⚠️ Это упражнение уже добавлено в батарею!")
                return
            
            # Добавляем упражнение
            await conn.execute("""
                INSERT INTO test_set_exercises (test_set_id, exercise_id)
                VALUES ($1, $2)
            """, battery_id, exercise_id)
            
            # Получаем название упражнения
            exercise = await conn.fetchrow("SELECT name FROM exercises WHERE id = $1", exercise_id)
            
            # Получаем обновленную информацию о батарее
            battery = await conn.fetchrow("""
                SELECT ts.name, COUNT(DISTINCT tse.id) as exercises_count
                FROM test_sets ts
                LEFT JOIN test_set_exercises tse ON ts.id = tse.test_set_id
                WHERE ts.id = $1
                GROUP BY ts.id, ts.name
            """, battery_id)
        
        await callback.answer(f"✅ '{exercise['name']}' добавлено!")
        
        # ИСПРАВЛЕНО: Показываем краткое сообщение об успешном добавлении
        text = f"✅ **Упражнение добавлено в батарею!**\n\n"
        text += f"📋 **Батарея:** {battery['name']}\n"
        text += f"➕ **Добавлено:** {exercise['name']}\n"
        text += f"📊 **Всего упражнений:** {battery['exercises_count']}\n\n"
        text += f"**Выберите действие:**"
        
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="➕ Добавить ещё", callback_data=f"add_exercises_{battery_id}")
        keyboard.button(text="📋 К батарее", callback_data=f"view_battery_{battery_id}")
        keyboard.button(text="📋 Мои батареи", callback_data="my_batteries")
        keyboard.adjust(1)
        
        await callback.message.edit_text(
            text,
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await callback.answer("❌ Ошибка добавления упражнения")
        print(f"Ошибка добавления упражнения: {e}")  # Для отладки


# ===== ГЛАВНОЕ МЕНЮ ДЛЯ ИГРОКОВ =====
async def player_batteries_main_menu(callback: CallbackQuery):
    """Главное меню батарей тестов для игроков"""
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="📋 Мои батареи", callback_data="my_assigned_batteries")
    keyboard.button(text="🔗 Присоединиться по коду", callback_data="join_battery")
    keyboard.button(text="📈 Мои результаты", callback_data="my_battery_results")
    keyboard.button(text="🔙 К тестам", callback_data="tests_menu")
    keyboard.adjust(1)
    
    try:
        async with db_manager.pool.acquire() as conn:
            # Статистика участника
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(DISTINCT tsp.test_set_id) as joined_batteries
                FROM test_set_participants tsp
                WHERE tsp.user_id = $1
            """, user['id'])
        
        joined_batteries = stats['joined_batteries'] or 0
        
        text = f"📋 **Мои батареи тестов**\n\n"
        
        if joined_batteries > 0:
            text += f"📊 **Ваша статистика:**\n"
            text += f"• Участвуете в батареях: **{joined_batteries}**\n\n"
            
            text += f"🎯 **Возможности:**\n"
            text += f"• Просматривать назначенные батареи\n"
            text += f"• Проходить тесты из батарей\n"
            text += f"• Отслеживать свой прогресс\n"
            text += f"• Присоединяться к новым батареям по коду\n\n"
        else:
            text += f"🆕 **Добро пожаловать в систему батарей тестов!**\n\n"
            text += f"📋 **Как это работает:**\n"
            text += f"• Тренер создает батарею тестов\n"
            text += f"• Вы присоединяетесь по коду\n"
            text += f"• Проходите назначенные тесты\n"
            text += f"• Тренер видит ваши результаты\n\n"
        
        text += f"**Выберите действие:**"
        
    except Exception as e:
        text = f"📋 **Мои батареи тестов**\n\n❌ Ошибка загрузки: {e}"
    
    await callback.message.edit_text(
        text,
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()

# ===== ПРИСОЕДИНЕНИЕ К БАТАРЕЕ =====
async def join_battery(callback: CallbackQuery, state: FSMContext):
    """Начало присоединения к батарее"""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="❌ Отменить", callback_data="player_batteries")
    
    await callback.message.edit_text(
        "🔗 **Присоединение к батарее тестов**\n\n"
        "Введите код доступа к батарее тестов:\n"
        "_Например: `TS-AB12` или `TS-XY-98`_\n\n"
        "💡 **Где взять код:**\n"
        "• У вашего тренера\n"
        "• В групповом чате команды\n"
        "• На доске объявлений спортзала",
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    await state.set_state(JoinBatteryStates.waiting_battery_code)
    await callback.answer()

async def process_battery_code(message: Message, state: FSMContext):
    """Обработка кода батареи"""
    code = message.text.strip().upper()
    user = await db_manager.get_user_by_telegram_id(message.from_user.id)
    
    try:
        async with db_manager.pool.acquire() as conn:
            # Ищем батарею по коду
            battery = await conn.fetchrow("""
                SELECT ts.*, COUNT(DISTINCT tse.id) as exercises_count
                FROM test_sets ts
                LEFT JOIN test_set_exercises tse ON ts.id = tse.test_set_id
                WHERE ts.access_code = $1 AND ts.is_active = true
                GROUP BY ts.id
            """, code)
            
            if not battery:
                await message.answer(
                    f"❌ **Батарея с кодом '{code}' не найдена**\n\n"
                    f"Проверьте код и попробуйте снова."
                )
                return
            
            # Проверяем, не присоединен ли уже
            existing = await conn.fetchrow("""
                SELECT id FROM test_set_participants 
                WHERE test_set_id = $1 AND user_id = $2
            """, battery['id'], user['id'])
            
            if existing:
                await message.answer(
                    f"⚠️ **Вы уже участвуете в этой батарее!**\n\n"
                    f"📋 **{battery['name']}**"
                )
                await state.clear()
                return
            
            # Присоединяем к батарее
            await conn.execute("""
                INSERT INTO test_set_participants (test_set_id, user_id)
                VALUES ($1, $2)
            """, battery['id'], user['id'])
        
        text = f"🎉 **Успешно присоединились к батарее!**\n\n"
        text += f"📋 **Название:** {battery['name']}\n"
        text += f"📊 **Упражнений:** {battery['exercises_count']}\n"
        text += f"📅 **Создано:** {battery['created_at'].strftime('%d.%m.%Y')}\n\n"
        
        if battery['description']:
            text += f"📝 **Описание:** {battery['description']}\n\n"
        
        text += f"🎯 **Теперь вы можете проходить тесты из этой батареи!**\n"
        text += f"Найдите её в разделе 'Мои батареи'."
        
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="📋 Мои батареи", callback_data="my_assigned_batteries")
        keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
        keyboard.adjust(1)
        
        await message.answer(
            text,
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )
        await state.clear()
        
    except Exception as e:
        await message.answer(f"❌ Ошибка присоединения: {e}")

# ===== ЗАГЛУШКИ =====
async def my_assigned_batteries(callback: CallbackQuery):
    """Временная заглушка"""
    await callback.answer("🚧 В разработке - мои назначенные батареи")

async def my_battery_results(callback: CallbackQuery):
    """Временная заглушка"""
    await callback.answer("🚧 В разработке - результаты батарей")

async def edit_battery(callback: CallbackQuery):
    """Временная заглушка"""
    await callback.answer("🚧 В разработке - редактирование батареи")

async def battery_results(callback: CallbackQuery):
    """Временная заглушка"""
    await callback.answer("🚧 В разработке - результаты участников")

async def cancel_battery_creation(callback: CallbackQuery, state: FSMContext):
    """Отмена создания батареи"""
    await state.clear()
    await my_batteries(callback)

async def back_to_add_exercises(callback: CallbackQuery, state: FSMContext):
    """Возврат к добавлению упражнений"""
    data = await state.get_data()
    battery_id = data.get('editing_battery_id')
    # callback.data — frozen-поле pydantic-модели aiogram 3.x, менять нельзя.
    # Рендерим экран напрямую, id батареи берём из FSM.
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔍 Поиск по названию", callback_data="search_for_battery")
    keyboard.button(text="📂 По категориям", callback_data="browse_cat_for_battery")
    keyboard.button(text="💪 По группам мышц", callback_data="browse_muscle_for_battery")
    keyboard.button(text="🔙 К батарее", callback_data=f"view_battery_{battery_id}")
    keyboard.adjust(1)

    text = (f"➕ **Добавление упражнений в батарею**\n\n"
            f"🎯 **Рекомендации:**\n"
            f"• Обычно батарея содержит 5-10 упражнений\n"
            f"• Выбирайте упражнения под конкретную цель\n"
            f"• Комбинируйте разные типы тестов\n\n"
            f"**Выберите способ поиска упражнений:**")
    await callback.message.edit_text(text, reply_markup=keyboard.as_markup(), parse_mode="Markdown")
    await callback.answer()

# ===== ОБРАБОТКА ТЕКСТОВЫХ СООБЩЕНИЙ =====
async def process_battery_text_input(message: Message, state: FSMContext):
    """Обработка текстовых вводов для батарей"""
    current_state = await state.get_state()
    
    if current_state == CreateBatteryStates.waiting_name:
        await process_battery_name(message, state)
    elif current_state == CreateBatteryStates.waiting_description:
        await process_battery_description(message, state)
    elif current_state == JoinBatteryStates.waiting_battery_code:
        await process_battery_code(message, state)
    elif current_state == EditBatteryStates.adding_exercises:
        await search_exercises_for_battery_text(message, state)
    else:
        await message.answer("🚧 Используйте кнопки для навигации")

async def search_exercises_for_battery_text(message: Message, state: FSMContext):
    """Поиск упражнений для батареи по тексту"""
    search_term = message.text.lower()
    data = await state.get_data()
    battery_id = data.get('editing_battery_id')
    
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
            text = f"🔍 **Найдено упражнений: {len(exercises)}**\n\n"
            text += f"💡 **Нажмите на упражнение чтобы добавить в батарею:**\n\n"
            
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
                    text=f"➕ {test_emoji} {ex['name']}", 
                    callback_data=f"add_to_battery_{ex['id']}"
                )
            
            keyboard.button(text="🔍 Новый поиск", callback_data=f"add_exercises_{battery_id}")
            keyboard.button(text="🔙 К батарее", callback_data=f"view_battery_{battery_id}")
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
            keyboard.button(text="🔍 Новый поиск", callback_data=f"add_exercises_{battery_id}")
            keyboard.button(text="🔙 К батарее", callback_data=f"view_battery_{battery_id}")
            
            await message.answer(text, reply_markup=keyboard.as_markup(), parse_mode="Markdown")
            
    except Exception as e:
        await message.answer(f"❌ Ошибка поиска: {e}")

# ===== РЕГИСТРАЦИЯ ОБРАБОТЧИКОВ =====
def register_battery_handlers(dp):
    """Регистрация обработчиков батарей тестов"""
    
    # Главное меню батарей
    dp.callback_query.register(coach_batteries_main_menu, F.data == "coach_batteries")
    dp.callback_query.register(player_batteries_main_menu, F.data == "player_batteries")
    
    # Создание батареи
    dp.callback_query.register(my_batteries, F.data == "my_batteries")
    dp.callback_query.register(create_battery, F.data == "create_battery")
    dp.callback_query.register(skip_battery_description, F.data == "skip_battery_description")
    dp.callback_query.register(cancel_battery_creation, F.data == "cancel_battery_creation")
    
    # Управление батареей
    dp.callback_query.register(view_battery_details, F.data.startswith("view_battery_"))
    dp.callback_query.register(add_exercises_to_battery, F.data.startswith("add_exercises_"))
    
    # Добавление упражнений
    dp.callback_query.register(search_exercises_for_battery, F.data == "search_for_battery")
    dp.callback_query.register(browse_categories_for_battery, F.data == "browse_cat_for_battery")
    dp.callback_query.register(browse_muscle_groups_for_battery, F.data == "browse_muscle_for_battery")
    dp.callback_query.register(show_battery_category_exercises, F.data.startswith("battery_cat_"))
    dp.callback_query.register(show_battery_muscle_exercises, F.data.startswith("battery_muscle_"))
    dp.callback_query.register(add_exercise_to_battery, F.data.startswith("add_to_battery_"))
    dp.callback_query.register(back_to_add_exercises, F.data == "back_to_add_exercises")
    
    # Присоединение к батарее
    dp.callback_query.register(join_battery, F.data == "join_battery")
    dp.callback_query.register(my_assigned_batteries, F.data == "my_assigned_batteries")
    dp.callback_query.register(my_battery_results, F.data == "my_battery_results")
    
    # Заглушки
    dp.callback_query.register(edit_battery, F.data.startswith("edit_battery_"))
    dp.callback_query.register(battery_results, F.data.startswith("battery_results_"))

__all__ = [
    'register_battery_handlers',
    'process_battery_text_input',
    'coach_batteries_main_menu',
    'player_batteries_main_menu'
]