# ===== ОБРАБОТЧИКИ КОМАНДНОЙ СИСТЕМЫ =====

from aiogram import F
from aiogram.types import CallbackQuery
from keyboards.main_keyboards_old import get_coming_soon_keyboard

def register_team_handlers(dp):
    """Регистрация обработчиков командной системы"""
    
    # Функции для тренеров
    dp.callback_query.register(feature_coming_soon, F.data == "create_team")
    dp.callback_query.register(feature_coming_soon, F.data == "add_student")
    dp.callback_query.register(feature_coming_soon, F.data == "my_teams")
    dp.callback_query.register(feature_coming_soon, F.data == "my_students")
    
    # Функции для игроков
    dp.callback_query.register(feature_coming_soon, F.data == "join_team")
    dp.callback_query.register(feature_coming_soon, F.data == "find_coach")
    dp.callback_query.register(feature_coming_soon, F.data == "my_team")
    
    # Функции тренировок (заглушки)
    dp.callback_query.register(feature_coming_soon, F.data == "my_workouts")
    dp.callback_query.register(feature_coming_soon, F.data == "find_workout")
    dp.callback_query.register(feature_coming_soon, F.data == "search_by_muscle")

async def feature_coming_soon(callback: CallbackQuery):
    """Заглушка для функций в разработке"""
    
    feature_names = {
        "my_workouts": "Мои тренировки",
        "find_workout": "Поиск тренировок", 
        "search_by_muscle": "Поиск по мышцам",
        "create_team": "Создание команды",
        "add_student": "Добавление подопечного",
        "my_teams": "Мои команды",
        "my_students": "Мои подопечные", 
        "join_team": "Присоединение к команде",
        "find_coach": "Поиск тренера",
        "my_team": "Моя команда"
    }
    
    feature_name = feature_names.get(callback.data, "Эта функция")
    keyboard = get_coming_soon_keyboard()
    
    await callback.message.edit_text(
        f"🚧 **{feature_name}**\n\n"
        f"Функция находится в разработке.\n"
        f"Скоро будет доступна!",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

# ===== ЗАГОТОВКИ ДЛЯ БУДУЩИХ ФУНКЦИЙ =====

async def create_team(callback: CallbackQuery):
    """Создание команды (будущая функция)"""
    # TODO: Реализовать создание команды
    pass

async def add_student(callback: CallbackQuery):
    """Добавление подопечного (будущая функция)"""
    # TODO: Реализовать добавление подопечного
    pass

async def my_teams(callback: CallbackQuery):
    """Мои команды (будущая функция)"""
    # TODO: Реализовать просмотр команд
    pass

async def my_students(callback: CallbackQuery):
    """Мои подопечные (будущая функция)"""
    # TODO: Реализовать просмотр подопечных
    pass

async def join_team(callback: CallbackQuery):
    """Присоединение к команде (будущая функция)"""
    # TODO: Реализовать присоединение к команде
    pass

async def find_coach(callback: CallbackQuery):
    """Поиск тренера (будущая функция)"""
    # TODO: Реализовать поиск тренера
    pass

async def my_team(callback: CallbackQuery):
    """Моя команда (будущая функция)"""
    # TODO: Реализовать просмотр своей команды
    pass





# ============== ПРОДОЛЖЕНИЕ МОДУЛЯ teams.py ==============
# Добавь этот код в конец файла teams.py

# ============== ПРОСМОТР КОМАНД ==============

@teams_router.callback_query(F.data == "my_teams")
async def show_my_teams(callback: CallbackQuery):
    """Показать команды пользователя"""
    try:
        user_teams = await db.get_user_teams(callback.from_user.id)

        if not user_teams:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🆕 Создать первую команду", callback_data="create_team")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="teams_main")]
            ])

            await callback.message.edit_text(
                "📭 <b>У вас пока нет команд</b>\n\n"
                "Создайте свою первую команду для управления подопечными!",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            await callback.answer()
            return

        # Создаем кнопки для каждой команды
        buttons = []
        for team in user_teams:
            user_role = await db.get_user_role_in_team(callback.from_user.id, team.id)
            role_emoji = get_role_emoji(user_role)

            button_text = f"{role_emoji} {team.name} ({len(team.members)} чел.)"
            buttons.append([InlineKeyboardButton(
                text=button_text, 
                callback_data=f"team_menu_{team.id}"
            )])

        # Добавляем кнопки управления
        buttons.extend([
            [InlineKeyboardButton(text="🆕 Создать команду", callback_data="create_team")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="teams_main")]
        ])

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

        await callback.message.edit_text(
            f"👥 <b>Ваши команды ({len(user_teams)})</b>\n\n"
            "Выберите команду для управления:\n\n"
            "<i>👑 - Капитан, ⭐ - Помощник, 👤 - Участник</i>",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Error in show_my_teams: {e}")
        await callback.answer("❌ Произошла ошибка")

@teams_router.callback_query(F.data.startswith("team_menu_"))
async def show_team_menu(callback: CallbackQuery):
    """Показать меню команды"""
    try:
        team_id = int(callback.data.split("_")[-1])
        team = await db.get_team(team_id)

        if not team:
            await callback.answer("❌ Команда не найдена")
            return

        user_role = await db.get_user_role_in_team(callback.from_user.id, team_id)
        if not user_role:
            await callback.answer("❌ У вас нет доступа к этой команде")
            return

        keyboard = get_team_management_keyboard(team_id, user_role)

        # Статистика команды
        active_members = len([m for m in team.members if m.is_active])
        role_emoji = get_role_emoji(user_role)
        role_name = get_role_name(user_role)

        description_text = team.description if team.description else "<i>Описание отсутствует</i>"

        await callback.message.edit_text(
            f"🏆 <b>{team.name}</b>\n\n"
            f"📋 <b>Описание:</b> {description_text}\n\n"
            f"{role_emoji} <b>Ваша роль:</b> {role_name}\n"
            f"👥 <b>Участников:</b> {active_members}\n"
            f"📅 <b>Создана:</b> {team.created_at.strftime('%d.%m.%Y')}",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Error in show_team_menu: {e}")
        await callback.answer("❌ Произошла ошибка")

# ============== ПРОСМОТР УЧАСТНИКОВ ==============

@teams_router.callback_query(F.data.startswith("team_members_"))
async def show_team_members(callback: CallbackQuery):
    """Показать участников команды"""
    try:
        team_id = int(callback.data.split("_")[-1])
        team = await db.get_team(team_id)

        if not team:
            await callback.answer("❌ Команда не найдена")
            return

        user_role = await db.get_user_role_in_team(callback.from_user.id, team_id)
        if not user_role:
            await callback.answer("❌ У вас нет доступа к этой команде")
            return

        if not team.members:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="➕ Добавить участников", callback_data=f"add_member_{team_id}")],
                [InlineKeyboardButton(text="🔙 К команде", callback_data=f"team_menu_{team_id}")]
            ])

            await callback.message.edit_text(
                f"👥 <b>Участники команды "{team.name}"</b>\n\n"
                "Пока что в команде никого нет.\n"
                "Добавьте первых участников!",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            await callback.answer()
            return

        # Сортируем участников по роли и дате добавления
        sorted_members = sorted(team.members, key=lambda m: (
            0 if m.role == 'captain' else 1 if m.role == 'assistant' else 2,
            m.joined_at
        ))

        members_text = ""
        for i, member in enumerate(sorted_members, 1):
            role_emoji = get_role_emoji(member.role)
            username_text = f"@{member.username}" if member.username else "без username"

            full_name = member.first_name
            if member.last_name:
                full_name += f" {member.last_name}"

            members_text += (
                f"{i}. {role_emoji} <b>{full_name}</b>\n"
                f"   {username_text}\n"
                f"   <i>В команде с {member.joined_at.strftime('%d.%m.%Y')}</i>\n\n"
            )

        keyboard = get_members_keyboard(team_id, user_role=user_role)

        text = (
            f"👥 <b>Участники команды "{team.name}"</b>\n"
            f"Всего: {len(sorted_members)}\n\n{members_text}"
        )

        # Telegram имеет ограничение на длину сообщения
        if len(text) > 4000:
            text = text[:3900] + "...\n\n<i>Список слишком длинный, показаны первые участники</i>"

        await callback.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Error in show_team_members: {e}")
        await callback.answer("❌ Произошла ошибка")

# ============== ДОБАВЛЕНИЕ УЧАСТНИКОВ ==============

@teams_router.callback_query(F.data.startswith("add_member_"))
async def start_add_member(callback: CallbackQuery, state: FSMContext):
    """Начать добавление участника"""
    try:
        team_id = int(callback.data.split("_")[-1])
        team = await db.get_team(team_id)

        if not team:
            await callback.answer("❌ Команда не найдена")
            return

        user_role = await db.get_user_role_in_team(callback.from_user.id, team_id)
        if user_role not in ['captain', 'assistant']:
            await callback.answer("❌ У вас нет прав для добавления участников")
            return

        # Проверяем лимит участников
        if len(team.members) >= team.max_members:
            await callback.message.edit_text(
                f"❌ <b>Достигнут лимит участников</b>\n\n"
                f"Максимальное количество участников в команде: {team.max_members}\n"
                "Удалите неактивных участников перед добавлением новых.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Назад", callback_data=f"team_menu_{team_id}")]
                ]),
                parse_mode="HTML"
            )
            await callback.answer()
            return

        await state.set_state(TeamStates.waiting_member_search)
        await state.update_data(team_id=team_id)

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📱 По номеру телефона", callback_data=f"add_by_phone_{team_id}")],
            [InlineKeyboardButton(text="🆔 По Telegram ID", callback_data=f"add_by_id_{team_id}")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data=f"team_menu_{team_id}")]
        ])

        await callback.message.edit_text(
            f"➕ <b>Добавление участника в "{team.name}"</b>\n\n"
            "Как вы хотите добавить участника?\n\n"
            "<b>Способы добавления:</b>\n"
            "🔍 <b>По поиску:</b> введите имя или @username\n"
            "📱 <b>По телефону:</b> попросите участника написать боту\n"
            "🆔 <b>По ID:</b> если знаете Telegram ID\n\n"
            "<i>Сейчас в команде: {len(team.members)}/{team.max_members}</i>",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Error in start_add_member: {e}")
        await callback.answer("❌ Произошла ошибка")

@teams_router.message(TeamStates.waiting_member_search)
async def process_member_search(message: Message, state: FSMContext):
    """Обработка поиска участника"""
    try:
        data = await state.get_data()
        team_id = data['team_id']
        search_query = message.text.strip()

        if len(search_query) < 2:
            await message.answer(
                "❌ Введите минимум 2 символа для поиска\n\n"
                "Попробуйте еще раз:",
                reply_markup=get_cancel_keyboard(f"team_menu_{team_id}")
            )
            return

        # В реальной реализации здесь был бы поиск по базе данных
        # Сейчас создаем заглушку для демонстрации
        found_users = []

        # Попробуем извлечь user_id если это число
        if search_query.isdigit():
            user_id = int(search_query)
            if TeamValidator.validate_user_id(user_id):
                # Проверяем, не является ли пользователь уже участником
                team = await db.get_team(team_id)
                is_member = any(member.user_id == user_id for member in team.members)

                if not is_member:
                    found_users.append({
                        'id': user_id,
                        'name': f'Пользователь {user_id}',
                        'username': None
                    })

        # Если это поиск по username
        elif search_query.startswith('@'):
            username = search_query[1:]  # Убираем @
            found_users.append({
                'id': 999999,  # Заглушка ID
                'name': f'Найден по @{username}',
                'username': username
            })

        # Если это текстовый поиск
        else:
            # В реальной реализации здесь был бы поиск по имени/фамилии
            found_users.append({
                'id': 888888,  # Заглушка ID
                'name': f'Результат поиска: {search_query}',
                'username': None
            })

        if not found_users:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Попробовать снова", callback_data=f"add_member_{team_id}")],
                [InlineKeyboardButton(text="❌ Отмена", callback_data=f"team_menu_{team_id}")]
            ])

            await message.answer(
                "😔 <b>Пользователи не найдены</b>\n\n"
                "Попробуйте:\n"
                "• Проверить правильность написания\n"
                "• Использовать точный @username\n"
                "• Убедиться, что пользователь есть в Telegram",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            return

        # Создаем кнопки для найденных пользователей
        buttons = []
        for user in found_users:
            username_text = f"@{user['username']}" if user['username'] else f"ID: {user['id']}"
            buttons.append([InlineKeyboardButton(
                text=f"👤 {user['name']} ({username_text})",
                callback_data=f"select_user_{user['id']}"
            )])

        buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data=f"team_menu_{team_id}")])
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

        await state.set_state(TeamStates.waiting_member_confirm)

        await message.answer(
            f"🔍 <b>Найдено пользователей: {len(found_users)}</b>\n\n"
            "Выберите пользователя для добавления в команду:",
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(f"Error in process_member_search: {e}")
        await message.answer("❌ Ошибка при поиске пользователей")

@teams_router.callback_query(F.data.startswith("select_user_"))
async def confirm_add_member(callback: CallbackQuery, state: FSMContext):
    """Подтверждение добавления участника"""
    try:
        user_id = int(callback.data.split("_")[-1])
        data = await state.get_data()
        team_id = data['team_id']

        team = await db.get_team(team_id)

        # Проверяем, не является ли пользователь уже участником
        is_member = any(member.user_id == user_id for member in team.members)
        if is_member:
            await callback.answer("❌ Этот пользователь уже участник команды")
            return

        # Добавляем участника
        success = await db.add_member_to_team(
            team_id=team_id,
            user_id=user_id,
            username=None,  # В реальной реализации получили бы из поиска
            first_name=f"Участник {user_id}",
            last_name=None
        )

        if success:
            await state.clear()

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="👥 Посмотреть участников", callback_data=f"team_members_{team_id}")],
                [InlineKeyboardButton(text="➕ Добавить еще", callback_data=f"add_member_{team_id}")],
                [InlineKeyboardButton(text="🔙 К команде", callback_data=f"team_menu_{team_id}")]
            ])

            await callback.message.edit_text(
                f"✅ <b>Участник добавлен!</b>\n\n"
                f"👤 <b>Пользователь:</b> {user_id}\n"
                f"🏆 <b>Команда:</b> {team.name}\n"
                f"📅 <b>Добавлен:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
                f"Теперь в команде {len(team.members) + 1} участников.",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            await callback.answer("✅ Участник добавлен!")
        else:
            await callback.answer("❌ Не удалось добавить участника")

    except Exception as e:
        logger.error(f"Error in confirm_add_member: {e}")
        await callback.answer("❌ Произошла ошибка")

# ============== УДАЛЕНИЕ УЧАСТНИКОВ ==============

@teams_router.callback_query(F.data.startswith("remove_member_"))
async def start_remove_member(callback: CallbackQuery):
    """Начать удаление участника"""
    try:
        team_id = int(callback.data.split("_")[-1])
        team = await db.get_team(team_id)

        if not team:
            await callback.answer("❌ Команда не найдена")
            return

        user_role = await db.get_user_role_in_team(callback.from_user.id, team_id)
        if user_role != 'captain':
            await callback.answer("❌ Только капитан может удалять участников")
            return

        # Показываем список участников для удаления (исключая капитана)
        removable_members = [m for m in team.members if m.role != 'captain' and m.is_active]

        if not removable_members:
            await callback.message.edit_text(
                "ℹ️ <b>Нет участников для удаления</b>\n\n"
                "В команде нет участников, которых можно удалить.\n"
                "(Капитана удалить нельзя)",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Назад", callback_data=f"team_members_{team_id}")]
                ]),
                parse_mode="HTML"
            )
            await callback.answer()
            return

        buttons = []
        for member in removable_members:
            role_emoji = get_role_emoji(member.role)
            full_name = member.first_name
            if member.last_name:
                full_name += f" {member.last_name}"

            buttons.append([InlineKeyboardButton(
                text=f"{role_emoji} {full_name}",
                callback_data=f"confirm_remove_{team_id}_{member.user_id}"
            )])

        buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data=f"team_members_{team_id}")])
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

        await callback.message.edit_text(
            f"➖ <b>Удаление участника из "{team.name}"</b>\n\n"
            "Выберите участника для удаления из команды:\n\n"
            "<i>⚠️ Это действие нельзя отменить!</i>",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Error in start_remove_member: {e}")
        await callback.answer("❌ Произошла ошибка")

@teams_router.callback_query(F.data.startswith("confirm_remove_"))
async def confirm_remove_member(callback: CallbackQuery):
    """Подтверждение удаления участника"""
    try:
        parts = callback.data.split("_")
        team_id = int(parts[2])
        user_id_to_remove = int(parts[3])

        team = await db.get_team(team_id)
        member_to_remove = next((m for m in team.members if m.user_id == user_id_to_remove), None)

        if not member_to_remove:
            await callback.answer("❌ Участник не найден")
            return

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🗑 Да, удалить", callback_data=f"final_remove_{team_id}_{user_id_to_remove}")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data=f"remove_member_{team_id}")]
        ])

        full_name = member_to_remove.first_name
        if member_to_remove.last_name:
            full_name += f" {member_to_remove.last_name}"

        await callback.message.edit_text(
            f"⚠️ <b>Подтверждение удаления</b>\n\n"
            f"Вы уверены, что хотите удалить участника?\n\n"
            f"👤 <b>Участник:</b> {full_name}\n"
            f"🏆 <b>Команда:</b> {team.name}\n\n"
            "<i>Это действие нельзя отменить!</i>",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Error in confirm_remove_member: {e}")
        await callback.answer("❌ Произошла ошибка")

@teams_router.callback_query(F.data.startswith("final_remove_"))
async def final_remove_member(callback: CallbackQuery):
    """Финальное удаление участника"""
    try:
        parts = callback.data.split("_")
        team_id = int(parts[2])
        user_id_to_remove = int(parts[3])

        success = await db.remove_member_from_team(
            team_id=team_id,
            user_id=user_id_to_remove,
            removed_by=callback.from_user.id
        )

        if success:
            team = await db.get_team(team_id)

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="👥 К участникам", callback_data=f"team_members_{team_id}")],
                [InlineKeyboardButton(text="🏆 К команде", callback_data=f"team_menu_{team_id}")]
            ])

            await callback.message.edit_text(
                f"✅ <b>Участник удален</b>\n\n"
                f"Участник успешно удален из команды "{team.name}".\n\n"
                f"👥 <b>Участников стало:</b> {len(team.members)}",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            await callback.answer("✅ Участник удален!")
        else:
            await callback.answer("❌ Не удалось удалить участника")

    except Exception as e:
        logger.error(f"Error in final_remove_member: {e}")
        await callback.answer("❌ Произошла ошибка")

# ============== СТАТИСТИКА КОМАНД ==============

@teams_router.callback_query(F.data == "teams_stats")
async def show_teams_stats(callback: CallbackQuery):
    """Показать статистику по всем командам пользователя"""
    try:
        user_teams = await db.get_user_teams(callback.from_user.id)

        if not user_teams:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🆕 Создать команду", callback_data="create_team")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="teams_main")]
            ])

            await callback.message.edit_text(
                "📊 <b>Статистика команд</b>\n\n"
                "У вас пока нет команд для отображения статистики.",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            await callback.answer()
            return

        total_members = 0
        total_captains = 0
        total_assistants = 0
        oldest_team = None
        newest_team = None
        largest_team = None

        stats_text = ""

        for team in user_teams:
            members_count = len(team.members)
            total_members += members_count

            # Подсчет ролей
            for member in team.members:
                if member.role == 'captain':
                    total_captains += 1
                elif member.role == 'assistant':
                    total_assistants += 1

            # Определение самой старой и новой команды
            if not oldest_team or team.created_at < oldest_team.created_at:
                oldest_team = team
            if not newest_team or team.created_at > newest_team.created_at:
                newest_team = team

            # Самая большая команда
            if not largest_team or members_count > len(largest_team.members):
                largest_team = team

            # Добавляем в текст статистики
            user_role = await db.get_user_role_in_team(callback.from_user.id, team.id)
            role_emoji = get_role_emoji(user_role)
            stats_text += f"{role_emoji} <b>{team.name}</b>: {members_count} чел.\n"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👥 Мои команды", callback_data="my_teams")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="teams_main")]
        ])

        await callback.message.edit_text(
            f"📊 <b>Статистика ваших команд</b>\n\n"
            f"🏆 <b>Всего команд:</b> {len(user_teams)}\n"
            f"👥 <b>Всего участников:</b> {total_members}\n"
            f"👑 <b>Вы капитан в:</b> {total_captains} командах\n"
            f"⭐ <b>Вы помощник в:</b> {total_assistants} командах\n\n"
            f"📈 <b>Самая большая команда:</b> {largest_team.name} ({len(largest_team.members)} чел.)\n"
            f"📅 <b>Самая старая:</b> {oldest_team.name} ({oldest_team.created_at.strftime('%d.%m.%Y')})\n"
            f"🆕 <b>Самая новая:</b> {newest_team.name} ({newest_team.created_at.strftime('%d.%m.%Y')})\n\n"
            f"<b>Ваши команды:</b>\n{stats_text}",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Error in show_teams_stats: {e}")
        await callback.answer("❌ Произошла ошибка")

# ============== ОБРАБОТЧИКИ ОТМЕНЫ ==============

@teams_router.callback_query(TeamStates.waiting_team_name, F.data == "teams_main")
@teams_router.callback_query(TeamStates.waiting_team_description, F.data == "teams_main")
@teams_router.callback_query(TeamStates.waiting_member_search, F.data.contains("team_menu_"))
async def cancel_operation(callback: CallbackQuery, state: FSMContext):
    """Отмена текущей операции"""
    await state.clear()

    if callback.data == "teams_main":
        await teams_main_callback(callback)
    elif callback.data.startswith("team_menu_"):
        await show_team_menu(callback)

    await callback.answer("❌ Операция отменена")

print("Создано продолжение модуля teams.py с обработчиками участников")

__all__ = [
    'register_team_handlers',
    'feature_coming_soon'
]


