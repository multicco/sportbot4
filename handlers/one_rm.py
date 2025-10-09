# ===== ОБРАБОТЧИКИ 1ПМ ТЕСТОВ =====

from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import db_manager
from keyboards.main_keyboards_old import get_coming_soon_keyboard
from utils.validators import validate_1rm_data
from utils.formatters import format_1rm_results

def register_one_rm_handlers(dp):
    """Регистрация обработчиков 1ПМ тестов"""
    
    dp.callback_query.register(new_1rm_test, F.data == "new_1rm_test")
    dp.callback_query.register(select_1rm_exercise, F.data.startswith("1rm_"))
    dp.callback_query.register(show_my_1rm_results, F.data == "my_1rm_results")
    dp.callback_query.register(show_1rm_stats, F.data == "1rm_stats")

async def new_1rm_test(callback: CallbackQuery):
    """Выбор упражнения для нового теста 1ПМ"""
    try:
        async with db_manager.pool.acquire() as conn:
            exercises = await conn.fetch("""
                SELECT id, name, category, muscle_group
                FROM exercises 
                WHERE category = 'Силовые'
                ORDER BY name
                LIMIT 15
            """)
        
        if exercises:
            text = "💪 **Выберите упражнение для теста 1ПМ:**\n\n"
            keyboard = InlineKeyboardBuilder()
            
            for ex in exercises:
                keyboard.button(
                    text=f"💪 {ex['name']}", 
                    callback_data=f"1rm_{ex['id']}"
                )
            
            keyboard.button(text="🔙 Назад", callback_data="one_rm_menu")
            keyboard.adjust(1)
            
            await callback.message.edit_text(
                text,
                reply_markup=keyboard.as_markup(),
                parse_mode="Markdown"
            )
        else:
            await callback.message.edit_text(
                "❌ Силовые упражнения не найдены. Проверьте БД.",
                parse_mode="Markdown"
            )
            
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    
    await callback.answer()

async def select_1rm_exercise(callback: CallbackQuery, state: FSMContext):
    """Выбор упражнения и переход к вводу данных"""
    exercise_id = callback.data.split("_")[1]
    
    try:
        async with db_manager.pool.acquire() as conn:
            exercise = await conn.fetchrow("SELECT name, category FROM exercises WHERE id = $1", int(exercise_id))
        
        if exercise:
            await state.update_data(exercise_id=exercise_id, exercise_name=exercise['name'])
            
            await callback.message.edit_text(
                f"💪 **Тест 1ПМ: {exercise['name']}**\n\n"
                f"🔬 **Введите данные через пробел:**\n"
                f"`вес повторения`\n\n"
                f"**Примеры:**\n"
                f"• `80 5` (80 кг на 5 повторений)\n"
                f"• `60 10` (60 кг на 10 повторений)\n\n"
                f"Система рассчитает 1ПМ по 3 формулам и выведет среднее!",
                parse_mode="Markdown"
            )
            await state.set_state("waiting_1rm_data")
        else:
            await callback.message.edit_text("❌ Упражнение не найдено")
            
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    
    await callback.answer()

async def show_my_1rm_results(callback: CallbackQuery):
    """Показать результаты 1ПМ пользователя"""
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    
    try:
        async with db_manager.pool.acquire() as conn:
            results = await conn.fetch("""
                SELECT e.name, orm.weight, orm.tested_at, orm.reps, orm.test_weight
                FROM one_rep_max orm
                JOIN exercises e ON orm.exercise_id = e.id
                WHERE orm.user_id = $1
                ORDER BY orm.tested_at DESC
                LIMIT 10
            """, user['id'])
        
        if results:
            text = f"📊 **Ваши результаты 1ПМ:**\n\n"
            for result in results:
                date = result['tested_at'].strftime('%d.%m.%Y')
                text += f"💪 **{result['name']}**\n"
                text += f"🏋️ 1ПМ: **{result['weight']} кг**\n"
                text += f"📝 Тест: {result['test_weight']}кг × {result['reps']} раз\n"
                text += f"📅 {date}\n\n"
        else:
            text = "📊 **У вас пока нет результатов 1ПМ**\n\n" \
                   "Пройдите первый тест для отслеживания прогресса!"
        
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="💪 Новый тест", callback_data="new_1rm_test")
        keyboard.button(text="🔙 К тестам", callback_data="one_rm_menu")
        
        await callback.message.edit_text(
            text,
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    
    await callback.answer()

async def show_1rm_stats(callback: CallbackQuery):
    """Показать статистику 1ПМ (функция в разработке)"""
    keyboard = get_coming_soon_keyboard()
    
    await callback.message.edit_text(
        f"🚧 **Статистика 1ПМ**\n\n"
        f"Функция находится в разработке.\n"
        f"Скоро будет доступна!",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

# ===== РАСЧЕТ 1ПМ =====
def calculate_1rm(weight, reps):
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

async def process_1rm_data(message: Message, state: FSMContext):
    """Обработка данных для теста 1ПМ"""
    parts = message.text.split()
    validation = validate_1rm_data(parts[0] if len(parts) > 0 else "", 
                                    parts[1] if len(parts) > 1 else "")
    
    if not validation['valid']:
        await message.answer(validation['error'])
        return
    
    weight = validation['weight']
    reps = validation['reps']
    
    # Расчет 1ПМ по формулам
    results = calculate_1rm(weight, reps)
    state_data = await state.get_data()
    exercise_name = state_data.get('exercise_name', 'Упражнение')
    
    # Сохраняем результат в БД
    user = await db_manager.get_user_by_telegram_id(message.from_user.id)
    
    try:
        async with db_manager.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO one_rep_max (user_id, exercise_id, weight, reps, test_weight, 
                                       formula_brzycki, formula_epley, formula_alternative, formula_average)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """, user['id'], int(state_data['exercise_id']), results['average'], 
                 reps, weight, results['brzycki'], results['epley'], 
                 results['alternative'], results['average'])
        
        # Формируем результат
        text = format_1rm_results(exercise_name, weight, reps, results)
        
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="💪 Новый тест", callback_data="new_1rm_test")
        keyboard.button(text="📊 Мои результаты", callback_data="my_1rm_results")
        keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
        
        await message.answer(text, reply_markup=keyboard.as_markup(), parse_mode="Markdown")
        await state.clear()
        
    except Exception as e:
        await message.answer(f"❌ Ошибка сохранения: {e}")

async def get_user_1rm_for_exercise(user_id: int, exercise_id: int):
    """Получить последний результат 1ПМ пользователя для упражнения"""
    try:
        async with db_manager.pool.acquire() as conn:
            result = await conn.fetchrow("""
                SELECT weight FROM one_rep_max 
                WHERE user_id = $1 AND exercise_id = $2 
                ORDER BY tested_at DESC LIMIT 1
            """, user_id, exercise_id)
        
        return float(result['weight']) if result else None
    except Exception:
        return None

__all__ = [
    'register_one_rm_handlers',
    'process_1rm_data',
    'calculate_1rm',
    'get_user_1rm_for_exercise'
]