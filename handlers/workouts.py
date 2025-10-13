# ===== ИСПРАВЛЕННЫЙ handlers/workouts.py С ИНТЕГРАЦИЕЙ СТАРОГО КОДА =====
from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database import db_manager
from states.workout_states import CreateWorkoutStates

# ===== ОБНОВЛЕННЫЕ FSM СОСТОЯНИЯ =====
# В states/workout_states.py должно быть:
"""
from aiogram.fsm.state import State, StatesGroup

class CreateWorkoutStates(StatesGroup):
    waiting_name = State()
    waiting_description = State()  
    selecting_blocks = State()
    adding_block_description = State()
    adding_exercises = State()
    configuring_exercise = State()
"""

# ===== ГЛАВНОЕ МЕНЮ ТРЕНИРОВОК =====
async def workouts_menu(callback: CallbackQuery):
    """Главное меню тренировок"""
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    
    try:
        async with db_manager.pool.acquire() as conn:
            # Статистика тренировок пользователя
            stats = await conn.fetchrow("""
                SELECT COUNT(*) as total_workouts,
                COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '7 days') as recent_workouts
                FROM workouts WHERE created_by = $1
            """, user['id'])
        
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="🏋️ Мои тренировки", callback_data="my_workouts")
        keyboard.button(text="🔍 Найти тренировку", callback_data="find_workout")
        keyboard.button(text="➕ Создать тренировку", callback_data="create_workout")
        keyboard.button(text="📊 Статистика", callback_data="workout_stats")
        keyboard.button(text="🔙 Главное меню", callback_data="main_menu")
        keyboard.adjust(2)
        
        text = f"🏋️ **Система тренировок**\n\n"
        
        total_workouts = stats['total_workouts'] or 0
        if total_workouts > 0:
            text += f"📊 **Ваша статистика:**\n"
            text += f"• Всего тренировок: **{total_workouts}**\n"
            text += f"• За неделю: **{stats['recent_workouts'] or 0}**\n\n"
        else:
            text += f"🆕 **Добро пожаловать в систему тренировок!**\n\n"
            text += f"💪 **Возможности:**\n"
            text += f"• Создавайте персональные тренировки\n"
            text += f"• Группируйте упражнения в блоки\n"
            text += f"• Отслеживайте прогресс\n"
            text += f"• Делитесь тренировками с командой\n\n"
        
        text += f"**Выберите действие:**"
        
        await callback.message.edit_text(
            text,
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    
    await callback.answer()

# ===== МОИ ТРЕНИРОВКИ =====
async def my_workouts(callback: CallbackQuery):
    """Показать тренировки пользователя"""
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    
    try:
        async with db_manager.pool.acquire() as conn:
            # Получаем тренировки пользователя
            workouts = await conn.fetch("""
                SELECT w.*, COUNT(DISTINCT we.id) as exercises_count
                FROM workouts w
                LEFT JOIN workout_exercises we ON w.id = we.workout_id
                WHERE w.created_by = $1
                GROUP BY w.id
                ORDER BY w.created_at DESC
                LIMIT 10
            """, user['id'])
        
        if workouts:
            text = f"🏋️ **Ваши тренировки ({len(workouts)}):**\n\n"
            
            keyboard = InlineKeyboardBuilder()
            
            for workout in workouts:
                text += f"💪 **{workout['name']}**\n"
                text += f"📊 Упражнений: {workout['exercises_count']} • "
                text += f"ID: `{workout.get('unique_id', workout['id'])}`\n"
                
                if workout['description']:
                    text += f"📝 _{workout['description'][:50]}{'...' if len(workout['description']) > 50 else ''}_\n"
                
                text += f"📅 {workout['created_at'].strftime('%d.%m.%Y')}\n\n"
                
                keyboard.button(
                    text=f"💪 {workout['name'][:20]}{'...' if len(workout['name']) > 20 else ''}",   
                    callback_data=f"view_workout_{workout['id']}"
                )
            
            keyboard.button(text="➕ Создать новую", callback_data="create_workout")
            keyboard.button(text="🔙 К тренировкам", callback_data="workouts_menu")
            keyboard.adjust(1)
            
        else:
            text = f"🏋️ **У вас пока нет тренировок**\n\n"
            text += f"Создайте первую тренировку!\n\n"
            text += f"💡 **Идеи для тренировок:**\n"
            text += f"• Силовая тренировка верха\n"
            text += f"• Кардио + функциональные\n"
            text += f"• Восстановительная тренировка\n"
            text += f"• Тренировка дома"
            
            keyboard = InlineKeyboardBuilder()
            keyboard.button(text="➕ Создать тренировку", callback_data="create_workout")
            keyboard.button(text="🔍 Найти готовую", callback_data="find_workout")
            keyboard.button(text="🔙 К тренировкам", callback_data="workouts_menu")
        
        await callback.message.edit_text(
            text,
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    
    await callback.answer()

# ===== СОЗДАНИЕ ТРЕНИРОВКИ С БЛОКАМИ =====
async def create_workout(callback: CallbackQuery, state: FSMContext):
    """Начало создания новой тренировки"""
    await callback.message.edit_text(
        "🏋️ **Создание новой тренировки**\n\n"
        "Введите название вашей тренировки:\n"
        "_Например: \"Силовая тренировка верха\" или \"ОФП для новичков\"_",
        parse_mode="Markdown"
    )
    await state.set_state(CreateWorkoutStates.waiting_name)
    await callback.answer()

async def process_workout_name(message: Message, state: FSMContext):
    """Обработка названия тренировки"""
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
    keyboard.button(text="❌ Отменить", callback_data="cancel_workout_creation")
    
    await message.answer(
        f"✅ **Название:** {workout_name}\n\n"
        f"📝 **Введите описание тренировки** (необязательно):\n"
        f"_Например: 'Силовая тренировка для развития верха тела'_\n\n"
        f"Или пропустите этот шаг:",
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    await state.set_state(CreateWorkoutStates.waiting_description)

async def process_workout_description(message: Message, state: FSMContext):
    """Обработка описания тренировки"""
    description = message.text.strip()
    await state.update_data(description=description)
    await show_block_selection_menu(message, state)

async def skip_description(callback: CallbackQuery, state: FSMContext):
    """Пропуск описания и переход к блокам"""
    await state.update_data(description="")
    await show_block_selection_menu(callback.message, state)
    await callback.answer()

# ===== МЕНЮ ВЫБОРА БЛОКОВ =====
async def show_block_selection_menu(message: Message, state: FSMContext):
    """Показать меню выбора блоков тренировки"""
    data = await state.get_data()
    selected_blocks = data.get('selected_blocks', {})
    
    text = f"🏗️ **Структура тренировки: {data['name']}**\n\n"
    text += f"📋 **Выберите блоки для вашей тренировки:**\n\n"
    
    # Показываем статус каждого блока
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
    
    # Кнопки для каждого блока
    for block_key, block_name in blocks.items():
        action = "✏️ Изменить" if block_key in selected_blocks else "➕ Добавить"
        keyboard.button(
            text=f"{action} {block_name.split(' ', 1)}", 
            callback_data=f"select_block_{block_key}"
        )
    
    # Управляющие кнопки
    if selected_blocks:
        keyboard.button(text="✅ Завершить создание", callback_data="finish_workout_creation")
    
    keyboard.button(text="❌ Отменить", callback_data="cancel_workout_creation")
    keyboard.adjust(2)
    
    try:
        await message.edit_text(text, reply_markup=keyboard.as_markup(), parse_mode="Markdown")
    except:
        await message.answer(text, reply_markup=keyboard.as_markup(), parse_mode="Markdown")
    
    await state.set_state(CreateWorkoutStates.selecting_blocks)

# ===== ВЫБОР БЛОКА =====
async def select_workout_block(callback: CallbackQuery, state: FSMContext):
    """Выбор и настройка блока тренировки"""
    
    # ИСПРАВЛЕНИЕ: Добавляем отладку и безопасное извлечение block_key
    print(f"🔍 DEBUG: callback.data = '{callback.data}'")
    
    # Безопасное разделение callback_data
    parts = callback.data.split("_")
    print(f"🔍 DEBUG: split parts = {parts}")
    
    if len(parts) < 3:
        print("❌ ERROR: Неполный callback_data")
        await callback.answer("❌ Ошибка данных кнопки")
        return
    
    # Берем именно третью часть как строку
    block_key = parts[2]
    print(f"🔍 DEBUG: block_key = '{block_key}' (тип: {type(block_key)})")
    
    # Проверяем, что block_key - строка
    if not isinstance(block_key, str):
        print(f"❌ ERROR: block_key должен быть строкой, получен {type(block_key)}")
        await callback.answer("❌ Ошибка типа данных")
        return
    
    # Проверяем, что block_key не пустой
    if not block_key or block_key == "":
        print("❌ ERROR: Пустой block_key")
        await callback.answer("❌ Пустой ключ блока")
        return
    
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
    
    # Проверяем, что block_key существует в словаре
    if block_key not in block_info:
        print(f"❌ ERROR: Неизвестный block_key = '{block_key}'")
        available_keys = list(block_info.keys())
        print(f"Доступные ключи: {available_keys}")
        await callback.answer(f"❌ Неизвестный блок: {block_key}")
        return
    
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

# ===== ОПИСАНИЕ БЛОКА =====
async def add_block_description(callback: CallbackQuery, state: FSMContext):
    """Добавление описания блока"""
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

async def skip_block_description(callback: CallbackQuery, state: FSMContext):
    """Пропуск описания блока"""
    await state.update_data(current_block_description="")
    await show_block_exercises_menu(callback.message, state)
    await callback.answer()

async def skip_entire_block(callback: CallbackQuery, state: FSMContext):
    """Пропуск всего блока"""
    await show_block_selection_menu(callback.message, state)
    await callback.answer()

async def back_to_blocks(callback: CallbackQuery, state: FSMContext):
    """Возврат к выбору блоков"""
    await show_block_selection_menu(callback.message, state)
    await callback.answer()

# ===== МЕНЮ УПРАЖНЕНИЙ БЛОКА =====
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

# ===== ЗАВЕРШЕНИЕ БЛОКА =====
async def finish_current_block(callback: CallbackQuery, state: FSMContext):
    """Завершение текущего блока"""
    data = await state.get_data()
    block_key = data.get('current_block')
    selected_blocks = data.get('selected_blocks', {})
    
    # Сохраняем блок
    current_block_data = selected_blocks.get(block_key, {'exercises': [], 'description': ''})
    current_block_data['description'] = data.get('current_block_description', '')
    selected_blocks[block_key] = current_block_data
    
    await state.update_data(selected_blocks=selected_blocks)
    await callback.answer("✅ Блок сохранен!")
    await show_block_selection_menu(callback.message, state)

# ===== ПОИСК УПРАЖНЕНИЙ ДЛЯ БЛОКОВ =====
async def find_exercise_for_block(callback: CallbackQuery, state: FSMContext):
    """Поиск упражнений для блока"""
    await callback.message.edit_text(
        "🔍 **Поиск упражнения для блока**\n\n"
        "Введите название упражнения:\n"
        "_Например: жим, приседания, планка, растяжка_",
        parse_mode="Markdown"
    )
    await state.set_state("searching_exercise_for_block")
    await callback.answer()

async def handle_block_exercise_search(message: Message, state: FSMContext):
    """Обработка поиска упражнений для блока"""
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

async def browse_categories_for_block(callback: CallbackQuery):
    """Просмотр категорий для блока"""
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

async def show_block_category_exercises(callback: CallbackQuery, state: FSMContext):
    """Показ упражнений категории для блока"""
    category = callback.data[10:]  # Убираем "block_cat_"
    
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

async def back_to_block_exercises(callback: CallbackQuery, state: FSMContext):
    """Возврат к упражнениям блока"""
    await show_block_exercises_menu(callback.message, state)
    await callback.answer()

# ===== ДОБАВЛЕНИЕ УПРАЖНЕНИЯ В БЛОК =====
async def add_exercise_to_block(callback: CallbackQuery, state: FSMContext):
    """Добавление упражнения в блок"""
    
    # ИСПРАВЛЕНИЕ: Правильно извлекаем exercise_id
    print(f"🔍 DEBUG: callback.data = '{callback.data}'")
    
    parts = callback.data.split("_")
    print(f"🔍 DEBUG: split parts = {parts}")
    
    # Проверяем, что достаточно частей (add_block_ex_123 = 4 части)
    if len(parts) < 4:
        print("❌ ERROR: Недостаточно частей в callback_data")
        await callback.answer("❌ Ошибка данных упражнения")
        return
    
    try:
        # Правильно: берем 4-й элемент (индекс 3) и преобразуем в int
        exercise_id = int(parts[3])  # add_block_ex_123 -> parts[3] = '123'
        print(f"🔍 DEBUG: exercise_id = {exercise_id}")
    except ValueError as e:
        print(f"❌ ERROR: Не удается преобразовать '{parts[3]}' в int: {e}")
        await callback.answer("❌ Некорректный ID упражнения")
        return
    
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
            
            # Показываем конфигурацию упражнения
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
        else:
            await callback.message.edit_text("❌ Упражнение не найдено")
            
    except Exception as e:
        print(f"❌ ERROR: Ошибка в базе данных: {e}")
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    await callback.answer()

# функция добавить тест

async def start_1rm_test(callback: CallbackQuery, state: FSMContext):
    print(f"🟢 START_1RM_TEST ВЫЗВАН! callback.data = {callback.data}")
    """Начало теста 1ПМ"""
    exercise_id = int(callback.data.split("_")[2])  # 1rm_ex_123
    
    try:
        async with db_manager.pool.acquire() as conn:
            exercise = await conn.fetchrow(
                "SELECT name FROM exercises WHERE id = $1", exercise_id
            )
        
        if exercise:
            await state.update_data(test_exercise_id=exercise_id)
            
            text = f"🔬 **Тест 1ПМ: {exercise['name']}**\n\n"
            text += f"📋 **Инструкция:**\n"
            text += f"1. Выполните упражнение с максимальным весом\n"
            text += f"2. Запишите количество повторений\n"
            text += f"3. Введите результат\n\n"
            text += f"**Формат ввода:** вес повторения\n"
            text += f"_Например: 100 5_ (100кг на 5 повторений)"
            
            await callback.message.edit_text(text, parse_mode="Markdown")
            await state.set_state("waiting_1rm_data")
        
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    await callback.answer()


async def advanced_block_config(callback: CallbackQuery, state: FSMContext):
    """Продвинутая настройка упражнения с процентами от 1ПМ"""
    data = await state.get_data()
    exercise_name = data.get('current_exercise_name', '')
    exercise_id = data.get('current_exercise_id')
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    
    try:
        async with db_manager.pool.acquire() as conn:
            # Получаем последний результат 1ПМ для упражнения
            user_1rm = await conn.fetchrow("""
                SELECT weight FROM one_rep_max 
                WHERE user_id = $1 AND exercise_id = $2 
                ORDER BY tested_at DESC LIMIT 1
            """, user['id'], exercise_id)
            
        text = f"📊 **Настройка с процентами от 1ПМ**\n\n"
        text += f"💪 **{exercise_name}**\n\n"
        
        if user_1rm:
            current_1rm = float(user_1rm['weight'])
            text += f"🏆 **Ваш текущий 1ПМ:** {current_1rm} кг\n\n"
            text += f"📋 **Готовые варианты:**\n"
            text += f"• `4 6 8 80` - 4×6-8 с 80% ({round(current_1rm * 0.8, 1)} кг), отдых 60с\n"
            text += f"• `3 8 12 70 90` - 3×8-12 с 70% ({round(current_1rm * 0.7, 1)} кг), отдых 90с\n"
            text += f"• `5 3 5 85 120` - 5×3-5 с 85% ({round(current_1rm * 0.85, 1)} кг), отдых 2м\n\n"
            text += f"🔧 **Формат ввода:**\n"
            text += f"`подходы повт_мин повт_макс процент [отдых]`\n\n"
            text += f"📝 **Примеры:**\n"
            text += f"• `4 6 8 75 90` - 4×6-8 с 75%, отдых 90 сек\n"
            text += f"• `3 10 12 70` - 3×10-12 с 70%, отдых 60 сек (по умолчанию)"
        else:
            text += f"❌ **У вас нет результатов 1ПМ для этого упражнения**\n\n"
            text += f"**Что делать:**\n"
            text += f"1. Пройдите тест 1ПМ для этого упражнения\n"
            text += f"2. Используйте простую настройку\n\n"
            
            keyboard = InlineKeyboardBuilder()
            keyboard.button(text="🔬 Пройти тест 1ПМ", callback_data=f"1rm_ex_{exercise_id}")
            keyboard.button(text="🏋️ Простая настройка", callback_data="simple_block_config")
            keyboard.button(text="🔙 Назад", callback_data="back_to_block_exercises")
            
            await callback.message.edit_text(
                text, 
                reply_markup=keyboard.as_markup(), 
                parse_mode="Markdown"
            )
            await callback.answer()
            return
            
        await callback.message.edit_text(text, parse_mode="Markdown")
        await state.set_state("advanced_block_config")
        
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    
    await callback.answer()

async def add_exercise_to_block_data(message: Message, state: FSMContext,   
                                   sets: int, reps_min: int, reps_max: int,   
                                   one_rm_percent: int = None, rest_seconds: int = 60):
    """Добавление упражнения в блок с полными параметрами"""
    data = await state.get_data()
    block_key = data.get('current_block')
    selected_blocks = data.get('selected_blocks', {})
    current_block_data = selected_blocks.get(block_key, {'exercises': [], 'description': ''})
    
    exercise_data = {
        'id': data['current_exercise_id'],
        'name': data['current_exercise_name'],
        'sets': sets,
        'reps_min': reps_min,
        'reps_max': reps_max,
        'one_rm_percent': one_rm_percent,
        'rest_seconds': rest_seconds
    }
    
    current_block_data['exercises'].append(exercise_data)
    selected_blocks[block_key] = current_block_data
    
    await state.update_data(selected_blocks=selected_blocks)
    
    # Формируем сообщение о успешном добавлении
    text = f"✅ **Упражнение добавлено в блок!**\n\n"
    text += f"💪 **{exercise_data['name']}**\n"
    
    if reps_min == reps_max:
        text += f"📊 **{sets}×{reps_min}**"
    else:
        text += f"📊 **{sets}×{reps_min}-{reps_max}**"
    
    if one_rm_percent:
        text += f" **({one_rm_percent}% от 1ПМ)**"
    
    # Форматируем время отдыха
    if rest_seconds >= 60:
        minutes = rest_seconds // 60
        seconds = rest_seconds % 60
        if seconds == 0:
            time_str = f"{minutes} мин"
        else:
            time_str = f"{minutes}м {seconds}с"
    else:
        time_str = f"{rest_seconds} сек"
        
    text += f"\n⏱️ **Отдых: {time_str}**"
    
    await message.answer(text, parse_mode="Markdown")
    await show_block_exercises_menu(message, state)

async def add_exercise_to_block_data(message: Message, state: FSMContext, 
                                   sets: int, reps_min: int, reps_max: int, 
                                   one_rm_percent: int = None, rest_seconds: int = 60):
    """Добавление упражнения в блок с параметрами"""
    data = await state.get_data()
    block_key = data.get('current_block')
    selected_blocks = data.get('selected_blocks', {})
    current_block_data = selected_blocks.get(block_key, {'exercises': [], 'description': ''})
    
    exercise_data = {
        'id': data['current_exercise_id'],
        'name': data['current_exercise_name'],
        'sets': sets,
        'reps_min': reps_min,
        'reps_max': reps_max,
        'one_rm_percent': one_rm_percent,
        'rest_seconds': rest_seconds  # ← ДОБАВИЛИ ПАРАМЕТР
    }
    
    current_block_data['exercises'].append(exercise_data)
    selected_blocks[block_key] = current_block_data
    
    await state.update_data(selected_blocks=selected_blocks)
    
    text = f"✅ **Упражнение добавлено в блок!**\n\n"
    text += f"💪 **{exercise_data['name']}**\n"
    
    if reps_min == reps_max:
        text += f"📊 **{sets}×{reps_min}**"
    else:
        text += f"📊 **{sets}×{reps_min}-{reps_max}**"
        
    if one_rm_percent:
        text += f" **({one_rm_percent}% 1ПМ)**"
    
    text += f"\n⏱️ **Отдых: {rest_seconds} сек**"
    
    await message.answer(text, parse_mode="Markdown")
    await show_block_exercises_menu(message, state)




# ===== НАСТРОЙКА УПРАЖНЕНИЙ =====
async def simple_block_config(callback: CallbackQuery, state: FSMContext):
    """Простая настройка - запрос параметров"""
    data = await state.get_data()
    exercise_name = data.get('current_exercise_name', '')
    
    text = f"🏋️ **Простая настройка упражнения**\n\n"
    text += f"💪 **{exercise_name}**\n\n"
    text += f"**Введите параметры:**\n"
    text += f"_Формат: подходы повторения отдых_\n"
    text += f"_Например: 8 8 90_ (8 подходов по 8 раз, 90 сек отдых)\n\n"
    text += f"**Готовые варианты:**\n"
    text += f"• **3 12 60** - 3×12, отдых 60 сек\n"
    text += f"• **4 8 90** - 4×8, отдых 90 сек\n"
    text += f"• **5 5 120** - 5×5, отдых 2 мин"
    
    await callback.message.edit_text(text, parse_mode="Markdown")
    await state.set_state("simple_block_config")
    await callback.answer()
    
    # Сохраняем в блок
    block_key = data.get('current_block')
    selected_blocks = data.get('selected_blocks', {})
    current_block_data = selected_blocks.get(block_key, {'exercises': [], 'description': ''})
    current_block_data['exercises'].append(exercise_data)
    selected_blocks[block_key] = current_block_data
    
    await state.update_data(selected_blocks=selected_blocks)
    await callback.answer("✅ Упражнение добавлено!")
    await show_block_exercises_menu(callback.message, state)

async def process_simple_block_config(message: Message, state: FSMContext):
    """Обработка простой настройки: подходы повторения отдых"""
    try:
        parts = message.text.split()
        if len(parts) != 3:
            await message.answer("❌ Неправильный формат. Используйте: подходы повторения отдых\nПример: 8 8 90")
            return
        
        sets = int(parts[0])
        reps = int(parts[1])  # Одинаковые мин и макс
        rest_seconds = int(parts[2])
        
        # Валидация
        if not (1 <= sets <= 15) or not (1 <= reps <= 50) or not (30 <= rest_seconds <= 300):
            await message.answer("❌ Некорректные параметры:\n• Подходы: 1-15\n• Повторения: 1-50\n• Отдых: 30-300 сек")
            return
        
        # Сохраняем с одинаковыми мин/макс повторениями
        await add_exercise_to_block_data(message, state, sets, reps, reps, None, rest_seconds)
        
    except ValueError:
        await message.answer("❌ Ошибка формата. Пример: 8 8 90")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")




# ===== ФИНАЛЬНОЕ СОХРАНЕНИЕ ТРЕНИРОВКИ =====
async def finish_workout_creation(callback: CallbackQuery, state: FSMContext):
    """Завершение создания тренировки"""
    data = await state.get_data()
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    selected_blocks = data.get('selected_blocks', {})
    
    try:
        # Подсчитываем общее количество упражнений
        total_exercises = sum(len(block_data['exercises']) for block_data in selected_blocks.values())
        
        if total_exercises == 0:
            await callback.answer("❌ Добавьте хотя бы одно упражнение!")
            return
        
        async with db_manager.pool.acquire() as conn:
            # Создаем тренировку
            workout_id = await conn.fetchval("""
                INSERT INTO workouts (name, description, created_by)
                VALUES ($1, $2, $3)
                RETURNING id
            """, data['name'], data.get('description', ''), user['id'])
            
            # Добавляем упражнения по блокам
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
                         exercise.get('one_rm_percent'), exercise['rest_seconds'])
        
        # Создаем итоговое сообщение
        text = f"🎉 **Тренировка создана успешно!**\n\n"
        text += f"🏋️ **Название:** {data['name']}\n"
        text += f"🆔 **ID:** {workout_id}\n"
        text += f"📋 **Всего упражнений:** {total_exercises}\n\n"
        
        # Показываем структуру по блокам
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

# ===== ОТМЕНА СОЗДАНИЯ =====
async def cancel_workout_creation(callback: CallbackQuery, state: FSMContext):
    """Отмена создания тренировки"""
    await state.clear()
    await workouts_menu(callback)

# ===== ЗАГЛУШКИ =====
async def find_workout(callback: CallbackQuery):
    """Поиск готовых тренировок"""
    await callback.answer("🚧 В разработке - поиск готовых тренировок")

async def workout_stats(callback: CallbackQuery):
    """Статистика тренировок"""
    await callback.answer("🚧 В разработке - статистика тренировок")

async def view_workout_details(callback: CallbackQuery):
    """Просмотр деталей тренировки"""
    await callback.answer("🚧 В разработке - просмотр тренировки")

# ===== ОБРАБОТКА ТЕКСТОВЫХ СООБЩЕНИЙ =====
async def process_workout_text_input(message: Message, state: FSMContext):
    """Обработка текстовых вводов для тренировок"""
    current_state = await state.get_state()
    
    if current_state == CreateWorkoutStates.waiting_name:
        await process_workout_name(message, state)
    elif current_state == CreateWorkoutStates.waiting_description:
        await process_workout_description(message, state)
    elif current_state == CreateWorkoutStates.adding_block_description:
        # Обработка описания блока
        description = message.text.strip()
        await state.update_data(current_block_description=description)
        
        await message.answer(
            f"✅ **Описание блока сохранено:**\n_{description}_\n\nПереходим к добавлению упражнений...",
            parse_mode="Markdown"
        )
        await show_block_exercises_menu(message, state)
    elif current_state == "searching_exercise_for_block":
        await handle_block_exercise_search(message, state)
    elif current_state == "advanced_block_config":  # ← ДОБАВИТЬ ЭТУ СТРОКУ
        await process_advanced_block_config(message, state)  # ← И ЭТУ СТРОКУ
    elif current_state == "simple_block_config":              # ← ДОБАВИТЬ ЭТУ СТРОКУ
        await process_simple_block_config(message, state)     # ← И ЭТУ СТРОКУ

    elif current_state == "waiting_1rm_result":               # ← ДОБАВИТЬ ЭТУ СТРОКУ
        await process_1rm_test_result(message, state)
    
    else:
        await message.answer("🚧 Используйте кнопки для навигации")


# обработчик 1пм
async def process_1rm_test_result(message: Message, state: FSMContext):
    """Полная обработка результата теста 1ПМ с расчетом по трем формулам"""
    try:
        parts = message.text.split()
        if len(parts) != 2:
            await message.answer(
                "❌ **Неправильный формат**\n\n"
                "📋 **Используйте:** вес повторения\n"
                "📝 **Примеры:**\n"
                "• 100 1 - 100кг на 1 раз\n"
                "• 80 5 - 80кг на 5 раз\n"
                "• 60 8 - 60кг на 8 раз",
                parse_mode="Markdown"
            )
            return
        
        weight = float(parts[0])
        reps = int(parts[1])
        
        # Валидация данных
        if weight <= 0:
            await message.answer("❌ Вес должен быть больше 0")
            return
            
        if reps <= 0 or reps > 30:
            await message.answer("❌ Количество повторений должно быть от 1 до 30")
            return
        
        # Расчет 1ПМ по трем формулам (КАК В СТАРОМ КОДЕ)
        results = calculate_1rm(weight, reps)
        
        # Получение данных из состояния
        data = await state.get_data()
        exercise_id = data.get('test_exercise_id')
        user = await db_manager.get_user_by_telegram_id(message.from_user.id)
        
        # Получение названия упражнения (ЕСЛИ fetchrow РАБОТАЕТ)
        exercise_name = "Упражнение"  # По умолчанию
        try:
            async with db_manager.pool.acquire() as conn:
                exercise = await conn.fetchrow(
                    "SELECT name FROM exercises WHERE id = $1", exercise_id
                )
                if exercise:
                    exercise_name = exercise['name']
        except Exception as db_error:
            print(f"⚠️ Не удалось получить название упражнения: {db_error}")
        
        # Сохранение результата в БД (ЕСЛИ БД РАБОТАЕТ)
        save_success = False
        try:
            async with db_manager.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO one_rep_max (
                        user_id, exercise_id, weight, reps, test_weight,
                        formula_brzycki, formula_epley, formula_alternative, formula_average
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """, 
                    user['id'], exercise_id, results['average'], reps, weight,
                    results['brzycki'], results['epley'], results['alternative'], results['average']
                )
            save_success = True
            print(f"✅ Результат сохранен в БД: {exercise_name}, {weight}кг×{reps}")
                
        except Exception as db_error:
            print(f"⚠️ Не удалось сохранить в БД: {db_error}")
            save_success = False
        
        # Формирование подробного результата (КАК В СТАРОМ КОДЕ)
        text = f"🎉 **Тест 1ПМ завершен!**\n\n"
        text += f"💪 **{exercise_name}**\n"
        text += f"🏋️ **Ваш результат:** {weight} кг × {reps} повт.\n\n"
        
        if reps == 1:
            text += f"🎯 **Ваш 1ПМ:** {weight} кг\n"
            text += f"_(Выполнено на 1 повторение - это и есть 1ПМ)_\n\n"
        else:
            text += f"📊 **Расчетный 1ПМ по формулам:**\n"
            text += f"• **Бжицкий:** {results['brzycki']} кг\n"
            text += f"• **Эпли:** {results['epley']} кг\n"
            text += f"• **Альтернативная:** {results['alternative']} кг\n\n"
            text += f"🎯 **Средний результат:** **{results['average']} кг**\n"
            text += f"_(Этот результат используется в тренировках)_\n\n"
        
        if save_success:
            text += f"✅ **Результат сохранен в базе данных**"
        else:
            text += f"⚠️ **Результат рассчитан, но не сохранен (проблема с БД)**"
        
        # Создание кнопок (КАК В СТАРОМ КОДЕ)
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="🔬 Новый тест", callback_data=f"1rm_ex_{exercise_id}")
        keyboard.button(text="📊 История тестов", callback_data="my_1rm_results")
        keyboard.button(text="🏋️ К тренировкам", callback_data="workouts_menu") 
        keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
        keyboard.adjust(2)
        
        await message.answer(
            text, 
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )
        
        await state.clear()
        
    except ValueError:
        await message.answer(
            "❌ **Ошибка формата данных**\n\n"
            "Убедитесь, что вводите числа\n"
            "📝 **Пример:** 80 5",
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"❌ Непредвиденная ошибка в process_1rm_test_result: {e}")
        await message.answer(f"❌ Ошибка: {str(e)[:100]}")
        await state.clear()

def calculate_1rm(weight, reps):
    """Расчет 1ПМ по трем научным формулам (КАК В СТАРОМ КОДЕ)"""
    w = float(weight)
    r = int(reps)
    
    if r == 1:
        return {
            'brzycki': w,
            'epley': w,
            'alternative': w,
            'average': w
        }
    
    # Формула Бжицкого (Brzycki): 1ПМ = вес / (1.0278 - 0.0278 × повторения)
    brzycki = w / (1.0278 - 0.0278 * r)
    
    # Формула Эпли (Epley): 1ПМ = вес × (1 + повторения/30)
    epley = w * (1 + r / 30.0)
    
    # Альтернативная формула: 1ПМ = вес / (1 - 0.025 × повторения)
    alternative = w / (1 - 0.025 * r)
    
    # Средний результат (основной для использования)
    average = (brzycki + epley + alternative) / 3.0
    
    return {
        'brzycki': round(brzycki, 1),
        'epley': round(epley, 1),
        'alternative': round(alternative, 1),
        'average': round(average, 1)
    }


def calculate_1rm(weight, reps):
    """Расчет 1ПМ по трем научным формулам"""
    w = float(weight)
    r = int(reps)
    
    # Если выполнено на 1 повторение - это и есть 1ПМ
    if r == 1:
        return {
            'brzycki': w,
            'epley': w,
            'alternative': w,
            'average': w
        }
    
    # Формула Бжицкого (Brzycki): 1ПМ = вес / (1.0278 - 0.0278 × повторения)
    brzycki = w / (1.0278 - 0.0278 * r)
    
    # Формула Эпли (Epley): 1ПМ = вес × (1 + повторения/30)
    epley = w * (1 + r / 30.0)
    
    # Альтернативная формула: 1ПМ = вес / (1 - 0.025 × повторения)
    alternative = w / (1 - 0.025 * r)
    
    # Средний результат (основной для использования)
    average = (brzycki + epley + alternative) / 3.0
    
    return {
        'brzycki': round(brzycki, 1),
        'epley': round(epley, 1),
        'alternative': round(alternative, 1),
        'average': round(average, 1)
    }


# расчет 1пм

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
    alternative = w / (1 - 0.025 * r)
    
    # Средняя
    average = (brzycki + epley + alternative) / 3.0
    
    return {
        'brzycki': round(brzycki, 1),
        'epley': round(epley, 1),
        'alternative': round(alternative, 1),
        'average': round(average, 1)
    }


async def start_1rm_test(callback: CallbackQuery, state: FSMContext):
    """Начало теста 1ПМ"""
    try:
        exercise_id = int(callback.data.split("_")[2])  # 1rm_ex_123
        await state.update_data(test_exercise_id=exercise_id)
        
        text = f"🔬 **Тест 1ПМ**\n\n"
        text += f"📋 **Введите результат:**\n"
        text += f"_Формат: вес повторения_\n"
        text += f"_Например: 80 5_"
        
        await callback.message.edit_text(text, parse_mode="Markdown")
        await state.set_state("waiting_1rm_result")
        
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    
    await callback.answer()


# ===== РЕГИСТРАЦИЯ ОБРАБОТЧИКОВ =====
def register_workout_handlers(dp):
    """Регистрация обработчиков тренировок"""
    
    # Главное меню тренировок
    dp.callback_query.register(workouts_menu, F.data == "workouts_menu")
    
    # Мои тренировки
    dp.callback_query.register(my_workouts, F.data == "my_workouts")
    dp.callback_query.register(view_workout_details, F.data.startswith("view_workout_"))
    
    # Создание тренировки
    dp.callback_query.register(create_workout, F.data == "create_workout")
    dp.callback_query.register(skip_description, F.data == "skip_description")
    dp.callback_query.register(cancel_workout_creation, F.data == "cancel_workout_creation")
    
    # Блоки тренировки
    dp.callback_query.register(select_workout_block, F.data.startswith("select_block_"))
    dp.callback_query.register(add_block_description, F.data == "add_block_description")
    dp.callback_query.register(skip_block_description, F.data == "skip_block_description")
    dp.callback_query.register(skip_entire_block, F.data == "skip_entire_block")
    dp.callback_query.register(back_to_blocks, F.data == "back_to_blocks")
    dp.callback_query.register(finish_current_block, F.data == "finish_current_block")
    
    # Упражнения блоков
    dp.callback_query.register(find_exercise_for_block, F.data == "find_exercise_for_block")
    dp.callback_query.register(browse_categories_for_block, F.data == "browse_categories_for_block")
    dp.callback_query.register(show_block_category_exercises, F.data.startswith("block_cat_"))
    dp.callback_query.register(back_to_block_exercises, F.data == "back_to_block_exercises")
    dp.callback_query.register(add_exercise_to_block, F.data.startswith("add_block_ex_"))
    
    # Настройка упражнений
    dp.callback_query.register(simple_block_config, F.data == "simple_block_config")
    dp.callback_query.register(advanced_block_config, F.data == "advanced_block_config")
    
    # Завершение
    dp.callback_query.register(finish_workout_creation, F.data == "finish_workout_creation")
    
    # Заглушки
    dp.callback_query.register(find_workout, F.data == "find_workout")
    dp.callback_query.register(workout_stats, F.data == "workout_stats")


    dp.callback_query.register(start_1rm_test, F.data.startswith("1rm_ex_"))
    
    # ДОБАВЬТЕ ЭТУ ДИАГНОСТИКУ В КОНЕЦ:
    print("🔥 REGISTER_WORKOUT_HANDLERS: Регистрирую start_1rm_test")
    
    try:
        dp.callback_query.register(start_1rm_test, F.data.startswith("1rm_ex_"))
        print("✅ start_1rm_test ЗАРЕГИСТРИРОВАН УСПЕШНО")
    except Exception as e:
        print(f"❌ ОШИБКА регистрации start_1rm_test: {e}")
    
    print("🔥 REGISTER_WORKOUT_HANDLERS: КОНЕЦ. Регистрация завершена успешно.")


__all__ = [
    'register_workout_handlers',
    'process_workout_text_input'
]
