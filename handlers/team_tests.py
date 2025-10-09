# ===== ИСПРАВЛЕННЫЙ КОМАНДНЫЕ ТЕСТЫ ДЛЯ ТРЕНЕРОВ - handlers/team_tests.py =====

from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import db_manager
from utils.validators import validate_test_set_name, validate_test_requirement
# Временно убираем несуществующие функции:
# from utils.formatters import format_test_set_summary, format_test_set_participants
from states.test_set_states import CreateTestSetStates

def register_team_test_handlers(dp):
    """Регистрация обработчиков командной системы тестирования"""
    
    # Меню тренера
    dp.callback_query.register(coach_test_sets_menu, F.data == "coach_test_sets")
    dp.callback_query.register(my_test_sets, F.data == "my_test_sets")
    dp.callback_query.register(create_test_set_start, F.data == "create_test_set")
    dp.callback_query.register(skip_test_set_description, F.data == "skip_test_set_description")
    # Создание набора тестов
    dp.callback_query.register(cancel_test_set_creation, F.data == "cancel_test_set_creation")
    dp.callback_query.register(set_test_set_visibility, F.data.startswith("visibility_"))
    
    # Управление упражнениями в наборе
    dp.callback_query.register(add_exercise_to_test_set, F.data == "add_exercise_to_set")
    dp.callback_query.register(search_exercise_for_test_set, F.data == "search_exercise_for_set")
    dp.callback_query.register(browse_categories_for_test_set, F.data == "browse_categories_for_set")
    dp.callback_query.register(show_test_set_category_exercises, F.data.startswith("test_set_cat_"))
    dp.callback_query.register(select_exercise_for_test_set, F.data.startswith("add_to_set_"))
    
    # Настройка упражнения в наборе
    dp.callback_query.register(configure_test_exercise, F.data.startswith("config_test_"))
    dp.callback_query.register(set_exercise_required, F.data.startswith("required_"))
    dp.callback_query.register(finish_test_set_creation, F.data == "finish_test_set")
    
    # Просмотр наборов и результатов
    dp.callback_query.register(view_test_set_details, F.data.startswith("view_set_"))
    dp.callback_query.register(view_test_set_results, F.data.startswith("results_"))
    dp.callback_query.register(manage_test_set, F.data.startswith("manage_"))

# ===== МЕНЮ ТРЕНЕРА =====
async def coach_test_sets_menu(callback: CallbackQuery):
    """Главное меню наборов тестов для тренера"""
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    
    if user['role'] not in ['coach', 'admin']:
        await callback.answer("❌ Только тренеры могут управлять наборами тестов!")
        return
    
    try:
        async with db_manager.pool.acquire() as conn:
            # Статистика тренера
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_sets,
                    COUNT(*) FILTER (WHERE visibility = 'public') as public_sets,
                    COUNT(*) FILTER (WHERE is_active = true) as active_sets
                FROM test_sets 
                WHERE created_by = $1
            """, user['id'])
            
            # Общая статистика участников
            participant_stats = await conn.fetchrow("""
                SELECT 
                    COUNT(DISTINCT tsp.user_id) as total_participants,
                    COUNT(DISTINCT tsr.participant_id) as active_participants
                FROM test_sets ts
                LEFT JOIN test_set_participants tsp ON ts.id = tsp.test_set_id
                LEFT JOIN test_set_results tsr ON tsp.id = tsr.participant_id
                WHERE ts.created_by = $1
            """, user['id'])
    
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="📊 Мои наборы тестов", callback_data="my_test_sets")
        keyboard.button(text="➕ Создать набор", callback_data="create_test_set")
        keyboard.button(text="📈 Общая статистика", callback_data="coach_test_stats")
        keyboard.button(text="🔍 Публичные наборы", callback_data="public_test_sets")
        keyboard.button(text="🔙 Главное меню", callback_data="main_menu")
        keyboard.adjust(2)
        
        text = f"👨‍🏫 **Командные тесты - Тренерская панель**\n\n"
        
        total_sets = stats['total_sets'] or 0
        if total_sets > 0:
            text += f"📊 **Ваша статистика:**\n"
            text += f"• Создано наборов: **{total_sets}**\n"
            text += f"• Активных наборов: **{stats['active_sets'] or 0}**\n"
            text += f"• Публичных наборов: **{stats['public_sets'] or 0}**\n\n"
            
            text += f"👥 **Участники:**\n"
            text += f"• Всего участников: **{participant_stats['total_participants'] or 0}**\n"
            text += f"• Активно тестируются: **{participant_stats['active_participants'] or 0}**\n\n"
        else:
            text += f"🆕 **Добро пожаловать в систему командного тестирования!**\n\n"
            text += f"Создавайте наборы тестов для своих подопечных:\n"
            text += f"• 🎯 Назначайте конкретные упражнения\n"
            text += f"• 📋 Устанавливайте минимальные нормативы\n"
            text += f"• 👥 Приглашайте участников по коду\n"
            text += f"• 📊 Отслеживайте прогресс в реальном времени\n\n"
        
        text += f"**Выберите действие:**"
        
        await callback.message.edit_text(
            text,
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    
    await callback.answer()

async def my_test_sets(callback: CallbackQuery):
    """Показать наборы тестов тренера"""
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    
    try:
        async with db_manager.pool.acquire() as conn:
            test_sets = await conn.fetch("""
                SELECT 
                    ts.*,
                    COUNT(DISTINCT tse.id) as exercises_count,
                    COUNT(DISTINCT tsp.id) as participants_count,
                    COUNT(DISTINCT tsr.id) as results_count
                FROM test_sets ts
                LEFT JOIN test_set_exercises tse ON ts.id = tse.test_set_id
                LEFT JOIN test_set_participants tsp ON ts.id = tsp.test_set_id
                LEFT JOIN test_set_results tsr ON ts.id = tsr.test_set_id
                WHERE ts.created_by = $1 AND ts.is_active = true
                GROUP BY ts.id
                ORDER BY ts.created_at DESC
                LIMIT 10
            """, user['id'])
        
        if test_sets:
            text = f"📊 **Ваши наборы тестов ({len(test_sets)}):**\n\n"
            
            keyboard = InlineKeyboardBuilder()
            
            for ts in test_sets:
                status_emoji = "🔒" if ts['visibility'] == 'private' else "🌐"
                
                text += f"{status_emoji} **{ts['name']}**\n"
                text += f"🆔 Код: `{ts['access_code']}`\n"
                text += f"📋 Упражнений: {ts['exercises_count']} • 👥 Участников: {ts['participants_count']}\n"
                
                if ts['description']:
                    text += f"📝 _{ts['description'][:60]}{'...' if len(ts['description']) > 60 else ''}_\n"
                
                text += f"📅 {ts['created_at'].strftime('%d.%m.%Y')}\n\n"
                
                keyboard.button(
                    text=f"📊 {ts['name'][:25]}{'...' if len(ts['name']) > 25 else ''}", 
                    callback_data=f"view_set_{ts['id']}"
                )
            
            keyboard.button(text="➕ Создать новый", callback_data="create_test_set")
            keyboard.button(text="🔙 Назад", callback_data="coach_test_sets")
            keyboard.adjust(1)
            
        else:
            text = f"📊 **У вас пока нет наборов тестов**\n\n"
            text += f"Создайте первый набор для своих подопечных!"
            
            keyboard = InlineKeyboardBuilder()
            keyboard.button(text="➕ Создать набор", callback_data="create_test_set")
            keyboard.button(text="🔙 Назад", callback_data="coach_test_sets")
        
        await callback.message.edit_text(
            text,
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    
    await callback.answer()

# ===== СОЗДАНИЕ НАБОРА ТЕСТОВ =====
async def create_test_set_start(callback: CallbackQuery, state: FSMContext):
    """Начало создания нового набора тестов"""
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    
    if user['role'] not in ['coach', 'admin']:
        await callback.answer("❌ Только тренеры могут создавать наборы тестов!")
        return
    
    await callback.message.edit_text(
        "📊 **Создание набора тестов**\n\n"
        "🎯 **Что такое набор тестов?**\n"
        "• Список упражнений для тестирования подопечных\n"
        "• Минимальные нормативы для каждого упражнения\n"
        "• Уникальный код для присоединения участников\n"
        "• Отслеживание результатов всех участников\n\n"
        "📝 **Введите название набора тестов:**\n"
        "_Например: \"Отбор в сборную 2025\" или \"Базовая подготовка\"_",
        parse_mode="Markdown"
    )
    await state.set_state(CreateTestSetStates.waiting_name)
    await callback.answer()

async def cancel_test_set_creation(callback: CallbackQuery, state: FSMContext):
    """Отмена создания набора тестов"""
    await state.clear()
    await callback.message.edit_text(
        "❌ **Создание набора тестов отменено**",
        parse_mode="Markdown"
    )
    await callback.answer()

async def set_test_set_visibility(callback: CallbackQuery, state: FSMContext):
    """Установка видимости набора тестов"""
    visibility = callback.data.split("_")[1]  # visibility_private или visibility_public
    await state.update_data(visibility=visibility)
    
    visibility_text = {
        'private': '🔒 **Приватный** - доступ только по коду',
        'public': '🌐 **Публичный** - виден всем пользователям'
    }
    
    await callback.message.edit_text(
        f"✅ **Выбрана видимость:** {visibility_text[visibility]}\n\n"
        f"📝 **Введите описание набора тестов** (необязательно):\n"
        f"_Например: \"Комплексная оценка физической подготовки для футболистов\"_\n\n"
        f"Или нажмите кнопку чтобы пропустить:",
        parse_mode="Markdown"
    )
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="⏭️ Пропустить описание", callback_data="skip_test_set_description")
    keyboard.button(text="❌ Отменить", callback_data="cancel_test_set_creation")
    
    await callback.message.edit_reply_markup(reply_markup=keyboard.as_markup())
    await state.set_state(CreateTestSetStates.waiting_description)
    await callback.answer()

# ===== ДОБАВЛЕНИЕ УПРАЖНЕНИЙ В НАБОР =====
async def add_exercise_to_test_set(callback: CallbackQuery):
    """Добавление упражнения в набор тестов"""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔍 Поиск по названию", callback_data="search_exercise_for_set")
    keyboard.button(text="📂 По категориям", callback_data="browse_categories_for_set")
    keyboard.button(text="🔙 К созданию набора", callback_data="back_to_test_set_creation")
    keyboard.adjust(1)
    
    await callback.message.edit_text(
        "🔍 **Добавление упражнения в набор тестов**\n\n"
        "Выберите способ поиска упражнений:\n\n"
        "💡 **Любое упражнение может стать тестом!**\n"
        "Вы сможете настроить минимальные требования.",
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()

# ===== ПУСТЫЕ ОБРАБОТЧИКИ (ЗАГЛУШКИ ДЛЯ СОВМЕСТИМОСТИ) =====
async def search_exercise_for_test_set(callback: CallbackQuery, state: FSMContext):
    await callback.answer("🚧 В разработке")

async def browse_categories_for_test_set(callback: CallbackQuery):
    await callback.answer("🚧 В разработке")

async def show_test_set_category_exercises(callback: CallbackQuery, state: FSMContext):
    await callback.answer("🚧 В разработке")

async def select_exercise_for_test_set(callback: CallbackQuery, state: FSMContext):
    await callback.answer("🚧 В разработке")

async def configure_test_exercise(callback: CallbackQuery, state: FSMContext):
    await callback.answer("🚧 В разработке")

async def set_exercise_required(callback: CallbackQuery, state: FSMContext):
    await callback.answer("🚧 В разработке")

async def finish_test_set_creation(callback: CallbackQuery, state: FSMContext):
    await callback.answer("🚧 В разработке")

async def view_test_set_details(callback: CallbackQuery):
    await callback.answer("🚧 В разработке")

async def view_test_set_results(callback: CallbackQuery):
    await callback.answer("🚧 В разработке")

async def manage_test_set(callback: CallbackQuery):
    await callback.answer("🚧 В разработке")

# ===== ОБРАБОТКА ТЕКСТОВЫХ СООБЩЕНИЙ =====
async def process_test_set_name(message: Message, state: FSMContext):
    """Обработка названия набора тестов"""
    test_set_name = message.text.strip()
    validation = validate_test_set_name(test_set_name)
    
    if not validation['valid']:
        await message.answer(validation['error'])
        return
    
    await state.update_data(name=test_set_name)
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔒 Приватный (по коду)", callback_data="visibility_private")
    keyboard.button(text="🌐 Публичный (для всех)", callback_data="visibility_public")
    keyboard.button(text="❌ Отменить", callback_data="cancel_test_set_creation")
    keyboard.adjust(1)
    
    await message.answer(
        f"✅ **Название:** {test_set_name}\n\n"
        f"👁️ **Выберите видимость набора:**\n\n"
        f"🔒 **Приватный** - доступ только по уникальному коду\n"
        f"🌐 **Публичный** - виден всем пользователям в каталоге",
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )

async def process_team_test_text_input(message: Message, state: FSMContext):
    current_state = await state.get_state()
    
    if current_state == CreateTestSetStates.waiting_name:
        await process_test_set_name(message, state)
    elif current_state == CreateTestSetStates.waiting_description:
        await process_test_set_description(message, state)  # ← ДОБАВИТЬ
    else:
        await message.answer("🚧 Неизвестное состояние")



async def skip_test_set_description(callback: CallbackQuery, state: FSMContext):
    """Пропуск описания и переход к сохранению набора"""
    await state.update_data(description="")
    await save_test_set_to_database(callback.message, state)
    await callback.answer()

async def process_test_set_description(message: Message, state: FSMContext):
    """Обработка описания набора тестов"""
    description = message.text.strip()
    
    if len(description) > 1000:
        await message.answer("❌ Описание слишком длинное. Максимум 1000 символов.")
        return
    
    await state.update_data(description=description)
    await save_test_set_to_database(message, state)

async def save_test_set_to_database(message, state: FSMContext):
    """Сохранение набора тестов в базу данных"""
    data = await state.get_data()
    user = await db_manager.get_user_by_telegram_id(message.from_user.id)
    
    try:
        async with db_manager.pool.acquire() as conn:
            test_set_id = await conn.fetchval("""
                INSERT INTO test_sets (name, description, created_by, visibility)
                VALUES ($1, $2, $3, $4)
                RETURNING id
            """, data['name'], data.get('description', ''), user['id'], data['visibility'])
            
            test_set = await conn.fetchrow("""
                SELECT access_code FROM test_sets WHERE id = $1
            """, test_set_id)
        
        visibility_text = "🔒 Приватный" if data['visibility'] == 'private' else "🌐 Публичный"
        
        text = f"🎉 **Набор тестов создан успешно!**\n\n"
        text += f"📊 **Название:** {data['name']}\n"
        text += f"👁️ **Видимость:** {visibility_text}\n"
        text += f"🆔 **Код доступа:** `{test_set['access_code']}`\n\n"
        
        if data.get('description'):
            text += f"📝 **Описание:** {data['description']}\n\n"
        
        text += f"🎯 **Поделитесь кодом `{test_set['access_code']}` с участниками!**"
        
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="📊 Мои наборы", callback_data="my_test_sets")
        keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
        keyboard.adjust(1)
        
        await message.answer(text, reply_markup=keyboard.as_markup(), parse_mode="Markdown")
        await state.clear()
        
    except Exception as e:
        await message.answer(f"❌ Ошибка создания набора тестов: {e}")


__all__ = [
    'register_team_test_handlers', 
    'process_team_test_text_input',
    'coach_test_sets_menu'
]