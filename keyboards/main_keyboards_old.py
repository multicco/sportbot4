# ===== ОБНОВЛЕННОЕ ГЛАВНОЕ МЕНЮ С КОМАНДНОЙ СИСТЕМОЙ ТЕСТИРОВАНИЯ =====

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

def get_workouts_menu_keyboard():
    """Клавиатура меню тренировок"""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🏋️ Мои тренировки", callback_data="my_workouts")
    keyboard.button(text="🔍 Найти тренировку", callback_data="find_workout")
    keyboard.button(text="➕ Создать тренировку", callback_data="create_workout")
    keyboard.button(text="🔙 Главное меню", callback_data="main_menu")
    keyboard.adjust(1)
    
    return keyboard.as_markup()

def get_tests_menu_keyboard(user_role):  # ← ОБНОВЛЕНО!
    """Клавиатура меню тестов с учетом роли пользователя"""
    keyboard = InlineKeyboardBuilder()
    
    if user_role in ['coach', 'admin']:
        # Меню для тренеров
        keyboard.button(text="👨‍🏫 Мои наборы тестов", callback_data="coach_test_sets")
        keyboard.button(text="📊 Индивидуальные тесты", callback_data="individual_tests_menu")
        keyboard.button(text="📈 Аналитика команды", callback_data="team_analytics")
        keyboard.button(text="🌐 Публичные наборы", callback_data="public_test_sets")
    else:
        # Меню для игроков
        keyboard.button(text="📊 Мои наборы тестов", callback_data="player_test_sets")
        keyboard.button(text="🔬 Индивидуальные тесты", callback_data="individual_tests_menu")
        keyboard.button(text="🏆 Мои достижения", callback_data="my_achievements")
        keyboard.button(text="🌐 Публичные наборы", callback_data="public_test_sets")
    
    keyboard.button(text="🔙 Главное меню", callback_data="main_menu")
    keyboard.adjust(2)
    
    return keyboard.as_markup()

def get_individual_tests_menu_keyboard():  # ← НОВОЕ МЕНЮ!
    """Клавиатура для индивидуальных тестов (старая система)"""
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
        keyboard.button(text="👥 Мои подопечные", callback_data="my_trainees")
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

# ===== НОВЫЕ КЛАВИАТУРЫ ДЛЯ КОМАНДНЫХ ТЕСТОВ =====

def get_coach_test_sets_keyboard():
    """Клавиатура для управления наборами тестов (тренеры)"""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="📊 Мои наборы", callback_data="my_test_sets")
    keyboard.button(text="➕ Создать набор", callback_data="create_test_set")
    keyboard.button(text="📈 Аналитика", callback_data="coach_test_analytics")
    keyboard.button(text="🌐 Публичные наборы", callback_data="browse_public_sets")
    keyboard.button(text="🔙 К тестам", callback_data="tests_menu")
    keyboard.adjust(2)
    
    return keyboard.as_markup()

def get_player_test_sets_keyboard():
    """Клавиатура для участия в тестах (игроки)"""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="📊 Мои наборы", callback_data="my_assigned_sets")
    keyboard.button(text="🔗 Присоединиться", callback_data="join_test_set")
    keyboard.button(text="🌐 Публичные наборы", callback_data="browse_public_sets")
    keyboard.button(text="📈 Мои результаты", callback_data="my_all_test_results")
    keyboard.button(text="🔙 К тестам", callback_data="tests_menu")
    keyboard.adjust(2)
    
    return keyboard.as_markup()

def get_test_set_visibility_keyboard():
    """Клавиатура выбора видимости набора тестов"""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔒 Приватный (по коду)", callback_data="visibility_private")
    keyboard.button(text="🌐 Публичный (для всех)", callback_data="visibility_public")
    keyboard.button(text="❌ Отменить", callback_data="cancel_test_set_creation")
    keyboard.adjust(1)
    
    return keyboard.as_markup()

def get_test_set_exercise_search_keyboard():
    """Клавиатура поиска упражнений для набора тестов"""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔍 Поиск по названию", callback_data="search_exercise_for_set")
    keyboard.button(text="📂 По категориям", callback_data="browse_categories_for_set")
    keyboard.button(text="🏋️ Силовые упражнения", callback_data="test_set_cat_Силовые")
    keyboard.button(text="⏱️ На выносливость", callback_data="test_set_cat_Функциональные")
    keyboard.button(text="🏃 Кардио упражнения", callback_data="test_set_cat_Кардио")
    keyboard.button(text="🔙 К созданию набора", callback_data="back_to_test_set_creation")
    keyboard.adjust(2)
    
    return keyboard.as_markup()

def get_test_exercise_config_keyboard():
    """Клавиатура настройки упражнения в наборе тестов"""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="✅ Обязательный тест", callback_data="required_true")
    keyboard.button(text="💡 Рекомендуемый тест", callback_data="required_false")
    keyboard.button(text="🔙 К выбору упражнения", callback_data="add_exercise_to_test_set")
    keyboard.adjust(2)
    
    return keyboard.as_markup()

def get_test_set_management_keyboard(test_set_id: int):
    """Клавиатура управления конкретным набором тестов"""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="📊 Результаты участников", callback_data=f"results_{test_set_id}")
    keyboard.button(text="⚙️ Редактировать", callback_data=f"edit_set_{test_set_id}")
    keyboard.button(text="👥 Участники", callback_data=f"participants_{test_set_id}")
    keyboard.button(text="📋 Экспорт данных", callback_data=f"export_{test_set_id}")
    keyboard.button(text="🔙 Мои наборы", callback_data="my_test_sets")
    keyboard.adjust(2)
    
    return keyboard.as_markup()

def get_public_test_sets_keyboard():
    """Клавиатура для просмотра публичных наборов тестов"""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔥 Популярные", callback_data="popular_test_sets")
    keyboard.button(text="🆕 Новые", callback_data="recent_test_sets")
    keyboard.button(text="🏋️ Силовые тесты", callback_data="strength_test_sets")
    keyboard.button(text="🏃 Кардио тесты", callback_data="cardio_test_sets")
    keyboard.button(text="⏱️ Выносливость", callback_data="endurance_test_sets")
    keyboard.button(text="🔍 Поиск", callback_data="search_public_sets")
    keyboard.button(text="🔙 Назад", callback_data="tests_menu")
    keyboard.adjust(2)
    
    return keyboard.as_markup()

__all__ = [
    # Основные меню
    'get_main_menu_keyboard',
    'get_workouts_menu_keyboard', 
    'get_tests_menu_keyboard',
    'get_individual_tests_menu_keyboard',  # ← НОВОЕ!
    'get_new_test_type_menu_keyboard',
    'get_teams_menu_keyboard',
    'get_coming_soon_keyboard',
    
    # Клавиатуры командных тестов
    'get_coach_test_sets_keyboard',
    'get_player_test_sets_keyboard', 
    'get_test_set_visibility_keyboard',
    'get_test_set_exercise_search_keyboard',
    'get_test_exercise_config_keyboard',
    'get_test_set_management_keyboard',
    'get_public_test_sets_keyboard'
]