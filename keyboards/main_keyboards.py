# ===== ОБНОВЛЕННЫЕ КЛАВИАТУРЫ С БАТАРЕЯМИ ТЕСТОВ =====

from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_main_menu_keyboard():
    """Клавиатура главного меню"""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🏋️ Тренировки", callback_data="workouts_menu")
    keyboard.button(text="📊 Тесты", callback_data="tests_menu")
    keyboard.button(text="🔍 Найти упражнение", callback_data="search_exercise")
    keyboard.button(text="👥 Команды", callback_data="teams_menu")
    keyboard.adjust(2)
    
    return keyboard.as_markup()

def get_tests_menu_keyboard(user_role):
    """Клавиатура меню тестов с учетом роли пользователя"""
    keyboard = InlineKeyboardBuilder()
    
    if user_role in ['coach', 'admin']:
        # Меню для тренеров
        keyboard.button(text="📋 Батареи тестов", callback_data="coach_batteries")  # ← НОВОЕ!
        keyboard.button(text="📊 Индивидуальные тесты", callback_data="individual_tests_menu")
        keyboard.button(text="📈 Аналитика команды", callback_data="team_analytics")
        keyboard.button(text="🌐 Публичные тесты", callback_data="public_test_sets")
    else:
        # Меню для игроков
        keyboard.button(text="📋 Мои батареи тестов", callback_data="player_batteries")  # ← НОВОЕ!
        keyboard.button(text="🔬 Индивидуальные тесты", callback_data="individual_tests_menu")
        keyboard.button(text="🏆 Мои достижения", callback_data="my_achievements")
        keyboard.button(text="🌐 Публичные тесты", callback_data="public_test_sets")
    
    keyboard.button(text="🔙 Главное меню", callback_data="main_menu")
    keyboard.adjust(2)
    
    return keyboard.as_markup()

def get_coach_batteries_keyboard():
    """Клавиатура для управления батареями тестов (тренеры)"""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="📋 Мои батареи", callback_data="my_batteries")
    keyboard.button(text="➕ Создать батарею", callback_data="create_battery")
    keyboard.button(text="📊 Аналитика команды", callback_data="team_analytics")
    keyboard.button(text="🔙 К тестам", callback_data="tests_menu")
    keyboard.adjust(2)
    
    return keyboard.as_markup()

def get_player_batteries_keyboard():
    """Клавиатура для батарей тестов (игроки)"""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="📋 Мои батареи", callback_data="my_assigned_batteries")
    keyboard.button(text="🔗 Присоединиться к батарее", callback_data="join_battery")
    keyboard.button(text="📈 Мои результаты", callback_data="my_battery_results")
    keyboard.button(text="🔙 К тестам", callback_data="tests_menu")
    keyboard.adjust(2)
    
    return keyboard.as_markup()

def get_battery_management_keyboard(battery_id: int):
    """Клавиатура управления конкретной батареей"""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔧 Редактировать", callback_data=f"edit_battery_{battery_id}")
    keyboard.button(text="📤 Назначить участникам", callback_data=f"assign_battery_{battery_id}")
    keyboard.button(text="📊 Результаты", callback_data=f"battery_results_{battery_id}")
    keyboard.button(text="📋 Мои батареи", callback_data="my_batteries")
    keyboard.adjust(1)
    
    return keyboard.as_markup()

def get_battery_edit_exercises_keyboard():
    """Клавиатура для добавления упражнений в батарею"""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔍 Поиск по названию", callback_data="search_for_battery")
    keyboard.button(text="📂 По категориям", callback_data="browse_cat_for_battery")
    keyboard.button(text="💪 По группам мышц", callback_data="browse_muscle_for_battery")
    keyboard.button(text="🔙 К редактированию", callback_data="back_to_edit")
    keyboard.adjust(1)
    
    return keyboard.as_markup()

# ===== ОСТАЛЬНЫЕ КЛАВИАТУРЫ БЕЗ ИЗМЕНЕНИЙ =====

def get_workouts_menu_keyboard():
    """Клавиатура меню тренировок"""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🏋️ Мои тренировки", callback_data="my_workouts")
    keyboard.button(text="🔍 Найти тренировку", callback_data="find_workout")
    keyboard.button(text="➕ Создать тренировку", callback_data="create_workout")
    keyboard.button(text="🔙 Главное меню", callback_data="main_menu")
    keyboard.adjust(1)
    
    return keyboard.as_markup()

def get_individual_tests_menu_keyboard():
    """Клавиатура для индивидуальных тестов"""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="📊 Мои тесты", callback_data="my_tests")
    keyboard.button(text="🔬 Новый тест", callback_data="new_test_menu") 
    keyboard.button(text="📈 Прогресс", callback_data="test_progress")
    keyboard.button(text="🏆 Рекорды", callback_data="test_records")
    keyboard.button(text="🔙 К тестам", callback_data="tests_menu")
    keyboard.adjust(2)
    
    return keyboard.as_markup()

def get_new_test_type_menu_keyboard():
    """Клавиатура выбора типа теста"""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🏋️ Силовые тесты", callback_data="test_type_strength")
    keyboard.button(text="⏱️ Тесты выносливости", callback_data="test_type_endurance") 
    keyboard.button(text="🏃 Скоростные тесты", callback_data="test_type_speed")
    keyboard.button(text="🔢 Количественные тесты", callback_data="test_type_quantity")
    keyboard.button(text="🔙 К индивидуальным тестам", callback_data="individual_tests_menu")
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
    # Основные меню
    'get_main_menu_keyboard',
    'get_workouts_menu_keyboard', 
    'get_tests_menu_keyboard',
    'get_individual_tests_menu_keyboard',
    'get_new_test_type_menu_keyboard',
    'get_teams_menu_keyboard',
    'get_coming_soon_keyboard',
    
    # Клавиатуры батарей тестов  ← НОВЫЕ!
    'get_coach_batteries_keyboard',
    'get_player_batteries_keyboard', 
    'get_battery_management_keyboard',
    'get_battery_edit_exercises_keyboard',
]