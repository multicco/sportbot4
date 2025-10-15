
"""
handlers/teams.py - Полный модуль управления командами и подопечными
✅ Работает с PostgreSQL
✅ Разделены команды (много игроков) и индивидуальные подопечные  
✅ FSM состояния изолированы от init.py
✅ Полная функциональность создания, просмотра, добавления
"""

from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
import logging

# Импорт нашей БД (нужно будет создать)
try:
    from database.teams_database import TeamsDB
    from database import db_manager  # Твой существующий pool
except ImportError:
    # Если нет модуля БД - используем заглушку
    TeamsDB = None
    db_manager = None
    logging.warning("Teams database module not found - using stub")

logger = logging.getLogger(__name__)

# ============== FSM СОСТОЯНИЯ ==============

class TeamStates(StatesGroup):
    # Создание команды
    waiting_team_name = State()
    waiting_team_description = State()
    waiting_sport_type = State()

    # Добавление игрока в команду
    waiting_player_first_name = State()
    waiting_player_last_name = State()
    waiting_player_position = State()
    waiting_player_jersey = State()
    waiting_player_telegram_id = State()

    # Индивидуальный подопечный
    waiting_student_first_name = State()
    waiting_student_last_name = State()
    waiting_student_specialization = State()
    waiting_student_level = State()
    waiting_student_telegram_id = State()

# ============== РОУТЕР И БД ==============

teams_router = Router()
teams_db = None  # Будет инициализирован в register_team_handlers

"""
handlers/teams.py - Полный модуль управления командами и подопечными
✅ Работает с PostgreSQL
✅ Разделены команды (много игроков) и индивидуальные подопечные
✅ FSM состояния изолированы от init.py
"""

from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
import logging

# Импорт нашей БД (нужно будет создать)
from database.teams_database import TeamsDB
from database import db_manager  # Твой существующий pool

logger = logging.getLogger(__name__)

# ============== FSM СОСТОЯНИЯ ==============

class TeamStates(StatesGroup):
    # Создание команды
    waiting_team_name = State()
    waiting_team_description = State()
    waiting_sport_type = State()

    # Добавление игрока в команду
    waiting_player_first_name = State()
    waiting_player_last_name = State()
    waiting_player_position = State()
    waiting_player_jersey = State()
    waiting_player_telegram_id = State()

    # Индивидуальный подопечный
    waiting_student_first_name = State()
    waiting_student_last_name = State()
    waiting_student_specialization = State()
    waiting_student_level = State()
    waiting_student_telegram_id = State()

# ============== РОУТЕР И БД ==============

teams_router = Router()
teams_db = None  # Будет инициализирован в register_team_handlers

# ============== ГЛАВНОЕ МЕНЮ ==============

@teams_router.message(Command("teams"))
async def cmd_teams(message: Message, state: FSMContext):
    """Команда /teams"""
    await state.clear()

    # Регистрируем тренера в БД
    await teams_db.register_coach(
        message.from_user.id, 
        message.from_user.first_name,
        message.from_user.last_name,
        message.from_user.username
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏆 Команды", callback_data="teams_menu")],
        [InlineKeyboardButton(text="👤 Подопечные", callback_data="students_menu")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="stats_menu")]
    ])

    await message.answer(
        "🏟️ <b>Управление командами и подопечными</b>\n\n"
        "📋 <b>Команды</b> - группы игроков (футбол, баскетбол, etc)\n"
        "👤 <b>Подопечные</b> - индивидуальные тренировки\n\n"
        "Выберите раздел:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@teams_router.callback_query(F.data == "main_menu")
async def cb_main_menu(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    await state.clear()

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏆 Команды", callback_data="teams_menu")],
        [InlineKeyboardButton(text="👤 Подопечные", callback_data="students_menu")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="stats_menu")]
    ])

    await callback.message.edit_text(
        "🏟️ <b>Управление командами и подопечными</b>\n\n"
        "📋 <b>Команды</b> - группы игроков (футбол, баскетбол, etc)\n"
        "👤 <b>Подопечные</b> - индивидуальные тренировки\n\n"
        "Выберите раздел:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

# ============== МЕНЮ КОМАНД ==============

@teams_router.callback_query(F.data == "teams_menu")
async def cb_teams_menu(callback: CallbackQuery, state: FSMContext):
    """Меню команд"""
    await state.clear()

    teams = await teams_db.get_coach_teams(callback.from_user.id)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🆕 Создать команду", callback_data="create_team")],
        [InlineKeyboardButton(text="📋 Мои команды", callback_data="my_teams")],
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
    ])

    teams_text = f"У вас {len(teams)} команд(ы)" if teams else "У вас пока нет команд"

    await callback.message.edit_text(
        f"🏆 <b>Управление командами</b>\n\n"
        f"📊 {teams_text}\n\n"
        "Команды предназначены для групповых видов спорта.",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

# ============== СОЗДАНИЕ КОМАНДЫ ==============

@teams_router.callback_query(F.data == "create_team")
async def cb_create_team(callback: CallbackQuery, state: FSMContext):
    """Начать создание команды"""
    await state.set_state(TeamStates.waiting_team_name)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="teams_menu")]
    ])

    await callback.message.edit_text(
        "🆕 <b>Создание команды</b>\n\n"
        "📝 Введите название команды (2-100 символов):\n\n"
        "Примеры: <i>\"Спартак U-16\", \"Женская сборная\", \"Основа\"</i>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

@teams_router.message(TeamStates.waiting_team_name)
async def process_team_name(message: Message, state: FSMContext):
    """Обработка названия команды"""
    name = message.text.strip()

    if len(name) < 2:
        await message.answer("❌ Название слишком короткое. Минимум 2 символа:")
        return

    if len(name) > 100:
        await message.answer("❌ Название слишком длинное. Максимум 100 символов:")
        return

    await state.update_data(team_name=name)
    await state.set_state(TeamStates.waiting_team_description)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭️ Пропустить", callback_data="skip_description")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="teams_menu")]
    ])

    await message.answer(
        f"✅ Название: <b>{name}</b>\n\n"
        "📋 Введите описание команды (или пропустите):\n\n"
        "Примеры: <i>\"Юношеская команда по футболу\", \"Профессиональная женская команда\"</i>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@teams_router.message(TeamStates.waiting_team_description)
async def process_team_description(message: Message, state: FSMContext):
    """Обработка описания команды"""
    description = message.text.strip()

    if len(description) > 500:
        await message.answer("❌ Описание слишком длинное. Максимум 500 символов:")
        return

    await state.update_data(team_description=description)
    await state.set_state(TeamStates.waiting_sport_type)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚽ Футбол", callback_data="sport_football")],
        [InlineKeyboardButton(text="🏀 Баскетбол", callback_data="sport_basketball")],
        [InlineKeyboardButton(text="🏐 Волейбол", callback_data="sport_volleyball")],
        [InlineKeyboardButton(text="🏒 Хоккей", callback_data="sport_hockey")],
        [InlineKeyboardButton(text="🏃 Легкая атлетика", callback_data="sport_athletics")],
        [InlineKeyboardButton(text="🥊 Единоборства", callback_data="sport_combat")],
        [InlineKeyboardButton(text="🏊 Плавание", callback_data="sport_swimming")],
        [InlineKeyboardButton(text="💪 ОФП", callback_data="sport_general")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="teams_menu")]
    ])

    data = await state.get_data()
    await message.answer(
        f"✅ Название: <b>{data['team_name']}</b>\n"
        f"📋 Описание: {description}\n\n"
        "🏃 Выберите вид спорта:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@teams_router.callback_query(F.data.startswith("sport_"))
@teams_router.callback_query(F.data == "skip_description")
async def cb_finalize_team(callback: CallbackQuery, state: FSMContext):
    """Завершение создания команды"""
    data = await state.get_data()

    if callback.data == "skip_description":
        sport_type = "general"
        description = ""
    else:
        sport_mapping = {
            "sport_football": "футбол",
            "sport_basketball": "баскетбол", 
            "sport_volleyball": "волейбол",
            "sport_hockey": "хоккей",
            "sport_athletics": "легкая атлетика",
            "sport_combat": "единоборства",
            "sport_swimming": "плавание",
            "sport_general": "ОФП"
        }
        sport_type = sport_mapping.get(callback.data, "general")
        description = data.get('team_description', '')

    # Создаем команду в БД
    try:
        team = await teams_db.create_team(
            coach_id=callback.from_user.id,
            name=data['team_name'],
            description=description,
            sport_type=sport_type,
            max_members=50
        )

        await state.clear()

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить игрока", callback_data=f"add_player_{team.id}")],
            [InlineKeyboardButton(text="👥 Посмотреть команду", callback_data=f"view_team_{team.id}")],
            [InlineKeyboardButton(text="🏆 К командам", callback_data="teams_menu")]
        ])

        await callback.message.edit_text(
            f"✅ <b>Команда создана!</b>\n\n"
            f"🏆 <b>Название:</b> {team.name}\n"
            f"📋 <b>Описание:</b> {description or 'Нет описания'}\n"
            f"🏃 <b>Вид спорта:</b> {sport_type}\n"
            f"👥 <b>Игроков:</b> 0\n"
            f"📅 <b>Создана:</b> {team.created_at.strftime('%d.%m.%Y %H:%M')}",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer("✅ Команда создана!")

    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)
        logger.error(f"Ошибка создания команды: {e}")

# ============== МОИ КОМАНДЫ ==============

@teams_router.callback_query(F.data == "my_teams")
async def cb_my_teams(callback: CallbackQuery, state: FSMContext):
    """Список моих команд"""
    await state.clear()

    teams = await teams_db.get_coach_teams(callback.from_user.id)

    if not teams:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🆕 Создать команду", callback_data="create_team")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="teams_menu")]
        ])

        await callback.message.edit_text(
            "📭 <b>У вас пока нет команд</b>\n\n"
            "Создайте первую команду!",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()
        return

    buttons = []
    for team in teams:
        sport_emoji = {
            "футбол": "⚽", "баскетбол": "🏀", "волейбол": "🏐",
            "хоккей": "🏒", "легкая атлетика": "🏃", "единоборства": "🥊",
            "плавание": "🏊", "ОФП": "💪"
        }.get(team.sport_type, "🏆")

        buttons.append([InlineKeyboardButton(
            text=f"{sport_emoji} {team.name} ({team.players_count} игр.)",
            callback_data=f"view_team_{team.id}"
        )])

    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="teams_menu")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text(
        f"🏆 <b>Ваши команды ({len(teams)})</b>\n\n"
        "Нажмите на команду для просмотра:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

# ============== ПРОСМОТР КОМАНДЫ ==============

@teams_router.callback_query(F.data.startswith("view_team_"))
async def cb_view_team(callback: CallbackQuery, state: FSMContext):
    """Просмотр команды"""
    await state.clear()
    team_id = int(callback.data.split("_")[-1])

    team = await teams_db.get_team(team_id)
    if not team:
        await callback.answer("❌ Команда не найдена")
        return

    players = await teams_db.get_team_players(team_id)

    sport_emoji = {
        "футбол": "⚽", "баскетбол": "🏀", "волейбол": "🏐",
        "хоккей": "🏒", "легкая атлетика": "🏃", "единоборства": "🥊", 
        "плавание": "🏊", "ОФП": "💪"
    }.get(team.sport_type, "🏆")

    buttons = [
        [InlineKeyboardButton(text="👥 Игроки", callback_data=f"team_players_{team_id}")],
        [InlineKeyboardButton(text="➕ Добавить игрока", callback_data=f"add_player_{team_id}")],
        [InlineKeyboardButton(text="🔙 К командам", callback_data="my_teams")]
    ]

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    description = team.description if team.description else "<i>Нет описания</i>"

    await callback.message.edit_text(
        f"{sport_emoji} <b>{team.name}</b>\n\n"
        f"📋 {description}\n\n"
        f"🏃 <b>Вид спорта:</b> {team.sport_type}\n"
        f"👥 <b>Игроков:</b> {len(players)}/{team.max_members}\n"
        f"📅 <b>Создана:</b> {team.created_at.strftime('%d.%m.%Y')}",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

# ПРОДОЛЖЕНИЕ В СЛЕДУЮЩЕМ БЛОКЕ...

# ============== ИГРОКИ КОМАНДЫ ==============

@teams_router.callback_query(F.data.startswith("team_players_"))
async def cb_team_players(callback: CallbackQuery, state: FSMContext):
    """Список игроков команды"""
    await state.clear()
    team_id = int(callback.data.split("_")[-1])

    team = await teams_db.get_team(team_id)
    players = await teams_db.get_team_players(team_id)

    if not players:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить игрока", callback_data=f"add_player_{team_id}")],
            [InlineKeyboardButton(text="🔙 К команде", callback_data=f"view_team_{team_id}")]
        ])

        await callback.message.edit_text(
            f"👥 <b>Игроки команды \"{team.name}\"</b>\n\n"
            "📭 В команде пока нет игроков\n\n"
            "Добавьте первого игрока!",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()
        return

    players_text = ""
    for i, player in enumerate(players, 1):
        name = f"{player.first_name}"
        if player.last_name:
            name += f" {player.last_name}"

        number = f"#{player.jersey_number}" if player.jersey_number else ""
        position = f"({player.position})" if player.position else ""

        players_text += f"{i}. {number} {name} {position}\n"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить игрока", callback_data=f"add_player_{team_id}")],
        [InlineKeyboardButton(text="🔙 К команде", callback_data=f"view_team_{team_id}")]
    ])

    await callback.message.edit_text(
        f"👥 <b>Игроки команды \"{team.name}\"</b>\n\n"
        f"{players_text}\n"
        f"Всего: {len(players)} игроков",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

# ============== ДОБАВЛЕНИЕ ИГРОКА ==============

@teams_router.callback_query(F.data.startswith("add_player_"))
async def cb_add_player(callback: CallbackQuery, state: FSMContext):
    """Начать добавление игрока"""
    team_id = int(callback.data.split("_")[-1])

    team = await teams_db.get_team(team_id)
    if not team:
        await callback.answer("❌ Команда не найдена")
        return

    await state.update_data(team_id=team_id)
    await state.set_state(TeamStates.waiting_player_first_name)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data=f"view_team_{team_id}")]
    ])

    await callback.message.edit_text(
        f"➕ <b>Добавление игрока в \"{team.name}\"</b>\n\n"
        "👤 Введите имя игрока:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

@teams_router.message(TeamStates.waiting_player_first_name)
async def process_player_first_name(message: Message, state: FSMContext):
    """Обработка имени игрока"""
    first_name = message.text.strip()

    if len(first_name) < 1:
        await message.answer("❌ Имя не может быть пустым:")
        return

    if len(first_name) > 100:
        await message.answer("❌ Имя слишком длинное. Максимум 100 символов:")
        return

    await state.update_data(player_first_name=first_name)
    await state.set_state(TeamStates.waiting_player_last_name)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭️ Пропустить", callback_data="skip_last_name")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_add_player")]
    ])

    await message.answer(
        f"✅ Имя: <b>{first_name}</b>\n\n"
        "👤 Введите фамилию игрока (или пропустите):",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@teams_router.callback_query(F.data == "skip_last_name")
async def cb_skip_last_name(callback: CallbackQuery, state: FSMContext):
    """Пропустить фамилию"""
    await state.update_data(player_last_name="")
    await ask_position(callback, state)

@teams_router.message(TeamStates.waiting_player_last_name) 
async def process_player_last_name(message: Message, state: FSMContext):
    """Обработка фамилии игрока"""
    last_name = message.text.strip()

    if len(last_name) > 100:
        await message.answer("❌ Фамилия слишком длинная. Максимум 100 символов:")
        return

    await state.update_data(player_last_name=last_name)
    await state.set_state(TeamStates.waiting_player_position)

    data = await state.get_data()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭️ Пропустить", callback_data="skip_position")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_add_player")]
    ])

    await message.answer(
        f"✅ Имя: <b>{data['player_first_name']} {last_name}</b>\n\n"
        "🏃 Введите позицию игрока (или пропустите):\n\n"
        "Примеры: <i>Нападающий, Защитник, Вратарь, Центральный</i>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

async def ask_position(callback: CallbackQuery, state: FSMContext):
    """Спросить позицию"""
    await state.set_state(TeamStates.waiting_player_position)

    data = await state.get_data()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭️ Пропустить", callback_data="skip_position")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_add_player")]
    ])

    player_name = data['player_first_name']
    if data.get('player_last_name'):
        player_name += f" {data['player_last_name']}"

    await callback.message.edit_text(
        f"✅ Имя: <b>{player_name}</b>\n\n"
        "🏃 Введите позицию игрока (или пропустите):\n\n"
        "Примеры: <i>Нападающий, Защитник, Вратарь, Центральный</i>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@teams_router.callback_query(F.data == "skip_position")
async def cb_skip_position(callback: CallbackQuery, state: FSMContext):
    """Пропустить позицию"""
    await state.update_data(player_position="")
    await ask_jersey_number(callback, state)

@teams_router.message(TeamStates.waiting_player_position)
async def process_player_position(message: Message, state: FSMContext):
    """Обработка позиции игрока"""
    position = message.text.strip()

    if len(position) > 50:
        await message.answer("❌ Позиция слишком длинная. Максимум 50 символов:")
        return

    await state.update_data(player_position=position)
    await state.set_state(TeamStates.waiting_player_jersey)

    data = await state.get_data()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭️ Пропустить", callback_data="skip_jersey")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_add_player")]
    ])

    player_name = data['player_first_name']
    if data.get('player_last_name'):
        player_name += f" {data['player_last_name']}"

    await message.answer(
        f"✅ Игрок: <b>{player_name}</b>\n"
        f"🏃 Позиция: <b>{position}</b>\n\n"
        "🔢 Введите номер на майке (или пропустите):\n\n"
        "Примеры: <i>7, 10, 23</i>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

async def ask_jersey_number(callback: CallbackQuery, state: FSMContext):
    """Спросить номер майки"""
    await state.set_state(TeamStates.waiting_player_jersey)

    data = await state.get_data()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭️ Пропустить", callback_data="skip_jersey")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_add_player")]
    ])

    player_name = data['player_first_name']
    if data.get('player_last_name'):
        player_name += f" {data['player_last_name']}"

    position_text = f"🏃 Позиция: <b>{data.get('player_position', 'Не указана')}</b>\n" if data.get('player_position') else ""

    await callback.message.edit_text(
        f"✅ Игрок: <b>{player_name}</b>\n"
        f"{position_text}\n"
        "🔢 Введите номер на майке (или пропустите):\n\n"
        "Примеры: <i>7, 10, 23</i>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@teams_router.callback_query(F.data == "skip_jersey")
async def cb_skip_jersey(callback: CallbackQuery, state: FSMContext):
    """Пропустить номер"""
    await state.update_data(player_jersey_number=None)
    await finalize_player_creation(callback, state)

@teams_router.message(TeamStates.waiting_player_jersey)
async def process_player_jersey(message: Message, state: FSMContext):
    """Обработка номера майки"""
    try:
        jersey_number = int(message.text.strip())

        if jersey_number < 1 or jersey_number > 999:
            await message.answer("❌ Номер должен быть от 1 до 999:")
            return

    except ValueError:
        await message.answer("❌ Номер должен быть числом:")
        return

    await state.update_data(player_jersey_number=jersey_number)
    await finalize_player_creation_msg(message, state)

async def finalize_player_creation(callback: CallbackQuery, state: FSMContext):
    """Завершить создание игрока через callback"""
    data = await state.get_data()

    try:
        player = await teams_db.add_team_player(
            team_id=data['team_id'],
            first_name=data['player_first_name'],
            last_name=data.get('player_last_name', ''),
            position=data.get('player_position', ''),
            jersey_number=data.get('player_jersey_number')
        )

        await state.clear()

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить еще игрока", callback_data=f"add_player_{data['team_id']}")],
            [InlineKeyboardButton(text="👥 Посмотреть игроков", callback_data=f"team_players_{data['team_id']}")],
            [InlineKeyboardButton(text="🔙 К команде", callback_data=f"view_team_{data['team_id']}")]
        ])

        player_name = player.first_name
        if player.last_name:
            player_name += f" {player.last_name}"

        position_text = f"🏃 <b>Позиция:</b> {player.position}\n" if player.position else ""
        jersey_text = f"🔢 <b>Номер:</b> {player.jersey_number}\n" if player.jersey_number else ""

        await callback.message.edit_text(
            f"✅ <b>Игрок добавлен!</b>\n\n"
            f"👤 <b>Имя:</b> {player_name}\n"
            f"{position_text}"
            f"{jersey_text}"
            f"📅 <b>Добавлен:</b> {player.joined_at.strftime('%d.%m.%Y %H:%M')}",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer("✅ Игрок добавлен!")

    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)
        logger.error(f"Ошибка добавления игрока: {e}")

async def finalize_player_creation_msg(message: Message, state: FSMContext):
    """Завершить создание игрока через сообщение"""
    data = await state.get_data()

    try:
        player = await teams_db.add_team_player(
            team_id=data['team_id'],
            first_name=data['player_first_name'],
            last_name=data.get('player_last_name', ''),
            position=data.get('player_position', ''),
            jersey_number=data.get('player_jersey_number')
        )

        await state.clear()

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить еще игрока", callback_data=f"add_player_{data['team_id']}")],
            [InlineKeyboardButton(text="👥 Посмотреть игроков", callback_data=f"team_players_{data['team_id']}")],
            [InlineKeyboardButton(text="🔙 К команде", callback_data=f"view_team_{data['team_id']}")]
        ])

        player_name = player.first_name
        if player.last_name:
            player_name += f" {player.last_name}"

        position_text = f"🏃 <b>Позиция:</b> {player.position}\n" if player.position else ""
        jersey_text = f"🔢 <b>Номер:</b> {player.jersey_number}\n" if player.jersey_number else ""

        await message.answer(
            f"✅ <b>Игрок добавлен!</b>\n\n"
            f"👤 <b>Имя:</b> {player_name}\n"
            f"{position_text}"
            f"{jersey_text}"
            f"📅 <b>Добавлен:</b> {player.joined_at.strftime('%d.%m.%Y %H:%M')}",
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
        logger.error(f"Ошибка добавления игрока: {e}")

@teams_router.callback_query(F.data == "cancel_add_player")
async def cb_cancel_add_player(callback: CallbackQuery, state: FSMContext):
    """Отмена добавления игрока"""
    data = await state.get_data()
    team_id = data.get('team_id')
    await state.clear()

    if team_id:
        await callback.message.edit_text(
            "❌ Добавление игрока отменено",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 К команде", callback_data=f"view_team_{team_id}")]
            ])
        )
    else:
        await callback.message.edit_text("❌ Добавление игрока отменено")

    await callback.answer()

# ПРОДОЛЖЕНИЕ СЛЕДУЕТ...

# ============== ИНДИВИДУАЛЬНЫЕ ПОДОПЕЧНЫЕ ==============

@teams_router.callback_query(F.data == "students_menu")
async def cb_students_menu(callback: CallbackQuery, state: FSMContext):
    """Меню индивидуальных подопечных"""
    await state.clear()

    students = await teams_db.get_individual_students(callback.from_user.id)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить подопечного", callback_data="add_student")],
        [InlineKeyboardButton(text="👥 Мои подопечные", callback_data="my_students")],
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
    ])

    students_text = f"У вас {len(students)} подопечных" if students else "У вас пока нет подопечных"

    await callback.message.edit_text(
        f"👤 <b>Индивидуальные подопечные</b>\n\n"
        f"📊 {students_text}\n\n"
        "Подопечные - это спортсмены для персональных тренировок.",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

@teams_router.callback_query(F.data == "add_student")
async def cb_add_student(callback: CallbackQuery, state: FSMContext):
    """Начать добавление подопечного"""
    await state.set_state(TeamStates.waiting_student_first_name)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="students_menu")]
    ])

    await callback.message.edit_text(
        "➕ <b>Добавление подопечного</b>\n\n"
        "👤 Введите имя подопечного:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

@teams_router.message(TeamStates.waiting_student_first_name)
async def process_student_first_name(message: Message, state: FSMContext):
    """Обработка имени подопечного"""
    first_name = message.text.strip()

    if len(first_name) < 1:
        await message.answer("❌ Имя не может быть пустым:")
        return

    if len(first_name) > 100:
        await message.answer("❌ Имя слишком длинное. Максимум 100 символов:")
        return

    await state.update_data(student_first_name=first_name)
    await state.set_state(TeamStates.waiting_student_last_name)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭️ Пропустить", callback_data="skip_student_last_name")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="students_menu")]
    ])

    await message.answer(
        f"✅ Имя: <b>{first_name}</b>\n\n"
        "👤 Введите фамилию подопечного (или пропустите):",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@teams_router.callback_query(F.data == "skip_student_last_name")
async def cb_skip_student_last_name(callback: CallbackQuery, state: FSMContext):
    """Пропустить фамилию подопечного"""
    await state.update_data(student_last_name="")
    await ask_student_specialization(callback, state)

@teams_router.message(TeamStates.waiting_student_last_name)
async def process_student_last_name(message: Message, state: FSMContext):
    """Обработка фамилии подопечного"""
    last_name = message.text.strip()

    if len(last_name) > 100:
        await message.answer("❌ Фамилия слишком длинная. Максимум 100 символов:")
        return

    await state.update_data(student_last_name=last_name)
    await ask_student_specialization_msg(message, state)

async def ask_student_specialization(callback: CallbackQuery, state: FSMContext):
    """Спросить специализацию через callback"""
    await state.set_state(TeamStates.waiting_student_specialization)

    data = await state.get_data()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏃 Бег", callback_data="spec_running")],
        [InlineKeyboardButton(text="💪 Силовые", callback_data="spec_strength")],
        [InlineKeyboardButton(text="🤸 Гимнастика", callback_data="spec_gymnastics")],
        [InlineKeyboardButton(text="🏊 Плавание", callback_data="spec_swimming")],
        [InlineKeyboardButton(text="🥊 Единоборства", callback_data="spec_combat")],
        [InlineKeyboardButton(text="⚽ Футбол", callback_data="spec_football")],
        [InlineKeyboardButton(text="🏀 Баскетбол", callback_data="spec_basketball")],
        [InlineKeyboardButton(text="💪 ОФП", callback_data="spec_general")],
        [InlineKeyboardButton(text="⏭️ Пропустить", callback_data="skip_student_specialization")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="students_menu")]
    ])

    student_name = data['student_first_name']
    if data.get('student_last_name'):
        student_name += f" {data['student_last_name']}"

    await callback.message.edit_text(
        f"✅ Подопечный: <b>{student_name}</b>\n\n"
        "🎯 Выберите специализацию тренировок:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

async def ask_student_specialization_msg(message: Message, state: FSMContext):
    """Спросить специализацию через сообщение"""
    await state.set_state(TeamStates.waiting_student_specialization)

    data = await state.get_data()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏃 Бег", callback_data="spec_running")],
        [InlineKeyboardButton(text="💪 Силовые", callback_data="spec_strength")],
        [InlineKeyboardButton(text="🤸 Гимнастика", callback_data="spec_gymnastics")],
        [InlineKeyboardButton(text="🏊 Плавание", callback_data="spec_swimming")],
        [InlineKeyboardButton(text="🥊 Единоборства", callback_data="spec_combat")],
        [InlineKeyboardButton(text="⚽ Футбол", callback_data="spec_football")],
        [InlineKeyboardButton(text="🏀 Баскетбол", callback_data="spec_basketball")],
        [InlineKeyboardButton(text="💪 ОФП", callback_data="spec_general")],
        [InlineKeyboardButton(text="⏭️ Пропустить", callback_data="skip_student_specialization")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="students_menu")]
    ])

    student_name = data['student_first_name']
    if data.get('student_last_name'):
        student_name += f" {data['student_last_name']}"

    await message.answer(
        f"✅ Подопечный: <b>{student_name}</b>\n\n"
        "🎯 Выберите специализацию тренировок:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@teams_router.callback_query(F.data.startswith("spec_"))
@teams_router.callback_query(F.data == "skip_student_specialization")
async def cb_student_specialization(callback: CallbackQuery, state: FSMContext):
    """Обработка специализации подопечного"""
    if callback.data == "skip_student_specialization":
        specialization = ""
    else:
        spec_mapping = {
            "spec_running": "Бег",
            "spec_strength": "Силовые тренировки",
            "spec_gymnastics": "Гимнастика",
            "spec_swimming": "Плавание",
            "spec_combat": "Единоборства",
            "spec_football": "Футбол",
            "spec_basketball": "Баскетбол",
            "spec_general": "ОФП"
        }
        specialization = spec_mapping.get(callback.data, "")

    await state.update_data(student_specialization=specialization)

    # Спрашиваем уровень
    await state.set_state(TeamStates.waiting_student_level)

    data = await state.get_data()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 Новичок", callback_data="level_beginner")],
        [InlineKeyboardButton(text="🟡 Средний", callback_data="level_intermediate")],
        [InlineKeyboardButton(text="🔴 Продвинутый", callback_data="level_advanced")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="students_menu")]
    ])

    student_name = data['student_first_name']
    if data.get('student_last_name'):
        student_name += f" {data['student_last_name']}"

    spec_text = f"🎯 <b>Специализация:</b> {specialization}\n" if specialization else ""

    await callback.message.edit_text(
        f"✅ Подопечный: <b>{student_name}</b>\n"
        f"{spec_text}\n"
        "📊 Выберите уровень подготовки:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

@teams_router.callback_query(F.data.startswith("level_"))
async def cb_student_level(callback: CallbackQuery, state: FSMContext):
    """Обработка уровня подопечного"""
    level_mapping = {
        "level_beginner": "beginner",
        "level_intermediate": "intermediate", 
        "level_advanced": "advanced"
    }

    level = level_mapping.get(callback.data, "beginner")
    await state.update_data(student_level=level)

    # Создаем подопечного в БД
    data = await state.get_data()

    try:
        student = await teams_db.add_individual_student(
            coach_id=callback.from_user.id,
            first_name=data['student_first_name'],
            last_name=data.get('student_last_name', ''),
            specialization=data.get('student_specialization', ''),
            level=level
        )

        await state.clear()

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить еще подопечного", callback_data="add_student")],
            [InlineKeyboardButton(text="👥 Посмотреть всех подопечных", callback_data="my_students")],
            [InlineKeyboardButton(text="🔙 К подопечным", callback_data="students_menu")]
        ])

        student_name = student.first_name
        if student.last_name:
            student_name += f" {student.last_name}"

        level_emoji = {"beginner": "🟢", "intermediate": "🟡", "advanced": "🔴"}
        level_text = {"beginner": "Новичок", "intermediate": "Средний", "advanced": "Продвинутый"}

        spec_text = f"🎯 <b>Специализация:</b> {student.specialization}\n" if student.specialization else ""

        await callback.message.edit_text(
            f"✅ <b>Подопечный добавлен!</b>\n\n"
            f"👤 <b>Имя:</b> {student_name}\n"
            f"{spec_text}"
            f"📊 <b>Уровень:</b> {level_emoji[level]} {level_text[level]}\n"
            f"📅 <b>Добавлен:</b> {student.joined_at.strftime('%d.%m.%Y %H:%M')}",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer("✅ Подопечный добавлен!")

    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)
        logger.error(f"Ошибка добавления подопечного: {e}")

# ============== МОИ ПОДОПЕЧНЫЕ ==============

@teams_router.callback_query(F.data == "my_students")
async def cb_my_students(callback: CallbackQuery, state: FSMContext):
    """Список моих подопечных"""
    await state.clear()

    students = await teams_db.get_individual_students(callback.from_user.id)

    if not students:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить подопечного", callback_data="add_student")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="students_menu")]
        ])

        await callback.message.edit_text(
            "👥 <b>Мои подопечные</b>\n\n"
            "📭 У вас пока нет подопечных\n\n"
            "Добавьте первого подопечного для персональных тренировок!",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()
        return

    students_text = ""
    level_emoji = {"beginner": "🟢", "intermediate": "🟡", "advanced": "🔴"}
    spec_emoji = {
        "Бег": "🏃", "Силовые тренировки": "💪", "Гимнастика": "🤸",
        "Плавание": "🏊", "Единоборства": "🥊", "Футбол": "⚽", 
        "Баскетбол": "🏀", "ОФП": "💪"
    }

    for i, student in enumerate(students, 1):
        name = student.first_name
        if student.last_name:
            name += f" {student.last_name}"

        emoji = spec_emoji.get(student.specialization, "👤")
        level = level_emoji.get(student.level, "")

        spec = f" ({student.specialization})" if student.specialization else ""
        students_text += f"{i}. {level} {emoji} {name}{spec}\n"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить подопечного", callback_data="add_student")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="students_menu")]
    ])

    await callback.message.edit_text(
        f"👥 <b>Мои подопечные ({len(students)})</b>\n\n"
        f"{students_text}\n"
        f"🟢 Новичок • 🟡 Средний • 🔴 Продвинутый",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

# ============== СТАТИСТИКА ==============

@teams_router.callback_query(F.data == "stats_menu")
async def cb_stats_menu(callback: CallbackQuery, state: FSMContext):
    """Общая статистика"""
    await state.clear()

    stats = await teams_db.get_coach_stats(callback.from_user.id)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
    ])

    await callback.message.edit_text(
        f"📊 <b>Ваша статистика</b>\n\n"
        f"🏆 <b>Команд:</b> {stats['teams_count']}\n"
        f"👥 <b>Игроков в командах:</b> {stats['team_players_count']}\n"
        f"👤 <b>Индивидуальных подопечных:</b> {stats['individual_students_count']}\n\n"
        f"🎯 <b>Всего спортсменов:</b> {stats['total_athletes']}\n\n"
        f"Продолжайте развивать свои команды!",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

# ============== РЕГИСТРАЦИЯ ==============

def register_team_handlers(dp):
    """Регистрация обработчиков команд"""
    global teams_db

    # Инициализируем БД команд
    teams_db = TeamsDB(db_manager.pool)

    # Регистрируем роутер
    dp.include_router(teams_router)
    logger.info("✅ Teams module registered with database support")

# ============== ИНИЦИАЛИЗАЦИЯ БД ==============

async def init_teams_database():
    """Инициализация таблиц команд"""
    global teams_db
    if teams_db:
        await teams_db.init_tables()

__all__ = ['register_team_handlers', 'init_teams_database']
