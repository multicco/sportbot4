# ===== УНИВЕРСАЛЬНАЯ СИСТЕМА ТЕСТОВ =====

from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import db_manager
from keyboards.main_keyboards_old import get_tests_menu_keyboard, get_new_test_type_menu_keyboard, get_coming_soon_keyboard
from utils.validators import validate_test_data
from utils.formatters import format_test_results, format_test_history

def register_test_handlers(dp):
    """Регистрация обработчиков универсальных тестов"""
    
    # Главное меню тестов
    dp.callback_query.register(tests_menu, F.data == "tests_menu")
    dp.callback_query.register(new_test_menu, F.data == "new_test_menu")
    dp.callback_query.register(my_tests, F.data == "my_tests")
    dp.callback_query.register(test_progress, F.data == "test_progress")
    dp.callback_query.register(test_records, F.data == "test_records")
    
    # Выбор типа теста
    dp.callback_query.register(test_type_strength, F.data == "test_type_strength")
    dp.callback_query.register(test_type_endurance, F.data == "test_type_endurance")
    dp.callback_query.register(test_type_speed, F.data == "test_type_speed")
    dp.callback_query.register(test_type_quantity, F.data == "test_type_quantity")
    
    # Выбор упражнения для теста
    dp.callback_query.register(select_test_exercise, F.data.startswith("test_ex_"))
    
    # Прохождение тестов (из детального просмотра упражнений)
    dp.callback_query.register(start_exercise_test, F.data.startswith("test_"))

async def tests_menu(callback: CallbackQuery):
    """Главное меню тестов"""
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    
    # Получаем статистику пользователя
    try:
        async with db_manager.pool.acquire() as conn:
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_tests,
                    COUNT(DISTINCT exercise_id) as tested_exercises,
                    MAX(tested_at) as last_test_date
                FROM user_tests 
                WHERE user_id = $1
            """, user['id'])
        
        keyboard = get_tests_menu_keyboard()
        
        text = f"📊 **Система тестирования**\n\n"
        
        if stats['total_tests'] > 0:
            text += f"📈 **Ваша статистика:**\n"
            text += f"• Пройдено тестов: {stats['total_tests']}\n"
            text += f"• Упражнений протестировано: {stats['tested_exercises']}\n"
            if stats['last_test_date']:
                last_date = stats['last_test_date'].strftime('%d.%m.%Y')
                text += f"• Последний тест: {last_date}\n"
        else:
            text += f"🆕 **Добро пожаловать в систему тестирования!**\n\n"
            text += f"Пройдите первые тесты для отслеживания прогресса.\n"
        
        text += f"\n🎯 **Типы тестов:**\n"
        text += f"• 🏋️ **Силовые** - максимальный вес (1ПМ)\n"
        text += f"• ⏱️ **Выносливость** - время удержания\n" 
        text += f"• 🏃 **Скоростные** - время на дистанцию\n"
        text += f"• 🔢 **Количественные** - максимум повторений\n\n"
        text += f"**Выберите действие:**"
        
        await callback.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    
    await callback.answer()

async def new_test_menu(callback: CallbackQuery):
    """Меню выбора типа нового теста"""
    keyboard = get_new_test_type_menu_keyboard()
    
    await callback.message.edit_text(
        "🔬 **Выберите тип теста:**\n\n"
        "🏋️ **Силовые тесты**\n"
        "Определение максимального веса (1ПМ)\n"
        "_Примеры: жим лежа, приседания, становая тяга_\n\n"
        
        "⏱️ **Тесты выносливости**\n"
        "Максимальное время удержания позиции\n"
        "_Примеры: планка, вис на турнике, статические упражнения_\n\n"
        
        "🏃 **Скоростные тесты**\n" 
        "Минимальное время на фиксированную дистанцию\n"
        "_Примеры: бег 30м, 100м, спринты_\n\n"
        
        "🔢 **Количественные тесты**\n"
        "Максимальное количество повторений\n"
        "_Примеры: отжимания, подтягивания, приседания_",
        
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

async def test_type_strength(callback: CallbackQuery):
    """Показать силовые упражнения для тестирования"""
    await show_exercises_by_test_type(callback, 'strength', '🏋️ Силовые тесты')

async def test_type_endurance(callback: CallbackQuery):
    """Показать упражнения на выносливость для тестирования"""
    await show_exercises_by_test_type(callback, 'endurance', '⏱️ Тесты выносливости')

async def test_type_speed(callback: CallbackQuery):
    """Показать скоростные упражнения для тестирования"""
    await show_exercises_by_test_type(callback, 'speed', '🏃 Скоростные тесты')

async def test_type_quantity(callback: CallbackQuery):
    """Показать количественные упражнения для тестирования"""
    await show_exercises_by_test_type(callback, 'quantity', '🔢 Количественные тесты')

async def show_exercises_by_test_type(callback: CallbackQuery, test_type: str, title: str):
    """Показать упражнения определенного типа для тестирования"""
    try:
        async with db_manager.pool.acquire() as conn:
            exercises = await conn.fetch("""
                SELECT id, name, muscle_group, description, measurement_unit
                FROM exercises 
                WHERE test_type = $1 
                ORDER BY name
            """, test_type)
        
        if exercises:
            text = f"**{title}**\n\n"
            text += f"Выберите упражнение для тестирования:\n\n"
            
            keyboard = InlineKeyboardBuilder()
            
            for ex in exercises:
                # Эмодзи по типу теста
                emoji = {
                    'strength': '🏋️',
                    'endurance': '⏱️', 
                    'speed': '🏃',
                    'quantity': '🔢'
                }.get(test_type, '📊')
                
                keyboard.button(
                    text=f"{emoji} {ex['name']} ({ex['muscle_group']})", 
                    callback_data=f"test_ex_{ex['id']}"
                )
            
            keyboard.button(text="🔙 Выбор типа теста", callback_data="new_test_menu")
            keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
            keyboard.adjust(1)
            
            await callback.message.edit_text(
                text,
                reply_markup=keyboard.as_markup(),
                parse_mode="Markdown"
            )
        else:
            await callback.message.edit_text(
                f"❌ Упражнения типа '{test_type}' не найдены.\n"
                f"Обратитесь к тренеру для добавления упражнений."
            )
            
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    
    await callback.answer()

async def select_test_exercise(callback: CallbackQuery, state: FSMContext):
    """Выбор упражнения для теста и переход к вводу данных"""
    exercise_id = int(callback.data.split("_")[2])
    await start_test_for_exercise(callback, state, exercise_id)

async def start_exercise_test(callback: CallbackQuery, state: FSMContext):
    """Начать тест для упражнения (из детального просмотра)"""
    exercise_id = int(callback.data.split("_")[1])
    await start_test_for_exercise(callback, state, exercise_id)

async def start_test_for_exercise(callback: CallbackQuery, state: FSMContext, exercise_id: int):
    """Начать тест для конкретного упражнения"""
    try:
        async with db_manager.pool.acquire() as conn:
            exercise = await conn.fetchrow("""
                SELECT name, test_type, measurement_unit, description
                FROM exercises WHERE id = $1
            """, exercise_id)
        
        if exercise:
            await state.update_data(
                test_exercise_id=exercise_id,
                test_exercise_name=exercise['name'],
                test_type=exercise['test_type'],
                measurement_unit=exercise['measurement_unit']
            )
            
            # Формируем инструкции по типу теста
            instructions = get_test_instructions(exercise['test_type'])
            
            text = f"🔬 **Тест: {exercise['name']}**\n\n"
            text += f"📋 **Тип:** {get_test_type_name(exercise['test_type'])}\n"
            text += f"📊 **Измерение:** {exercise['measurement_unit']}\n\n"
            text += f"**Инструкции:**\n{instructions['text']}\n\n"
            text += f"**Формат ввода:** {instructions['format']}\n\n"
            text += f"**Примеры:** {instructions['examples']}"
            
            await callback.message.edit_text(text, parse_mode="Markdown")
            await state.set_state(f"waiting_{exercise['test_type']}_test_data")
        else:
            await callback.message.edit_text("❌ Упражнение не найдено")
            
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    
    await callback.answer()

# ===== ОБРАБОТКА ДАННЫХ ТЕСТОВ =====
async def process_strength_test_data(message: Message, state: FSMContext):
    """Обработка данных силового теста"""
    parts = message.text.split()
    validation = validate_test_data('strength', parts)
    
    if not validation['valid']:
        await message.answer(validation['error'])
        return
    
    # Расчет 1ПМ по формулам
    one_rm_result = calculate_one_rm(validation['weight'], validation['reps'])
    await save_test_result(message, state, one_rm_result['average'], 'kg', {
        'test_weight': validation['weight'],
        'test_reps': validation['reps'],
        'formulas': one_rm_result
    })

async def process_endurance_test_data(message: Message, state: FSMContext):
    """Обработка данных теста на выносливость"""
    validation = validate_test_data('endurance', [message.text])
    
    if not validation['valid']:
        await message.answer(validation['error'])
        return
    
    await save_test_result(message, state, validation['time_seconds'], 'seconds', {
        'duration_seconds': validation['time_seconds']
    })

async def process_speed_test_data(message: Message, state: FSMContext):
    """Обработка данных скоростного теста"""
    parts = message.text.split()
    validation = validate_test_data('speed', parts)
    
    if not validation['valid']:
        await message.answer(validation['error'])
        return
    
    # Расчет скорости: расстояние / время
    speed = validation['distance'] / validation['time_seconds']
    await save_test_result(message, state, speed, 'm/s', {
        'distance': validation['distance'],
        'time_seconds': validation['time_seconds']
    })

async def process_quantity_test_data(message: Message, state: FSMContext):
    """Обработка данных количественного теста"""
    validation = validate_test_data('quantity', [message.text])
    
    if not validation['valid']:
        await message.answer(validation['error'])
        return
    
    await save_test_result(message, state, validation['max_reps'], 'reps', {
        'max_reps': validation['max_reps']
    })

async def save_test_result(message: Message, state: FSMContext, result_value: float, result_unit: str, additional_data: dict):
    """Сохранение результата теста в БД"""
    data = await state.get_data()
    user = await db_manager.get_user_by_telegram_id(message.from_user.id)
    
    try:
        async with db_manager.pool.acquire() as conn:
            # Сохраняем тест
            test_id = await conn.fetchval("""
                INSERT INTO user_tests (
                    user_id, exercise_id, test_type, result_value, result_unit,
                    test_weight, test_reps, distance, time_seconds, 
                    duration_seconds, max_reps
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                RETURNING id
            """, 
                user['id'], data['test_exercise_id'], data['test_type'],
                result_value, result_unit,
                additional_data.get('test_weight'),
                additional_data.get('test_reps'),
                additional_data.get('distance'),
                additional_data.get('time_seconds'),
                additional_data.get('duration_seconds'),
                additional_data.get('max_reps')
            )
        
        # Формируем сообщение о результате
        text = format_test_results(
            data['test_exercise_name'], 
            data['test_type'],
            result_value, 
            result_unit,
            additional_data
        )
        
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="🔬 Новый тест", callback_data="new_test_menu")
        keyboard.button(text="📊 Мои тесты", callback_data="my_tests")
        keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
        keyboard.adjust(2)
        
        await message.answer(text, reply_markup=keyboard.as_markup(), parse_mode="Markdown")
        await state.clear()
        
    except Exception as e:
        await message.answer(f"❌ Ошибка сохранения: {e}")

# ===== ПРОСМОТР РЕЗУЛЬТАТОВ =====
async def my_tests(callback: CallbackQuery):
    """Показать результаты тестов пользователя"""
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    
    try:
        async with db_manager.pool.acquire() as conn:
            results = await conn.fetch("""
                SELECT 
                    e.name as exercise_name, 
                    ut.test_type,
                    ut.result_value, 
                    ut.result_unit,
                    ut.tested_at,
                    ut.test_weight,
                    ut.test_reps
                FROM user_tests ut
                JOIN exercises e ON ut.exercise_id = e.id
                WHERE ut.user_id = $1
                ORDER BY ut.tested_at DESC
                LIMIT 15
            """, user['id'])
        
        if results:
            text = f"📊 **Ваши результаты тестов:**\n\n"
            
            for result in results:
                emoji = {
                    'strength': '🏋️',
                    'endurance': '⏱️', 
                    'speed': '🏃',
                    'quantity': '🔢'
                }.get(result['test_type'], '📊')
                
                date = result['tested_at'].strftime('%d.%m.%Y')
                text += f"{emoji} **{result['exercise_name']}**\n"
                text += f"📈 Результат: **{result['result_value']} {result['result_unit']}**\n"
                
                if result['test_type'] == 'strength' and result['test_weight']:
                    text += f"📝 Тест: {result['test_weight']}кг × {result['test_reps']} раз\n"
                
                text += f"📅 {date}\n\n"
        else:
            text = "📊 **У вас пока нет результатов тестов**\n\n" \
                   "Пройдите первый тест для отслеживания прогресса!"
        
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="🔬 Новый тест", callback_data="new_test_menu")
        keyboard.button(text="🔙 К тестам", callback_data="tests_menu")
        
        await callback.message.edit_text(
            text,
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    
    await callback.answer()

async def test_progress(callback: CallbackQuery):
    """Прогресс тестов (функция в разработке)"""
    keyboard = get_coming_soon_keyboard()
    
    await callback.message.edit_text(
        f"🚧 **Прогресс тестов**\n\n"
        f"Функция находится в разработке.\n"
        f"Скоро будут доступны графики прогресса!",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

async def test_records(callback: CallbackQuery):
    """Рекорды (функция в разработке)"""
    keyboard = get_coming_soon_keyboard()
    
    await callback.message.edit_text(
        f"🚧 **Рекорды и достижения**\n\n"
        f"Функция находится в разработке.\n"
        f"Скоро будет доступна система рекордов!",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====
def get_test_type_name(test_type: str) -> str:
    """Получить человекочитаемое название типа теста"""
    return {
        'strength': '🏋️ Силовой тест',
        'endurance': '⏱️ Тест выносливости',
        'speed': '🏃 Скоростной тест', 
        'quantity': '🔢 Количественный тест'
    }.get(test_type, 'Неизвестный тест')

def get_test_instructions(test_type: str) -> dict:
    """Получить инструкции для типа теста"""
    instructions = {
        'strength': {
            'text': 'Выполните упражнение с максимальным весом на указанное количество повторений.',
            'format': '`вес повторения`',
            'examples': '• `80 5` (80 кг на 5 повторений)\n• `100 1` (100 кг на 1 повторение)'
        },
        'endurance': {
            'text': 'Выполняйте упражнение максимально долго. Время указывайте в секундах.',
            'format': '`секунды`',
            'examples': '• `90` (90 секунд)\n• `120` (2 минуты)'
        },
        'speed': {
            'text': 'Пройдите дистанцию максимально быстро. Укажите дистанцию и время.',
            'format': '`дистанция_м время_сек`',
            'examples': '• `100 15.2` (100м за 15.2 сек)\n• `30 4.5` (30м за 4.5 сек)'
        },
        'quantity': {
            'text': 'Выполните максимальное количество повторений без отдыха.',
            'format': '`количество`',
            'examples': '• `45` (45 повторений)\n• `100` (100 повторений)'
        }
    }
    
    return instructions.get(test_type, {
        'text': 'Выполните тест согласно описанию упражнения.',
        'format': 'Введите результат',
        'examples': 'Следуйте инструкциям'
    })

def calculate_one_rm(weight: float, reps: int) -> dict:
    """Расчет 1ПМ по трем формулам"""
    w = float(weight)
    r = int(reps)
    
    if r == 1:
        return {
            'brzycki': w,
            'epley': w,
            'alternative': w,
            'average': w
        }
    
    # Формула Бжицкого
    brzycki = w / (1.0278 - 0.0278 * r)
    
    # Формула Эпли
    epley = w * (1 + r / 30.0)
    
    # Альтернативная формула
    alternative = w * (1 + 0.025 * r)
    
    # Среднее значение
    average = (brzycki + epley + alternative) / 3.0
    
    return {
        'brzycki': round(brzycki, 1),
        'epley': round(epley, 1), 
        'alternative': round(alternative, 1),
        'average': round(average, 1)
    }

# ===== ОБРАБОТКА ТЕКСТОВЫХ СООБЩЕНИЙ =====
async def process_test_text_input(message: Message, state: FSMContext):
    """Обработка текстовых вводов для тестов"""
    current_state = await state.get_state()
    
    if current_state == "waiting_strength_test_data":
        await process_strength_test_data(message, state)
    elif current_state == "waiting_endurance_test_data":
        await process_endurance_test_data(message, state)
    elif current_state == "waiting_speed_test_data":
        await process_speed_test_data(message, state)
    elif current_state == "waiting_quantity_test_data":
        await process_quantity_test_data(message, state)

async def get_user_test_result_for_workout(user_id: int, exercise_id: int):
    """Получить последний результат теста пользователя для использования в тренировке"""
    try:
        async with db_manager.pool.acquire() as conn:
            result = await conn.fetchrow("""
                SELECT result_value, result_unit, test_type
                FROM user_tests 
                WHERE user_id = $1 AND exercise_id = $2 
                ORDER BY tested_at DESC LIMIT 1
            """, user_id, exercise_id)
        
        return dict(result) if result else None
    except Exception:
        return None

__all__ = [
    'register_test_handlers',
    'process_test_text_input',
    'get_user_test_result_for_workout'
]