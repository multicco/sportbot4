
"""
handlers/teams.py - РАБОЧАЯ ВЕРСИЯ С FSM
Поддерживает создание команд через FSM состояния
"""

from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# ============== FSM СОСТОЯНИЯ ==============

class TeamStates(StatesGroup):
    waiting_team_name = State()
    waiting_team_description = State()
    waiting_player_name = State()
    waiting_student_name = State()

# ============== ПРОСТАЯ БД В ПАМЯТИ ==============

teams_db = {}  # {user_id: [{"name": "Team", "description": "Desc", "players": [], "created": datetime}]}
students_db = {}  # {user_id: [{"name": "Student", "added": datetime}]}

# ============== РОУТЕР ==============

teams_router = Router()

# ============== ГЛАВНОЕ МЕНЮ ==============

@teams_router.message(Command("teams"))
async def teams_main_command(message: Message, state: FSMContext):
    """Главная команда /teams"""
    await state.clear()  # Сброс любых FSM состояний

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🆕 Создать команду", callback_data="create_team_simple")],
        [InlineKeyboardButton(text="👥 Мои команды", callback_data="my_teams_simple")],
        [InlineKeyboardButton(text="👤 Подопечные", callback_data="my_students_simple")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="teams_stats_simple")]
    ])

    user_id = message.from_user.id
    teams_count = len(teams_db.get(user_id, []))
    students_count = len(students_db.get(user_id, []))

    await message.answer(
        f"🏆 <b>Управление командами</b>\n\n"
        f"📊 Команд: {teams_count}\n"
        f"👤 Подопечных: {students_count}\n\n"
        "Выберите действие:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    logger.info(f"User {message.from_user.id} opened teams menu")

# ============== СОЗДАНИЕ КОМАНДЫ ==============

@teams_router.callback_query(F.data == "create_team_simple")
async def create_team_simple(callback: CallbackQuery, state: FSMContext):
    """Начать создание команды"""
    await state.set_state(TeamStates.waiting_team_name)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="teams_back")]
    ])

    await callback.message.edit_text(
        "🆕 <b>Создание команды</b>\n\n"
        "📝 Введите название команды:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

    logger.info(f"User {callback.from_user.id} started team creation")

# 🔥 ЭТО КЛЮЧЕВОЙ ОБРАБОТЧИК - ЕГО НЕ ХВАТАЛО!
@teams_router.message(TeamStates.waiting_team_name)
async def process_team_name(message: Message, state: FSMContext):
    """Обработка названия команды"""
    team_name = message.text.strip()

    logger.info(f"📝 User {message.from_user.id} ввел название команды: {team_name}")

    if len(team_name) < 2:
        await message.answer("❌ Название слишком короткое. Минимум 2 символа:")
        return

    if len(team_name) > 50:
        await message.answer("❌ Название слишком длинное. Максимум 50 символов:")
        return

    await state.update_data(team_name=team_name)
    await state.set_state(TeamStates.waiting_team_description)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭️ Пропустить", callback_data="skip_description")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="teams_back")]
    ])

    await message.answer(
        f"✅ Название: <b>{team_name}</b>\n\n"
        "📋 Введите описание команды (или пропустите):",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@teams_router.message(TeamStates.waiting_team_description)
async def process_team_description(message: Message, state: FSMContext):
    """Обработка описания команды"""
    description = message.text.strip()

    logger.info(f"📝 User {message.from_user.id} ввел описание: {description}")

    if len(description) > 200:
        await message.answer("❌ Описание слишком длинное. Максимум 200 символов:")
        return

    # Создаем команду
    data = await state.get_data()
    team_name = data.get('team_name', 'Команда')

    await create_team_in_db(message.from_user.id, team_name, description, message, state)

@teams_router.callback_query(F.data == "skip_description")
async def skip_description(callback: CallbackQuery, state: FSMContext):
    """Пропустить описание"""
    data = await state.get_data()
    team_name = data.get('team_name', 'Команда')

    await create_team_in_db(callback.from_user.id, team_name, "", callback, state, is_callback=True)

async def create_team_in_db(user_id: int, name: str, description: str, update, state: FSMContext, is_callback: bool = False):
    """Создание команды в БД"""
    # Создаем команду
    if user_id not in teams_db:
        teams_db[user_id] = []

    team = {
        "name": name,
        "description": description,
        "players": [],
        "created": datetime.now()
    }

    teams_db[user_id].append(team)

    await state.clear()

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить игрока", callback_data="add_player")],
        [InlineKeyboardButton(text="👥 Посмотреть команды", callback_data="my_teams_simple")],
        [InlineKeyboardButton(text="🏆 К командам", callback_data="teams_back")]
    ])

    text = (
        f"✅ <b>Команда создана!</b>\n\n"
        f"🏆 <b>Название:</b> {name}\n"
        f"📋 <b>Описание:</b> {description or 'Нет описания'}\n"
        f"👥 <b>Игроков:</b> 0\n"
        f"📅 <b>Создана:</b> {team['created'].strftime('%d.%m.%Y %H:%M')}"
    )

    if is_callback:
        await update.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await update.answer("✅ Команда создана!")
    else:
        await update.answer(text, reply_markup=keyboard, parse_mode="HTML")

    logger.info(f"✅ User {user_id} создал команду: {name}")

# ============== МОИ КОМАНДЫ ==============

@teams_router.callback_query(F.data == "my_teams_simple")
async def my_teams_simple(callback: CallbackQuery, state: FSMContext):
    """Мои команды"""
    await state.clear()

    user_teams = teams_db.get(callback.from_user.id, [])

    if not user_teams:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🆕 Создать первую команду", callback_data="create_team_simple")],
            [InlineKeyboardButton(text="🔙 К командам", callback_data="teams_back")]
        ])

        await callback.message.edit_text(
            "👥 <b>Мои команды</b>\n\n"
            "📭 У вас пока нет созданных команд\n\n"
            "Создайте первую команду!",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    else:
        teams_text = ""
        for i, team in enumerate(user_teams, 1):
            teams_text += f"{i}. 🏆 {team['name']} ({len(team['players'])} игр.)\n"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🆕 Создать команду", callback_data="create_team_simple")],
            [InlineKeyboardButton(text="🔙 К командам", callback_data="teams_back")]
        ])

        await callback.message.edit_text(
            f"👥 <b>Мои команды ({len(user_teams)})</b>\n\n"
            f"{teams_text}",
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    await callback.answer()

# ============== ПОДОПЕЧНЫЕ (упрощенно) ==============

@teams_router.callback_query(F.data == "my_students_simple")
async def my_students_simple(callback: CallbackQuery, state: FSMContext):
    """Мои подопечные"""
    await state.clear()

    user_students = students_db.get(callback.from_user.id, [])

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить подопечного", callback_data="add_student")],
        [InlineKeyboardButton(text="🔙 К командам", callback_data="teams_back")]
    ])

    if not user_students:
        await callback.message.edit_text(
            "👤 <b>Мои подопечные</b>\n\n"
            "📭 У вас пока нет подопечных\n\n"
            "Добавьте первого подопечного для персональных тренировок!",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    else:
        students_text = ""
        for i, student in enumerate(user_students, 1):
            students_text += f"{i}. 👤 {student['name']}\n"

        await callback.message.edit_text(
            f"👤 <b>Мои подопечные ({len(user_students)})</b>\n\n"
            f"{students_text}",
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    await callback.answer()

@teams_router.callback_query(F.data == "add_student")
async def add_student(callback: CallbackQuery, state: FSMContext):
    """Добавить подопечного"""
    await state.set_state(TeamStates.waiting_student_name)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="my_students_simple")]
    ])

    await callback.message.edit_text(
        "➕ <b>Добавление подопечного</b>\n\n"
        "👤 Введите имя подопечного:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

@teams_router.message(TeamStates.waiting_student_name)
async def process_student_name(message: Message, state: FSMContext):
    """Обработка имени подопечного"""
    student_name = message.text.strip()

    logger.info(f"📝 User {message.from_user.id} добавляет подопечного: {student_name}")

    if len(student_name) < 1:
        await message.answer("❌ Имя не может быть пустым:")
        return

    if len(student_name) > 50:
        await message.answer("❌ Имя слишком длинное. Максимум 50 символов:")
        return

    # Добавляем подопечного
    if message.from_user.id not in students_db:
        students_db[message.from_user.id] = []

    student = {
        "name": student_name,
        "added": datetime.now()
    }

    students_db[message.from_user.id].append(student)

    await state.clear()

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить еще", callback_data="add_student")],
        [InlineKeyboardButton(text="👤 Посмотреть всех", callback_data="my_students_simple")],
        [InlineKeyboardButton(text="🏆 К командам", callback_data="teams_back")]
    ])

    await message.answer(
        f"✅ <b>Подопечный добавлен!</b>\n\n"
        f"👤 <b>Имя:</b> {student_name}\n"
        f"📅 <b>Добавлен:</b> {student['added'].strftime('%d.%m.%Y %H:%M')}",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    logger.info(f"✅ User {message.from_user.id} добавил подопечного: {student_name}")

# ============== СТАТИСТИКА ==============

@teams_router.callback_query(F.data == "teams_stats_simple")
async def teams_stats_simple(callback: CallbackQuery, state: FSMContext):
    """Статистика команд"""
    await state.clear()

    user_teams = teams_db.get(callback.from_user.id, [])
    user_students = students_db.get(callback.from_user.id, [])

    total_players = sum(len(team["players"]) for team in user_teams)

    await callback.message.edit_text(
        f"📊 <b>Статистика команд</b>\n\n"
        f"📈 <b>Общие показатели:</b>\n"
        f"🏆 Команд создано: {len(user_teams)}\n"
        f"👥 Всего игроков: {total_players}\n"
        f"👤 Подопечных: {len(user_students)}\n"
        f"🎯 Всего спортсменов: {total_players + len(user_students)}\n\n"
        f"💾 <i>Данные сохраняются в памяти (до перезапуска)</i>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 К командам", callback_data="teams_back")]
        ]),
        parse_mode="HTML"
    )
    await callback.answer()

# ============== НАЗАД ==============

@teams_router.callback_query(F.data == "teams_back")
async def teams_back(callback: CallbackQuery, state: FSMContext):
    """Возврат к главному меню команд"""
    await state.clear()

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🆕 Создать команду", callback_data="create_team_simple")],
        [InlineKeyboardButton(text="👥 Мои команды", callback_data="my_teams_simple")],
        [InlineKeyboardButton(text="👤 Подопечные", callback_data="my_students_simple")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="teams_stats_simple")]
    ])

    user_id = callback.from_user.id
    teams_count = len(teams_db.get(user_id, []))
    students_count = len(students_db.get(user_id, []))

    await callback.message.edit_text(
        f"🏆 <b>Управление командами</b>\n\n"
        f"📊 Команд: {teams_count}\n"
        f"👤 Подопечных: {students_count}\n\n"
        "Выберите действие:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

# ============== ЗАГЛУШКИ ДЛЯ СОВМЕСТИМОСТИ ==============

@teams_router.callback_query(F.data == "add_player")
async def add_player_placeholder(callback: CallbackQuery, state: FSMContext):
    """Заглушка добавления игрока"""
    await state.clear()

    await callback.message.edit_text(
        "➕ <b>Добавление игрока</b>\n\n"
        "🚧 Функция в разработке\n\n"
        "Пока используйте базовые функции создания команд и подопечных.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 К командам", callback_data="teams_back")]
        ]),
        parse_mode="HTML"
    )
    await callback.answer()

# ============== РЕГИСТРАЦИЯ ==============

def register_team_handlers(dp):
    """Регистрация обработчиков команд"""
    dp.include_router(teams_router)
    logger.info("✅ Team handlers registered successfully")

__all__ = ['register_team_handlers']
