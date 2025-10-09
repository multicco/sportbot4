# ===== ОБНОВЛЕННОЕ ГЛАВНОЕ МЕНЮ С УНИВЕРСАЛЬНЫМИ ТЕСТАМИ =====

from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_main_menu_keyboard():
    """Клавиатура главного меню"""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🏋️ Тренировки", callback_data="workouts_menu")
    keyboard.button(text="📊 Тесты", callback_data="tests_menu")  # ← ИЗМЕНЕНО!
    keyboard.button(text="🔍 Найти упражнение", callback_data="search_exercise")
    keyboard.button(text="👥 Команды", callback_data="teams_menu")
    keyboard.adjust(2)
    
    return keyboard.as_markup()

def get_workouts_menu_keyboard():
    """Клавиатура меню тренировок"""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🏋️ Мои тренировки", callback_data="my_workouts")
    keyboard.button(text="🔍 Найти тренировку", callback_data="find_workout")
    keyboard.button(text="➕ Создать тренировку", callback_data="create_workout")
    keyboard.button(text="🔙 Главное меню", callback_data="main_menu")
    keyboard.adjust(1)
    
    return keyboard.as_markup()

def get_tests_menu_keyboard():  # ← НОВОЕ МЕНЮ!
    """Клавиатура меню универсальных тестов"""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="📊 Мои тесты", callback_data="my_tests")
    keyboard.button(text="🔬 Новый тест", callback_data="new_test_menu") 
    keyboard.button(text="📈 Прогресс", callback_data="test_progress")
    keyboard.button(text="🏆 Рекорды", callback_data="test_records")
    keyboard.button(text="🔙 Главное меню", callback_data="main_menu")
    keyboard.adjust(2)
    
    return keyboard.as_markup()

def get_new_test_type_menu_keyboard():  # ← МЕНЮ ВЫБОРА ТИПА ТЕСТА!
    """Клавиатура выбора типа теста"""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🏋️ Силовые тесты", callback_data="test_type_strength")
    keyboard.button(text="⏱️ Тесты выносливости", callback_data="test_type_endurance") 
    keyboard.button(text="🏃 Скоростные тесты", callback_data="test_type_speed")
    keyboard.button(text="🔢 Количественные тесты", callback_data="test_type_quantity")
    keyboard.button(text="🔙 К тестам", callback_data="tests_menu")
    keyboard.adjust(2)
    
    return keyboard.as_markup()

def get_teams_menu_keyboard(user_role):
    """Клавиатура меню команд (зависит от роли пользователя)"""
    keyboard = InlineKeyboardBuilder()
    
    if user_role in ['coach', 'admin']:
        keyboard.button(text="🏗️ Создать команду", callback_data="create_team")
        keyboard.button(text="👤 Добавить подопечного", callback_data="add_student")
        keyboard.button(text="🏆 Мои команды", callback_data="my_teams")
        keyboard.button(text="👥 Мои подопечные", callback_data="my_students")
    else:
        keyboard.button(text="🔗 Присоединиться к команде", callback_data="join_team")
        keyboard.button(text="👨‍🏫 Найти тренера", callback_data="find_coach")
        keyboard.button(text="👥 Моя команда", callback_data="my_team")
    
    keyboard.button(text="🔙 Главное меню", callback_data="main_menu")
    keyboard.adjust(1)
    
    return keyboard.as_markup()

def get_coming_soon_keyboard():
    """Клавиатура для функций в разработке"""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔙 Назад", callback_data="main_menu")
    
    return keyboard.as_markup()

__all__ = [
    'get_main_menu_keyboard',
    'get_workouts_menu_keyboard', 
    'get_tests_menu_keyboard',      # ← НОВОЕ!
    'get_new_test_type_menu_keyboard', # ← НОВОЕ!
    'get_teams_menu_keyboard',
    'get_coming_soon_keyboard'
]