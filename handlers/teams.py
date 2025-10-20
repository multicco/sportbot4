import logging
from typing import Optional, List
from datetime import datetime

from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest
from aiogram.utils.keyboard import InlineKeyboardBuilder
from states.team_states import JoinTeamStates
from database.teams_database import teams_database
from states.workout_assignment_states import AssignWorkoutStates
from typing import Dict, List, Optional, Tuple


# Импортируем реализацию БД из папки database
try:
    from database.teams_database import init_teams_database, TeamsDatabase
except Exception as e:
    init_teams_database = None
    TeamsDatabase = None
    logging.getLogger(__name__).exception("Failed to import database.teams_database: %s", e)

logger = logging.getLogger(__name__)

# Роутер
teams_router = Router(name="teams")

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from states.team_states import JoinTeamStates
from database.teams_database import teams_database
import logging

# ИСПРАВЛЕНИЕ: Импортируйте оба класса состояний
from states.team_states import JoinTeamStates, AddMemberStates

logger = logging.getLogger(__name__)

# Добавить к существующему teams_router


@teams_router.message(Command("join"))
async def cmd_join_team(message: Message, state: FSMContext):
    """Команда для присоединения к команде по коду"""
    args = message.text.split(maxsplit=1)
    
    if len(args) < 2:
        await message.answer(
            "🎟️ **Присоединение к команде**\n\n"
            "Введите команду с кодом приглашения:\n"
            "`/join КОД`\n\n"
            "Например: `/join abc12345`",
            parse_mode="Markdown"
        )
        return
    
    access_code = args.strip()
    
    # Ищем команду по коду
    team = await teams_database.get_team_by_access_code(access_code)
    
    if not team:
        await message.answer(
            "❌ **Неверный код приглашения**\n\n"
            "Проверьте код и попробуйте снова.",
            parse_mode="Markdown"
        )
        return
    
    # Проверяем, не состоит ли уже в команде
    already_in = await teams_database.check_player_in_team(
        message.from_user.id, 
        team.id
    )
    
    if already_in:
        await message.answer(
            f"ℹ️ Вы уже состоите в команде **{team.name}**!\n\n"
            f"Используйте /myteam для просмотра ваших команд.",
            parse_mode="Markdown"
        )
        return
    
    # Проверяем лимит игроков
    if team.players_count >= team.max_players:
        await message.answer(
            f"❌ **Команда {team.name} заполнена**\n\n"
            f"В команде уже {team.players_count}/{team.max_players} игроков.",
            parse_mode="Markdown"
        )
        return
    
    # Сохраняем данные команды и начинаем регистрацию
    await state.update_data(
        team_id=team.id,
        team_name=team.name,
        access_code=access_code
    )
    
    await message.answer(
        f"🏆 **Присоединение к команде {team.name}**\n\n"
        f"📝 Вид спорта: {team.sport_type}\n"
        f"👥 Игроков: {team.players_count}/{team.max_players}\n\n"
        f"Для завершения регистрации ответьте на несколько вопросов.\n\n"
        f"**Введите ваше имя:**",
        parse_mode="Markdown"
    )
    
    await state.set_state(JoinTeamStates.waiting_first_name)


@teams_router.message(JoinTeamStates.waiting_first_name)
async def process_join_first_name(message: Message, state: FSMContext):
    """Обработка имени"""
    first_name = message.text.strip()
    
    if len(first_name) < 2:
        await message.answer("❌ Имя слишком короткое. Минимум 2 символа.")
        return
    
    await state.update_data(first_name=first_name)
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="⏭️ Пропустить", callback_data="skip_last_name")
    
    await message.answer(
        f"✅ Имя: **{first_name}**\n\n"
        f"**Введите вашу фамилию:**\n"
        f"(или нажмите кнопку, чтобы пропустить)",
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    
    await state.set_state(JoinTeamStates.waiting_last_name)


@teams_router.message(JoinTeamStates.waiting_last_name)
async def process_join_last_name(message: Message, state: FSMContext):
    """Обработка фамилии"""
    last_name = message.text.strip()
    await state.update_data(last_name=last_name)
    await ask_position(message, state)


@teams_router.callback_query(F.data == "skip_last_name")
async def skip_last_name(callback: CallbackQuery, state: FSMContext):
    """Пропустить фамилию"""
    await state.update_data(last_name=None)
    await ask_position(callback.message, state)
    await callback.answer()


async def ask_position(message: Message, state: FSMContext):
    """Запросить позицию игрока"""
    data = await state.get_data()
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="⏭️ Пропустить", callback_data="skip_position")
    
    await message.answer(
        f"**Укажите вашу позицию:**\n"
        f"(например: нападающий, защитник, вратарь)\n\n"
        f"Или нажмите кнопку, чтобы пропустить.",
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    
    await state.set_state(JoinTeamStates.waiting_position)


@teams_router.message(JoinTeamStates.waiting_position)
async def process_join_position(message: Message, state: FSMContext):
    """Обработка позиции"""
    position = message.text.strip()
    await state.update_data(position=position)
    await ask_jersey_number(message, state)


@teams_router.callback_query(F.data == "skip_position")
async def skip_position(callback: CallbackQuery, state: FSMContext):
    """Пропустить позицию"""
    await state.update_data(position=None)
    await ask_jersey_number(callback.message, state)
    await callback.answer()


async def ask_jersey_number(message: Message, state: FSMContext):
    """Запросить номер игрока"""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="⏭️ Пропустить", callback_data="skip_jersey")
    
    await message.answer(
        f"**Введите ваш игровой номер:**\n"
        f"(число от 0 до 99)\n\n"
        f"Или нажмите кнопку, чтобы пропустить.",
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    
    await state.set_state(JoinTeamStates.waiting_jersey_number)


@teams_router.message(JoinTeamStates.waiting_jersey_number)
async def process_join_jersey(message: Message, state: FSMContext):
    """Обработка номера"""
    try:
        jersey_number = int(message.text.strip())
        
        if jersey_number < 0 or jersey_number > 99:
            await message.answer("❌ Номер должен быть от 0 до 99")
            return
        
        await state.update_data(jersey_number=jersey_number)
        await complete_join(message, state)
        
    except ValueError:
        await message.answer("❌ Введите число от 0 до 99")


@teams_router.callback_query(F.data == "skip_jersey")
async def skip_jersey(callback: CallbackQuery, state: FSMContext):
    """Пропустить номер"""
    await state.update_data(jersey_number=None)
    await complete_join(callback.message, state)
    await callback.answer()


async def complete_join(message: Message, state: FSMContext):
    """Завершить присоединение к команде"""
    data = await state.get_data()
    
    try:
        # Добавляем игрока в команду
        player = await teams_database.add_team_player(
            team_id=data['team_id'],
            first_name=data['first_name'],
            last_name=data.get('last_name'),
            position=data.get('position'),
            jersey_number=data.get('jersey_number'),
            telegram_id=message.from_user.id
        )
        
        # Формируем текст
        full_name = data['first_name']
        if data.get('last_name'):
            full_name += f" {data['last_name']}"
        
        text = f"🎉 **Поздравляем!**\n\n"
        text += f"Вы успешно присоединились к команде **{data['team_name']}**!\n\n"
        text += f"👤 Имя: {full_name}\n"
        
        if data.get('position'):
            text += f"⚽ Позиция: {data['position']}\n"
        
        if data.get('jersey_number') is not None:
            text += f"🔢 Номер: {data['jersey_number']}\n"
        
        text += f"\n💡 Используйте /myteam для просмотра ваших команд"
        
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="🏆 Мои команды", callback_data="my_teams_as_player")
        keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
        keyboard.adjust(1)
        
        await message.answer(
            text,
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )
        
        # Отправляем уведомление тренеру
        from main import bot
        team = await teams_database.get_team_by_id(data['team_id'])
        
        try:
            await bot.send_message(
                team.coach_telegram_id,
                f"👋 **Новый игрок в команде {team.name}!**\n\n"
                f"👤 {full_name}\n"
                f"⚽ Позиция: {data.get('position', 'не указана')}\n"
                f"🔢 Номер: {data.get('jersey_number', 'не указан')}",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Failed to notify coach: {e}")
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error completing join: {e}")
        await message.answer(
            f"❌ **Ошибка при добавлении в команду**\n\n"
            f"Попробуйте еще раз позже.",
            parse_mode="Markdown"
        )
@teams_router.message(Command("myteam"))
async def cmd_my_teams(message: Message):
    """Показать команды игрока"""
    teams = await teams_database.get_player_teams(message.from_user.id)
    
    if not teams:
        await message.answer(
            "ℹ️ **Вы не состоите ни в одной команде**\n\n"
            "Чтобы присоединиться, попросите тренера отправить вам код команды,\n"
            "затем используйте команду:\n"
            "`/join КОД`",
            parse_mode="Markdown"
        )
        return
    
    text = f"🏆 **Ваши команды ({len(teams)}):**\n\n"
    
    keyboard = InlineKeyboardBuilder()
    
    for team in teams:
        text += f"**{team.name}**\n"
        text += f"📝 {team.sport_type}\n"
        text += f"👥 Игроков: {team.players_count}/{team.max_players}\n"
        text += f"🆔 Код: `{team.access_code if hasattr(team, 'access_code') else 'N/A'}`\n\n"
        
        keyboard.button(
            text=f"🏆 {team.name}",
            callback_data=f"view_team_player_{team.id}"
        )
    
    keyboard.button(text="➕ Присоединиться к команде", callback_data="join_new_team")
    keyboard.adjust(1)
    
    await message.answer(
        text,
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )


@teams_router.callback_query(F.data == "join_new_team")
async def join_new_team_button(callback: CallbackQuery):
    """Кнопка присоединения к новой команде"""
    await callback.message.answer(
        "🎟️ **Присоединение к команде**\n\n"
        "Введите команду с кодом приглашения:\n"
        "`/join КОД`\n\n"
        "Например: `/join abc12345`",
        parse_mode="Markdown"
    )
    await callback.answer()


# Глобальный экземпляр БД для модуля
teams_db: TeamsDatabase | None = None




# FSM состояния
class TeamStates(StatesGroup):
    waiting_team_name = State()
    waiting_team_description = State()
    waiting_team_sport = State()
    waiting_player_first_name = State()
    waiting_player_last_name = State()
    waiting_player_position = State()
    waiting_player_jersey = State()
    waiting_student_first_name = State()
    waiting_student_last_name = State()
    waiting_student_specialization = State()
    waiting_student_level = State()


# Вспомогательные функции
async def safe_edit_text(message: Message, text: str, reply_markup: Optional[InlineKeyboardMarkup] = None, parse_mode: str = "HTML") -> None:
    """Безопасно редактируем сообщение — игнорируем TelegramBadRequest если текст/кнопки не изменились."""
    try:
        await message.edit_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            logger.debug("safe_edit_text: message is not modified — пропускаем")
        else:
            logger.exception("safe_edit_text unexpected error: %s", e)
            raise


def build_main_menu() -> InlineKeyboardMarkup:
    """Создает главное меню с командами, подопечными и статистикой."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏆 Команды", callback_data="teams_menu")],
            [InlineKeyboardButton(text="👤 Подопечные", callback_data="students_menu")],
            [InlineKeyboardButton(text="📊 Статистика", callback_data="stats_menu")]
        ]
    )


def build_teams_menu(teams_count: int) -> InlineKeyboardMarkup:
    """Создает меню управления командами."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🆕 Создать команду", callback_data="create_team")],
            [InlineKeyboardButton(text="📋 Мои команды", callback_data="my_teams")],
            [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
        ]
    )


async def init_teams_module_async(db_manager) -> bool:
    """Инициализация модуля и таблиц БД. Вызывается из main.py."""
    global teams_db
    try:
        logger.info("🔧 Initializing teams module...")
        if init_teams_database is None:
            raise RuntimeError("database.teams_database is not available")

        if not hasattr(db_manager, 'pool') or db_manager.pool is None:
            raise RuntimeError("db_manager.pool is not initialized")

        teams_db = init_teams_database(db_manager.pool)
        await teams_db.init_tables()
        logger.info("✅ Teams module loaded and database initialized")
        return True
    except Exception as e:
        logger.exception("❌ Failed to initialize teams module: %s", e)
        raise


# Хендлеры: команды
@teams_router.message(Command("teams"))
async def cmd_teams(message: Message, state: FSMContext) -> None:
    """Обработчик команды /teams для открытия главного меню."""
    await state.clear()
    stats = await get_coach_stats(message.from_user.id)
    text = (
        f"🏟️ <b>Управление командами и подопечными</b>\n\n"
        f"🏆 Команд: {stats['teams_count']}\n"
        f"👥 Игроков в командах: {stats['team_players_count']}\n"
        f"👤 Индивидуальных подопечных: {stats['individual_students_count']}\n"
        f"🎯 Всего спортсменов: {stats['total_athletes']}\n\n"
        "Выберите раздел:"
    )
    await message.answer(text, reply_markup=build_main_menu(), parse_mode="HTML")
    logger.info("User %s opened teams main menu", message.from_user.id)


@teams_router.callback_query(F.data == "main_menu")
async def cb_main_menu(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик возврата в главное меню."""
    await state.clear()
    stats = await get_coach_stats(callback.from_user.id)
    text = (
        f"🏟️ <b>Управление командами и подопечными</b>\n\n"
        f"🏆 Команд: {stats['teams_count']}\n"
        f"👥 Игроков в командах: {stats['team_players_count']}\n"
        f"👤 Индивидуальных подопечных: {stats['individual_students_count']}\n"
        f"🎯 Всего спортсменов: {stats['total_athletes']}\n\n"
        "Выберите раздел:"
    )
    await safe_edit_text(callback.message, text, reply_markup=build_main_menu())
    await callback.answer()
    logger.info("User %s returned to main menu", callback.from_user.id)


@teams_router.callback_query(F.data == "teams_menu")
async def cb_teams_menu(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик открытия меню управления командами."""
    await state.clear()
    teams = await get_coach_teams(callback.from_user.id)
    text = (
        f"🏆 <b>Управление командами</b>\n\n"
        f"📊 У вас {len(teams)} команд(ы)\n\n"
        "Команды предназначены для групповых видов спорта."
    )
    await safe_edit_text(callback.message, text, reply_markup=build_teams_menu(len(teams)))
    await callback.answer()
    logger.info("User %s opened teams menu", callback.from_user.id)


@teams_router.callback_query(F.data == "create_team")
async def cb_create_team(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик начала создания команды."""
    await state.set_state(TeamStates.waiting_team_name)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="teams_menu")]])
    await safe_edit_text(callback.message, "🆕 <b>Создание команды</b>\n\n📝 Введите название команды (2-100 символов):", reply_markup=kb)
    await callback.answer()
    logger.info("User %s started creating a team", callback.from_user.id)


@teams_router.message(TeamStates.waiting_team_name)
async def process_team_name(message: Message, state: FSMContext) -> None:
    """Обработка ввода названия команды."""
    team_name = message.text.strip()
    logger.info("process_team_name: user=%s name=%s", message.from_user.id, team_name)

    if len(team_name) < 2:
        await message.answer("❌ Название слишком короткое. Минимум 2 символа:")
        return
    if len(team_name) > 100:
        await message.answer("❌ Название слишком длинное. Максимум 100 символов:")
        return

    await state.update_data(team_name=team_name)
    await state.set_state(TeamStates.waiting_team_description)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⏭️ Пропустить", callback_data="skip_description")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="teams_menu")]
        ]
    )
    await message.answer(f"✅ Название: <b>{team_name}</b>\n\n📋 Введите описание команды (или пропустите):", reply_markup=kb, parse_mode="HTML")


@teams_router.message(TeamStates.waiting_team_description)
async def process_team_description(message: Message, state: FSMContext) -> None:
    """Обработка ввода описания команды."""
    description = message.text.strip()
    if len(description) > 500:
        await message.answer("❌ Описание слишком длинное. Максимум 500 символов:")
        return
    await state.update_data(team_description=description)
    await ask_sport_type(message, state, is_callback=False)


@teams_router.callback_query(F.data == "skip_description")
async def cb_skip_description(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик пропуска описания команды."""
    await state.update_data(team_description="")
    await ask_sport_type(callback, state, is_callback=True)


async def ask_sport_type(update: Message | CallbackQuery, state: FSMContext, is_callback: bool = True) -> None:
    """Запрос вида спорта для команды."""
    await state.set_state(TeamStates.waiting_team_sport)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⚽ Футбол", callback_data="team_sport_football")],
            [InlineKeyboardButton(text="🏀 Баскетбол", callback_data="team_sport_basketball")],
            [InlineKeyboardButton(text="🏐 Волейбол", callback_data="team_sport_volleyball")],
            [InlineKeyboardButton(text="🏒 Хоккей", callback_data="team_sport_hockey")],
            [InlineKeyboardButton(text="🏃 Легкая атлетика", callback_data="team_sport_athletics")],
            [InlineKeyboardButton(text="🥊 Единоборства", callback_data="team_sport_combat")],
            [InlineKeyboardButton(text="🏊 Плавание", callback_data="team_sport_swimming")],
            [InlineKeyboardButton(text="💪 ОФП", callback_data="team_sport_general")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="teams_menu")]
        ]
    )
    data = await state.get_data()
    team_name = data.get('team_name', 'Команда')
    description = data.get('team_description', '')
    desc_text = f"📋 Описание: {description}\n" if description else ""
    text = f"✅ Название: <b>{team_name}</b>\n{desc_text}\n🏃 Выберите вид спорта:"

    if is_callback:
        await safe_edit_text(update.message, text, reply_markup=kb)
    else:
        await update.answer(text, reply_markup=kb, parse_mode="HTML")


@teams_router.callback_query(F.data.startswith("team_sport_"))
async def cb_finalize_team_creation(callback: CallbackQuery, state: FSMContext) -> None:
    """Завершение создания команды."""
    mapping = {
        "team_sport_football": "футбол",
        "team_sport_basketball": "баскетбол",
        "team_sport_volleyball": "волейбол",
        "team_sport_hockey": "хоккей",
        "team_sport_athletics": "легкая атлетика",
        "team_sport_combat": "единоборства",
        "team_sport_swimming": "плавание",
        "team_sport_general": "ОФП",
    }
    sport_type = mapping.get(callback.data, "ОФП")
    data = await state.get_data()

    try:
        team = await create_team(callback.from_user.id, data['team_name'], data.get('team_description', ''), sport_type)
        await state.clear()
        if team:
            text = (
                f"✅ <b>Команда создана!</b>\n\n"
                f"🏆 <b>Название:</b> {team.name}\n"
                f"📋 <b>Описание:</b> {team.description or 'Нет описания'}\n"
                f"🏃 <b>Вид спорта:</b> {team.sport_type}\n"
                f"👥 <b>Игроков:</b> {team.players_count}\n"
                f"📅 <b>Создана:</b> {team.created_at.strftime('%d.%m.%Y %H:%M')}"
            )
            kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="➕ Добавить игрока", callback_data=f"add_player_{team.id}")],
                    [InlineKeyboardButton(text="👥 Посмотреть команду", callback_data=f"view_team_{team.id}")],
                    [InlineKeyboardButton(text="🏆 К командам", callback_data="teams_menu")]
                ]
            )
            await safe_edit_text(callback.message, text, reply_markup=kb)
            await callback.answer("✅ Команда создана!")
            logger.info("Team created: id=%s coach=%s name=%s", getattr(team, 'id', None), callback.from_user.id, team.name)
        else:
            await callback.answer("❌ Ошибка создания команды", show_alert=True)
            logger.warning("Failed to create team for user %s", callback.from_user.id)
    except Exception as e:
        logger.exception("Exception while finalizing team creation: %s", e)
        await callback.answer("❌ Внутренняя ошибка", show_alert=True)


@teams_router.callback_query(F.data == "my_teams")
async def cb_my_teams(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик просмотра списка команд."""
    await state.clear()
    teams = await get_coach_teams(callback.from_user.id)

    if not teams:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🆕 Создать команду", callback_data="create_team")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="teams_menu")]
            ]
        )
        await safe_edit_text(callback.message, "📭 <b>У вас пока нет команд</b>\n\nСоздайте первую команду!", reply_markup=kb)
        await callback.answer()
        return

    buttons = [[InlineKeyboardButton(text=f"{team.name} ({team.players_count})", callback_data=f"view_team_{team.id}")] for team in teams]
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="teams_menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await safe_edit_text(callback.message, f"🏆 <b>Ваши команды ({len(teams)})</b>\n\nНажмите на команду для просмотра:", reply_markup=kb)
    await callback.answer()


@teams_router.callback_query(F.data.startswith("view_team_"))
async def cb_view_team(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик просмотра информации о команде."""
    await state.clear()
    team_id = int(callback.data.split('_')[-1])
    team = await get_team_by_id(team_id)
    if not team:
        await callback.answer("❌ Команда не найдена")
        return

    players = await get_team_players(team_id)
    text = (
        f"🏆 <b>{team.name}</b>\n\n"
        f"📋 {team.description or 'Нет описания'}\n\n"
        f"🏃 <b>Вид спорта:</b> {team.sport_type}\n"
        f"👥 <b>Игроков:</b> {len(players)}/{team.max_players}\n"
        f"📅 <b>Создана:</b> {team.created_at.strftime('%d.%m.%Y')}"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👥 Игроки", callback_data=f"team_players_{team_id}")],
            [InlineKeyboardButton(text="📋 Тренировки", callback_data=f"team_workouts_{team_id}")],  # НОВАЯ КНОПКА
            [InlineKeyboardButton(text="➕ Добавить игрока", callback_data=f"add_player_{team_id}")],
            [InlineKeyboardButton(text="🔙 К командам", callback_data="my_teams")]
        ]
    )
    await safe_edit_text(callback.message, text, reply_markup=kb)
    await callback.answer()
    text += f"🆔 **Код команды:** `{team.access_code}`\n"
    text += f"💡 Отправьте этот код игрокам для присоединения!\n\n"

@teams_router.callback_query(F.data.startswith("team_players_"))
async def cb_team_players(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик просмотра списка игроков команды."""
    await state.clear()
    team_id = int(callback.data.split('_')[-1])
    team = await get_team_by_id(team_id)
    players = await get_team_players(team_id)

    if not players:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="➕ Добавить игрока", callback_data=f"add_player_{team_id}")],
                [InlineKeyboardButton(text="🔙 К команде", callback_data=f"view_team_{team_id}")]
            ]
        )
        await safe_edit_text(callback.message, f"👥 <b>Игроки команды \"{team.name}\"</b>\n\n📭 В команде пока нет игроков\n\nДобавьте первого игрока!", reply_markup=kb)
        await callback.answer()
        return

    players_text = ""
    for i, p in enumerate(players, 1):
        full = p.first_name + (f" {p.last_name}" if getattr(p, 'last_name', None) else "")
        num = f"#{p.jersey_number}" if getattr(p, 'jersey_number', None) else ""
        pos = f"({p.position})" if getattr(p, 'position', None) else ""
        players_text += f"{i}. {num} {full} {pos}\n"

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить игрока", callback_data=f"add_player_{team_id}")],
            [InlineKeyboardButton(text="🔙 К команде", callback_data=f"view_team_{team_id}")]
        ]
    )
    await safe_edit_text(callback.message, f"👥 <b>Игроки команды \"{team.name}\"</b>\n\n{players_text}\nВсего: {len(players)} игроков", reply_markup=kb)
    await callback.answer()


# ===== ВЫБОР МЕТОДА ДОБАВЛЕНИЯ УЧАСТНИКА =====
@teams_router.callback_query(F.data.startswith("add_player_"))
async def start_add_player_flow(callback: CallbackQuery, state: FSMContext):
    """Начало процесса добавления игрока с выбором метода"""
    team_id = int(callback.data.split("_")[-1])
    team = await get_team_by_id(team_id)
    
    if not team:
        await callback.answer("❌ Команда не найдена")
        return
    
    # Сохраняем ID команды
    await state.update_data(team_id=team_id)
    await state.set_state(AddMemberStates.choosing_method)
    
    # Создаем удобное меню выбора
    keyboard = InlineKeyboardBuilder()
    keyboard.button(
        text="🆔 По Telegram ID", 
        callback_data=f"add_method_telegram_id"
    )
    keyboard.button(
        text="✍️ Ввести вручную", 
        callback_data=f"add_method_manual"
    )
    keyboard.button(
        text="📋 Пригласительная ссылка", 
        callback_data=f"generate_invite_{team_id}"
    )
    keyboard.button(
        text="❌ Отмена", 
        callback_data=f"view_team_{team_id}"
    )
    keyboard.adjust(1)
    
    await callback.message.edit_text(
        f"➕ **Добавление игрока в команду \"{team.name}\"**\n\n"
        f"Выберите способ добавления:\n\n"
        f"🆔 **По Telegram ID** - если знаете ID пользователя\n"
        f"✍️ **Ввести вручную** - имя, фамилия, позиция\n"
        f"📋 **Пригласительная ссылка** - игрок сам присоединится\n\n"
        f"💡 *Telegram ID можно узнать, попросив игрока написать боту @userinfobot*",
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()


# ===== ДОБАВЛЕНИЕ ПО TELEGRAM ID =====
@teams_router.callback_query(F.data == "add_method_telegram_id")
async def add_by_telegram_id_start(callback: CallbackQuery, state: FSMContext):
    """Начало добавления по Telegram ID"""
    data = await state.get_data()
    team_id = data.get('team_id')
    
    await state.set_state(AddMemberStates.waiting_telegram_id)
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="❌ Отмена", callback_data=f"view_team_{team_id}")
    
    await callback.message.edit_text(
        "🆔 **Добавление по Telegram ID**\n\n"
        "Введите Telegram ID игрока (только цифры):\n\n"
        "💡 *Как узнать Telegram ID:*\n"
        "1. Попросите игрока написать боту @userinfobot\n"
        "2. Бот пришлет его ID\n"
        "3. Отправьте эти цифры сюда\n\n"
        "Пример: `123456789`",
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()

@teams_router.message(TeamStates.waiting_player_first_name)
async def process_player_first_name(message: Message, state: FSMContext) -> None:
    """Обработка ввода имени игрока."""
    first = message.text.strip()
    if len(first) < 1:
        await message.answer("❌ Имя не может быть пустым:")
        return
    if len(first) > 100:
        await message.answer("❌ Имя слишком длинное. Максимум 100 символов:")
        return
    await state.update_data(player_first_name=first)
    await state.set_state(TeamStates.waiting_player_last_name)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⏭️ Пропустить", callback_data="skip_last_name")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_add_player")]
        ]
    )
    await message.answer(f"✅ Имя: <b>{first}</b>\n\n👤 Введите фамилию игрока (или пропустите):", reply_markup=kb, parse_mode="HTML")


@teams_router.message(AddMemberStates.waiting_telegram_id)
async def process_telegram_id_input(message: Message, state: FSMContext):
    """Обработка ввода Telegram ID"""
    data = await state.get_data()
    team_id = data.get('team_id')
    
    # Валидация ID
    telegram_id_str = message.text.strip()
    
    if not telegram_id_str.isdigit():
        await message.answer(
            "❌ **Неверный формат**\n\n"
            "Telegram ID должен содержать только цифры.\n"
            "Попробуйте еще раз:",
            parse_mode="Markdown"
        )
        return
    
    telegram_id = int(telegram_id_str)
    
    # Проверяем валидность ID (обычно от 1 до 10 миллиардов)
    if telegram_id < 1 or telegram_id > 10000000000:
        await message.answer(
            "❌ **Некорректный ID**\n\n"
            "Telegram ID должен быть числом от 1 до 10 миллиардов.\n"
            "Проверьте правильность и попробуйте еще раз:"
        )
        return
    
    # Проверяем, не состоит ли уже в команде
    is_member = await teams_database.check_player_in_team(telegram_id, team_id)
    
    if is_member:
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="🔙 Назад", callback_data=f"add_player_{team_id}")
        
        await message.answer(
            f"ℹ️ **Игрок уже в команде**\n\n"
            f"Пользователь с ID `{telegram_id}` уже является участником команды.",
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )
        await state.clear()
        return
    
    # Ищем информацию о пользователе
    user_info = await teams_database.find_user_by_telegram_id(telegram_id)
    
    # Сохраняем данные
    await state.update_data(
        telegram_id=telegram_id,
        user_info=user_info
    )
    await state.set_state(AddMemberStates.waiting_confirmation)
    
    # Показываем информацию для подтверждения
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="✅ Подтвердить", callback_data="confirm_add_by_id")
    keyboard.button(text="❌ Отмена", callback_data=f"view_team_{team_id}")
    keyboard.adjust(1)
    
    if user_info:
        # Пользователь найден в системе
        full_name = user_info['first_name']
        if user_info.get('last_name'):
            full_name += f" {user_info['last_name']}"
        username_text = f"@{user_info['username']}" if user_info.get('username') else "не указан"
        
        text = (
            f"✅ **Пользователь найден!**\n\n"
            f"👤 **Имя:** {full_name}\n"
            f"📱 **Username:** {username_text}\n"
            f"🆔 **Telegram ID:** `{telegram_id}`\n\n"
            f"Подтвердите добавление в команду:"
        )
    else:
        # Пользователь не найден
        text = (
            f"⚠️ **Пользователь не найден в системе**\n\n"
            f"🆔 **Telegram ID:** `{telegram_id}`\n\n"
            f"Пользователь будет добавлен в команду, но ему потребуется "
            f"написать боту `/start`, чтобы завершить регистрацию.\n\n"
            f"Продолжить?"
        )
    
    await message.answer(
        text,
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )


@teams_router.callback_query(F.data == "confirm_add_by_id")
async def confirm_add_by_telegram_id(callback: CallbackQuery, state: FSMContext):
    """Подтверждение добавления по Telegram ID"""
    data = await state.get_data()
    team_id = data.get('team_id')
    telegram_id = data.get('telegram_id')
    user_info = data.get('user_info')
    
    try:
        # Добавляем игрока в команду
        player = await teams_database.add_player_by_telegram_id(
            team_id=team_id,
            telegram_id=telegram_id,
            added_by=callback.from_user.id
        )
        
        if player:
            await state.clear()
            
            # Получаем обновленную информацию о команде
            team = await get_team_by_id(team_id)
            
            keyboard = InlineKeyboardBuilder()
            keyboard.button(
                text="➕ Добавить еще", 
                callback_data=f"add_player_{team_id}"
            )
            keyboard.button(
                text="👥 Посмотреть игроков", 
                callback_data=f"team_players_{team_id}"
            )
            keyboard.button(
                text="🔙 К команде", 
                callback_data=f"view_team_{team_id}"
            )
            keyboard.adjust(1)
            
            full_name = player.first_name
            if player.last_name:
                full_name += f" {player.last_name}"
            
            await callback.message.edit_text(
                f"🎉 **Игрок успешно добавлен!**\n\n"
                f"👤 **Игрок:** {full_name}\n"
                f"🆔 **Telegram ID:** `{telegram_id}`\n"
                f"🏆 **Команда:** {team.name}\n"
                f"📅 **Добавлен:** {player.joined_at.strftime('%d.%m.%Y %H:%M')}\n\n"
                f"💡 Игрок получит уведомление о добавлении в команду.",
                reply_markup=keyboard.as_markup(),
                parse_mode="Markdown"
            )
            
            # Отправляем уведомление игроку (если он есть в системе)
            if user_info:
                try:
                    from main import bot
                    await bot.send_message(
                        telegram_id,
                        f"🎉 **Вы добавлены в команду!**\n\n"
                        f"🏆 **Команда:** {team.name}\n"
                        f"📝 **Описание:** {team.description or 'Нет описания'}\n\n"
                        f"Используйте команду /myteam для просмотра своих команд.",
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.error(f"Failed to notify player {telegram_id}: {e}")
            
            await callback.answer("✅ Игрок добавлен!")
        else:
            await callback.answer("❌ Не удалось добавить игрока", show_alert=True)
            
    except Exception as e:
        logger.error(f"Error adding player by telegram_id: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)

# ===== ГЕНЕРАЦИЯ ПРИГЛАСИТЕЛЬНОЙ ССЫЛКИ =====
@teams_router.callback_query(F.data.startswith("generate_invite_"))
async def generate_team_invite(callback: CallbackQuery):
    """Генерация пригласительной ссылки для команды"""
    team_id = int(callback.data.split("_")[-1])
    team = await get_team_by_id(team_id)
    
    if not team:
        await callback.answer("❌ Команда не найдена")
        return
    
    # Генерируем или получаем код доступа
    if not team.access_code:
        # Если кода нет - генерируем новый
        import secrets
        access_code = secrets.token_urlsafe(8)[:8]
        # Сохраняем в БД (нужно добавить метод в teams_database.py)
        await teams_database.update_team_access_code(team_id, access_code)
    else:
        access_code = team.access_code
    
    # Создаем ссылку для присоединения
    bot_username = (await callback.bot.get_me()).username
    invite_link = f"https://t.me/{bot_username}?start=join_{access_code}"
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="📋 Скопировать код", callback_data=f"copy_code_{access_code}")
    keyboard.button(text="🔄 Создать новый код", callback_data=f"regenerate_code_{team_id}")
    keyboard.button(text="🔙 Назад", callback_data=f"add_player_{team_id}")
    keyboard.adjust(1)
    
    await callback.message.edit_text(
        f"📋 **Пригласительная ссылка для команды \"{team.name}\"**\n\n"
        f"🔗 **Ссылка для приглашения:**\n"
        f"`{invite_link}`\n\n"
        f"🆔 **Код доступа:**\n"
        f"`{access_code}`\n\n"
        f"💡 **Как использовать:**\n"
        f"• Отправьте ссылку игрокам\n"
        f"• Игроки перейдут по ссылке и автоматически начнут регистрацию\n"
        f"• Или они могут ввести `/join {access_code}` вручную\n\n"
        f"⚠️ Держите код в секрете от посторонних!",
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()

# ===== ОБРАБОТКА ДОБАВЛЕНИЯ ВРУЧНУЮ =====
@teams_router.callback_query(F.data == "add_method_manual")
async def add_method_manual(callback: CallbackQuery, state: FSMContext):
    """Переход к ручному добавлению игрока"""
    # Используем существующую логику из вашего кода
    data = await state.get_data()
    team_id = data.get('team_id')
    
    await state.set_state(TeamStates.waiting_player_first_name)
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="❌ Отмена", callback_data=f"view_team_{team_id}")
    
    await callback.message.edit_text(
        f"➕ **Добавление игрока вручную**\n\n"
        f"👤 Введите имя игрока:",
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()


@teams_router.message(TeamStates.waiting_player_last_name)
async def process_player_last_name(message: Message, state: FSMContext) -> None:
    """Обработка ввода фамилии игрока."""
    last = message.text.strip()
    if len(last) > 100:
        await message.answer("❌ Фамилия слишком длинная. Максимум 100 символов:")
        return
    await state.update_data(player_last_name=last)
    await ask_player_position(message, state, is_callback=False)


@teams_router.callback_query(F.data == "skip_last_name")
async def cb_skip_last_name(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик пропуска фамилии игрока."""
    await state.update_data(player_last_name="")
    await ask_player_position(callback, state, is_callback=True)


async def ask_player_position(update: Message | CallbackQuery, state: FSMContext, is_callback: bool = True) -> None:
    """Запрос позиции игрока."""
    await state.set_state(TeamStates.waiting_player_position)
    data = await state.get_data()
    first = data['player_first_name']
    last = data.get('player_last_name', '')
    full = f"{first} {last}".strip()
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⏭️ Пропустить", callback_data="skip_position")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_add_player")]
        ]
    )
    text = f"✅ Игрок: <b>{full}</b>\n\n🏃 Введите позицию игрока (или пропустите):"
    if is_callback:
        await safe_edit_text(update.message, text, reply_markup=kb)
    else:
        await update.answer(text, reply_markup=kb, parse_mode="HTML")


@teams_router.message(TeamStates.waiting_player_position)
async def process_player_position(message: Message, state: FSMContext) -> None:
    """Обработка ввода позиции игрока."""
    pos = message.text.strip()
    if len(pos) > 50:
        await message.answer("❌ Позиция слишком длинная. Максимум 50 символов:")
        return
    await state.update_data(player_position=pos)
    await ask_player_jersey(message, state, is_callback=False)


@teams_router.callback_query(F.data == "skip_position")
async def cb_skip_position(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик пропуска позиции игрока."""
    await state.update_data(player_position="")
    await ask_player_jersey(callback, state, is_callback=True)


async def ask_player_jersey(update: Message | CallbackQuery, state: FSMContext, is_callback: bool = True) -> None:
    """Запрос номера на майке игрока."""
    await state.set_state(TeamStates.waiting_player_jersey)
    data = await state.get_data()
    first = data['player_first_name']
    last = data.get('player_last_name', '')
    pos = data.get('player_position', '')
    full = f"{first} {last}".strip()
    pos_text = f"🏃 Позиция: <b>{pos}</b>\n" if pos else ""
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⏭️ Пропустить", callback_data="skip_jersey_number")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_add_player")]
        ]
    )
    text = f"✅ Игрок: <b>{full}</b>\n{pos_text}\n🔢 Введите номер на майке (или пропустите):"
    if is_callback:
        await safe_edit_text(update.message, text, reply_markup=kb)
    else:
        await update.answer(text, reply_markup=kb, parse_mode="HTML")


@teams_router.message(TeamStates.waiting_player_jersey)
async def process_player_jersey(message: Message, state: FSMContext) -> None:
    """Обработка ввода номера на майке."""
    txt = message.text.strip()
    try:
        jersey = int(txt)
        if jersey < 1 or jersey > 999:
            await message.answer("❌ Номер должен быть от 1 до 999:")
            return
    except ValueError:
        await message.answer("❌ Номер должен быть числом:")
        return

    await state.update_data(player_jersey=jersey)
    await finalize_player_creation(message, state, is_callback=False)


@teams_router.callback_query(F.data == "skip_jersey_number")
async def cb_skip_jersey(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик пропуска номера на майке."""
    await state.update_data(player_jersey=None)
    await finalize_player_creation(callback, state, is_callback=True)


async def finalize_player_creation(update: Message | CallbackQuery, state: FSMContext, is_callback: bool = True) -> None:
    """Завершение добавления игрока в команду."""
    data = await state.get_data()
    team_id = data.get('team_id')
    try:
        player = await add_team_player(
            team_id=team_id,
            first_name=data['player_first_name'],
            last_name=data.get('player_last_name') or None,
            position=data.get('player_position') or None,
            jersey_number=data.get('player_jersey')
        )
        await state.clear()
        if player:
            full = player.first_name + (f" {player.last_name}" if getattr(player, 'last_name', None) else "")
            kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="➕ Добавить еще игрока", callback_data=f"add_player_{team_id}")],
                    [InlineKeyboardButton(text="👥 Посмотреть игроков", callback_data=f"team_players_{team_id}")],
                    [InlineKeyboardButton(text="🔙 К команде", callback_data=f"view_team_{team_id}")]
                ]
            )
            text = (
                f"✅ <b>Игрок добавлен!</b>\n\n"
                f"👤 <b>Имя:</b> {full}\n"
                f"📅 <b>Добавлен:</b> {getattr(player, 'joined_at', datetime.now()).strftime('%d.%m.%Y %H:%M')}"
            )
            if is_callback:
                await safe_edit_text(update.message, text, reply_markup=kb)
                await update.answer("✅ Игрок добавлен!")
            else:
                await update.answer(text, reply_markup=kb, parse_mode="HTML")
            logger.info("Player added to team %s: %s", team_id, full)
        else:
            if is_callback:
                await update.answer("❌ Ошибка добавления игрока", show_alert=True)
            else:
                await update.answer("❌ Ошибка добавления игрока")
            logger.warning("Failed to add player to team %s", team_id)
    except Exception as e:
        logger.exception("Exception while adding player: %s", e)
        if is_callback:
            await update.answer("❌ Внутренняя ошибка", show_alert=True)
        else:
            await update.answer("❌ Внутренняя ошибка")


@teams_router.callback_query(F.data == "students_menu")
async def cb_students_menu(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик открытия меню подопечных."""
    await state.clear()
    students = await get_individual_students(callback.from_user.id)
    text = (
        f"👤 <b>Индивидуальные подопечные</b>\n\n"
        f"📊 У вас {len(students)} подопечных\n\n"
        "Подопечные для персональных тренировок."
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить подопечного", callback_data="add_student")],
            [InlineKeyboardButton(text="👥 Мои подопечные", callback_data="my_students")],
            [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
        ]
    )
    await safe_edit_text(callback.message, text, reply_markup=kb)
    await callback.answer()


@teams_router.callback_query(F.data == "add_student")
async def cb_add_student(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик начала добавления подопечного."""
    await state.set_state(TeamStates.waiting_student_first_name)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="students_menu")]])
    await safe_edit_text(callback.message, "➕ <b>Добавление подопечного</b>\n\n👤 Введите имя подопечного:", reply_markup=kb)
    await callback.answer()


@teams_router.message(TeamStates.waiting_student_first_name)
async def process_student_first_name(message: Message, state: FSMContext) -> None:
    """Обработка ввода имени подопечного."""
    first = message.text.strip()
    if len(first) < 1:
        await message.answer("❌ Имя не может быть пустым:")
        return
    await state.update_data(student_first_name=first)
    await state.set_state(TeamStates.waiting_student_last_name)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⏭️ Пропустить", callback_data="skip_student_last_name")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="students_menu")]
        ]
    )
    await message.answer(f"✅ Имя: <b>{first}</b>\n\n👤 Введите фамилию подопечного (или пропустите):", reply_markup=kb, parse_mode="HTML")


@teams_router.message(TeamStates.waiting_student_last_name)
async def process_student_last_name(message: Message, state: FSMContext) -> None:
    """Обработка ввода фамилии подопечного."""
    last = message.text.strip()
    await state.update_data(student_last_name=last)
    await ask_student_specialization(message, state, is_callback=False)


@teams_router.callback_query(F.data == "skip_student_last_name")
async def cb_skip_student_last_name(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик пропуска фамилии подопечного."""
    await state.update_data(student_last_name="")
    await ask_student_specialization(callback, state, is_callback=True)


async def ask_student_specialization(update: Message | CallbackQuery, state: FSMContext, is_callback: bool = True) -> None:
    """Запрос специализации подопечного."""
    await state.set_state(TeamStates.waiting_student_specialization)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏃 Бег", callback_data="spec_running")],
            [InlineKeyboardButton(text="💪 Силовые", callback_data="spec_strength")],
            [InlineKeyboardButton(text="🤸 Гимнастика", callback_data="spec_gymnastics")],
            [InlineKeyboardButton(text="🏊 Плавание", callback_data="spec_swimming")],
            [InlineKeyboardButton(text="🥊 Единоборства", callback_data="spec_combat")],
            [InlineKeyboardButton(text="⚽ Футбол", callback_data="spec_football")],
            [InlineKeyboardButton(text="🏀 Баскетбол", callback_data="spec_basketball")],
            [InlineKeyboardButton(text="💪 ОФП", callback_data="spec_general")],
            [InlineKeyboardButton(text="⏭️ Пропустить", callback_data="skip_specialization")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="students_menu")]
        ]
    )
    data = await state.get_data()
    full = f"{data.get('student_first_name')} {data.get('student_last_name', '')}".strip()
    text = f"✅ Подопечный: <b>{full}</b>\n\n🎯 Выберите специализацию тренировок:"
    if is_callback:
        await safe_edit_text(update.message, text, reply_markup=kb)
    else:
        await update.answer(text, reply_markup=kb, parse_mode="HTML")


@teams_router.callback_query(F.data.startswith("spec_") | F.data == "skip_specialization")
async def cb_student_specialization(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработка выбора специализации подопечного."""
    if callback.data == "skip_specialization":
        spec = ""
    else:
        mapping = {
            "spec_running": "Бег",
            "spec_strength": "Силовые тренировки",
            "spec_gymnastics": "Гимнастика",
            "spec_swimming": "Плавание",
            "spec_combat": "Единоборства",
            "spec_football": "Футбол",
            "spec_basketball": "Баскетбол",
            "spec_general": "ОФП",
        }
        spec = mapping.get(callback.data, "")
    await state.update_data(student_specialization=spec)
    await ask_student_level(callback, state)


async def ask_student_level(callback: CallbackQuery, state: FSMContext) -> None:
    """Запрос уровня подготовки подопечного."""
    await state.set_state(TeamStates.waiting_student_level)
    data = await state.get_data()
    full = f"{data.get('student_first_name')} {data.get('student_last_name', '')}".strip()
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🟢 Новичок", callback_data="level_beginner")],
            [InlineKeyboardButton(text="🟡 Средний", callback_data="level_intermediate")],
            [InlineKeyboardButton(text="🔴 Продвинутый", callback_data="level_advanced")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="students_menu")]
        ]
    )
    text = f"✅ Подопечный: <b>{full}</b>\n\n📊 Выберите уровень подготовки:"
    await safe_edit_text(callback.message, text, reply_markup=kb)
    await callback.answer()


@teams_router.callback_query(F.data.startswith("level_"))
async def cb_student_level(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработка выбора уровня подготовки подопечного."""
    mapping = {"level_beginner": "beginner", "level_intermediate": "intermediate", "level_advanced": "advanced"}
    level = mapping.get(callback.data, "beginner")
    data = await state.get_data()
    try:
        student = await add_individual_student(
            coach_telegram_id=callback.from_user.id,
            first_name=data['student_first_name'],
            last_name=data.get('student_last_name') or None,
            specialization=data.get('student_specialization') or None,
            level=level
        )
        await state.clear()
        if student:
            text = (
                f"✅ <b>Подопечный добавлен!</b>\n\n"
                f"👤 <b>{student.first_name} {student.last_name or ''}</b>\n"
                f"📊 Уровень: {student.level}"
            )
            kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="➕ Добавить еще подопечного", callback_data="add_student")],
                    [InlineKeyboardButton(text="👥 Посмотреть всех подопечных", callback_data="my_students")],
                    [InlineKeyboardButton(text="🔙 К подопечным", callback_data="students_menu")]
                ]
            )
            await safe_edit_text(callback.message, text, reply_markup=kb)
            await callback.answer("✅ Подопечный добавлен!")
            logger.info("Individual student added: coach=%s name=%s", callback.from_user.id, student.first_name)
        else:
            await callback.answer("❌ Ошибка добавления подопечного", show_alert=True)
            logger.warning("Failed to add individual student for coach %s", callback.from_user.id)
    except Exception as e:
        logger.exception("Exception while adding student: %s", e)
        await callback.answer("❌ Внутренняя ошибка", show_alert=True)


@teams_router.callback_query(F.data == "my_students")
async def cb_my_students(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик просмотра списка подопечных."""
    await state.clear()
    students = await get_individual_students(callback.from_user.id)
    if not students:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="➕ Добавить подопечного", callback_data="add_student")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="students_menu")]
            ]
        )
        await safe_edit_text(callback.message, "📭 <b>У вас пока нет подопечных</b>\n\nДобавьте первого подопечного!", reply_markup=kb)
        await callback.answer()
        return

    text = ""
    for i, s in enumerate(students, 1):
        text += f"{i}. {s.first_name} {s.last_name or ''} — {s.level}\n"
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить подопечного", callback_data="add_student")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="students_menu")]
        ]
    )
    await safe_edit_text(callback.message, f"👥 <b>Мои подопечные ({len(students)})</b>\n\n{text}", reply_markup=kb)
    await callback.answer()


@teams_router.callback_query(F.data == "stats_menu")
async def cb_stats_menu(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик просмотра статистики."""
    await state.clear()
    stats = await get_coach_stats(callback.from_user.id)
    text = (
        f"📊 <b>Ваша статистика</b>\n\n"
        f"🏆 Команд: {stats['teams_count']}\n"
        f"👥 Игроков в командах: {stats['team_players_count']}\n"
        f"👤 Индивидуальных подопечных: {stats['individual_students_count']}\n\n"
        f"🎯 Всего спортсменов: {stats['total_athletes']}"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]])
    await safe_edit_text(callback.message, text, reply_markup=kb)
    await callback.answer()


# Работа с БД
async def get_coach_stats(coach_telegram_id: int) -> dict:
    """Получение статистики тренера."""
    if teams_db:
        try:
            return await teams_db.get_coach_statistics(coach_telegram_id)
        except Exception as e:
            logger.exception("get_coach_stats DB error: %s", e)
            return {'teams_count': 0, 'team_players_count': 0, 'individual_students_count': 0, 'total_athletes': 0}
    return {'teams_count': 0, 'team_players_count': 0, 'individual_students_count': 0, 'total_athletes': 0}


async def create_team(coach_telegram_id: int, name: str, description: str = "", sport_type: str = "ОФП") -> Optional:
    """Создание команды в БД."""
    if teams_db:
        try:
            return await teams_db.create_team(coach_telegram_id, name, description, sport_type)
        except Exception as e:
            logger.exception("create_team DB error: %s", e)
            return None
    logger.warning("create_team called but teams_db is None")
    return None


async def get_coach_teams(coach_telegram_id: int) -> List:
    """Получение списка команд тренера."""
    if teams_db:
        try:
            return await teams_db.get_coach_teams(coach_telegram_id)
        except Exception as e:
            logger.exception("get_coach_teams DB error: %s", e)
            return []
    return []


async def get_team_by_id(team_id: int) -> Optional:
    """Получение команды по ID."""
    if teams_db:
        try:
            return await teams_db.get_team_by_id(team_id)
        except Exception as e:
            logger.exception("get_team_by_id DB error: %s", e)
            return None
    return None


async def get_team_players(team_id: int) -> List:
    """Получение списка игроков команды."""
    if teams_db:
        try:
            return await teams_db.get_team_players(team_id)
        except Exception as e:
            logger.exception("get_team_players DB error: %s", e)
            return []
    return []


async def add_team_player(team_id: int, first_name: str, last_name: Optional[str] = None, position: Optional[str] = None, jersey_number: Optional[int] = None) -> Optional:
    """Добавление игрока в команду."""
    if teams_db:
        try:
            return await teams_db.add_team_player(team_id, first_name, last_name, position, jersey_number)
        except Exception as e:
            logger.exception("add_team_player DB error: %s", e)
            return None
    return None


async def add_individual_student(coach_telegram_id: int, first_name: str, last_name: Optional[str] = None, specialization: Optional[str] = None, level: str = "beginner") -> Optional:
    """Добавление индивидуального подопечного."""
    if teams_db:
        try:
            return await teams_db.add_individual_student(coach_telegram_id, first_name, last_name, specialization, level)
        except Exception as e:
            logger.exception("add_individual_student DB error: %s", e)
            return None
    return None


async def get_individual_students(coach_telegram_id: int) -> List:
    """Получение списка индивидуальных подопечных."""
    if teams_db:
        try:
            return await teams_db.get_individual_students(coach_telegram_id)
        except Exception as e:
            logger.exception("get_individual_students DB error: %s", e)
            return []
    return []


@teams_router.callback_query(F.data.startswith("team_workouts_"))
async def show_team_workouts(callback: CallbackQuery, state: FSMContext):
    """Показать тренировки команды"""
    await state.clear()
    team_id = int(callback.data.split("_")[-1])
    
    team = await get_team_by_id(team_id)
    if not team:
        await callback.answer("❌ Команда не найдена")
        return
    
    # Получаем назначенные тренировки
    workouts = await teams_database.get_team_workouts(team_id)
    
    if not workouts:
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="➕ Назначить тренировку", callback_data=f"assign_workout_{team_id}")
        keyboard.button(text="🔙 К команде", callback_data=f"view_team_{team_id}")
        keyboard.adjust(1)
        
        await callback.message.edit_text(
            f"📋 **Тренировки команды \"{team.name}\"**\n\n"
            f"Пока нет назначенных тренировок.\n"
            f"Назначьте первую тренировку команде!",
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )
        await callback.answer()
        return
    
    # Формируем текст со списком тренировок
    text = f"📋 **Тренировки команды \"{team.name}\"**\n\n"
    
    keyboard = InlineKeyboardBuilder()
    
    for w in workouts:
        # Прогресс бар
        if w.total_players > 0:
            progress_pct = int((w.completed / w.total_players) * 100)
            progress_bar = "🟩" * (progress_pct // 10) + "⬜" * (10 - progress_pct // 10)
        else:
            progress_bar = "⬜" * 10
            progress_pct = 0
        
        # Дедлайн
        deadline_text = ""
        if w.deadline:
            deadline_text = f"\n⏰ До: {w.deadline.strftime('%d.%m.%Y')}"
        
        text += (
            f"💪 **{w.workout_name}**\n"
            f"{progress_bar} {progress_pct}%\n"
            f"✅ Выполнили: {w.completed}/{w.total_players}\n"
            f"⏳ В процессе: {w.in_progress}\n"
            f"📅 Назначено: {w.assigned_at.strftime('%d.%m %H:%M')}"
            f"{deadline_text}\n\n"
        )
        
        keyboard.button(
            text=f"📊 {w.workout_name} ({w.completed}/{w.total_players})",
            callback_data=f"workout_progress_{w.id}"
        )
    
    keyboard.button(text="➕ Назначить тренировку", callback_data=f"assign_workout_{team_id}")
    keyboard.button(text="🔙 К команде", callback_data=f"view_team_{team_id}")
    keyboard.adjust(1)
    
    await callback.message.edit_text(
        text,
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()

@teams_router.callback_query(F.data.startswith("assign_workout_"))
async def start_assign_workout(callback: CallbackQuery, state: FSMContext):
    """Начать процесс назначения тренировки"""
    team_id = int(callback.data.split("_")[-1])
    
    team = await get_team_by_id(team_id)
    if not team:
        await callback.answer("❌ Команда не найдена")
        return
    
    await state.update_data(team_id=team_id, assignment_type='team')
    await state.set_state(AssignWorkoutStates.choosing_workout_method)
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="💪 Мои тренировки", callback_data="workout_method_my")
    keyboard.button(text="🔗 По коду", callback_data="workout_method_code")
    keyboard.button(text="🔍 Поиск публичных", callback_data="workout_method_search")
    keyboard.button(text="🆕 Создать новую", callback_data="workout_method_create")
    keyboard.button(text="❌ Отмена", callback_data=f"team_workouts_{team_id}")
    keyboard.adjust(1)
    
    await callback.message.edit_text(
        f"➕ **Назначение тренировки команде \"{team.name}\"**\n\n"
        f"👥 Игроков: {team.players_count}\n\n"
        f"Выберите способ добавления тренировки:\n\n"
        f"💪 **Мои тренировки** - из созданных вами\n"
        f"🔗 **По коду** - если знаете код тренировки\n"
        f"🔍 **Поиск** - найти публичную тренировку\n"
        f"🆕 **Создать** - новую тренировку",
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()

# ===== ВЫБОР МЕТОДА НАЗНАЧЕНИЯ =====

@teams_router.callback_query(F.data == "workout_method_code")
async def workout_method_code(callback: CallbackQuery, state: FSMContext):
    """Назначение по коду"""
    await state.set_state(AssignWorkoutStates.entering_workout_code)
    
    data = await state.get_data()
    team_id = data.get('team_id')
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="❌ Отмена", callback_data=f"assign_workout_{team_id}")
    
    await callback.message.edit_text(
        "🔗 **Назначение тренировки по коду**\n\n"
        "Введите код тренировки (обычно 8 символов):\n\n"
        "💡 *Код можно найти в описании тренировки или получить от другого тренера*\n\n"
        "Пример: `abc12345`",
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()

@teams_router.message(AssignWorkoutStates.entering_workout_code)
async def process_workout_code(message: Message, state: FSMContext):
    """Обработка кода тренировки"""
    code = message.text.strip()
    
    # Ищем тренировку по коду
    workout = await teams_database.get_workout_by_code(code, message.from_user.id)
    
    if not workout:
        await message.answer(
            "❌ **Тренировка не найдена**\n\n"
            "Проверьте правильность кода или убедитесь, что:\n"
            "• Тренировка публичная\n"
            "• Или вы её автор\n\n"
            "Попробуйте еще раз:",
            parse_mode="Markdown"
        )
        return
    
    # Сохраняем выбранную тренировку
    await state.update_data(selected_workout=workout)
    await show_workout_confirmation(message, state, workout)

async def show_workout_confirmation(message: Message, state: FSMContext, workout: Dict):
    """Показать подтверждение назначения"""
    data = await state.get_data()
    team_id = data.get('team_id')
    
    await state.set_state(AssignWorkoutStates.confirming_assignment)
    
    creator_name = workout.get('creator_name', 'Неизвестен')
    if workout.get('creator_last_name'):
        creator_name += f" {workout['creator_last_name']}"
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="✅ Назначить", callback_data="confirm_assign_workout")
    keyboard.button(text="💬 Добавить комментарий", callback_data="add_assignment_notes")
    keyboard.button(text="⏰ Установить дедлайн", callback_data="set_assignment_deadline")
    keyboard.button(text="❌ Отмена", callback_data=f"assign_workout_{team_id}")
    keyboard.adjust(1)
    
    text = (
        f"✅ **Тренировка найдена!**\n\n"
        f"💪 **Название:** {workout['name']}\n"
        f"📝 **Описание:** {workout.get('description', 'Нет описания')}\n"
        f"👤 **Автор:** {creator_name}\n"
        f"⚡ **Сложность:** {workout.get('difficulty_level', 'средняя')}\n"
        f"⏱️ **Длительность:** ~{workout.get('estimated_duration_minutes', 60)} мин\n"
        f"🔗 **Код:** `{workout['unique_id']}`\n\n"
        f"Назначить эту тренировку команде?"
    )
    
    await message.answer(text, reply_markup=keyboard.as_markup(), parse_mode="Markdown")

@teams_router.callback_query(F.data == "add_assignment_notes")
async def add_assignment_notes(callback: CallbackQuery, state: FSMContext):
    """Добавить комментарий к назначению"""
    await state.set_state(AssignWorkoutStates.adding_notes)
    
    await callback.message.edit_text(
        "💬 **Комментарий для команды**\n\n"
        "Введите комментарий (будет виден всем игрокам):\n\n"
        "Например: *\"Сосредоточьтесь на технике, не спешите\"*",
        parse_mode="Markdown"
    )
    await callback.answer()

@teams_router.message(AssignWorkoutStates.adding_notes)
async def process_assignment_notes(message: Message, state: FSMContext):
    """Обработка комментария"""
    notes = message.text.strip()
    await state.update_data(assignment_notes=notes)
    
    data = await state.get_data()
    workout = data.get('selected_workout')
    
    await message.answer(
        f"✅ Комментарий добавлен:\n\n"
        f"💬 \"{notes}\"\n\n"
        f"Продолжим назначение тренировки?",
        parse_mode="Markdown"
    )
    
    await show_workout_confirmation(message, state, workout)

@teams_router.callback_query(F.data == "confirm_assign_workout")
async def confirm_assign_workout(callback: CallbackQuery, state: FSMContext):
    """Подтвердить назначение тренировки"""
    data = await state.get_data()
    team_id = data.get('team_id')
    workout = data.get('selected_workout')
    notes = data.get('assignment_notes')
    deadline = data.get('assignment_deadline')
    
    # Назначаем тренировку
    success = await teams_database.assign_workout_to_team(
        workout_id=workout['id'],
        team_id=team_id,
        assigned_by=callback.from_user.id,
        notes=notes,
        deadline=deadline
    )
    
    if success:
        await state.clear()
        
        team = await get_team_by_id(team_id)
        
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="📋 Тренировки команды", callback_data=f"team_workouts_{team_id}")
        keyboard.button(text="🏆 К команде", callback_data=f"view_team_{team_id}")
        keyboard.adjust(1)
        
        await callback.message.edit_text(
            f"🎉 **Тренировка успешно назначена!**\n\n"
            f"💪 **Тренировка:** {workout['name']}\n"
            f"🏆 **Команда:** {team.name}\n"
            f"👥 **Игроков:** {team.players_count}\n\n"
            f"✅ Все игроки получат уведомление о новой тренировке!",
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )
        
        # Отправляем уведомления игрокам
        await notify_team_about_workout(team_id, workout, notes)
        
        await callback.answer("✅ Тренировка назначена!")
    else:
        await callback.answer("❌ Ошибка при назначении", show_alert=True)

async def notify_team_about_workout(team_id: int, workout: Dict, notes: str = None):
    """Отправить уведомления игрокам о новой тренировке"""
    from main import bot
    
    # Получаем игроков команды с telegram_id
    players = await teams_database.get_team_players(team_id)
    
    notes_text = f"\n\n💬 **Комментарий тренера:**\n{notes}" if notes else ""
    
    for player in players:
        if player.telegram_id:
            try:
                keyboard = InlineKeyboardBuilder()
                keyboard.button(text="💪 Начать тренировку", callback_data=f"start_workout_{workout['id']}")
                keyboard.button(text="📋 Мои тренировки", callback_data="my_workouts")
                keyboard.adjust(1)
                
                await bot.send_message(
                    player.telegram_id,
                    f"🆕 **Новая тренировка!**\n\n"
                    f"💪 **Название:** {workout['name']}\n"
                    f"📝 **Описание:** {workout.get('description', 'Нет описания')}\n"
                    f"⏱️ **Длительность:** ~{workout.get('estimated_duration_minutes', 60)} мин"
                    f"{notes_text}\n\n"
                    f"Удачной тренировки! 💪",
                    reply_markup=keyboard.as_markup(),
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Failed to notify player {player.telegram_id}: {e}")

@teams_router.callback_query(F.data.startswith("workout_progress_"))
async def show_workout_progress(callback: CallbackQuery):
    """Показать прогресс по тренировке"""
    workout_team_id = int(callback.data.split("_")[-1])
    
    # Получаем детальный прогресс
    progress = await teams_database.get_team_workout_progress(workout_team_id)
    
    if not progress:
        await callback.answer("❌ Данные не найдены")
        return
    
    # Группируем по статусам
    completed = [p for p in progress if p['status'] == 'completed']
    in_progress = [p for p in progress if p['status'] == 'in_progress']
    pending = [p for p in progress if p['status'] == 'pending']
    
    text = "📊 **Прогресс выполнения тренировки**\n\n"
    
    # Выполнили (с RPE)
    if completed:
        text += "✅ **Выполнили:**\n"
        for p in completed:
            name = f"{p['first_name']} {p['last_name'] or ''}".strip()
            num = f"#{p['jersey_number']}" if p['jersey_number'] else ""
            rpe_text = f" (RPE: {p['rpe']:.1f}/10)" if p['rpe'] else ""
            completed_date = p['completed_at'].strftime('%d.%m %H:%M') if p['completed_at'] else ""
            text += f"  {num} {name}{rpe_text} - {completed_date}\n"
        text += "\n"
    
    # В процессе
    if in_progress:
        text += "⏳ **В процессе:**\n"
        for p in in_progress:
            name = f"{p['first_name']} {p['last_name'] or ''}".strip()
            num = f"#{p['jersey_number']}" if p['jersey_number'] else ""
            text += f"  {num} {name}\n"
        text += "\n"
    
    # Не начали
    if pending:
        text += "⏱️ **Не начали:**\n"
        for p in pending:
            name = f"{p['first_name']} {p['last_name'] or ''}".strip()
            num = f"#{p['jersey_number']}" if p['jersey_number'] else ""
            text += f"  {num} {name}\n"
    
    # Средний RPE
    if completed:
        avg_rpe = sum(p['rpe'] for p in completed if p['rpe']) / len([p for p in completed if p['rpe']])
        text += f"\n📈 **Средний RPE:** {avg_rpe:.1f}/10"
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔙 Назад", callback_data="back_to_team_workouts")
    
    await callback.message.edit_text(text, reply_markup=keyboard.as_markup(), parse_mode="Markdown")
    await callback.answer()



# Экспорт
def get_teams_router() -> Router:
    """Экспорт роутера команд."""
    logger.info("Exporting teams router")
    return teams_router
def get_teams_router() -> Router:
    """Возвращает роутер модуля teams."""
    return teams_router

__all__ = ["get_teams_router", "init_teams_module_async"]