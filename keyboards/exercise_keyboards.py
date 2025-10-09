# ===== КЛАВИАТУРЫ УПРАЖНЕНИЙ =====

from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_exercise_search_keyboard(user_role):
    """Клавиатура поиска упражнений"""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔍 Поиск по названию", callback_data="search_by_name")
    keyboard.button(text="📂 По категориям", callback_data="search_by_category")
    keyboard.button(text="💪 По группам мышц", callback_data="search_by_muscle")
    
    # КНОПКА ДОБАВЛЕНИЯ УПРАЖНЕНИЙ ТОЛЬКО ДЛЯ ТРЕНЕРОВ И АДМИНОВ
    if user_role in ['coach', 'admin']:
        keyboard.button(text="➕ Добавить упражнение", callback_data="add_new_exercise")
    
    keyboard.button(text="🔙 Главное меню", callback_data="main_menu")
    keyboard.adjust(1)
    
    return keyboard.as_markup()

def get_categories_keyboard(categories):
    """Клавиатура категорий упражнений"""
    keyboard = InlineKeyboardBuilder()
    
    for cat in categories:
        keyboard.button(text=f"📂 {cat['category']}", callback_data=f"cat_{cat['category']}")
    
    keyboard.button(text="🔙 Назад", callback_data="search_exercise")
    keyboard.adjust(2)
    
    return keyboard.as_markup()

def get_exercise_creation_keyboard():
    """Клавиатура выбора способа создания упражнения"""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="📂 Выбрать категорию", callback_data="select_existing_category")
    keyboard.button(text="📝 Новая категория", callback_data="create_new_category")
    keyboard.button(text="❌ Отменить", callback_data="cancel_exercise_creation")
    keyboard.adjust(1)
    
    return keyboard.as_markup()

def get_equipment_keyboard():
    """Клавиатура выбора оборудования"""
    equipment_options = [
        "Собственный вес", "Штанга", "Гантели", "Тренажер",
        "Турник", "Брусья", "Скакалка", "Фитбол",
        "Резинки", "Гири", "Нет", "Другое"
    ]
    
    keyboard = InlineKeyboardBuilder()
    for eq in equipment_options:
        keyboard.button(text=f"🔧 {eq}", callback_data=f"choose_eq_{eq}")
    
    keyboard.button(text="❌ Отменить", callback_data="cancel_exercise_creation")
    keyboard.adjust(3)
    
    return keyboard.as_markup()

def get_difficulty_keyboard():
    """Клавиатура выбора уровня сложности"""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🟢 Новичок", callback_data="diff_beginner")
    keyboard.button(text="🟡 Средний", callback_data="diff_intermediate") 
    keyboard.button(text="🔴 Продвинутый", callback_data="diff_advanced")
    keyboard.button(text="❌ Отменить", callback_data="cancel_exercise_creation")
    keyboard.adjust(1)
    
    return keyboard.as_markup()

def get_category_selection_keyboard(categories):
    """Клавиатура выбора категории при создании"""
    keyboard = InlineKeyboardBuilder()
    
    for cat in categories:
        keyboard.button(
            text=f"📂 {cat['category']}", 
            callback_data=f"choose_cat_{cat['category']}"
        )
    
    keyboard.button(text="📝 Создать новую категорию", callback_data="create_new_category")
    keyboard.button(text="❌ Отменить", callback_data="cancel_exercise_creation")
    keyboard.adjust(2)
    
    return keyboard.as_markup()

def get_muscle_group_selection_keyboard(muscle_groups):
    """Клавиатура выбора группы мышц"""
    keyboard = InlineKeyboardBuilder()
    
    for mg in muscle_groups:
        keyboard.button(
            text=f"💪 {mg['muscle_group']}", 
            callback_data=f"choose_mg_{mg['muscle_group']}"
        )
    
    keyboard.button(text="📝 Создать новую группу", callback_data="create_new_muscle_group")
    keyboard.button(text="❌ Отменить", callback_data="cancel_exercise_creation")
    keyboard.adjust(3)
    
    return keyboard.as_markup()

def get_exercise_list_keyboard(exercises, context="search"):
    """Клавиатура со списком упражнений"""
    keyboard = InlineKeyboardBuilder()
    
    for ex in exercises:
        keyboard.button(
            text=f"{ex['name']} ({ex['muscle_group']})", 
            callback_data=f"select_ex_{ex['id']}"
        )
    
    if context == "search":
        keyboard.button(text="🔙 К поиску", callback_data="search_exercise")
    elif context == "category":
        keyboard.button(text="🔙 К категориям", callback_data="search_by_category")
    
    keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
    keyboard.adjust(1)
    
    return keyboard.as_markup()

def get_exercise_info_keyboard():
    """Клавиатура для информации об упражнении"""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔙 К поиску", callback_data="search_exercise")
    keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
    keyboard.adjust(2)
    
    return keyboard.as_markup()

def get_exercise_creation_success_keyboard():
    """Клавиатура после успешного создания упражнения"""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="➕ Создать еще", callback_data="add_new_exercise")
    keyboard.button(text="🔍 К поиску", callback_data="search_exercise")
    keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
    keyboard.adjust(2)
    
    return keyboard.as_markup()

def get_search_results_keyboard():
    """Клавиатура для результатов поиска"""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔍 Новый поиск", callback_data="search_by_name")
    keyboard.button(text="🔙 К поиску", callback_data="search_exercise")
    keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
    keyboard.adjust(1)
    
    return keyboard.as_markup()

__all__ = [
    'get_exercise_search_keyboard',
    'get_categories_keyboard', 
    'get_exercise_creation_keyboard',
    'get_equipment_keyboard',
    'get_difficulty_keyboard',
    'get_category_selection_keyboard',
    'get_muscle_group_selection_keyboard',
    'get_exercise_list_keyboard',
    'get_exercise_info_keyboard',
    'get_exercise_creation_success_keyboard',
    'get_search_results_keyboard'
]