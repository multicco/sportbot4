# ===== КЛАВИАТУРЫ ТРЕНИРОВОК =====

from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_workout_blocks_keyboard(selected_blocks=None):
    """Клавиатура выбора блоков тренировки"""
    if selected_blocks is None:
        selected_blocks = {}
    
    blocks = {
        'warmup': '🔥 Разминка',
        'nervous_prep': '⚡ Подготовка НС', 
        'main': '💪 Основная часть',
        'cooldown': '🧘 Заминка'
    }
    
    keyboard = InlineKeyboardBuilder()
    
    for block_key, block_name in blocks.items():
        action = "✏️ Изменить" if block_key in selected_blocks else "➕ Добавить"
        keyboard.button(
            text=f"{action} {block_name.split(' ', 1)[1]}", 
            callback_data=f"select_block_{block_key}"
        )
    
    if selected_blocks:
        keyboard.button(text="✅ Завершить создание", callback_data="finish_workout_creation")
    
    keyboard.button(text="❌ Отменить", callback_data="cancel_workout_creation")
    keyboard.adjust(2)
    
    return keyboard.as_markup()

def get_block_description_keyboard():
    """Клавиатура для работы с описанием блока"""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="📝 Добавить описание блока", callback_data="add_block_description")
    keyboard.button(text="⏭️ Сразу к упражнениям", callback_data="skip_block_description")
    keyboard.button(text="🗑️ Пропустить блок", callback_data="skip_entire_block")
    keyboard.button(text="🔙 К выбору блоков", callback_data="back_to_blocks")
    keyboard.adjust(1)
    
    return keyboard.as_markup()

def get_block_exercises_keyboard(has_exercises=False):
    """Клавиатура для добавления упражнений в блок"""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔍 Найти упражнение", callback_data="find_exercise_for_block")
    keyboard.button(text="📂 По категориям", callback_data="browse_categories_for_block")
    
    if has_exercises:
        keyboard.button(text="✅ Завершить блок", callback_data="finish_current_block")
        keyboard.button(text="🗑️ Удалить последнее", callback_data="remove_last_block_exercise")
    else:
        keyboard.button(text="✅ Пустой блок", callback_data="finish_current_block")
    
    keyboard.button(text="🔙 К выбору блоков", callback_data="back_to_blocks")
    keyboard.adjust(2)
    
    return keyboard.as_markup()

def get_exercise_config_keyboard():
    """Клавиатура настройки упражнения"""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🏋️ Простая настройка", callback_data="simple_block_config")
    keyboard.button(text="📊 С процентами от 1ПМ", callback_data="advanced_block_config")
    keyboard.button(text="🔙 Назад к выбору", callback_data="back_to_block_exercises")
    keyboard.adjust(1)
    
    return keyboard.as_markup()

def get_workout_creation_success_keyboard():
    """Клавиатура после успешного создания тренировки"""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🏋️ Мои тренировки", callback_data="my_workouts")
    keyboard.button(text="➕ Создать еще", callback_data="create_workout")
    keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
    keyboard.adjust(2)
    
    return keyboard.as_markup()

def get_workout_description_keyboard():
    """Клавиатура для описания тренировки"""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="⏭️ Пропустить описание", callback_data="skip_description")
    
    return keyboard.as_markup()

def get_block_categories_keyboard(categories):
    """Клавиатура категорий для блока"""
    keyboard = InlineKeyboardBuilder()
    
    for cat in categories:
        keyboard.button(
            text=f"📂 {cat['category']}", 
            callback_data=f"block_cat_{cat['category']}"
        )
    
    keyboard.button(text="🔙 К упражнениям блока", callback_data="back_to_block_exercises")
    keyboard.adjust(2)
    
    return keyboard.as_markup()

def get_block_exercise_list_keyboard(exercises):
    """Клавиатура со списком упражнений для блока"""
    keyboard = InlineKeyboardBuilder()
    
    for ex in exercises:
        keyboard.button(
            text=f"{ex['name']} ({ex['muscle_group']})", 
            callback_data=f"add_block_ex_{ex['id']}"
        )
    
    keyboard.button(text="🔙 К категориям", callback_data="browse_categories_for_block")
    keyboard.adjust(1)
    
    return keyboard.as_markup()

def get_advanced_config_no_1rm_keyboard(exercise_id):
    """Клавиатура при отсутствии 1ПМ для продвинутой настройки"""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="💪 Пройти тест 1ПМ", callback_data=f"1rm_{exercise_id}")
    keyboard.button(text="🔙 Простая настройка", callback_data="simple_block_config")
    
    return keyboard.as_markup()

def get_workout_list_keyboard(workouts):
    """Клавиатура со списком тренировок"""
    keyboard = InlineKeyboardBuilder()
    
    for workout in workouts:
        keyboard.button(
            text=f"🏋️ {workout['name']}", 
            callback_data=f"select_workout_{workout['id']}"
        )
    
    keyboard.button(text="🔙 К тренировкам", callback_data="workouts_menu")
    keyboard.adjust(1)
    
    return keyboard.as_markup()

def get_workout_details_keyboard(workout_id, is_owner=False):
    """Клавиатура для просмотра деталей тренировки"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.button(text="▶️ Начать тренировку", callback_data=f"start_workout_{workout_id}")
    keyboard.button(text="📋 Детали", callback_data=f"workout_details_{workout_id}")
    
    if is_owner:
        keyboard.button(text="✏️ Редактировать", callback_data=f"edit_workout_{workout_id}")
        keyboard.button(text="🗑️ Удалить", callback_data=f"delete_workout_{workout_id}")
    else:
        keyboard.button(text="📝 Копировать", callback_data=f"copy_workout_{workout_id}")
    
    keyboard.button(text="🔙 Назад", callback_data="my_workouts")
    keyboard.adjust(2)
    
    return keyboard.as_markup()

def get_workout_execution_keyboard(current_exercise_index, total_exercises):
    """Клавиатура для выполнения тренировки"""
    keyboard = InlineKeyboardBuilder()
    
    if current_exercise_index > 0:
        keyboard.button(text="⬅️ Предыдущее", callback_data="prev_exercise")
    
    keyboard.button(text="✅ Завершить подход", callback_data="complete_set")
    
    if current_exercise_index < total_exercises - 1:
        keyboard.button(text="➡️ Следующее", callback_data="next_exercise")
    
    keyboard.button(text="⏸️ Пауза", callback_data="pause_workout")
    keyboard.button(text="🏁 Завершить тренировку", callback_data="finish_workout")
    
    keyboard.adjust(2)
    
    return keyboard.as_markup()

def get_rest_timer_keyboard(rest_seconds):
    """Клавиатура таймера отдыха"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.button(text="⏩ Пропустить отдых", callback_data="skip_rest")
    keyboard.button(text="➕ +30 сек", callback_data="add_rest_30")
    keyboard.button(text="➖ -30 сек", callback_data="sub_rest_30")
    keyboard.button(text="⏹️ Остановить", callback_data="stop_rest")
    
    keyboard.adjust(2)
    
    return keyboard.as_markup()

def get_rpe_rating_keyboard():
    """Клавиатура оценки RPE (1-10)"""
    keyboard = InlineKeyboardBuilder()
    
    for i in range(1, 11):
        keyboard.button(text=f"{i}", callback_data=f"rpe_{i}")
    
    keyboard.button(text="❓ Что такое RPE?", callback_data="rpe_help")
    keyboard.adjust(5)
    
    return keyboard.as_markup()

def get_workout_finished_keyboard(workout_id):
    """Клавиатура после завершения тренировки"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.button(text="📊 Статистика тренировки", callback_data=f"workout_stats_{workout_id}")
    keyboard.button(text="🔄 Повторить тренировку", callback_data=f"repeat_workout_{workout_id}")
    keyboard.button(text="📝 Оставить отзыв", callback_data=f"rate_workout_{workout_id}")
    keyboard.button(text="🏠 Главное меню", callback_data="main_menu")
    
    keyboard.adjust(1)
    
    return keyboard.as_markup()

__all__ = [
    'get_workout_blocks_keyboard',
    'get_block_description_keyboard',
    'get_block_exercises_keyboard',
    'get_exercise_config_keyboard',
    'get_workout_creation_success_keyboard',
    'get_workout_description_keyboard',
    'get_block_categories_keyboard',
    'get_block_exercise_list_keyboard',
    'get_advanced_config_no_1rm_keyboard',
    'get_workout_list_keyboard',
    'get_workout_details_keyboard',
    'get_workout_execution_keyboard',
    'get_rest_timer_keyboard',
    'get_rpe_rating_keyboard',
    'get_workout_finished_keyboard'
]