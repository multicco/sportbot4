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
                SELECT weight FROM onerepmax 
                WHERE user_id = $1 AND exercise_id = $2 
                ORDER BY tested_at DESC LIMIT 1
            """, user['id'], exercise_id)
        
        text = f"📊 **Настройка с процентами от 1ПМ**\n\n"
        text += f"💪 **{exercise_name}**\n\n"
        
        if user_1rm:
            current_1rm = float(user_1rm['weight'])
            text += f"🏆 **Ваш текущий 1ПМ:** {current_1rm} кг\n\n"
            text += f"📋 **Готовые варианты:**\n"
            text += f"• **4 6 8 80** - 4×6-8 с 80% ({round(current_1rm * 0.8, 1)} кг)\n"
            text += f"• **3 8 12 70** - 3×8-12 с 70% ({round(current_1rm * 0.7, 1)} кг)\n"
            text += f"• **5 3 5 85** - 5×3-5 с 85% ({round(current_1rm * 0.85, 1)} кг)\n\n"
            text += f"**Или введите свой вариант:**\n"
            text += f"_Формат: подходы повтор_мин повтор_макс процент_\n"
            text += f"_Например: 4 6 8 80_"
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

async def process_advanced_block_config(message: Message, state: FSMContext):
    """Обработка ввода продвинутой настройки с 1ПМ"""
    try:
        parts = message.text.split()
        if len(parts) not in [3, 4]:
            await message.answer("❌ Неправильный формат. Используйте: подходы повтор_мин повтор_макс [процент]")
            return
        
        sets = int(parts[0])
        reps_min = int(parts[1])
        reps_max = int(parts[2])
        one_rm_percent = int(parts[3]) if len(parts) == 4 else None
        
        # Валидация
        if not (1 <= sets <= 10) or not (1 <= reps_min <= 50) or not (reps_min <= reps_max <= 50):
            await message.answer("❌ Некорректные параметры: подходы 1-10, повторения 1-50")
            return
        
        if one_rm_percent and not (30 <= one_rm_percent <= 120):
            await message.answer("❌ Процент от 1ПМ должен быть от 30 до 120%")
            return
        
        # Сохраняем упражнение в блок
        await add_exercise_to_block_data(message, state, sets, reps_min, reps_max, one_rm_percent)
        
    except ValueError:
        await message.answer("❌ Ошибка формата. Пример: 4 6 8 80")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

async def add_exercise_to_block_data(message: Message, state: FSMContext, 
                                   sets: int, reps_min: int, reps_max: int, 
                                   one_rm_percent: int = None):
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
        'rest_seconds': 90
    }
    
    current_block_data['exercises'].append(exercise_data)
    selected_blocks[block_key] = current_block_data
    
    await state.update_data(selected_blocks=selected_blocks)
    
    text = f"✅ **Упражнение добавлено в блок!**\n\n"
    text += f"💪 **{exercise_data['name']}**\n"
    text += f"📊 **{sets}×{reps_min}-{reps_max}**"
    if one_rm_percent:
        text += f" **({one_rm_percent}% 1ПМ)**"
    
    await message.answer(text, parse_mode="Markdown")
    await show_block_exercises_menu(message, state)



# ===== НАСТРОЙКА УПРАЖНЕНИЙ =====
async def simple_block_config(callback: CallbackQuery, state: FSMContext):
    """Простая настройка упражнения"""
    data = await state.get_data()
    
    # Добавляем упражнение с базовыми параметрами
    exercise_data = {
        'id': data['current_exercise_id'],
        'name': data['current_exercise_name'],
        'sets': 3,
        'reps_min': 8,
        'reps_max': 12,
        'rest_seconds': 60,
        'one_rm_percent': None
    }
    
    # Сохраняем в блок
    block_key = data.get('current_block')
    selected_blocks = data.get('selected_blocks', {})
    current_block_data = selected_blocks.get(block_key, {'exercises': [], 'description': ''})
    current_block_data['exercises'].append(exercise_data)
    selected_blocks[block_key] = current_block_data
    
    await state.update_data(selected_blocks=selected_blocks)
    await callback.answer("✅ Упражнение добавлено!")
    await show_block_exercises_menu(callback.message, state)



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
    else:
        await message.answer("🚧 Используйте кнопки для навигации")

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

__all__ = [
    'register_workout_handlers',
    'process_workout_text_input'
]
