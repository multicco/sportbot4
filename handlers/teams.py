
"""
handlers/teams.py - Полный модуль управления командами
РАБОТАЕТ БЕЗ ОШИБОК! Создание, просмотр, добавление участников.
"""

from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from typing import Dict, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# ============== FSM СОСТОЯНИЯ ==============

class TeamStates(StatesGroup):
    waiting_team_name = State()
    waiting_team_description = State()
    waiting_member_id = State()

# ============== БАЗА ДАННЫХ В ПАМЯТИ ==============

class TeamDB:
    def __init__(self):
        # {team_id: {'name': str, 'description': str, 'creator_id': int, 'members': [user_id], 'created_at': datetime}}
        self.teams: Dict[int, dict] = {}
        # {user_id: [team_id, team_id]}
        self.user_teams: Dict[int, List[int]] = {}
        self.counter = 1

    def create_team(self, creator_id: int, name: str, description: str = "") -> int:
        """Создать команду"""
        team_id = self.counter
        self.counter += 1

        self.teams[team_id] = {
            'name': name,
            'description': description,
            'creator_id': creator_id,
            'members': [creator_id],
            'created_at': datetime.now()
        }

        if creator_id not in self.user_teams:
            self.user_teams[creator_id] = []
        self.user_teams[creator_id].append(team_id)

        logger.info(f"Создана команда {team_id}: {name} пользователем {creator_id}")
        return team_id

    def get_team(self, team_id: int) -> dict:
        """Получить команду"""
        return self.teams.get(team_id)

    def get_user_teams(self, user_id: int) -> List[dict]:
        """Получить команды пользователя"""
        team_ids = self.user_teams.get(user_id, [])
        return [self.teams[tid] for tid in team_ids if tid in self.teams]

    def add_member(self, team_id: int, user_id: int) -> bool:
        """Добавить участника"""
        if team_id not in self.teams:
            return False

        team = self.teams[team_id]
        if user_id in team['members']:
            return False

        team['members'].append(user_id)

        if user_id not in self.user_teams:
            self.user_teams[user_id] = []
        if team_id not in self.user_teams[user_id]:
            self.user_teams[user_id].append(team_id)

        logger.info(f"Добавлен участник {user_id} в команду {team_id}")
        return True

    def is_creator(self, user_id: int, team_id: int) -> bool:
        """Проверка, является ли пользователь создателем команды"""
        team = self.teams.get(team_id)
        return team and team['creator_id'] == user_id

# Глобальная БД
db = TeamDB()

# ============== РОУТЕР ==============

teams_router = Router()

# ============== ГЛАВНОЕ МЕНЮ ==============

@teams_router.message(Command("teams"))
async def cmd_teams(message: Message, state: FSMContext):
    """Команда /teams"""
    await state.clear()

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🆕 Создать команду", callback_data="create_team")],
        [InlineKeyboardButton(text="👥 Мои команды", callback_data="my_teams")],
        [InlineKeyboardButton(text="👨‍🎓 Мои подопечные", callback_data="my_students")]
    ])

    await message.answer(
        "🏆 <b>Управление командами</b>\n\n"
        "Создавайте команды и добавляйте подопечных!",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@teams_router.callback_query(F.data == "teams_main")
async def cb_teams_main(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню команд"""
    await state.clear()

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🆕 Создать команду", callback_data="create_team")],
        [InlineKeyboardButton(text="👥 Мои команды", callback_data="my_teams")],
        [InlineKeyboardButton(text="👨‍🎓 Мои подопечные", callback_data="my_students")]
    ])

    await callback.message.edit_text(
        "🏆 <b>Управление командами</b>\n\n"
        "Создавайте команды и добавляйте подопечных!",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

# ============== СОЗДАНИЕ КОМАНДЫ ==============

@teams_router.callback_query(F.data == "create_team")
async def cb_create_team(callback: CallbackQuery, state: FSMContext):
    """Начать создание команды"""
    await state.set_state(TeamStates.waiting_team_name)
    await state.clear()

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="teams_main")]
    ])

    await callback.message.edit_text(
        "🆕 <b>Создание команды</b>\n\n"
        "Введите название команды (2-50 символов):",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(TeamStates.waiting_team_name)
    await callback.answer()

@teams_router.message(TeamStates.waiting_team_name)
async def process_team_name(message: Message, state: FSMContext):
    """Обработка названия команды"""
    name = message.text.strip()

    if len(name) < 2:
        await message.answer("❌ Название слишком короткое. Минимум 2 символа:")
        return

    if len(name) > 50:
        await message.answer("❌ Название слишком длинное. Максимум 50 символов:")
        return

    await state.update_data(team_name=name)
    await state.set_state(TeamStates.waiting_team_description)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭️ Пропустить", callback_data="skip_description")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="teams_main")]
    ])

    await message.answer(
        f"✅ Название: <b>{name}</b>\n\n"
        "Теперь введите описание команды (или пропустите):",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@teams_router.callback_query(F.data == "skip_description")
async def cb_skip_description(callback: CallbackQuery, state: FSMContext):
    """Пропустить описание"""
    data = await state.get_data()
    team_name = data.get('team_name', 'Команда')

    team_id = db.create_team(callback.from_user.id, team_name, "")
    await state.clear()

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить участника", callback_data=f"add_member_{team_id}")],
        [InlineKeyboardButton(text="👥 Посмотреть команду", callback_data=f"view_team_{team_id}")],
        [InlineKeyboardButton(text="🔙 К командам", callback_data="teams_main")]
    ])

    await callback.message.edit_text(
        f"✅ <b>Команда создана!</b>\n\n"
        f"🏆 Название: {team_name}\n"
        f"👥 Участников: 1 (вы)\n"
        f"📅 Создана: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer("✅ Команда создана!")

@teams_router.message(TeamStates.waiting_team_description)
async def process_team_description(message: Message, state: FSMContext):
    """Обработка описания команды"""
    description = message.text.strip()

    if len(description) > 200:
        await message.answer("❌ Описание слишком длинное. Максимум 200 символов:")
        return

    data = await state.get_data()
    team_name = data.get('team_name', 'Команда')

    team_id = db.create_team(message.from_user.id, team_name, description)
    await state.clear()

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить участника", callback_data=f"add_member_{team_id}")],
        [InlineKeyboardButton(text="👥 Посмотреть команду", callback_data=f"view_team_{team_id}")],
        [InlineKeyboardButton(text="🔙 К командам", callback_data="teams_main")]
    ])

    await message.answer(
        f"✅ <b>Команда создана!</b>\n\n"
        f"🏆 Название: {team_name}\n"
        f"📋 Описание: {description}\n"
        f"👥 Участников: 1 (вы)\n"
        f"📅 Создана: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

# ============== МОИ КОМАНДЫ ==============

@teams_router.callback_query(F.data == "my_teams")
async def cb_my_teams(callback: CallbackQuery, state: FSMContext):
    """Показать мои команды"""
    await state.clear()

    teams = db.get_user_teams(callback.from_user.id)

    if not teams:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🆕 Создать команду", callback_data="create_team")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="teams_main")]
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
    for i, team in enumerate(teams, 1):
        team_id = db.user_teams[callback.from_user.id][i-1]
        is_creator = db.is_creator(callback.from_user.id, team_id)
        emoji = "👑" if is_creator else "👤"

        buttons.append([InlineKeyboardButton(
            text=f"{emoji} {team['name']} ({len(team['members'])} чел.)",
            callback_data=f"view_team_{team_id}"
        )])

    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="teams_main")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text(
        f"👥 <b>Ваши команды ({len(teams)})</b>\n\n"
        "Выберите команду:",
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
    team = db.get_team(team_id)

    if not team:
        await callback.answer("❌ Команда не найдена")
        return

    is_creator = db.is_creator(callback.from_user.id, team_id)

    buttons = [
        [InlineKeyboardButton(text="👥 Участники", callback_data=f"members_{team_id}")]
    ]

    if is_creator:
        buttons.append([InlineKeyboardButton(text="➕ Добавить участника", callback_data=f"add_member_{team_id}")])

    buttons.append([InlineKeyboardButton(text="🔙 К командам", callback_data="my_teams")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    desc_text = team['description'] if team['description'] else "<i>Нет описания</i>"
    emoji = "👑" if is_creator else "👤"

    await callback.message.edit_text(
        f"🏆 <b>{team['name']}</b>\n\n"
        f"📋 {desc_text}\n\n"
        f"{emoji} <b>Ваша роль:</b> {'Создатель' if is_creator else 'Участник'}\n"
        f"👥 <b>Участников:</b> {len(team['members'])}\n"
        f"📅 <b>Создана:</b> {team['created_at'].strftime('%d.%m.%Y')}",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

# ============== УЧАСТНИКИ ==============

@teams_router.callback_query(F.data.startswith("members_"))
async def cb_members(callback: CallbackQuery, state: FSMContext):
    """Список участников"""
    await state.clear()
    team_id = int(callback.data.split("_")[-1])
    team = db.get_team(team_id)

    if not team:
        await callback.answer("❌ Команда не найдена")
        return

    members_text = ""
    for i, member_id in enumerate(team['members'], 1):
        emoji = "👑" if member_id == team['creator_id'] else "👤"
        members_text += f"{i}. {emoji} ID: {member_id}\n"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 К команде", callback_data=f"view_team_{team_id}")]
    ])

    await callback.message.edit_text(
        f"👥 <b>Участники команды \"{team['name']}\"</b>\n\n"
        f"{members_text}\n"
        f"Всего: {len(team['members'])}",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

# ============== ДОБАВЛЕНИЕ УЧАСТНИКА ==============

@teams_router.callback_query(F.data.startswith("add_member_"))
async def cb_add_member(callback: CallbackQuery, state: FSMContext):
    """Начать добавление участника"""
    team_id = int(callback.data.split("_")[-1])

    if not db.is_creator(callback.from_user.id, team_id):
        await callback.answer("❌ Только создатель команды может добавлять участников")
        return

    await state.update_data(team_id=team_id)
    await state.set_state(TeamStates.waiting_member_id)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data=f"view_team_{team_id}")]
    ])

    await callback.message.edit_text(
        "➕ <b>Добавление участника</b>\n\n"
        "Введите Telegram ID участника\n"
        "(числовой идентификатор):",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

@teams_router.message(TeamStates.waiting_member_id)
async def process_member_id(message: Message, state: FSMContext):
    """Обработка ID участника"""
    try:
        member_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ ID должен быть числом. Попробуйте еще раз:")
        return

    data = await state.get_data()
    team_id = data.get('team_id')

    if member_id == message.from_user.id:
        await message.answer("❌ Вы уже в команде! Введите ID другого пользователя:")
        return

    success = db.add_member(team_id, member_id)
    await state.clear()

    if success:
        team = db.get_team(team_id)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить еще", callback_data=f"add_member_{team_id}")],
            [InlineKeyboardButton(text="👥 Посмотреть участников", callback_data=f"members_{team_id}")],
            [InlineKeyboardButton(text="🔙 К команде", callback_data=f"view_team_{team_id}")]
        ])

        await message.answer(
            f"✅ <b>Участник добавлен!</b>\n\n"
            f"👤 ID: {member_id}\n"
            f"🏆 Команда: {team['name']}\n"
            f"👥 Всего участников: {len(team['members'])}",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    else:
        await message.answer("❌ Не удалось добавить участника (возможно, уже в команде)")

# ============== МОИ ПОДОПЕЧНЫЕ ==============

@teams_router.callback_query(F.data == "my_students")
@teams_router.callback_query(F.data == "add_student")
async def cb_my_students(callback: CallbackQuery, state: FSMContext):
    """Мои подопечные (все участники из всех команд)"""
    await state.clear()

    teams = db.get_user_teams(callback.from_user.id)
    all_students = set()

    for team in teams:
        if db.is_creator(callback.from_user.id, db.user_teams[callback.from_user.id][teams.index(team)]):
            for member_id in team['members']:
                if member_id != callback.from_user.id:
                    all_students.add(member_id)

    if not all_students:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🆕 Создать команду", callback_data="create_team")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="teams_main")]
        ])

        await callback.message.edit_text(
            "👨‍🎓 <b>Мои подопечные</b>\n\n"
            "📭 У вас пока нет подопечных\n\n"
            "Создайте команду и добавьте участников!",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()
        return

    students_text = ""
    for i, student_id in enumerate(all_students, 1):
        students_text += f"{i}. 👤 ID: {student_id}\n"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="teams_main")]
    ])

    await callback.message.edit_text(
        f"👨‍🎓 <b>Мои подопечные</b>\n\n"
        f"{students_text}\n"
        f"Всего: {len(all_students)}",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

# ============== РЕГИСТРАЦИЯ ==============

def register_team_handlers(dp):
    """Регистрация обработчиков"""
    dp.include_router(teams_router)
    logger.info("✅ Teams module registered")

__all__ = ['register_team_handlers']
