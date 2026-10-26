# ===== ПОЛНЫЙ ОБНОВЛЕННЫЙ handlers/workouts.py =====

from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import db_manager
from states.workout_states import CreateWorkoutStates

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
                SELECT w.*, COUNT(DISTINCT wb.id) as blocks_count,
                       COUNT(DISTINCT wbe.id) as exercises_count
                FROM workouts w
                LEFT JOIN workout_blocks wb ON w.id = wb.workout_id
                LEFT JOIN workout_block_exercises wbe ON wb.id = wbe.workout_block_id
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
                text += f"📊 Блоков: {workout['blocks_count']} • Упражнений: {workout['exercises_count']}\n"
                
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

# ===== ПРОСМОТР ТРЕНИРОВКИ =====
async def view_workout_details(callback: CallbackQuery):
    """Просмотр деталей тренировки"""
    workout_id = int(callback.data.split("_")[2])  # view_workout_{id}
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    
    try:
        async with db_manager.pool.acquire() as conn:
            # Получаем тренировку
            workout = await conn.fetchrow("""
                SELECT * FROM workouts 
                WHERE id = $1 AND created_by = $2
            """, workout_id, user['id'])
            
            if not workout:
                await callback.answer("❌ Тренировка не найдена!")
                return
            
            # Получаем блоки тренировки
            blocks = await conn.fetch("""
                SELECT wb.*, COUNT(wbe.id) as exercises_count
                FROM workout_blocks wb
                LEFT JOIN workout_block_exercises wbe ON wb.id = wbe.workout_block_id
                WHERE wb.workout_id = $1
                GROUP BY wb.id
                ORDER BY wb.block_order
            """, workout_id)
        
        text = f"💪 **{workout['name']}**\n\n"
        text += f"📅 **Создано:** {workout['created_at'].strftime('%d.%m.%Y')}\n"
        
        if workout['description']:
            text += f"📝 **Описание:** {workout['description']}\n"
        
        text += f"📊 **Блоков:** {len(blocks)}\n\n"
        
        if blocks:
            text += f"🏗️ **Структура тренировки:**\n"
            block_icons = {
                'warmup': '🔥',
                'cns': '🧠',
                'main': '💪',
                'cooldown': '🧘'
            }
            for i, block in enumerate(blocks, 1):
                icon = block_icons.get(block.get('block_type', 'main'), '💪')
                text += f"{i}. {icon} **{block['name']}** ({block['exercises_count']} упр.)\n"
                if block['description']:
                    text += f"   _{block['description'][:40]}{'...' if len(block['description']) > 40 else ''}_\n"
        else:
            text += f"📭 **Блоков пока нет**\n"
            text += f"Добавьте блоки с упражнениями для создания тренировки."
        
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="🏗️ Редактировать", callback_data=f"edit_workout_{workout_id}")
        keyboard.button(text="▶️ Начать тренировку", callback_data=f"start_workout_{workout_id}")
        keyboard.button(text="📋 Детали блоков", callback_data=f"workout_blocks_{workout_id}")
        keyboard.button(text="🏋️ Мои тренировки", callback_data="my_workouts")
        keyboard.adjust(1)
        
        await callback.message.edit_text(
            text,
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    
    await callback.answer()

# ===== СОЗДАНИЕ ТРЕНИРОВКИ =====
async def create_workout(callback: CallbackQuery, state: FSMContext):
    """Начало создания новой тренировки"""
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="❌ Отменить", callback_data="workouts_menu")
    
    await callback.message.edit_text(
        "💪 **Создание новой тренировки**\n\n"
        "🎯 **Как создать эффективную тренировку:**\n"
        "• Придумайте конкретное название\n"
        "• Определите цель (сила, выносливость, похудение)\n"
        "• Разбейте на логические блоки\n"
        "• Добавьте 4-8 упражнений в каждый блок\n\n"
        "📋 **Примеры названий:**\n"
        "• 'Силовая тренировка верха'\n"
        "• 'Кардио + пресс'\n"
        "• 'Функциональная тренировка'\n\n"
        "📝 **Введите название тренировки:**",
        reply_markup=keyboard.as_markup(),
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
    keyboard.button(text="⏭️ Пропустить описание", callback_data="skip_workout_description")
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
    
    if len(description) > 500:
        await message.answer("❌ Описание слишком длинное. Максимум 500 символов.")
        return
    
    await state.update_data(description=description)
    await create_workout_constructor(message, state)

async def skip_workout_description(callback: CallbackQuery, state: FSMContext):
    """Пропуск описания и переход к конструктору"""
    await state.update_data(description="")
    await create_workout_constructor(callback.message, state)
    await callback.answer()

# ===== КОНСТРУКТОР ТРЕНИРОВКИ =====
async def create_workout_constructor(message, state: FSMContext):
    """Переход к конструктору тренировки с полной структурой"""
    data = await state.get_data()
    
    text = f"🏗️ **Конструктор тренировки**\n\n"
    text += f"💪 **Название:** {data['name']}\n"
    
    if data.get('description'):
        text += f"📝 **Описание:** {data['description']}\n"
    
    text += f"\n🎯 **Создадим полную структуру тренировки:**\n\n"
    text += f"**Этап 1:** 🔥 **Разминка** (5-10 мин)\n"
    text += f"• Общая подготовка тела к нагрузке\n\n"
    text += f"**Этап 2:** 🧠 **Подготовка нервной системы** (5-10 мин)\n"
    text += f"• Активация ЦНС перед основной работой\n\n"
    text += f"**Этап 3:** 💪 **Основная часть** (30-45 мин)\n"
    text += f"• Целевая нагрузка тренировки\n\n"
    text += f"**Этап 4:** 🧘 **Заминка** (5-10 мин)\n"
    text += f"• Восстановление после нагрузки\n\n"
    text += f"**Выберите блок для добавления:**"
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔥 Добавить разминку", callback_data="add_warmup_block")
    keyboard.button(text="🧠 Подготовка ЦНС", callback_data="add_cns_block")
    keyboard.button(text="💪 Основная часть", callback_data="add_main_block")
    keyboard.button(text="🧘 Добавить заминку", callback_data="add_cooldown_block")
    keyboard.button(text="📋 Создать пустую тренировку", callback_data="save_empty_workout")
    keyboard.button(text="❌ Отменить", callback_data="cancel_workout_creation")
    keyboard.adjust(1)
    
    await message.answer(
        text,
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )

# ===== ДОБАВЛЕНИЕ БЛОКОВ =====
async def add_warmup_block(callback: CallbackQuery, state: FSMContext):
    """Добавление блока разминки"""
    await state.update_data(current_block_type="warmup")
    
    text = f"🔥 **Создание блока разминки**\n\n"
    text += f"💡 **Разминка подготавливает тело к нагрузке:**\n"
    text += f"• Легкое кардио (5-7 минут)\n"
    text += f"• Динамическая растяжка\n"
    text += f"• Суставная гимнастика\n"
    text += f"• Активация основных мышц\n\n"
    text += f"📝 **Название блока разминки:**\n"
    text += f"_Например: 'Динамическая разминка' или 'Подготовка к тренировке'_"
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔙 К конструктору", callback_data="back_to_constructor")
    
    await callback.message.edit_text(
        text,
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    await state.set_state(CreateWorkoutStates.adding_block_description)
    await callback.answer()

async def add_cns_block(callback: CallbackQuery, state: FSMContext):
    """Добавление блока подготовки нервной системы"""
    await state.update_data(current_block_type="cns")
    
    text = f"🧠 **Создание блока подготовки ЦНС**\n\n"
    text += f"⚡ **Подготовка нервной системы критически важна:**\n\n"
    text += f"🎯 **Цели блока:**\n"
    text += f"• Активация центральной нервной системы\n"
    text += f"• Повышение нервно-мышечной координации\n"
    text += f"• Подготовка к максимальным усилиям\n"
    text += f"• Улучшение техники выполнения\n\n"
    text += f"💡 **Типичные упражнения:**\n"
    text += f"• Подводящие движения с легким весом (30-50% от рабочего)\n"
    text += f"• Взрывные движения (прыжки, броски)\n"
    text += f"• Активация стабилизаторов\n"
    text += f"• Нейромышечные паттерны\n\n"
    text += f"📝 **Название блока ЦНС:**\n"
    text += f"_Например: 'Активация ЦНС', 'Подготовка нервной системы' или 'Нейромышечная подготовка'_"
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔙 К конструктору", callback_data="back_to_constructor")
    
    await callback.message.edit_text(
        text,
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    await state.set_state(CreateWorkoutStates.adding_block_description)
    await callback.answer()

async def add_main_block(callback: CallbackQuery, state: FSMContext):
    """Добавление основного блока"""
    await state.update_data(current_block_type="main")
    
    text = f"💪 **Создание основного блока**\n\n"
    text += f"🎯 **Основная часть - ядро тренировки:**\n"
    text += f"• Силовые упражнения\n"
    text += f"• Функциональные движения\n"
    text += f"• Кардио интервалы\n"
    text += f"• Изолирующие упражнения\n\n"
    text += f"📝 **Название основного блока:**\n"
    text += f"_Например: 'Силовая часть', 'Верх тела' или 'Кардио блок'_"
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔙 К конструктору", callback_data="back_to_constructor")
    
    await callback.message.edit_text(
        text,
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    await state.set_state(CreateWorkoutStates.adding_block_description)
    await callback.answer()

async def add_cooldown_block(callback: CallbackQuery, state: FSMContext):
    """Добавление блока заминки"""
    await state.update_data(current_block_type="cooldown")
    
    text = f"🧘 **Создание блока заминки**\n\n"
    text += f"😌 **Заминка восстанавливает организм:**\n"
    text += f"• Статическая растяжка\n"
    text += f"• Дыхательные упражнения\n"
    text += f"• Легкая ходьба\n"
    text += f"• Расслабление мышц\n\n"
    text += f"📝 **Название блока заминки:**\n"
    text += f"_Например: 'Растяжка', 'Восстановление' или 'Релакс блок'_"
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔙 К конструктору", callback_data="back_to_constructor")
    
    await callback.message.edit_text(
        text,
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    await state.set_state(CreateWorkoutStates.adding_block_description)
    await callback.answer()

async def process_block_name(message: Message, state: FSMContext):
    """Обработка названия блока"""
    block_name = message.text.strip()
    data = await state.get_data()
    block_type = data.get('current_block_type')
    
    if len(block_name) < 2:
        await message.answer("❌ Название слишком короткое. Минимум 2 символа.")
        return
        
    if len(block_name) > 100:
        await message.answer("❌ Название слишком длинное. Максимум 100 символов.")
        return
    
    # Сохраняем блок в state
    blocks = data.get('workout_blocks', [])
    block_info = {
        'name': block_name,
        'type': block_type,
        'exercises': []
    }
    blocks.append(block_info)
    await state.update_data(workout_blocks=blocks)
    
    # Переходим к добавлению упражнений в блок
    type_names = {
        'warmup': '🔥 разминки',
        'cns': '🧠 подготовки ЦНС',
        'main': '💪 основного блока', 
        'cooldown': '🧘 заминки'
    }
    
    type_tips = {
        'warmup': 'легкие кардио и растягивающие упражнения',
        'cns': 'подводящие движения с легким весом, взрывные упражнения',
        'main': 'целевые упражнения с рабочими весами',
        'cooldown': 'статическая растяжка и расслабляющие упражнения'
    }
    
    text = f"✅ **Блок {type_names.get(block_type)} создан!**\n\n"
    text += f"📋 **Название:** {block_name}\n\n"
    text += f"💡 **Рекомендуется добавить:** {type_tips.get(block_type)}\n\n"
    text += f"➕ **Добавим упражнения в блок:**"
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔍 Поиск по названию", callback_data="search_exercise_for_block")
    keyboard.button(text="📂 По категориям", callback_data="browse_categories_for_block")
    keyboard.button(text="💪 По группам мышц", callback_data="browse_muscles_for_block")
    
    # Специальные рекомендации для блока ЦНС
    if block_type == 'cns':
        keyboard.button(text="⚡ Взрывные упражнения", callback_data="explosive_exercises_for_cns")
        keyboard.button(text="🎯 Подводящие движения", callback_data="preparatory_exercises_for_cns")
    
    keyboard.button(text="📋 Завершить блок", callback_data="finish_current_block")
    keyboard.button(text="🔙 К конструктору", callback_data="back_to_constructor")
    keyboard.adjust(1)
    
    await message.answer(
        text,
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    await state.set_state(CreateWorkoutStates.selecting_exercises)

# ===== НАВИГАЦИЯ =====
async def back_to_constructor(callback: CallbackQuery, state: FSMContext):
    """Возврат к конструктору тренировки"""
    await create_workout_constructor(callback.message, state)
    await callback.answer()

async def cancel_workout_creation(callback: CallbackQuery, state: FSMContext):
    """Отмена создания тренировки"""
    await state.clear()
    await my_workouts(callback)

# ===== СОХРАНЕНИЕ ПУСТОЙ ТРЕНИРОВКИ =====
async def save_empty_workout(callback: CallbackQuery, state: FSMContext):
    """Сохранение пустой тренировки"""
    data = await state.get_data()
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    
    try:
        async with db_manager.pool.acquire() as conn:
            workout_id = await conn.fetchval("""
                INSERT INTO workouts (name, description, created_by)
                VALUES ($1, $2, $3)
                RETURNING id
            """, data['name'], data.get('description', ''), user['id'])
        
        text = f"📋 **Пустая тренировка создана**\n\n"
        text += f"💪 **Название:** {data['name']}\n"
        text += f"📭 **Блоков:** 0 (можете добавить позже)\n\n"
        text += f"🎯 **Добавьте блоки и упражнения когда будете готовы!**"
        
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="🏗️ Добавить блоки", callback_data=f"edit_workout_{workout_id}")
        keyboard.button(text="💪 К тренировке", callback_data=f"view_workout_{workout_id}")
        keyboard.button(text="🏋️ Мои тренировки", callback_data="my_workouts")
        keyboard.adjust(1)
        
        await callback.message.edit_text(
            text, reply_markup=keyboard.as_markup(), parse_mode="Markdown"
        )
        await state.clear()
        
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    
    await callback.answer()

# ===== ЗАГЛУШКИ ДЛЯ УПРАЖНЕНИЙ В БЛОКАХ =====
async def search_exercise_for_block(callback: CallbackQuery):
    """Поиск упражнений для блока (заглушка)"""
    await callback.answer("🚧 В разработке - поиск упражнений для блока")

async def browse_categories_for_block(callback: CallbackQuery):
    """Категории упражнений для блока (заглушка)"""
    await callback.answer("🚧 В разработке - категории упражнений")

async def browse_muscles_for_block(callback: CallbackQuery):
    """Группы мышц для блока (заглушка)"""
    await callback.answer("🚧 В разработке - группы мышц")

async def finish_current_block(callback: CallbackQuery):
    """Завершение текущего блока (заглушка)"""
    await callback.answer("🚧 В разработке - завершение блока")

async def explosive_exercises_for_cns(callback: CallbackQuery):
    """Взрывные упражнения для подготовки ЦНС"""
    text = f"⚡ **Взрывные упражнения для активации ЦНС:**\n\n"
    text += f"🚧 **В разработке**\n\n"
    text += f"💡 **Будут доступны:**\n"
    text += f"• Прыжки на тумбу\n"
    text += f"• Медбол броски\n"
    text += f"• Взрывные отжимания\n"
    text += f"• Баллистические движения\n"
    text += f"• Плиометрические упражнения"
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔙 К добавлению упражнений", callback_data="back_to_adding_exercises")
    
    await callback.message.edit_text(
        text,
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()

async def preparatory_exercises_for_cns(callback: CallbackQuery):
    """Подводящие движения для подготовки ЦНС"""
    text = f"🎯 **Подводящие движения для активации ЦНС:**\n\n"
    text += f"🚧 **В разработке**\n\n"
    text += f"💡 **Будут доступны:**\n"
    text += f"• Жим с 30-50% от максимума\n"
    text += f"• Приседания с легким весом\n"
    text += f"• Тяги с акцентом на скорость\n"
    text += f"• Активационные движения\n"
    text += f"• Специально-подготовительные упражнения"
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔙 К добавлению упражнений", callback_data="back_to_adding_exercises")
    
    await callback.message.edit_text(
        text,
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()

async def back_to_adding_exercises(callback: CallbackQuery):
    """Возврат к добавлению упражнений в текущий блок"""
    await callback.answer("🔙 Возвращаемся к добавлению упражнений")

# ===== ОСТАЛЬНЫЕ ЗАГЛУШКИ =====
async def find_workout(callback: CallbackQuery):
    """Поиск готовых тренировок"""
    await callback.answer("🚧 В разработке - поиск готовых тренировок")

async def workout_stats(callback: CallbackQuery):
    """Статистика тренировок"""
    await callback.answer("🚧 В разработке - статистика тренировок")

async def edit_workout(callback: CallbackQuery):
    """Редактирование тренировки"""
    await callback.answer("🚧 В разработке - редактирование тренировки")

async def start_workout(callback: CallbackQuery):
    """Начало выполнения тренировки"""
    await callback.answer("🚧 В разработке - выполнение тренировки")

async def workout_blocks(callback: CallbackQuery):
    """Просмотр блоков тренировки"""
    await callback.answer("🚧 В разработке - детали блоков")

# ===== ОБРАБОТКА ТЕКСТОВЫХ СООБЩЕНИЙ =====
async def process_workout_text_input(message: Message, state: FSMContext):
    """Обработка текстовых вводов для тренировок"""
    current_state = await state.get_state()
    
    if current_state == CreateWorkoutStates.waiting_name:
        await process_workout_name(message, state)
    elif current_state == CreateWorkoutStates.waiting_description:
        await process_workout_description(message, state)
    elif current_state == CreateWorkoutStates.adding_block_description:
        await process_block_name(message, state)
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
    dp.callback_query.register(skip_workout_description, F.data == "skip_workout_description")
    dp.callback_query.register(cancel_workout_creation, F.data == "cancel_workout_creation")
    
    # Конструктор тренировки - добавление блоков
    dp.callback_query.register(add_warmup_block, F.data == "add_warmup_block")
    dp.callback_query.register(add_cns_block, F.data == "add_cns_block")
    dp.callback_query.register(add_main_block, F.data == "add_main_block")
    dp.callback_query.register(add_cooldown_block, F.data == "add_cooldown_block")
    dp.callback_query.register(back_to_constructor, F.data == "back_to_constructor")
    dp.callback_query.register(save_empty_workout, F.data == "save_empty_workout")
    
    # Добавление упражнений в блоки - заглушки
    dp.callback_query.register(search_exercise_for_block, F.data == "search_exercise_for_block")
    dp.callback_query.register(browse_categories_for_block, F.data == "browse_categories_for_block")
    dp.callback_query.register(browse_muscles_for_block, F.data == "browse_muscles_for_block")
    dp.callback_query.register(finish_current_block, F.data == "finish_current_block")
    
    # Специальные упражнения для ЦНС
    dp.callback_query.register(explosive_exercises_for_cns, F.data == "explosive_exercises_for_cns")
    dp.callback_query.register(preparatory_exercises_for_cns, F.data == "preparatory_exercises_for_cns")
    dp.callback_query.register(back_to_adding_exercises, F.data == "back_to_adding_exercises")
    
    # Остальные заглушки
    dp.callback_query.register(find_workout, F.data == "find_workout")
    dp.callback_query.register(workout_stats, F.data == "workout_stats")
    dp.callback_query.register(edit_workout, F.data.startswith("edit_workout_"))
    dp.callback_query.register(start_workout, F.data.startswith("start_workout_"))
    dp.callback_query.register(workout_blocks, F.data.startswith("workout_blocks_"))

__all__ = [
    'register_workout_handlers',
    'process_workout_text_input'
]