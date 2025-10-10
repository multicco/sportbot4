# ===== ПОЛНЫЙ ФАЙЛ main.py ДЛЯ СПОРТИВНОГО БОТА =====

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import BotCommand, BotCommandScopeDefault
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import F

from config import config
from database import init_database, db_manager

# ===== НАСТРОЙКА ЛОГИРОВАНИЯ =====
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ===== СОЗДАНИЕ БОТА И ДИСПЕТЧЕРА =====
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ===== FSM СОСТОЯНИЯ =====
class CreateWorkoutStates(StatesGroup):
    waiting_name = State()
    waiting_description = State()  
    selecting_blocks = State()
    adding_block_description = State()
    adding_exercises = State()
    configuring_exercise = State()

# ===== КОМАНДА /START =====
@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Обработка команды /start"""
    user = message.from_user
    
    # Проверяем, есть ли пользователь в БД
    existing_user = await db_manager.get_user_by_telegram_id(user.id)
    
    if not existing_user:
        # Создаем нового пользователя
        await db_manager.create_user(
            telegram_id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            username=user.username
        )
        welcome_text = f"👋 **Добро пожаловать, {user.first_name}!**\n\n"
        welcome_text += f"Вы успешно зарегистрированы в спортивном боте.\n"
    else:
        welcome_text = f"👋 **С возвращением, {user.first_name}!**\n\n"
    
    welcome_text += f"🏋️ **Возможности бота:**\n"
    welcome_text += f"• 💪 Тестирование 1ПМ для любых упражнений\n"
    welcome_text += f"• 🏋️ Создание и выполнение тренировок\n"
    welcome_text += f"• 📊 Система оценки нагрузки RPE\n"
    welcome_text += f"• 👥 Командные тренировки\n"
    welcome_text += f"• 📈 Подробная статистика прогресса\n\n"
    welcome_text += f"Выберите действие:"
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🏋️ Тренировки", callback_data="workouts_menu")
    keyboard.button(text="💪 Тест 1ПМ", callback_data="one_rm_menu")
    keyboard.button(text="🔍 Найти упражнение", callback_data="search_exercise")
    keyboard.button(text="👥 Команды", callback_data="teams_menu")
    keyboard.adjust(2)
    
    await message.answer(
        welcome_text,
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )

# ===== ОБРАБОТЧИКИ ГЛАВНОГО МЕНЮ =====
@dp.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: CallbackQuery):
    """Возврат в главное меню"""
    user = callback.from_user
    
    text = f"🏠 **Главное меню**\n\n"
    text += f"Добро пожаловать, {user.first_name}!\n\n"
    text += f"🏋️ **Возможности бота:**\n"
    text += f"• 💪 Тестирование 1ПМ для любых упражнений\n"
    text += f"• 🏋️ Создание и выполнение тренировок с блоками\n"
    text += f"• 📊 Система оценки нагрузки RPE\n"
    text += f"• 👥 Командные тренировки\n"
    text += f"• 📈 Подробная статистика прогресса\n\n"
    text += f"Выберите действие:"
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🏋️ Тренировки", callback_data="workouts_menu")
    keyboard.button(text="💪 Тест 1ПМ", callback_data="one_rm_menu")
    keyboard.button(text="🔍 Найти упражнение", callback_data="search_exercise")
    keyboard.button(text="👥 Команды", callback_data="teams_menu")
    keyboard.adjust(2)
    
    await callback.message.edit_text(
        text,
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()

# ===== МЕНЮ ТРЕНИРОВОК =====
@dp.callback_query(F.data == "workouts_menu")
async def workouts_menu(callback: CallbackQuery):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🏋️ Мои тренировки", callback_data="my_workouts")
    keyboard.button(text="🔍 Найти тренировку", callback_data="find_workout")
    keyboard.button(text="➕ Создать тренировку", callback_data="create_workout")
    keyboard.button(text="🔙 Главное меню", callback_data="main_menu")
    keyboard.adjust(1)
    
    await callback.message.edit_text(
        "🏋️ **Меню тренировок**\n\n"
        "🆕 **Новая функция: Блочная структура!**\n"
        "• 🔥 Разминка\n"
        "• ⚡ Подготовка нервной системы\n"
        "• 💪 Основная часть\n"
        "• 🧘 Заминка\n\n"
        "Выберите действие:",
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()

# ===== МЕНЮ 1ПМ ТЕСТОВ =====
@dp.callback_query(F.data == "one_rm_menu")
async def one_rm_menu(callback: CallbackQuery):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="💪 Новый тест 1ПМ", callback_data="new_1rm_test")
    keyboard.button(text="📊 Мои результаты", callback_data="my_1rm_results")
    keyboard.button(text="📈 Статистика", callback_data="1rm_stats")
    keyboard.button(text="🔙 Главное меню", callback_data="main_menu")
    keyboard.adjust(1)
    
    await callback.message.edit_text(
        "💪 **Тесты 1ПМ**\n\n"
        "🔬 **Новая система:**\n"
        "• Тестирование любых упражнений\n"
        "• Среднее по 3 формулам\n"
        "• Учет веса тела\n"
        "• Использование в тренировках\n\n"
        "Выберите действие:",
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()

# ===== МЕНЮ ПОИСКА УПРАЖНЕНИЙ =====
@dp.callback_query(F.data == "search_exercise")
async def search_exercise_menu(callback: CallbackQuery):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔍 Поиск по названию", callback_data="search_by_name")
    keyboard.button(text="📂 По категориям", callback_data="search_by_category")
    keyboard.button(text="💪 По группам мышц", callback_data="search_by_muscle")
    keyboard.button(text="🔙 Главное меню", callback_data="main_menu")
    keyboard.adjust(1)
    
    await callback.message.edit_text(
        "🔍 **Поиск упражнений**\n\n"
        "База содержит 25+ упражнений для всех групп мышц\n"
        "и различных уровней подготовки.\n\n"
        "Выберите способ поиска:",
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()

# ===== МЕНЮ КОМАНД =====
@dp.callback_query(F.data == "teams_menu")
async def teams_menu(callback: CallbackQuery):
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    
    keyboard = InlineKeyboardBuilder()
    
    if user['role'] in ['coach', 'admin']:
        keyboard.button(text="🏗️ Создать команду", callback_data="create_team")
        keyboard.button(text="👤 Добавить подопечного", callback_data="add_student")
        keyboard.button(text="🏆 Мои команды", callback_data="my_teams")
        keyboard.button(text="👥 Мои подопечные", callback_data="my_students")
    else:
        keyboard.button(text="🔗 Присоединиться к команде", callback_data="join_team")
        keyboard.button(text="👨‍🏫 Найти тренера", callback_data="find_coach")
        keyboard.button(text="👥 Моя команда", callback_data="my_team")
    
    keyboard.button(text="🔙 Главное меню", callback_data="main_menu")
    keyboard.adjust(1)
    
    role_text = "тренера" if user['role'] in ['coach', 'admin'] else "игрока"
    
    await callback.message.edit_text(
        f"👥 **Командная система**\n\n"
        f"**Ваша роль:** {role_text.title()}\n\n"
        f"🎯 **Возможности:**\n"
        f"• Командные тренировки\n"
        f"• Индивидуальное тренерство\n"
        f"• Статистика прогресса\n"
        f"• Система кодов приглашений\n\n"
        f"Выберите действие:",
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()

# ===== ПОИСК УПРАЖНЕНИЙ =====
@dp.callback_query(F.data == "search_by_name")
async def search_exercise_by_name(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🔍 **Поиск упражнений по названию**\n\n"
        "Введите название упражнения для поиска:\n"
        "Например: `жим`, `приседания`, `планка`",
        parse_mode="Markdown"
    )
    await state.set_state("waiting_search")
    await callback.answer()

@dp.callback_query(F.data == "search_by_category")
async def search_by_category(callback: CallbackQuery):
    try:
        async with db_manager.pool.acquire() as conn:
            categories = await conn.fetch("SELECT DISTINCT category FROM exercises ORDER BY category")
        
        keyboard = InlineKeyboardBuilder()
        for cat in categories:
            keyboard.button(text=f"📂 {cat['category']}", callback_data=f"cat_{cat['category']}")
        keyboard.button(text="🔙 Назад", callback_data="search_exercise")
        keyboard.adjust(2)
        
        await callback.message.edit_text(
            "📂 **Выберите категорию:**",
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    await callback.answer()

@dp.callback_query(F.data.startswith("cat_"))
async def show_category_exercises(callback: CallbackQuery):
    category = callback.data[4:]
    
    try:
        async with db_manager.pool.acquire() as conn:
            exercises = await conn.fetch(
                "SELECT name, muscle_group, description FROM exercises WHERE category = $1 ORDER BY name",
                category
            )
        
        if exercises:
            text = f"📂 **Категория: {category}**\n\n"
            for ex in exercises[:15]:
                text += f"💪 **{ex['name']}**\n"
                text += f"🎯 {ex['muscle_group']}\n"
                text += f"📝 {ex['description'][:80]}...\n\n"
        else:
            text = f"❌ Упражнения в категории '{category}' не найдены"
        
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="🔙 К категориям", callback_data="search_by_category")
        keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
        
        await callback.message.edit_text(
            text,
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    await callback.answer()

# ===== ТЕСТЫ 1ПМ =====
@dp.callback_query(F.data == "new_1rm_test")
async def new_1rm_test(callback: CallbackQuery):
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

@dp.callback_query(F.data.startswith("1rm_"))
async def select_1rm_exercise(callback: CallbackQuery, state: FSMContext):
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

@dp.callback_query(F.data == "my_1rm_results")
async def show_my_1rm_results(callback: CallbackQuery):
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

# ===== СОЗДАНИЕ ТРЕНИРОВКИ С БЛОКАМИ =====
@dp.callback_query(F.data == "create_workout")
async def start_create_workout(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🏋️ **Создание новой тренировки**\n\n"
        "🆕 **Новая функция: блочная структура!**\n"
        "• 🔥 Разминка\n"
        "• ⚡ Подготовка нервной системы\n"
        "• 💪 Основная часть\n"
        "• 🧘 Заминка\n\n"
        "Введите название вашей тренировки:\n"
        "_Например: \"Силовая тренировка верха\" или \"ОФП для новичков\"_",
        parse_mode="Markdown"
    )
    await state.set_state(CreateWorkoutStates.waiting_name)
    await callback.answer()

@dp.callback_query(F.data == "skip_description")
async def skip_description(callback: CallbackQuery, state: FSMContext):
    await state.update_data(description="")
    await show_block_selection_menu(callback.message, state)
    await callback.answer()

async def show_block_selection_menu(message: Message, state: FSMContext):
    """Показать меню выбора блоков тренировки"""
    data = await state.get_data()
    selected_blocks = data.get('selected_blocks', {})
    
    text = f"🏗️ **Структура тренировки: {data['name']}**\n\n"
    text += f"📋 **Выберите блоки для вашей тренировки:**\n\n"
    
    blocks = {
        'warmup': '🔥 Разминка',
        'nervous_prep': '⚡ Подготовка нервной системы', 
        'main': '💪 Основная часть',
        'cooldown': '🧘 Заминка'
    }
    
    for block_key, block_name in blocks.items():
        status = "✅" if block_key in selected_blocks else "⭕"
        text += f"{status} **{block_name}**"
        if block_key in selected_blocks:
            exercises_count = len(selected_blocks[block_key].get('exercises', []))
            text += f" ({exercises_count} упр.)"
            if selected_blocks[block_key].get('description'):
                text += f"\n   _📝 {selected_blocks[block_key]['description'][:50]}..._"
        text += "\n\n"
    
    keyboard = InlineKeyboardBuilder()
    
    for block_key, block_name in blocks.items():
        action = "✏️ Изменить" if block_key in selected_blocks else "➕ Добавить"
        keyboard.button(
            text=f"{action} {block_name.split(' ', 1)[1]}", 
            callback_data=f"select_block_{block_key}"
        )
    
    if selected_blocks:
        keyboard.button(text="✅ Завершить создание", callback_data="finish_workout_creation")
    
    keyboard.button(text="❌ Отменить", callback_data="cancel_workout_creation")
    keyboard.adjust(2)
    
    try:
        await message.edit_text(text, reply_markup=keyboard.as_markup(), parse_mode="Markdown")
    except:
        await message.answer(text, reply_markup=keyboard.as_markup(), parse_mode="Markdown")
    
    await state.set_state(CreateWorkoutStates.selecting_blocks)

@dp.callback_query(F.data.startswith("select_block_"))
async def select_workout_block(callback: CallbackQuery, state: FSMContext):
    block_key = callback.data.split("_", 2)[2]
    
    block_info = {
        'warmup': {
            'name': '🔥 Разминка',
            'description': 'Подготовка тела к нагрузке, разогрев мышц и суставов',
            'examples': 'Легкое кардио, динамическая растяжка, суставная гимнастика'
        },
        'nervous_prep': {
            'name': '⚡ Подготовка нервной системы',
            'description': 'Активация нервной системы перед основной работой',
            'examples': 'Взрывные движения, активационные упражнения, плиометрика'
        },
        'main': {
            'name': '💪 Основная часть',
            'description': 'Главная тренировочная нагрузка',
            'examples': 'Основные упражнения, силовая работа, технические элементы'
        },
        'cooldown': {
            'name': '🧘 Заминка',
            'description': 'Восстановление и расслабление после тренировки',
            'examples': 'Статическая растяжка, дыхательные упражнения, расслабление'
        }
    }
    
    info = block_info[block_key]
    await state.update_data(current_block=block_key)
    
    text = f"📋 **{info['name']}**\n\n"
    text += f"**Описание:**\n{info['description']}\n\n"
    text += f"**Примеры упражнений:**\n{info['examples']}\n\n"
    text += f"**Что вы хотите сделать с этим блоком?**"
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="📝 Добавить описание блока", callback_data="add_block_description")
    keyboard.button(text="⏭️ Сразу к упражнениям", callback_data="skip_block_description")
    keyboard.button(text="🗑️ Пропустить блок", callback_data="skip_entire_block")
    keyboard.button(text="🔙 К выбору блоков", callback_data="back_to_blocks")
    keyboard.adjust(1)
    
    await callback.message.edit_text(
        text,
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data == "add_block_description")
async def add_block_description(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    block_key = data.get('current_block')
    
    block_names = {
        'warmup': '🔥 Разминка',
        'nervous_prep': '⚡ Подготовка нервной системы',
        'main': '💪 Основная часть', 
        'cooldown': '🧘 Заминка'
    }
    
    await callback.message.edit_text(
        f"📝 **Описание блока: {block_names[block_key]}**\n\n"
        f"Введите описание для этого блока:\n"
        f"_Например: \"10 минут легкого кардио + суставная разминка\"_\n\n"
        f"Или опишите цели и особенности данного блока.",
        parse_mode="Markdown"
    )
    await state.set_state(CreateWorkoutStates.adding_block_description)
    await callback.answer()

@dp.callback_query(F.data == "skip_block_description")
async def skip_block_description(callback: CallbackQuery, state: FSMContext):
    await state.update_data(current_block_description="")
    await show_block_exercises_menu(callback.message, state)
    await callback.answer()

@dp.callback_query(F.data == "skip_entire_block")
async def skip_entire_block(callback: CallbackQuery, state: FSMContext):
    await show_block_selection_menu(callback.message, state)
    await callback.answer()

@dp.callback_query(F.data == "back_to_blocks")
async def back_to_blocks(callback: CallbackQuery, state: FSMContext):
    await show_block_selection_menu(callback.message, state)
    await callback.answer()

async def show_block_exercises_menu(message: Message, state: FSMContext):
    """Показать меню добавления упражнений в блок"""
    data = await state.get_data()
    block_key = data.get('current_block')
    selected_blocks = data.get('selected_blocks', {})
    current_block_data = selected_blocks.get(block_key, {'exercises': [], 'description': data.get('current_block_description', '')})
    
    block_names = {
        'warmup': '🔥 Разминка',
        'nervous_prep': '⚡ Подготовка нервной системы',
        'main': '💪 Основная часть',
        'cooldown': '🧘 Заминка'
    }
    
    exercises = current_block_data['exercises']
    
    text = f"🏋️ **{block_names[block_key]}**\n\n"
    
    if current_block_data['description']:
        text += f"📝 _{current_block_data['description']}_\n\n"
    
    if exercises:
        text += f"**📋 Упражнения в блоке: {len(exercises)}**\n"
        for i, ex in enumerate(exercises, 1):
            text += f"{i}. {ex['name']} - {ex['sets']}×{ex['reps_min']}-{ex['reps_max']}"
            if ex.get('one_rm_percent'):
                text += f" ({ex['one_rm_percent']}% 1ПМ)"
            text += "\n"
        text += "\n"
    
    text += "➕ **Добавьте упражнения в блок:**"
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔍 Найти упражнение", callback_data="find_exercise_for_block")
    keyboard.button(text="📂 По категориям", callback_data="browse_categories_for_block")
    
    if exercises:
        keyboard.button(text="✅ Завершить блок", callback_data="finish_current_block")
        keyboard.button(text="🗑️ Удалить последнее", callback_data="remove_last_block_exercise")
    else:
        keyboard.button(text="✅ Пустой блок", callback_data="finish_current_block")
    
    keyboard.button(text="🔙 К выбору блоков", callback_data="back_to_blocks")
    keyboard.adjust(2)
    
    try:
        await message.edit_text(text, reply_markup=keyboard.as_markup(), parse_mode="Markdown")
    except:
        await message.answer(text, reply_markup=keyboard.as_markup(), parse_mode="Markdown")
    
    await state.set_state(CreateWorkoutStates.adding_exercises)

@dp.callback_query(F.data == "find_exercise_for_block")
async def find_exercise_for_block(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🔍 **Поиск упражнения для блока**\n\n"
        "Введите название упражнения:\n"
        "_Например: жим, приседания, планка, растяжка_",
        parse_mode="Markdown"
    )
    await state.set_state("searching_exercise_for_block")
    await callback.answer()

@dp.callback_query(F.data == "browse_categories_for_block")
async def browse_categories_for_block(callback: CallbackQuery):
    try:
        async with db_manager.pool.acquire() as conn:
            categories = await conn.fetch("SELECT DISTINCT category FROM exercises ORDER BY category")
        
        keyboard = InlineKeyboardBuilder()
        for cat in categories:
            keyboard.button(
                text=f"📂 {cat['category']}", 
                callback_data=f"block_cat_{cat['category']}"
            )
        keyboard.button(text="🔙 К упражнениям блока", callback_data="back_to_block_exercises")
        keyboard.adjust(2)
        
        await callback.message.edit_text(
            "📂 **Выберите категорию упражнений:**",
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    await callback.answer()

@dp.callback_query(F.data.startswith("block_cat_"))
async def show_block_category_exercises(callback: CallbackQuery, state: FSMContext):
    category = callback.data[10:]
    
    try:
        async with db_manager.pool.acquire() as conn:
            exercises = await conn.fetch(
                "SELECT id, name, muscle_group FROM exercises WHERE category = $1 ORDER BY name",
                category
            )
        
        if exercises:
            text = f"📂 **{category} упражнения:**\n\n"
            keyboard = InlineKeyboardBuilder()
            
            for ex in exercises:
                keyboard.button(
                    text=f"{ex['name']} ({ex['muscle_group']})", 
                    callback_data=f"add_block_ex_{ex['id']}"
                )
            
            keyboard.button(text="🔙 К категориям", callback_data="browse_categories_for_block")
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

@dp.callback_query(F.data == "back_to_block_exercises")
async def back_to_block_exercises(callback: CallbackQuery, state: FSMContext):
    await show_block_exercises_menu(callback.message, state)
    await callback.answer()

@dp.callback_query(F.data.startswith("add_block_ex_"))
async def add_exercise_to_block(callback: CallbackQuery, state: FSMContext):
    exercise_id = int(callback.data.split("_")[3])
    
    try:
        async with db_manager.pool.acquire() as conn:
            exercise = await conn.fetchrow(
                "SELECT id, name, category, muscle_group FROM exercises WHERE id = $1", 
                exercise_id
            )
        
        if exercise:
            await state.update_data(
                current_exercise_id=exercise_id,
                current_exercise_name=exercise['name']
            )
            
            text = f"⚙️ **Настройка упражнения для блока**\n\n"
            text += f"💪 **{exercise['name']}**\n"
            text += f"📂 {exercise['category']} • {exercise['muscle_group']}\n\n"
            text += f"**Настройте параметры:**"
            
            keyboard = InlineKeyboardBuilder()
            keyboard.button(text="🏋️ Простая настройка", callback_data="simple_block_config")
            keyboard.button(text="📊 С процентами от 1ПМ", callback_data="advanced_block_config")
            keyboard.button(text="🔙 Назад к выбору", callback_data="back_to_block_exercises")
            keyboard.adjust(1)
            
            await callback.message.edit_text(
                text,
                reply_markup=keyboard.as_markup(),
                parse_mode="Markdown"
            )
            
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    await callback.answer()

@dp.callback_query(F.data == "simple_block_config")
async def simple_block_config(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    exercise_name = data.get('current_exercise_name', 'Упражнение')
    
    text = f"🏋️ **Простая настройка: {exercise_name}**\n\n"
    text += f"Введите параметры в формате:\n"
    text += f"`подходы повторения_мин повторения_макс`\n\n"
    text += f"**Примеры:**\n"
    text += f"• `3 8 12` - 3 подхода по 8-12 повторений\n"
    text += f"• `4 6 8` - 4 подхода по 6-8 повторений\n"
    text += f"• `1 60 60` - 1 подход на 60 секунд (для планки)\n"
    text += f"• `2 10 15` - 2 подхода по 10-15 повторений"
    
    await callback.message.edit_text(text, parse_mode="Markdown")
    await state.set_state("simple_block_config")
    await callback.answer()

@dp.callback_query(F.data == "advanced_block_config")
async def advanced_block_config(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    exercise_name = data.get('current_exercise_name', 'Упражнение')
    exercise_id = data.get('current_exercise_id')
    
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    
    try:
        async with db_manager.pool.acquire() as conn:
            user_1rm = await conn.fetchrow("""
                SELECT weight FROM one_rep_max 
                WHERE user_id = $1 AND exercise_id = $2 
                ORDER BY tested_at DESC LIMIT 1
            """, user['id'], exercise_id)
        
        text = f"📊 **Настройка с 1ПМ: {exercise_name}**\n\n"
        
        if user_1rm:
            current_1rm = float(user_1rm['weight'])
            text += f"💪 **Ваш текущий 1ПМ:** {current_1rm} кг\n\n"
            text += f"Введите параметры в формате:\n"
            text += f"`подходы повторения_мин повторения_макс процент_1ПМ`\n\n"
            text += f"**Примеры:**\n"
            text += f"• `4 6 8 80` - 4×6-8 на 80% (≈{round(current_1rm * 0.8, 1)}кг)\n"
            text += f"• `3 8 12 70` - 3×8-12 на 70% (≈{round(current_1rm * 0.7, 1)}кг)\n"
            text += f"• `5 3 5 85` - 5×3-5 на 85% (≈{round(current_1rm * 0.85, 1)}кг)"
            
            await callback.message.edit_text(text, parse_mode="Markdown")
            await state.set_state("advanced_block_config")
        else:
            text += f"⚠️ **У вас нет результата 1ПМ для этого упражнения**\n\n"
            text += f"Введите параметры БЕЗ процентов или пройдите тест 1ПМ."
            
            keyboard = InlineKeyboardBuilder()
            keyboard.button(text="💪 Пройти тест 1ПМ", callback_data=f"1rm_{exercise_id}")
            keyboard.button(text="🔙 Простая настройка", callback_data="simple_block_config")
            
            await callback.message.edit_text(
                text, 
                reply_markup=keyboard.as_markup(),
                parse_mode="Markdown"
            )
        
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    await callback.answer()

@dp.callback_query(F.data == "finish_current_block")
async def finish_current_block(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    block_key = data.get('current_block')
    selected_blocks = data.get('selected_blocks', {})
    
    current_block_data = selected_blocks.get(block_key, {'exercises': [], 'description': ''})
    current_block_data['description'] = data.get('current_block_description', '')
    selected_blocks[block_key] = current_block_data
    
    await state.update_data(selected_blocks=selected_blocks)
    await callback.answer("✅ Блок сохранен!")
    await show_block_selection_menu(callback.message, state)

@dp.callback_query(F.data == "finish_workout_creation")
async def finish_workout_creation(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    selected_blocks = data.get('selected_blocks', {})
    
    try:
        total_exercises = sum(len(block_data['exercises']) for block_data in selected_blocks.values())
        
        if total_exercises == 0:
            await callback.answer("❌ Добавьте хотя бы одно упражнение!")
            return
        
        async with db_manager.pool.acquire() as conn:
            workout_id = await conn.fetchval("""
                INSERT INTO workouts (name, description, created_by, visibility, difficulty_level, estimated_duration_minutes)
                VALUES ($1, $2, $3, 'private', 'intermediate', $4)
                RETURNING id
            """, data['name'], data.get('description', ''), user['id'], total_exercises * 8)
            
            workout_unique_id = await conn.fetchval("SELECT unique_id FROM workouts WHERE id = $1", workout_id)
            
            exercise_order = 0
            for phase, block_data in selected_blocks.items():
                for exercise in block_data['exercises']:
                    exercise_order += 1
                    await conn.execute("""
                        INSERT INTO workout_exercises (
                            workout_id, exercise_id, phase, order_in_phase, sets, 
                            reps_min, reps_max, one_rm_percent, rest_seconds
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    """, workout_id, exercise['id'], phase, exercise_order, exercise['sets'], 
                         exercise['reps_min'], exercise['reps_max'], 
                         exercise['one_rm_percent'], exercise['rest_seconds'])
        
        text = f"🎉 **Тренировка создана успешно!**\n\n"
        text += f"🏋️ **Название:** {data['name']}\n"
        text += f"🆔 **Код:** `{workout_unique_id}`\n"
        text += f"📋 **Всего упражнений:** {total_exercises}\n\n"
        
        block_names = {
            'warmup': '🔥 Разминка',
            'nervous_prep': '⚡ Подготовка НС',
            'main': '💪 Основная часть',
            'cooldown': '🧘 Заминка'
        }
        
        for phase, block_data in selected_blocks.items():
            if block_data['exercises']:
                text += f"**{block_names[phase]}:** {len(block_data['exercises'])} упр.\n"
                if block_data.get('description'):
                    text += f"   _{block_data['description']}_\n"
        
        text += f"\n💡 **Поделитесь кодом** `{workout_unique_id}` с другими!"
        
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="🏋️ Мои тренировки", callback_data="my_workouts")
        keyboard.button(text="➕ Создать еще", callback_data="create_workout")
        keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
        keyboard.adjust(2)
        
        await callback.message.edit_text(
            text,
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )
        
        await state.clear()
        
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка сохранения: {e}")
    
    await callback.answer()

@dp.callback_query(F.data == "cancel_workout_creation")
async def cancel_workout_creation(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "❌ **Создание тренировки отменено**",
        parse_mode="Markdown"
    )
    await callback.answer()

# ===== ЗАГЛУШКИ ДЛЯ БУДУЩИХ ФУНКЦИЙ =====
@dp.callback_query(F.data.in_([
    "my_workouts", "find_workout", "1rm_stats", "search_by_muscle",
    "create_team", "add_student", "my_teams", "my_students",
    "join_team", "find_coach", "my_team"
]))
async def feature_coming_soon(callback: CallbackQuery):
    feature_names = {
        "my_workouts": "Мои тренировки",
        "find_workout": "Поиск тренировок", 
        "1rm_stats": "Статистика 1ПМ",
        "search_by_muscle": "Поиск по мышцам",
        "create_team": "Создание команды",
        "add_student": "Добавление подопечного",
        "my_teams": "Мои команды",
        "my_students": "Мои подопечные", 
        "join_team": "Присоединение к команде",
        "find_coach": "Поиск тренера",
        "my_team": "Моя команда"
    }
    
    feature_name = feature_names.get(callback.data, "Эта функция")
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔙 Назад", callback_data="main_menu")
    
    await callback.message.edit_text(
        f"🚧 **{feature_name}**\n\n"
        f"Функция находится в разработке.\n"
        f"Скоро будет доступна!",
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()

# ===== ЕДИНЫЙ ОБРАБОТЧИК СООБЩЕНИЙ =====
@dp.message()
async def handle_user_input(message: Message, state: FSMContext):
    """Обработка всех текстовых сообщений пользователя"""
    current_state = await state.get_state()
    
    # ===== СОЗДАНИЕ ТРЕНИРОВКИ С БЛОКАМИ =====
    if current_state == CreateWorkoutStates.waiting_name:
        await process_workout_name(message, state)
        return
    
    elif current_state == CreateWorkoutStates.waiting_description:
        await process_workout_description(message, state)
        return
    
    elif current_state == CreateWorkoutStates.adding_block_description:
        description = message.text.strip()
        
        if len(description) > 200:
            await message.answer("❌ Описание слишком длинное. Максимум 200 символов.")
            return
            
        await state.update_data(current_block_description=description)
        
        await message.answer(
            f"✅ **Описание блока сохранено:**\n\n"
            f"_{description}_\n\n"
            f"Переходим к добавлению упражнений в блок...",
            parse_mode="Markdown"
        )
        
        await show_block_exercises_menu(message, state)
        return
    
    elif current_state == "simple_block_config":
        await process_simple_block_config(message, state)
        return
        
    elif current_state == "advanced_block_config":
        await process_advanced_block_config(message, state)
        return
    
    elif current_state == "searching_exercise_for_block":
        await handle_block_exercise_search(message, state)
        return
    
    # ===== ПОИСК УПРАЖНЕНИЙ =====
    elif current_state == "waiting_search":
        search_term = message.text.lower()
        
        try:
            async with db_manager.pool.acquire() as conn:
                exercises = await conn.fetch("""
                    SELECT name, category, muscle_group, description 
                    FROM exercises 
                    WHERE LOWER(name) LIKE $1 
                       OR LOWER(category) LIKE $1
                       OR LOWER(muscle_group) LIKE $1
                    ORDER BY 
                        CASE WHEN LOWER(name) LIKE $1 THEN 1 ELSE 2 END,
                        name
                    LIMIT 10
                """, f"%{search_term}%")
            
            if exercises:
                text = f"🔍 **Найдено: {len(exercises)} упражнений**\n\n"
                for ex in exercises:
                    text += f"💪 **{ex['name']}**\n"
                    text += f"📂 {ex['category']} • {ex['muscle_group']}\n"
                    text += f"📝 {ex['description'][:100]}...\n\n"
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
    
    # ===== 1ПМ ТЕСТЫ =====
    elif current_state == "waiting_1rm_data":
        try:
            parts = message.text.split()
            if len(parts) != 2:
                await message.answer("❌ Неверный формат. Введите: `вес повторения`\nПример: `80 5`")
                return
            
            weight = float(parts[0])
            reps = int(parts[1])
            
            if weight <= 0 or reps <= 0 or reps > 30:
                await message.answer("❌ Проверьте данные:\n• Вес > 0\n• Повторения 1-30")
                return
            
            # Расчет 1ПМ по формулам
            def calculate_1rm(w, r):
                w = float(w)
                r = int(r)
                
                if r == 1:
                    return {
                        'brzycki': w,
                        'epley': w,
                        'alternative': w,
                        'average': w
                    }
                
                brzycki = w / (1.0278 - 0.0278 * r)
                epley = w * (1 + r / 30.0)
                alternative = w * (1 + 0.025 * r)
                average = (brzycki + epley + alternative) / 3.0
                
                return {
                    'brzycki': round(brzycki, 1),
                    'epley': round(epley, 1), 
                    'alternative': round(alternative, 1),
                    'average': round(average, 1)
                }
            
            results = calculate_1rm(weight, reps)
            state_data = await state.get_data()
            exercise_name = state_data.get('exercise_name', 'Упражнение')
            
            # Сохраняем результат
            user = await db_manager.get_user_by_telegram_id(message.from_user.id)
            async with db_manager.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO one_rep_max (user_id, exercise_id, weight, reps, test_weight, 
                                           formula_brzycki, formula_epley, formula_alternative, formula_average)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """, user['id'], int(state_data['exercise_id']), results['average'], 
                     reps, weight, results['brzycki'], results['epley'], 
                     results['alternative'], results['average'])
            
            text = f"🎉 **Результат теста 1ПМ**\n\n"
            text += f"💪 **Упражнение:** {exercise_name}\n"
            text += f"📊 **Тестовые данные:** {weight} кг × {reps} раз\n\n"
            text += f"**📈 Расчет по формулам:**\n"
            text += f"• Бжицкого: {results['brzycki']} кг\n"
            text += f"• Эпли: {results['epley']} кг\n" 
            text += f"• Альтернативная: {results['alternative']} кг\n\n"
            text += f"🎯 **Ваш 1ПМ: {results['average']} кг**\n"
            text += f"_(среднее по 3 формулам)_"
            
            keyboard = InlineKeyboardBuilder()
            keyboard.button(text="💪 Новый тест", callback_data="new_1rm_test")
            keyboard.button(text="📊 Мои результаты", callback_data="my_1rm_results")
            keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
            
            await message.answer(text, reply_markup=keyboard.as_markup(), parse_mode="Markdown")
            await state.clear()
            
        except ValueError:
            await message.answer("❌ Ошибка формата данных. Используйте числа.\nПример: `80 5`")
        except Exception as e:
            await message.answer(f"❌ Ошибка сохранения: {e}")
    
    else:
        # Если состояние не определено, показываем справку
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
        
        await message.answer(
            "ℹ️ Используйте меню бота для навигации.\n"
            "Нажмите /start для возврата в главное меню.",
            reply_markup=keyboard.as_markup()
        )

# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====
async def process_workout_name(message: Message, state: FSMContext):
    workout_name = message.text.strip()
    
    if len(workout_name) < 3:
        await message.answer("❌ Название слишком короткое. Минимум 3 символа.")
        return
    
    if len(workout_name) > 100:
        await message.answer("❌ Название слишком длинное. Максимум 100 символов.")
        return
    
    await state.update_data(name=workout_name)
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="⏭️ Пропустить описание", callback_data="skip_description")
    
    await message.answer(
        f"✅ **Название:** {workout_name}\n\n"
        f"📝 Теперь введите описание тренировки:\n"
        f"_Например: \"Программа для развития силы основных групп мышц\"_\n\n"
        f"Или нажмите кнопку чтобы пропустить:",
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    await state.set_state(CreateWorkoutStates.waiting_description)

async def process_workout_description(message: Message, state: FSMContext):
    description = message.text.strip()
    await state.update_data(description=description)
    await show_block_selection_menu(message, state)

async def handle_block_exercise_search(message: Message, state: FSMContext):
    search_term = message.text.lower()
    
    try:
        async with db_manager.pool.acquire() as conn:
            exercises = await conn.fetch("""
                SELECT id, name, category, muscle_group 
                FROM exercises 
                WHERE LOWER(name) LIKE $1 
                   OR LOWER(muscle_group) LIKE $1
                ORDER BY name
                LIMIT 10
            """, f"%{search_term}%")
        
        if exercises:
            text = f"🔍 **Найдено упражнений: {len(exercises)}**\n\n"
            keyboard = InlineKeyboardBuilder()
            
            for ex in exercises:
                keyboard.button(
                    text=f"{ex['name']} ({ex['muscle_group']})", 
                    callback_data=f"add_block_ex_{ex['id']}"
                )
            
            keyboard.button(text="🔙 К блоку", callback_data="back_to_block_exercises")
            keyboard.adjust(1)
            
            await message.answer(
                text,
                reply_markup=keyboard.as_markup(),
                parse_mode="Markdown"
            )
            await state.set_state(CreateWorkoutStates.adding_exercises)
        else:
            await message.answer(f"❌ Упражнения по запросу '{search_term}' не найдены")
            
    except Exception as e:
        await message.answer(f"❌ Ошибка поиска: {e}")

async def process_simple_block_config(message: Message, state: FSMContext):
    """Обработка простой конфигурации блока"""
    try:
        parts = message.text.split()
        if len(parts) != 3:
            await message.answer("❌ Неверный формат. Используйте: `подходы мин_повт макс_повт`")
            return
        
        sets = int(parts[0])
        reps_min = int(parts[1])
        reps_max = int(parts[2])
        
        if not (1 <= sets <= 10) or not (1 <= reps_min <= 200) or not (reps_min <= reps_max <= 200):
            await message.answer("❌ Проверьте параметры:\n• Подходы: 1-10\n• Повторения: 1-200\n• Мин ≤ Макс")
            return
        
        await add_exercise_to_block_data(message, state, sets, reps_min, reps_max)
        
    except ValueError:
        await message.answer("❌ Используйте только числа. Пример: `3 8 12`")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

async def process_advanced_block_config(message: Message, state: FSMContext):
    """Обработка продвинутой конфигурации блока с 1ПМ"""
    try:
        parts = message.text.split()
        if len(parts) not in [3, 4]:
            await message.answer("❌ Формат: `подходы мин_повт макс_повт [процент_1ПМ]`")
            return
        
        sets = int(parts[0])
        reps_min = int(parts[1])
        reps_max = int(parts[2])
        one_rm_percent = int(parts[3]) if len(parts) == 4 else None
        
        if not (1 <= sets <= 10) or not (1 <= reps_min <= 50) or not (reps_min <= reps_max <= 50):
            await message.answer("❌ Проверьте параметры:\n• Подходы: 1-10\n• Повторения: 1-50")
            return
            
        if one_rm_percent and not (30 <= one_rm_percent <= 120):
            await message.answer("❌ Процент 1ПМ должен быть от 30% до 120%")
            return
        
        await add_exercise_to_block_data(message, state, sets, reps_min, reps_max, one_rm_percent)
        
    except ValueError:
        await message.answer("❌ Используйте только числа. Пример: `4 6 8 80`")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

async def add_exercise_to_block_data(message: Message, state: FSMContext, sets: int, reps_min: int, reps_max: int, one_rm_percent: int = None):
    """Добавить упражнение в блок"""
    data = await state.get_data()
    block_key = data.get('current_block')
    selected_blocks = data.get('selected_blocks', {})
    
    current_block_data = selected_blocks.get(block_key, {'exercises': [], 'description': data.get('current_block_description', '')})
    
    exercise_data = {
        'id': data['current_exercise_id'],
        'name': data['current_exercise_name'],
        'sets': sets,
        'reps_min': reps_min,
        'reps_max': reps_max,
        'one_rm_percent': one_rm_percent,
        'rest_seconds': 90
    }
    
    current_block_data['exercises'].append(exercise_data)
    selected_blocks[block_key] = current_block_data
    await state.update_data(selected_blocks=selected_blocks)
    
    text = f"✅ **Упражнение добавлено в блок!**\n\n"
    text += f"💪 {exercise_data['name']}\n"
    text += f"📊 {sets}×{reps_min}-{reps_max}"
    if one_rm_percent:
        text += f" ({one_rm_percent}% 1ПМ)"
    
    await message.answer(text, parse_mode="Markdown")
    await show_block_exercises_menu(message, state)

# ===== ГЛАВНАЯ ФУНКЦИЯ =====
async def main():
    """Главная функция запуска бота"""
    try:
        # Инициализация базы данных
        await init_database()
        
        # Информация о запуске
        bot_info = await bot.get_me()
        logger.info(f"🚀 Бот {bot_info.first_name} (@{bot_info.username}) запущен!")
        
        # Запуск поллинга
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
    finally:
        # Закрытие соединений
        await db_manager.close_pool()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())