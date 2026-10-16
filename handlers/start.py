# ===== ОБНОВЛЕННЫЙ START.PY С ПОДДЕРЖКОЙ УНИВЕРСАЛЬНЫХ ТЕСТОВ =====
import logging
logger = logging.getLogger(__name__)
from aiogram import F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from database import db_manager
from aiogram.utils.keyboard import InlineKeyboardBuilder
from keyboards.main_keyboards_old import (
    get_main_menu_keyboard, get_workouts_menu_keyboard, 
    get_tests_menu_keyboard, get_teams_menu_keyboard  # ← ОБНОВЛЕНО!
)

def register_start_handlers(dp):
    """Регистрация обработчиков команды /start и меню"""
    
    dp.message.register(cmd_start, Command("start"))
    dp.callback_query.register(back_to_main_menu, F.data == "main_menu")
    dp.callback_query.register(workouts_menu, F.data == "workouts_menu")
    dp.callback_query.register(tests_menu_handler, F.data == "tests_menu")  # ← ОБНОВЛЕНО!
    dp.callback_query.register(teams_menu, F.data == "teams_menu")

async def cmd_start(message: Message):
    """Обработка команды /start"""
    user = message.from_user
    
    # Проверяем, есть ли пользователь в БД
    existing_user = await db_manager.get_user_by_telegram_id(user.id)
    
    if not existing_user:
        # Создаем нового пользователя
        await db_manager.create_user(
            telegram_id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            username=user.username
        )
        welcome_text = f"👋 **Добро пожаловать, {user.first_name}!**\n\n"
        welcome_text += f"Вы успешно зарегистрированы в спортивном боте.\n"
    else:
        welcome_text = f"👋 **С возвращением, {user.first_name}!**\n\n"
    
    welcome_text += f"🏋️ **Возможности бота:**\n"
    welcome_text += f"• 🔍 **Детальный поиск упражнений** с кликабельными результатами\n"
    welcome_text += f"• 📊 **Универсальная система тестов** - силовые, скоростные, выносливость\n"
    welcome_text += f"• 🏋️ **Блочные тренировки** с автоматическим расчетом нагрузки\n"
    welcome_text += f"• 🎯 **Проценты от личных рекордов** в тренировках\n"
    welcome_text += f"• 👥 **Командные тренировки** и система наставничества\n"
    welcome_text += f"• 📈 **Подробная статистика** прогресса\n\n"
    welcome_text += f"Выберите действие:"
    
    keyboard = get_main_menu_keyboard()
    
    await message.answer(
        welcome_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

async def back_to_main_menu(callback: CallbackQuery):
    """Возврат в главное меню"""
    user = callback.from_user
    
    text = f"🏠 **Главное меню**\n\n"
    text += f"Добро пожаловать, {user.first_name}!\n\n"
    text += f"🏋️ **Обновления системы:**\n"
    text += f"• 🔍 **Новый поиск упражнений** - кликабельные результаты с деталями\n"
    text += f"• 📊 **Универсальные тесты** - силовые, выносливость, скорость, количество\n"
    text += f"• 🎯 **Проценты от тестов** - используйте личные рекорды в тренировках\n"
    text += f"• 🏋️ **Блочная структура** тренировок с 4 фазами\n\n"
    text += f"**🆕 Что нового:**\n"
    text += f"• Любое упражнение может быть тестом\n"
    text += f"• Планка на 60 сек → 120% = 72 сек в тренировке\n"
    text += f"• Жим 100кг → 80% = 80кг в тренировке\n\n"
    text += f"Выберите действие:"
    
    keyboard = get_main_menu_keyboard()
    
    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

async def workouts_menu(callback: CallbackQuery):
    """Меню тренировок — с правильными кнопками в зависимости от роли"""
    try:
        user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
        role = user.get('role', 'player') if user else 'player'

        kb = InlineKeyboardBuilder()

        # Общие кнопки
        kb.button(text="Найти тренировку", callback_data="find_workout")

        if role in ['admin', 'trainer', 'coach']:
            kb.button(text="Мои шаблоны", callback_data="my_templates")        # ← Правильно для тренера
            kb.button(text="Создать тренировку", callback_data="create_workout")
            kb.button(text="Статистика", callback_data="workout_statistics")
        else:
            kb.button(text="Мои тренировки", callback_data="my_workouts")      # ← Правильно для игрока
            kb.button(text="Мои достижения", callback_data="my_achievements")

        kb.button(text="Главное меню", callback_data="main_menu")
        kb.adjust(1)

        text = "<b>Меню тренировок</b>\n\n"
        text += "Новые возможности:\n"
        text += "• Блочная структура: разминка → подготовка НС → основная → заминка\n"
        text += "• Проценты от тестов: используйте личные рекорды в упражнениях\n"
        text += "• Умные расчеты: автоматический подбор нагрузки\n"
        text += "• Интеграция с тестами: все ваши рекорды учитываются\n\n"
        text += "Выберите действие:"

        await callback.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="HTML")
        await callback.answer()

    except Exception as e:
        logger.exception("Ошибка в workouts_menu")
        await callback.answer("Ошибка", show_alert=True)

async def tests_menu_handler(callback: CallbackQuery):  # ← НОВАЯ ФУНКЦИЯ!
    """Обработчик меню тестов - перенаправляет в модуль тестов"""
    # Импортируем здесь, чтобы избежать циклических импортов
    from handlers.tests import tests_menu
    await tests_menu(callback)

async def teams_menu(callback: CallbackQuery):
    """Меню команд"""
    # ФАТАЛЬНОЕ ИСПРАВЛЕНИЕ: раньше при отсутствии пользователя в БД
    # user был None и user['role'] вызывал TypeError — кнопка «Команды» падала.
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)

    if not user:
        # Пользователя ещё нет в БД — регистрируем его автоматически
        await db_manager.create_user(
            telegram_id=callback.from_user.id,
            first_name=callback.from_user.first_name,
            last_name=callback.from_user.last_name,
            username=callback.from_user.username
        )
        user = await db_manager.get_user_by_telegram_id(callback.from_user.id) or {}

    role = (user.get('role') if isinstance(user, dict) else getattr(user, 'role', None)) or 'player'

    keyboard = get_teams_menu_keyboard(role)

    role_text = "тренера" if role in ['coach', 'admin'] else "игрока"
    
    await callback.message.edit_text(
        f"👥 **Командная система**\n\n"
        f"**Ваша роль:** {role_text.title()}\n\n"
        f"🎯 **Возможности:**\n"
        f"• 🏗️ **Командные тренировки** с общими целями\n"
        f"• 👨‍🏫 **Индивидуальное тренерство** и наставничество\n"
        f"• 📊 **Мониторинг прогресса** учеников в реальном времени\n"
        f"• 🔗 **Система кодов приглашений** для быстрого подключения\n"
        f"• 📈 **Сравнительная статистика** и мотивация\n\n"
        f"Выберите действие:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

__all__ = ['register_start_handlers']