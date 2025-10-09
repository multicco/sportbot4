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

__all__ = [
    'register_team_handlers',
    'feature_coming_soon'
]