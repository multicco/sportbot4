# ===== ИСПРАВЛЕННЫЙ handlers/workouts.py С РАБОЧИМИ ТРЕНИРОВКАМИ =====

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
            for i, block in enumerate(blocks, 1):
                text += f"{i}. **{block['name']}** ({block['exercises_count']} упр.)\n"
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

# ===== ЗАГЛУШКИ =====
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

async def process_workout_text_input(message: Message, state: FSMContext):
    """Обработка текстовых вводов для тренировок"""
    current_state = await state.get_state()
    
    if current_state == CreateWorkoutStates.waiting_name:
        await process_workout_name(message, state)
    elif current_state == CreateWorkoutStates.waiting_description:
        await process_workout_description(message, state)  # ← ИСПРАВЛЕНО!
    else:
        await message.answer("🚧 Используйте кнопки для навигации")

async def process_workout_description(message: Message, state: FSMContext):
    """Обработка описания тренировки"""
    description = message.text.strip()
    
    if len(description) > 500:
        await message.answer("❌ Описание слишком длинное. Максимум 500 символов.")
        return
    
    await state.update_data(description=description)
    await create_workout_constructor(message, state)  # ← ИСПРАВЛЕНО!


async def skip_workout_description(callback: CallbackQuery, state: FSMContext):
    """Пропуск описания и переход к конструктору"""
    await state.update_data(description="")
    await create_workout_constructor(callback.message, state)  # ← ИСПРАВЛЕНО!
    await callback.answer()


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

async def cancel_workout_creation(callback: CallbackQuery, state: FSMContext):
    """Отмена создания тренировки"""
    await state.clear()
    await my_workouts(callback)


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
    
    # Создание тренировки
    dp.callback_query.register(create_workout, F.data == "create_workout")
    dp.callback_query.register(skip_workout_description, F.data == "skip_workout_description")
    dp.callback_query.register(cancel_workout_creation, F.data == "cancel_workout_creation")

    
    # Заглушки
    dp.callback_query.register(find_workout, F.data == "find_workout")
    dp.callback_query.register(workout_stats, F.data == "workout_stats")
    dp.callback_query.register(edit_workout, F.data.startswith("edit_workout_"))
    dp.callback_query.register(start_workout, F.data.startswith("start_workout_"))
    dp.callback_query.register(workout_blocks, F.data.startswith("workout_blocks_"))

    dp.callback_query.register(skip_workout_description, F.data == "skip_workout_description")
    dp.callback_query.register(cancel_workout_creation, F.data == "cancel_workout_creation")
__all__ = [
    'register_workout_handlers',
    'process_workout_text_input'
]


