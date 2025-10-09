# ===== ИСПРАВЛЕННЫЕ КОМАНДНЫЕ ТЕСТЫ ДЛЯ ИГРОКОВ - handlers/player_tests.py =====

from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import db_manager
from utils.validators import validate_test_data
# Временно убираем несуществующие функции:
# from utils.formatters import format_test_set_for_participant, format_test_result_for_set
from states.test_set_states import JoinTestSetStates, TestExecutionStates

def register_player_test_handlers(dp):
    """Регистрация обработчиков командных тестов для игроков"""
    
    # Основные функции
    dp.callback_query.register(player_test_sets_menu, F.data == "player_test_sets")
    dp.callback_query.register(join_test_set_start, F.data == "join_test_set")
    dp.callback_query.register(my_assigned_test_sets, F.data == "my_assigned_sets")
    dp.callback_query.register(browse_public_test_sets, F.data == "browse_public_sets")
    
    # Присоединение к набору тестов
    dp.callback_query.register(confirm_join_test_set, F.data.startswith("confirm_join_"))
    dp.callback_query.register(cancel_join_test_set, F.data == "cancel_join")
    
    # Прохождение тестов
    dp.callback_query.register(view_assigned_test_set, F.data.startswith("assigned_set_"))
    dp.callback_query.register(start_test_from_set, F.data.startswith("start_set_test_"))
    dp.callback_query.register(view_my_test_results, F.data.startswith("my_results_"))

# ===== ГЛАВНОЕ МЕНЮ ДЛЯ ИГРОКОВ =====
async def player_test_sets_menu(callback: CallbackQuery):
    """Главное меню наборов тестов для игроков"""
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    
    try:
        async with db_manager.pool.acquire() as conn:
            # Статистика участника
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(DISTINCT tsp.test_set_id) as joined_sets,
                    COUNT(DISTINCT tsr.exercise_id) as completed_tests,
                    COUNT(DISTINCT ts.id) FILTER (WHERE ts.visibility = 'public') as available_public_sets
                FROM test_set_participants tsp
                RIGHT JOIN users u ON u.id = $1
                LEFT JOIN test_set_results tsr ON tsp.id = tsr.participant_id
                LEFT JOIN test_sets ts ON ts.visibility = 'public' AND ts.is_active = true
                WHERE tsp.user_id = $1 OR tsp.user_id IS NULL
            """, user['id'])
    
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="📊 Мои наборы тестов", callback_data="my_assigned_sets")
        keyboard.button(text="🔗 Присоединиться по коду", callback_data="join_test_set")
        keyboard.button(text="🌐 Публичные наборы", callback_data="browse_public_sets")
        keyboard.button(text="📈 Мои результаты", callback_data="my_all_test_results")
        keyboard.button(text="🔙 Главное меню", callback_data="main_menu")
        keyboard.adjust(2)
        
        text = f"👤 **Командные тесты - Панель участника**\n\n"
        
        joined_sets = stats['joined_sets'] or 0
        completed_tests = stats['completed_tests'] or 0
        
        if joined_sets > 0:
            text += f"📊 **Ваша статистика:**\n"
            text += f"• Участвуете в наборах: **{joined_sets}**\n"
            text += f"• Завершенных тестов: **{completed_tests}**\n\n"
            
            # Получаем актуальные наборы
            try:
                async with db_manager.pool.acquire() as conn:
                    active_sets = await conn.fetch("""
                        SELECT ts.name, COUNT(DISTINCT tse.id) as total_tests, 
                               COUNT(DISTINCT tsr.id) as completed_tests
                        FROM test_set_participants tsp
                        JOIN test_sets ts ON tsp.test_set_id = ts.id
                        LEFT JOIN test_set_exercises tse ON ts.id = tse.test_set_id
                        LEFT JOIN test_set_results tsr ON tsp.id = tsr.participant_id AND tse.exercise_id = tsr.exercise_id
                        WHERE tsp.user_id = $1 AND ts.is_active = true
                        GROUP BY ts.id, ts.name
                        LIMIT 3
                    """, user['id'])
                
                if active_sets:
                    text += f"🎯 **Активные наборы:**\n"
                    for s in active_sets:
                        progress = f"{s['completed_tests'] or 0}/{s['total_tests']}"
                        text += f"• {s['name']}: {progress} тестов\n"
                    text += "\n"
            except:
                pass  # Игнорируем ошибки статистики
        else:
            text += f"🆕 **Добро пожаловать в систему командного тестирования!**\n\n"
            text += f"📋 **Как это работает:**\n"
            text += f"• Тренер создает набор тестов\n"
            text += f"• Вы присоединяетесь по коду\n"
            text += f"• Проходите назначенные тесты\n"
            text += f"• Тренер видит ваши результаты\n\n"
        
        available_public = stats['available_public_sets'] or 0
        if available_public > 0:
            text += f"🌐 **Доступно публичных наборов:** {available_public}\n\n"
        
        text += f"**Выберите действие:**"
        
        await callback.message.edit_text(
            text,
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    
    await callback.answer()

# ===== ПРИСОЕДИНЕНИЕ К НАБОРУ ТЕСТОВ =====
async def join_test_set_start(callback: CallbackQuery, state: FSMContext):
    """Начало присоединения к набору тестов"""
    await callback.message.edit_text(
        "🔗 **Присоединение к набору тестов**\n\n"
        "Введите код доступа к набору тестов:\n"
        "_Например: `TS-AB12` или `TS-XY-98`_\n\n"
        "💡 **Где взять код:**\n"
        "• У вашего тренера\n"
        "• В групповом чате команды\n"
        "• На доске объявлений спортзала",
        parse_mode="Markdown"
    )
    await state.set_state(JoinTestSetStates.waiting_access_code)
    await callback.answer()

# ===== ЗАГЛУШКИ ДЛЯ ОСТАЛЬНЫХ ФУНКЦИЙ =====
async def confirm_join_test_set(callback: CallbackQuery, state: FSMContext):
    await callback.answer("🚧 В разработке")

async def cancel_join_test_set(callback: CallbackQuery, state: FSMContext):
    await callback.answer("🚧 В разработке")

async def my_assigned_test_sets(callback: CallbackQuery):
    await callback.answer("🚧 В разработке")

async def browse_public_test_sets(callback: CallbackQuery):
    await callback.answer("🚧 В разработке")

async def view_assigned_test_set(callback: CallbackQuery):
    await callback.answer("🚧 В разработке")

async def start_test_from_set(callback: CallbackQuery, state: FSMContext):
    await callback.answer("🚧 В разработке")

async def view_my_test_results(callback: CallbackQuery):
    await callback.answer("🚧 В разработке")

# ===== ОБРАБОТКА ТЕКСТОВЫХ СООБЩЕНИЙ =====
async def process_player_test_text_input(message: Message, state: FSMContext):
    """Обработка текстовых сообщений для игроков"""
    current_state = await state.get_state()
    
    if current_state == JoinTestSetStates.waiting_access_code:
        await message.answer("🚧 Функция присоединения в разработке")
    else:
        await message.answer("🚧 В разработке")

__all__ = [
    'register_player_test_handlers',
    'process_player_test_text_input',
    'player_test_sets_menu'
]