# ===== ОБРАБОТЧИКИ ТРЕНИРОВОК =====

from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import db_manager
from states.workout_states import CreateWorkoutStates
from keyboards.workout_keyboards import (
    get_workout_blocks_keyboard, get_block_description_keyboard,
    get_block_exercises_keyboard, get_exercise_config_keyboard,
    get_workout_creation_success_keyboard, get_workout_description_keyboard,
    get_block_categories_keyboard, get_block_exercise_list_keyboard,
    get_advanced_config_no_1rm_keyboard
)
from utils.validators import validate_workout_name, validate_exercise_config
from utils.formatters import (
    format_workout_block_info, format_exercise_list,
    format_block_summary, format_weight_recommendation
)
from handlers.one_rm import get_user_1rm_for_exercise

def register_workout_handlers(dp):
    """Регистрация обработчиков тренировок"""
    
    # Создание тренировки
    dp.callback_query.register(start_create_workout, F.data == "create_workout")
    dp.callback_query.register(cancel_workout_creation, F.data == "cancel_workout_creation")
    dp.callback_query.register(skip_description, F.data == "skip_description")
    
    # Работа с блоками
    dp.callback_query.register(select_workout_block, F.data.startswith("select_block_"))
    dp.callback_query.register(add_block_description, F.data == "add_block_description")
    dp.callback_query.register(skip_block_description, F.data == "skip_block_description")
    dp.callback_query.register(skip_entire_block, F.data == "skip_entire_block")
    dp.callback_query.register(back_to_blocks, F.data == "back_to_blocks")
    
    # Добавление упражнений в блоки
    dp.callback_query.register(find_exercise_for_block, F.data == "find_exercise_for_block")
    dp.callback_query.register(browse_categories_for_block, F.data == "browse_categories_for_block")
    dp.callback_query.register(show_block_category_exercises, F.data.startswith("block_cat_"))
    dp.callback_query.register(back_to_block_exercises, F.data == "back_to_block_exercises")
    dp.callback_query.register(add_exercise_to_block, F.data.startswith("add_block_ex_"))
    
    # Настройка упражнений
    dp.callback_query.register(simple_block_config, F.data == "simple_block_config")
    dp.callback_query.register(advanced_block_config, F.data == "advanced_block_config")
    
    # Завершение блоков и тренировок
    dp.callback_query.register(finish_current_block, F.data == "finish_current_block")
    dp.callback_query.register(finish_workout_creation, F.data == "finish_workout_creation")

# ===== СОЗДАНИЕ ТРЕНИРОВКИ =====
async def start_create_workout(callback: CallbackQuery, state: FSMContext):
    """Начало создания новой тренировки"""
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

async def cancel_workout_creation(callback: CallbackQuery, state: FSMContext):
    """Отмена создания тренировки"""
    await state.clear()
    await callback.message.edit_text(
        "❌ **Создание тренировки отменено**",
        parse_mode="Markdown"
    )
    await callback.answer()

async def skip_description(callback: CallbackQuery, state: FSMContext):
    """Пропуск описания тренировки"""
    await state.update_data(description="")
    await show_block_selection_menu(callback.message, state)
    await callback.answer()

# ===== РАБОТА С БЛОКАМИ =====
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
    
    keyboard = get_workout_blocks_keyboard(selected_blocks)
    
    try:
        await message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    except:
        await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
    
    await state.set_state(CreateWorkoutStates.selecting_blocks)

async def select_workout_block(callback: CallbackQuery, state: FSMContext):
    """Выбор блока тренировки для настройки"""
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
    
    keyboard = get_block_description_keyboard()
    
    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

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

# ===== ДОБАВЛЕНИЕ УПРАЖНЕНИЙ В БЛОКИ =====
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
        text += format_exercise_list(exercises) + "\n"
    
    text += "➕ **Добавьте упражнения в блок:**"
    
    keyboard = get_block_exercises_keyboard(bool(exercises))
    
    try:
        await message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    except:
        await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
    
    await state.set_state(CreateWorkoutStates.adding_exercises)

async def find_exercise_for_block(callback: CallbackQuery, state: FSMContext):
    """Поиск упражнения для добавления в блок"""
    await callback.message.edit_text(
        "🔍 **Поиск упражнения для блока**\n\n"
        "Введите название упражнения:\n"
        "_Например: жим, приседания, планка, растяжка_",
        parse_mode="Markdown"
    )
    await state.set_state("searching_exercise_for_block")
    await callback.answer()

async def browse_categories_for_block(callback: CallbackQuery):
    """Просмотр категорий упражнений для блока"""
    try:
        async with db_manager.pool.acquire() as conn:
            categories = await conn.fetch("SELECT DISTINCT category FROM exercises ORDER BY category")
        
        keyboard = get_block_categories_keyboard(categories)
        
        await callback.message.edit_text(
            "📂 **Выберите категорию упражнений:**",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    await callback.answer()

async def show_block_category_exercises(callback: CallbackQuery, state: FSMContext):
    """Показать упражнения категории для блока"""
    category = callback.data[10:]  # Убираем "block_cat_"
    
    try:
        async with db_manager.pool.acquire() as conn:
            exercises = await conn.fetch(
                "SELECT id, name, muscle_group FROM exercises WHERE category = $1 ORDER BY name",
                category
            )
        
        if exercises:
            text = f"📂 **{category} упражнения:**\n\n"
            keyboard = get_block_exercise_list_keyboard(exercises)
            
            await callback.message.edit_text(
                text,
                reply_markup=keyboard,
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

async def add_exercise_to_block(callback: CallbackQuery, state: FSMContext):
    """Добавление упражнения в блок"""
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
            
            keyboard = get_exercise_config_keyboard()
            
            await callback.message.edit_text(
                text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    await callback.answer()

# ===== НАСТРОЙКА УПРАЖНЕНИЙ =====
async def simple_block_config(callback: CallbackQuery, state: FSMContext):
    """Простая настройка упражнения"""
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

async def advanced_block_config(callback: CallbackQuery, state: FSMContext):
    """Продвинутая настройка упражнения с 1ПМ"""
    data = await state.get_data()
    exercise_name = data.get('current_exercise_name', 'Упражнение')
    exercise_id = data.get('current_exercise_id')
    
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    
    # Получаем 1ПМ пользователя для этого упражнения
    current_1rm = await get_user_1rm_for_exercise(user['id'], exercise_id)
    
    text = f"📊 **Настройка с 1ПМ: {exercise_name}**\n\n"
    
    if current_1rm:
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
        
        keyboard = get_advanced_config_no_1rm_keyboard(exercise_id)
        
        await callback.message.edit_text(
            text, 
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    
    await callback.answer()

# ===== ЗАВЕРШЕНИЕ СОЗДАНИЯ =====
async def finish_current_block(callback: CallbackQuery, state: FSMContext):
    """Завершение настройки текущего блока"""
    data = await state.get_data()
    block_key = data.get('current_block')
    selected_blocks = data.get('selected_blocks', {})
    
    current_block_data = selected_blocks.get(block_key, {'exercises': [], 'description': ''})
    current_block_data['description'] = data.get('current_block_description', '')
    selected_blocks[block_key] = current_block_data
    
    await state.update_data(selected_blocks=selected_blocks)
    await callback.answer("✅ Блок сохранен!")
    await show_block_selection_menu(callback.message, state)

async def finish_workout_creation(callback: CallbackQuery, state: FSMContext):
    """Завершение создания тренировки"""
    data = await state.get_data()
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    selected_blocks = data.get('selected_blocks', {})
    
    try:
        total_exercises = sum(len(block_data['exercises']) for block_data in selected_blocks.values())
        
        if total_exercises == 0:
            await callback.answer("❌ Добавьте хотя бы одно упражнение!")
            return
        
        # Сохраняем тренировку в БД
        async with db_manager.pool.acquire() as conn:
            workout_id = await conn.fetchval("""
                INSERT INTO workouts (name, description, created_by, visibility, difficulty_level, estimated_duration_minutes)
                VALUES ($1, $2, $3, 'private', 'intermediate', $4)
                RETURNING id
            """, data['name'], data.get('description', ''), user['id'], total_exercises * 8)
            
            workout_unique_id = await conn.fetchval("SELECT unique_id FROM workouts WHERE id = $1", workout_id)
            
            # Сохраняем упражнения
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
        
        # Формируем сообщение об успехе
        text = f"🎉 **Тренировка создана успешно!**\n\n"
        text += f"🏋️ **Название:** {data['name']}\n"
        text += f"🆔 **Код:** `{workout_unique_id}`\n"
        text += f"📋 **Всего упражнений:** {total_exercises}\n\n"
        
        text += format_block_summary(selected_blocks)
        
        text += f"\n💡 **Поделитесь кодом** `{workout_unique_id}` с другими!"
        
        keyboard = get_workout_creation_success_keyboard()
        
        await callback.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        await state.clear()
        
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка сохранения: {e}")
    
    await callback.answer()

# ===== ОБРАБОТКА ТЕКСТОВЫХ СООБЩЕНИЙ =====
async def process_workout_name(message: Message, state: FSMContext):
    """Обработка названия тренировки"""
    workout_name = message.text.strip()
    validation = validate_workout_name(workout_name)
    
    if not validation['valid']:
        await message.answer(validation['error'])
        return
    
    await state.update_data(name=workout_name)
    
    keyboard = get_workout_description_keyboard()
    
    await message.answer(
        f"✅ **Название:** {workout_name}\n\n"
        f"📝 Теперь введите описание тренировки:\n"
        f"_Например: \"Программа для развития силы основных групп мышц\"_\n\n"
        f"Или нажмите кнопку чтобы пропустить:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await state.set_state(CreateWorkoutStates.waiting_description)

async def process_workout_description(message: Message, state: FSMContext):
    """Обработка описания тренировки"""
    description = message.text.strip()
    await state.update_data(description=description)
    await show_block_selection_menu(message, state)

async def process_block_description(message: Message, state: FSMContext):
    """Обработка описания блока"""
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

async def handle_block_exercise_search(message: Message, state: FSMContext):
    """Обработка поиска упражнения для блока"""
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
            keyboard = get_block_exercise_list_keyboard(exercises)
            
            await message.answer(
                text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            await state.set_state(CreateWorkoutStates.adding_exercises)
        else:
            await message.answer(f"❌ Упражнения по запросу '{search_term}' не найдены")
            
    except Exception as e:
        await message.answer(f"❌ Ошибка поиска: {e}")

async def process_simple_block_config(message: Message, state: FSMContext):
    """Обработка простой конфигурации блока"""
    parts = message.text.split()
    validation = validate_exercise_config(
        parts[0] if len(parts) > 0 else "",
        parts[1] if len(parts) > 1 else "",
        parts[2] if len(parts) > 2 else ""
    )
    
    if not validation['valid']:
        await message.answer(validation['error'])
        return
    
    await add_exercise_to_block_data(message, state, 
                                   validation['sets'], 
                                   validation['reps_min'], 
                                   validation['reps_max'])

async def process_advanced_block_config(message: Message, state: FSMContext):
    """Обработка продвинутой конфигурации блока с 1ПМ"""
    parts = message.text.split()
    one_rm_percent = parts[3] if len(parts) == 4 else None
    
    validation = validate_exercise_config(
        parts[0] if len(parts) > 0 else "",
        parts[1] if len(parts) > 1 else "",
        parts[2] if len(parts) > 2 else "",
        one_rm_percent
    )
    
    if not validation['valid']:
        await message.answer(validation['error'])
        return
    
    await add_exercise_to_block_data(message, state,
                                   validation['sets'],
                                   validation['reps_min'], 
                                   validation['reps_max'],
                                   validation['one_rm_percent'])

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

# ===== ОБРАБОТКА ТЕКСТОВЫХ СОСТОЯНИЙ =====
async def process_workout_text_input(message: Message, state: FSMContext):
    """Обработка текстовых вводов для создания тренировок"""
    current_state = await state.get_state()
    
    if current_state == CreateWorkoutStates.waiting_name:
        await process_workout_name(message, state)
    
    elif current_state == CreateWorkoutStates.waiting_description:
        await process_workout_description(message, state)
    
    elif current_state == CreateWorkoutStates.adding_block_description:
        await process_block_description(message, state)
        
    elif current_state == "simple_block_config":
        await process_simple_block_config(message, state)
        
    elif current_state == "advanced_block_config":
        await process_advanced_block_config(message, state)
    
    elif current_state == "searching_exercise_for_block":
        await handle_block_exercise_search(message, state)

__all__ = ['register_workout_handlers', 'process_workout_text_input']