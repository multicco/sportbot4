# ===== ПОЛНЫЙ ИСПРАВЛЕННЫЙ EXERCISES.PY БЕЗ ОШИБОК =====

from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
import logging
logger = logging.getLogger(__name__)
from states.exercise_states import CreateExerciseStates

from database import db_manager
from states.exercise_states import CreateExerciseStates
from states.workout_states import CreateWorkoutStates
from keyboards.exercise_keyboards import (
    get_exercise_search_keyboard, get_categories_keyboard, 
    get_equipment_keyboard, get_difficulty_keyboard
)
from utils.validators import (
    validate_exercise_name, validate_exercise_description,
    validate_exercise_instructions
)
from utils.formatters import format_exercise_info
#from handlers.workouts import _safe_edit_or_send

from utils.helpers import _safe_edit_or_send

def register_exercise_handlers(dp):
    """Регистрация обработчиков упражнений"""
    
    # Поиск упражнений
    dp.callback_query.register(search_exercise_menu, F.data == "search_exercise")
    dp.callback_query.register(search_exercise_by_name, F.data == "search_by_name")
    dp.callback_query.register(search_by_category, F.data == "search_by_category")
    dp.callback_query.register(search_by_muscle_group, F.data == "search_by_muscle")
    dp.callback_query.register(show_category_exercises, F.data.startswith("cat_"))
    dp.callback_query.register(show_muscle_group_exercises, F.data.startswith("muscle_"))
    
    # НОВАЯ ФУНКЦИЯ: Детальный просмотр упражнения
    dp.callback_query.register(show_exercise_details, F.data.startswith("exercise_"))
    dp.callback_query.register(back_from_exercise_details, F.data == "back_from_exercise")
    
    # Создание упражнений (только для тренеров)
    dp.callback_query.register(start_add_exercise, F.data == "add_new_exercise")
    dp.callback_query.register(cancel_exercise_creation, F.data == "cancel_exercise_creation")
    
    # Выбор категории
    dp.callback_query.register(select_existing_category, F.data == "select_existing_category")
    dp.callback_query.register(choose_category, F.data.startswith("choose_cat_"))
    dp.callback_query.register(create_new_category, F.data == "create_new_category")
    
    # Выбор группы мышц
    dp.callback_query.register(choose_muscle_group, F.data.startswith("choose_mg_"))
    dp.callback_query.register(create_new_muscle_group, F.data == "create_new_muscle_group")
    
    # Выбор оборудования
    dp.callback_query.register(choose_equipment, F.data.startswith("choose_eq_"))
    
    # Выбор сложности
    dp.callback_query.register(choose_difficulty, F.data.startswith("diff_"))

# ===== ПОИСК УПРАЖНЕНИЙ =====
async def search_exercise_menu(callback: CallbackQuery,state: FSMContext = None):
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    keyboard = get_exercise_search_keyboard(user['role'])
    
    base_text = (
        "🔍 **Поиск упражнений**\n\n"
        "База содержит упражнения для всех групп мышц\n"
        "и различных уровней подготовки.\n\n"
        "💡 **Нажимайте на упражнения для подробной информации!**\n\n"
    )
    
    if user['role'] in ['coach', 'admin']:
        trainer_text = "🆕 **Для тренеров:** Можете добавлять новые упражнения!\n\n"
    else:
        trainer_text = ""
    
    full_text = base_text + trainer_text + "Выберите способ поиска:"
    
    await callback.message.edit_text(
        full_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()
    if state:
        current_data = await state.get_data()
        if current_data.get("searching_in_block"):
            await state.update_data(searching_in_block=current_data["searching_in_block"])

async def search_exercise_by_name(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🔍 **Поиск упражнений по названию**\n\n"
        "Введите название упражнения для поиска:\n"
        "Например: `жим`, `приседания`, `планка`\n\n"
        "💡 **Найденные упражнения будут кликабельными!**",
        parse_mode="Markdown"
    )
    await state.set_state("waiting_search")
    await callback.answer()

async def search_by_category(callback: CallbackQuery):
    try:
        async with db_manager.pool.acquire() as conn:
            categories = await conn.fetch("SELECT DISTINCT category FROM exercises ORDER BY category")
        
        keyboard = get_categories_keyboard(categories)
        
        await callback.message.edit_text(
            "📂 **Выберите категорию:**\n\n"
            "💡 **Упражнения будут кликабельными для детального просмотра**",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    await callback.answer()

async def search_by_muscle_group(callback: CallbackQuery):
    """Поиск упражнений по группам мышц"""
    try:
        async with db_manager.pool.acquire() as conn:
            muscle_groups = await conn.fetch("SELECT DISTINCT muscle_group FROM exercises ORDER BY muscle_group")
        
        keyboard = InlineKeyboardBuilder()
        
        for mg in muscle_groups:
            keyboard.button(
                text=f"💪 {mg['muscle_group']}", 
                callback_data=f"muscle_{mg['muscle_group']}"
            )
        
        keyboard.button(text="🔙 Назад", callback_data="search_exercise")
        keyboard.adjust(2)
        
        await callback.message.edit_text(
            "💪 **Выберите группу мышц:**\n\n"
            "💡 **Упражнения будут кликабельными для детального просмотра**",
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    await callback.answer()

async def show_category_exercises(callback: CallbackQuery):
    """Показать упражнения категории С КЛИКАБЕЛЬНЫМИ КНОПКАМИ"""
    category = callback.data[4:]
    
    try:
        async with db_manager.pool.acquire() as conn:
            exercises = await conn.fetch(
                "SELECT id, name, muscle_group, description, test_type FROM exercises WHERE category = $1 ORDER BY name",
                category
            )
        
        if exercises:
            text = f"📂 **Категория: {category}**\n\n"
            text += f"**Найдено упражнений: {len(exercises)}**\n"
            text += f"💡 **Нажмите на упражнение для детального просмотра**\n\n"
            
            keyboard = InlineKeyboardBuilder()
            
            for ex in exercises:
                # Добавляем эмодзи в зависимости от типа теста
                test_emoji = {
                    'strength': '🏋️',
                    'endurance': '⏱️', 
                    'speed': '🏃',
                    'quantity': '🔢',
                    'none': '💪'
                }.get(ex['test_type'] if ex['test_type'] else 'none', '💪')
                
                keyboard.button(
                    text=f"{test_emoji} {ex['name']}", 
                    callback_data=f"exercise_{ex['id']}"
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

async def show_muscle_group_exercises(callback: CallbackQuery):
    """Показать упражнения группы мышц С КЛИКАБЕЛЬНЫМИ КНОПКАМИ"""
    muscle_group = callback.data[7:]  # Убираем "muscle_"
    
    try:
        async with db_manager.pool.acquire() as conn:
            exercises = await conn.fetch(
                "SELECT id, name, category, description, test_type FROM exercises WHERE muscle_group = $1 ORDER BY name",
                muscle_group
            )
        
        if exercises:
            text = f"💪 **Группа мышц: {muscle_group}**\n\n"
            text += f"**Найдено упражнений: {len(exercises)}**\n"
            text += f"💡 **Нажмите на упражнение для детального просмотра**\n\n"
            
            keyboard = InlineKeyboardBuilder()
            
            for ex in exercises:
                # Добавляем эмодзи в зависимости от типа теста
                test_emoji = {
                    'strength': '🏋️',
                    'endurance': '⏱️', 
                    'speed': '🏃',
                    'quantity': '🔢',
                    'none': '💪'
                }.get(ex['test_type'] if ex['test_type'] else 'none', '💪')
                
                keyboard.button(
                    text=f"{test_emoji} {ex['name']} ({ex['category']})", 
                    callback_data=f"exercise_{ex['id']}"
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

# ===== НОВАЯ ФУНКЦИЯ: ДЕТАЛЬНЫЙ ПРОСМОТР УПРАЖНЕНИЯ =====
async def show_exercise_details(callback: CallbackQuery, state: FSMContext):
    """Показать детальную информацию об упражнении"""
    exercise_id = int(callback.data.split("_")[1])
    
    try:
        async with db_manager.pool.acquire() as conn:
            exercise = await conn.fetchrow("""
                SELECT e.*, u.first_name as author_name 
                FROM exercises e
                LEFT JOIN users u ON e.created_by = u.id  
                WHERE e.id = $1
            """, exercise_id)
        
        if exercise:
            # Сохраняем ID для навигации
            await state.update_data(current_exercise_id=exercise_id, last_search_context="details")
            
            # Получаем личный рекорд пользователя
            user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
            personal_record = await get_user_best_test_result(user['id'], exercise_id)
            
            # Формируем детальное описание
            text = format_exercise_info(dict(exercise))
            
            # Добавляем информацию о тестировании
            test_type_names = {
                'strength': '🏋️ Силовой тест',
                'endurance': '⏱️ Тест выносливости', 
                'speed': '🏃 Скоростной тест',
                'quantity': '🔢 Количественный тест',
                'none': '❌ Не тестируемое'
            }
            
            test_type = exercise['test_type'] if exercise['test_type'] else 'none'
            if test_type != 'none':
                text += f"\n\n**🔬 Тестирование:**\n"
                text += f"{test_type_names[test_type]}\n"
                text += f"📊 Единица измерения: {exercise['measurement_unit']}\n"
                
                if personal_record:
                    text += f"🏆 **Ваш рекорд:** {personal_record['result_value']} {personal_record['result_unit']}\n"
                    text += f"📅 Дата: {personal_record['tested_at'].strftime('%d.%m.%Y')}\n"
                else:
                    text += f"📝 **Тестов пока нет** - пройдите первый!\n"
            
            # Добавляем информацию об авторе
            if exercise['author_name']:
                text += f"\n👤 **Автор:** {exercise['author_name']}"
            
            # Создаем клавиатуру
            keyboard = InlineKeyboardBuilder()
            
            # Кнопка тестирования (если доступно)
            if test_type != 'none':
                keyboard.button(text="🔬 Пройти тест", callback_data=f"test_{exercise_id}")
            
            # Кнопка использования в тренировке
            keyboard.button(text="🏋️ Использовать в тренировке", callback_data=f"use_in_workout_{exercise_id}")
            
            # Кнопки навигации
            keyboard.button(text="🔙 Назад к поиску", callback_data="back_from_exercise")
            keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
            keyboard.adjust(1)
            
            await callback.message.edit_text(
                text,
                reply_markup=keyboard.as_markup(),
                parse_mode="Markdown"
            )
        else:
            await callback.message.edit_text("❌ Упражнение не найдено")
            
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    
    await callback.answer()

async def back_from_exercise_details(callback: CallbackQuery, state: FSMContext):
    """Возврат назад от детального просмотра"""
    await search_exercise_menu(callback)

# ===== СОЗДАНИЕ НОВОГО УПРАЖНЕНИЯ =====
async def start_add_exercise(callback: CallbackQuery, state: FSMContext):
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    
    # Проверка прав доступа
    if user['role'] not in ['coach', 'admin']:
        await callback.answer("❌ Только тренеры могут добавлять упражнения!")
        return
    
    await callback.message.edit_text(
        "➕ **Добавление нового упражнения**\n\n"
        "🏋️ **Вы создаете упражнение для всех пользователей системы!**\n\n"
        "Введите **название упражнения**:\n"
        "_Например: \"Жим гантелей на наклонной скамье\" или \"Планка с подъемом ног\"_",
        parse_mode="Markdown"
    )
    await state.set_state(CreateExerciseStates.waiting_name)
    await callback.answer()

async def cancel_exercise_creation(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "❌ **Создание упражнения отменено**",
        parse_mode="Markdown"
    )
    await callback.answer()

async def select_existing_category(callback: CallbackQuery, state: FSMContext):
    try:
        async with db_manager.pool.acquire() as conn:
            categories = await conn.fetch("SELECT DISTINCT category FROM exercises ORDER BY category")
        
        keyboard = InlineKeyboardBuilder()
        
        for cat in categories:
            keyboard.button(
                text=f"📂 {cat['category']}", 
                callback_data=f"choose_cat_{cat['category']}"
            )
        
        keyboard.button(text="📝 Создать новую категорию", callback_data="create_new_category")
        keyboard.button(text="❌ Отменить", callback_data="cancel_exercise_creation")
        keyboard.adjust(2)
        
        await callback.message.edit_text(
            "📂 **Выберите существующую категорию:**\n\n",
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    await callback.answer()

async def choose_category(callback: CallbackQuery, state: FSMContext):
    category = callback.data[11:]  # Убираем "choose_cat_"
    await state.update_data(category=category)
    await ask_muscle_group(callback.message, state, edit=True)
    await callback.answer()

async def create_new_category(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "📝 **Создание новой категории**\n\n"
        "Введите название новой категории упражнений:\n"
        "_Например: \"Кроссфит\", \"Реабилитация\", \"Йога\"_\n\n"
        "**Существующие категории:**\n"
        "• Силовые\n"
        "• Функциональные\n"
        "• Кардио\n"
        "• Растяжка",
        parse_mode="Markdown"
    )
    await state.set_state("waiting_new_category")
    await callback.answer()

async def ask_muscle_group(message: Message, state: FSMContext, edit: bool = False):
    try:
        async with db_manager.pool.acquire() as conn:
            muscle_groups = await conn.fetch("SELECT DISTINCT muscle_group FROM exercises ORDER BY muscle_group")
        
        keyboard = InlineKeyboardBuilder()
        
        for mg in muscle_groups:
            keyboard.button(
                text=f"💪 {mg['muscle_group']}", 
                callback_data=f"choose_mg_{mg['muscle_group']}"
            )
        
        keyboard.button(text="📝 Создать новую группу", callback_data="create_new_muscle_group")
        keyboard.button(text="❌ Отменить", callback_data="cancel_exercise_creation")
        keyboard.adjust(3)
        
        text = "💪 **Выберите группу мышц:**\n\n"
        
        if edit:
            await message.edit_text(text, reply_markup=keyboard.as_markup(), parse_mode="Markdown")
        else:
            await message.answer(text, reply_markup=keyboard.as_markup(), parse_mode="Markdown")
            
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

async def choose_muscle_group(callback: CallbackQuery, state: FSMContext):
    muscle_group = callback.data[10:]  # Убираем "choose_mg_"
    await state.update_data(muscle_group=muscle_group)
    await ask_equipment(callback.message, state, edit=True)
    await callback.answer()

async def create_new_muscle_group(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "💪 **Создание новой группы мышц**\n\n"
        "Введите название группы мышц:\n"
        "_Например: \"Предплечья\", \"Шея\", \"Стабилизаторы\"_",
        parse_mode="Markdown"
    )
    await state.set_state("waiting_new_muscle_group")
    await callback.answer()

async def ask_equipment(message: Message, state: FSMContext, edit: bool = False):
    keyboard = get_equipment_keyboard()
    text = "🏋️ **Выберите необходимое оборудование:**\n\n"
    
    if edit:
        await message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

async def choose_equipment(callback: CallbackQuery, state: FSMContext):
    equipment = callback.data[10:]  # Убираем "choose_eq_"
    
    if equipment == "Другое":
        await callback.message.edit_text(
            "🔧 **Укажите оборудование**\n\n"
            "Введите название оборудования:\n"
            "_Например: \"TRX петли\", \"Медицинский мяч\"_",
            parse_mode="Markdown"
        )
        await state.set_state("waiting_custom_equipment")
        await callback.answer()
        return
    
    await state.update_data(equipment=equipment)
    await ask_difficulty(callback.message, state, edit=True)
    await callback.answer()

async def ask_difficulty(message: Message, state: FSMContext, edit: bool = False):
    keyboard = get_difficulty_keyboard()
    text = "⭐ **Выберите уровень сложности:**\n\n"
    
    if edit:
        await message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

async def choose_difficulty(callback: CallbackQuery, state: FSMContext):
    difficulty = callback.data[5:]  # Убираем "diff_"
    await state.update_data(difficulty_level=difficulty)
    
    await callback.message.edit_text(
        "📝 **Описание упражнения**\n\n"
        "Введите краткое описание упражнения:\n"
        "_Например: \"Изолированное упражнение для развития грудных мышц\"_",
        parse_mode="Markdown"
    )
    await state.set_state(CreateExerciseStates.waiting_description)
    await callback.answer()

# ===== ОБРАБОТКА ВВОДА ДАННЫХ =====
async def process_exercise_name(message: Message, state: FSMContext):
    exercise_name = message.text.strip()
    validation = validate_exercise_name(exercise_name)
    
    if not validation['valid']:
        await message.answer(validation['error'])
        return
    
    # Проверяем, нет ли уже такого упражнения
    try:
        async with db_manager.pool.acquire() as conn:
            existing = await conn.fetchrow(
                "SELECT name FROM exercises WHERE LOWER(name) = LOWER($1)", 
                exercise_name
            )
        
        if existing:
            await message.answer(f"❌ Упражнение '{exercise_name}' уже существует в базе!")
            return
    
    except Exception as e:
        await message.answer(f"❌ Ошибка проверки: {e}")
        return
    
    await state.update_data(name=exercise_name)
    await select_existing_category_for_new_exercise(message, state)

async def select_existing_category_for_new_exercise(message: Message, state: FSMContext):
    try:
        async with db_manager.pool.acquire() as conn:
            categories = await conn.fetch("SELECT DISTINCT category FROM exercises ORDER BY category")
        
        keyboard = InlineKeyboardBuilder()
        
        for cat in categories:
            keyboard.button(
                text=f"📂 {cat['category']}", 
                callback_data=f"choose_cat_{cat['category']}"
            )
        
        keyboard.button(text="📝 Новая категория", callback_data="create_new_category")
        keyboard.button(text="❌ Отменить", callback_data="cancel_exercise_creation")
        keyboard.adjust(2)
        
        await message.answer(
            "📂 **Выберите категорию:**\n\n",
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

async def process_exercise_description(message: Message, state: FSMContext):
    description = message.text.strip()
    validation = validate_exercise_description(description)
    
    if not validation['valid']:
        await message.answer(validation['error'])
        return
    
    await state.update_data(description=description)
    
    await message.answer(
        "📋 **Инструкции по выполнению**\n\n"
        "Введите подробные инструкции по технике выполнения:",
        parse_mode="Markdown"
    )
    await state.set_state(CreateExerciseStates.waiting_instructions)

async def process_exercise_instructions(message: Message, state: FSMContext):
    instructions = message.text.strip()
    validation = validate_exercise_instructions(instructions)
    
    if not validation['valid']:
        await message.answer(validation['error'])
        return
    
    await state.update_data(instructions=instructions)
    await save_new_exercise(message, state)

async def save_new_exercise(message: Message, state: FSMContext):
    """Сохранение нового упражнения в БД"""
    data = await state.get_data()
    user = await db_manager.get_user_by_telegram_id(message.from_user.id)
    
    try:
        async with db_manager.pool.acquire() as conn:
            exercise_id = await conn.fetchval("""
                INSERT INTO exercises (
                    name, category, muscle_group, equipment, difficulty_level,
                    description, instructions, created_by
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id
            """, 
                data['name'], data['category'], data['muscle_group'],
                data['equipment'], data['difficulty_level'], 
                data['description'], data['instructions'], user['id']
            )
        
        # Успешное создание
        text = f"🎉 **Упражнение создано успешно!**\n\n"
        text += f"💪 **Название:** {data['name']}\n"
        text += f"📂 **Категория:** {data['category']}\n"
        text += f"🎯 **Группа мышц:** {data['muscle_group']}\n"
        text += f"🔧 **Оборудование:** {data['equipment']}\n"
        text += f"⭐ **Сложность:** {data['difficulty_level']}\n"
        text += f"**ID упражнения:** {exercise_id}"
        
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="➕ Создать еще", callback_data="add_new_exercise")
        keyboard.button(text="🔍 К поиску", callback_data="search_exercise")
        keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
        keyboard.adjust(2)
        
        await message.answer(
            text,
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )
        
        await state.clear()
        
    except Exception as e:
        await message.answer(f"❌ Ошибка сохранения: {e}")

# ===== ОБРАБОТКА ПОИСКА УПРАЖНЕНИЙ =====
async def handle_exercise_search(message: Message, state: FSMContext):
    search_term = message.text.lower()
    
    try:
        async with db_manager.pool.acquire() as conn:
            exercises = await conn.fetch("""
                SELECT id, name, category, muscle_group, description, test_type 
                FROM exercises 
                WHERE LOWER(name) LIKE $1 
                   OR LOWER(category) LIKE $1
                   OR LOWER(muscle_group) LIKE $1
                ORDER BY name
                LIMIT 15
            """, f"%{search_term}%")
        
        if exercises:
            text = f"🔍 **Найдено: {len(exercises)} упражнений**\n\n"
            text += f"💡 **Нажмите на упражнение для детального просмотра:**\n\n"
            
            keyboard = InlineKeyboardBuilder()
            
            for ex in exercises:
                # Добавляем эмодзи в зависимости от типа теста
                test_emoji = {
                    'strength': '🏋️',
                    'endurance': '⏱️', 
                    'speed': '🏃',
                    'quantity': '🔢',
                    'none': '💪'
                }.get(ex['test_type'] if ex['test_type'] else 'none', '💪')
                
                keyboard.button(
                    text=f"{test_emoji} {ex['name']} • {ex['muscle_group']}", 
                    callback_data=f"exercise_{ex['id']}"
                )
            
            # keyboard.button(text="🔍 Новый поиск", callback_data="search_by_name")
            
            keyboard.button(text="🔙 К поиску", callback_data="search_exercise")
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
            keyboard.button(text="🔍 Новый поиск", callback_data="search_by_name")
            keyboard.button(text="🔙 К поиску", callback_data="search_exercise")
            keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
            
            await message.answer(text, reply_markup=keyboard.as_markup(), parse_mode="Markdown")
            
        await state.clear()
        
    except Exception as e:
        await message.answer(f"❌ Ошибка поиска: {e}")

# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====
async def get_user_best_test_result(user_id: int, exercise_id: int):
    """Получить лучший результат пользователя по упражнению"""
    try:
        async with db_manager.pool.acquire() as conn:
            # Проверяем есть ли таблица user_tests
            table_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'user_tests'
                )
            """)
            
            if not table_exists:
                return None
            
            result = await conn.fetchrow("""
                SELECT result_value, result_unit, tested_at, test_type
                FROM user_tests 
                WHERE user_id = $1 AND exercise_id = $2 
                ORDER BY tested_at DESC
                LIMIT 1
            """, user_id, exercise_id)
        
        return dict(result) if result else None
    except Exception:
        return None

# ===== ОБРАБОТКА ТЕКСТОВЫХ СОСТОЯНИЙ =====
async def process_exercise_text_input(message: Message, state: FSMContext):
    """Обработка текстовых вводов для создания упражнений"""
    current_state = await state.get_state()
    
    if current_state == CreateExerciseStates.waiting_name:
        await process_exercise_name(message, state)
    
    elif current_state == "waiting_new_category":
        category = message.text.strip()
        if len(category) < 3 or len(category) > 50:
            await message.answer("❌ Название категории должно быть от 3 до 50 символов")
            return
        await state.update_data(category=category)
        await ask_muscle_group(message, state)
    
    elif current_state == "waiting_new_muscle_group":
        muscle_group = message.text.strip()
        if len(muscle_group) < 3 or len(muscle_group) > 50:
            await message.answer("❌ Название группы мышц должно быть от 3 до 50 символов")
            return
        await state.update_data(muscle_group=muscle_group)
        await ask_equipment(message, state)
    
    elif current_state == "waiting_custom_equipment":
        equipment = message.text.strip()
        if len(equipment) < 2 or len(equipment) > 50:
            await message.answer("❌ Название оборудования должно быть от 2 до 50 символов")
            return
        await state.update_data(equipment=equipment)
        await ask_difficulty(message, state)
    
    elif current_state == CreateExerciseStates.waiting_description:
        await process_exercise_description(message, state)
    
    elif current_state == CreateExerciseStates.waiting_instructions:
        await process_exercise_instructions(message, state)
    
    elif current_state == "waiting_search":
        await handle_exercise_search(message, state)




# #@workouts_router.callback_query(F.data.startswith("use_in_workout_"))
# async def use_in_workout_with_params(callback: CallbackQuery, state: FSMContext):
#     logger.info("use_in_workout_with_params: START")
#     ex_id = int(callback.data.split("_")[-1])
    
#     # Проверяем, что мы в создании тренировки
#     if (await state.get_state()) != CreateWorkoutStates.searching_exercise_for_block:
#         await callback.answer("Только при создании тренировки.", show_alert=True)
#         return

#     data = await state.get_data()
#     block = data.get("searching_in_block")
#     if not block:
#         await callback.answer("Ошибка: блок не выбран.", show_alert=True)
#         return

#     async with db_manager.pool.acquire() as conn:
#         ex = await conn.fetchrow("SELECT name, test_type FROM exercises WHERE id = $1", ex_id)
#     if not ex:
#         await callback.answer("Упражнение не найдено.", show_alert=True)
#         return

#     # Сохраняем данные для ввода
#     await state.update_data(
#         pending_ex_id=ex_id,
#         pending_ex_name=ex["name"],
#         pending_ex_block=block
#     )

#     await callback.message.edit_text(
#         f"**Добавление: {ex['name']}**\n\n"
#         "Введите параметры:\n"
#         "`подходы повторы %1ПМ отдых`\n\n"
#         "Пример: `3 10 75 90`\n"
#         "Или без %: `3 10 - 90`",
#         parse_mode="Markdown"
#     )
#     await state.set_state(CreateWorkoutStates.configuring_exercise)
#     await callback.answer()

# async def _show_exercises_for_block(message: Message, state: FSMContext):
#     data = await state.get_data()
#     current_block = data.get("current_block")
#     # Query exercises for this block, создаём меню
#     kb = InlineKeyboardBuilder()
#     # Добавляем кнопки упражнений, например:
#     kb.button(text="Жим лёжа", callback_data="create_add_ex_1")
#     kb.button(text="Отмена", callback_data="back_to_constructor")
#     kb.adjust(1)
#     await _safe_edit_or_send(message, f"Выберите упражнение для блока {current_block}:", reply_markup=kb.as_markup(), parse_mode="Markdown")


# async def process_param_input(message: Message, state: FSMContext):
#     text = message.text.strip()
#     data = await state.get_data()
#     ex_id = data.get("pending_ex_id")
#     ex_name = data.get("pending_ex_name")
#     block = data.get("pending_ex_block")

#     if not all([ex_id, ex_name, block]):
#         await message.answer("Ошибка. Начните заново.")
#         await state.clear()
#         return

#     parts = text.split()
#     if len(parts) != 4:
#         await message.answer("Нужно 4 значения: `3 10 75 90`")
#         return

#     try:
#         sets = int(parts[0])
#         reps = int(parts[1])
#         percent = parts[2]
#         rest = int(parts[3])
#         if sets <= 0 or reps <= 0 or rest < 0:
#             raise ValueError
#         one_rm_percent = None if percent == "-" else int(percent)
#         if one_rm_percent and not (1 <= one_rm_percent <= 200):
#             raise ValueError
#     except:
#         await message.answer("Неверный формат. Пример: `3 10 75 90`")
#         return

#     # Добавляем в блок
#     selected = data.get("selected_blocks", {})
#     selected.setdefault(block, {"description": "", "exercises": []})
#     selected[block]["exercises"].append({
#         "id": ex_id,
#         "name": ex_name,
#         "sets": sets,
#         "reps_min": reps,
#         "reps_max": reps,
#         "one_rm_percent": one_rm_percent,
#         "rest_seconds": rest
#     })
#     await state.update_data(selected_blocks=selected)

#     param_text = f"{sets}×{reps}"
#     if one_rm_percent:
#         param_text += f" ({one_rm_percent}%)"
#     if rest > 0:
#         param_text += f", отдых {rest}с"

#     await message.answer(f"**{ex_name}** добавлено: {param_text}")
#     await _show_exercises_for_block(message, state)
#     await state.clear()
__all__ = ['register_exercise_handlers', 'process_exercise_text_input']