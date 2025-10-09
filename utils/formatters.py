# ===== ОБНОВЛЕННЫЕ ФОРМАТТЕРЫ С ПОДДЕРЖКОЙ УНИВЕРСАЛЬНЫХ ТЕСТОВ =====

def format_workout_summary(workout_data):
    """Форматирование краткой информации о тренировке"""
    name = workout_data.get('name', 'Тренировка')
    description = workout_data.get('description', '')
    exercises_count = workout_data.get('exercises_count', 0)
    unique_id = workout_data.get('unique_id', 'WKT-UNKNOWN')
    
    text = f"🏋️ **{name}**\n"
    text += f"🆔 **Код:** `{unique_id}`\n"
    text += f"📋 **Упражнений:** {exercises_count}\n"
    
    if description:
        text += f"📝 **Описание:** {description[:100]}{'...' if len(description) > 100 else ''}\n"
    
    return text

def format_exercise_info(exercise_data):
    """Форматирование детальной информации об упражнении"""
    name = exercise_data.get('name', 'Упражнение')
    category = exercise_data.get('category', 'Неизвестно')
    muscle_group = exercise_data.get('muscle_group', 'Неизвестно')
    equipment = exercise_data.get('equipment', 'Неизвестно')
    difficulty = exercise_data.get('difficulty_level', 'Неизвестно')
    description = exercise_data.get('description', '')
    instructions = exercise_data.get('instructions', '')
    test_type = exercise_data.get('test_type', 'none')
    measurement_unit = exercise_data.get('measurement_unit', '')
    
    text = f"💪 **{name}**\n\n"
    text += f"📂 **Категория:** {category}\n"
    text += f"🎯 **Группа мышц:** {muscle_group}\n"
    text += f"🔧 **Оборудование:** {equipment}\n"
    text += f"⭐ **Сложность:** {format_difficulty_level(difficulty)}\n"
    
    # Добавляем информацию о тестировании
    if test_type != 'none':
        test_type_names = {
            'strength': '🏋️ Силовой тест',
            'endurance': '⏱️ Тест выносливости',
            'speed': '🏃 Скоростной тест', 
            'quantity': '🔢 Количественный тест'
        }
        text += f"🔬 **Тестирование:** {test_type_names.get(test_type, 'Тест')}\n"
        text += f"📊 **Единица измерения:** {format_measurement_unit(measurement_unit)}\n"
    
    text += "\n"
    
    if description:
        text += f"📝 **Описание:**\n{description}\n\n"
    
    if instructions:
        text += f"📋 **Техника выполнения:**\n{instructions}"
    
    return text

def format_exercise_config(exercise_data):
    """Форматирование конфигурации упражнения"""
    name = exercise_data.get('name', 'Упражнение')
    sets = exercise_data.get('sets', 0)
    reps_min = exercise_data.get('reps_min', 0)
    reps_max = exercise_data.get('reps_max', 0)
    one_rm_percent = exercise_data.get('one_rm_percent')
    test_percent = exercise_data.get('test_percent')  # Новое поле для процентов от теста
    target_value = exercise_data.get('target_value')  # Целевое значение от теста
    target_unit = exercise_data.get('target_unit', '')  # Единица измерения
    rest_seconds = exercise_data.get('rest_seconds', 90)
    
    text = f"💪 **{name}**\n"
    
    # Основные параметры
    if reps_min and reps_max:
        text += f"📊 {sets}×{reps_min}-{reps_max}"
    elif target_value:
        text += f"📊 {sets}×{target_value} {target_unit}"
    
    # Проценты от теста или 1ПМ
    if test_percent:
        text += f" ({test_percent}% от теста)"
    elif one_rm_percent:
        text += f" ({one_rm_percent}% 1ПМ)"
    
    text += f"\n⏱️ Отдых: {format_time_duration(rest_seconds)}"
    
    return text

def format_workout_block_info(block_key, block_data):
    """Форматирование информации о блоке тренировки"""
    block_names = {
        'warmup': '🔥 Разминка',
        'nervous_prep': '⚡ Подготовка НС',
        'main': '💪 Основная часть',
        'cooldown': '🧘 Заминка'
    }
    
    name = block_names.get(block_key, 'Блок')
    exercises = block_data.get('exercises', [])
    description = block_data.get('description', '')
    
    text = f"**{name}**"
    
    if exercises:
        text += f" ({len(exercises)} упр.)"
    
    if description:
        text += f"\n   _📝 {description[:50]}{'...' if len(description) > 50 else ''}_"
    
    return text

def format_exercise_list(exercises):
    """Форматирование списка упражнений"""
    if not exercises:
        return "📋 **Упражнений пока нет**"
    
    text = f"**📋 Упражнения: {len(exercises)}**\n"
    
    for i, ex in enumerate(exercises, 1):
        text += f"{i}. {format_exercise_config(ex)}\n"
    
    return text

def format_block_summary(selected_blocks):
    """Форматирование краткой информации о блоках"""
    if not selected_blocks:
        return "⭕ **Блоки не выбраны**"
    
    block_names = {
        'warmup': '🔥 Разминка',
        'nervous_prep': '⚡ Подготовка НС',
        'main': '💪 Основная часть',
        'cooldown': '🧘 Заминка'
    }
    
    text = ""
    for phase, block_data in selected_blocks.items():
        if block_data['exercises']:
            text += f"**{block_names[phase]}:** {len(block_data['exercises'])} упр.\n"
            if block_data.get('description'):
                text += f"   _{block_data['description']}_\n"
    
    return text

# ===== НОВЫЕ ФОРМАТТЕРЫ ДЛЯ УНИВЕРСАЛЬНЫХ ТЕСТОВ =====

def format_test_results(exercise_name: str, test_type: str, result_value: float, result_unit: str, additional_data: dict) -> str:
    """Форматирование результатов универсального теста"""
    
    # Эмодзи по типу теста
    emoji = {
        'strength': '🏋️',
        'endurance': '⏱️',
        'speed': '🏃',
        'quantity': '🔢'
    }.get(test_type, '📊')
    
    # Название типа теста
    test_type_names = {
        'strength': 'Силовой тест',
        'endurance': 'Тест выносливости',
        'speed': 'Скоростной тест',
        'quantity': 'Количественный тест'
    }
    
    text = f"🎉 **Тест завершен!**\n\n"
    text += f"{emoji} **{exercise_name}**\n"
    text += f"📋 **Тип:** {test_type_names.get(test_type, 'Тест')}\n\n"
    
    # Основной результат
    unit_display = format_measurement_unit(result_unit)
    text += f"🏆 **Ваш результат: {result_value} {unit_display}**\n\n"
    
    # Дополнительная информация по типу теста
    if test_type == 'strength':
        formulas = additional_data.get('formulas', {})
        test_weight = additional_data.get('test_weight')
        test_reps = additional_data.get('test_reps')
        
        if test_weight and test_reps:
            text += f"📊 **Тестовые данные:** {test_weight} кг × {test_reps} раз\n\n"
        
        if formulas:
            text += f"**📈 Расчет 1ПМ по формулам:**\n"
            text += f"• Бжицкого: {formulas.get('brzycki', 0)} кг\n"
            text += f"• Эпли: {formulas.get('epley', 0)} кг\n"
            text += f"• Альтернативная: {formulas.get('alternative', 0)} кг\n\n"
            text += f"🎯 **Среднее значение:** {result_value} кг"
    
    elif test_type == 'endurance':
        duration = additional_data.get('duration_seconds')
        if duration:
            text += f"📊 **Время удержания:** {format_time_duration(duration)}\n"
            text += f"💪 Отличная выносливость!"
    
    elif test_type == 'speed':
        distance = additional_data.get('distance')
        time_seconds = additional_data.get('time_seconds')
        if distance and time_seconds:
            text += f"📊 **Дистанция:** {distance} м\n"
            text += f"⏱️ **Время:** {time_seconds} сек\n"
            text += f"🏃 **Скорость:** {result_value:.2f} м/с\n"
            
            # Переводим в км/ч для понятности
            speed_kmh = result_value * 3.6
            text += f"📈 **В км/ч:** {speed_kmh:.1f} км/ч"
    
    elif test_type == 'quantity':
        max_reps = additional_data.get('max_reps')
        if max_reps:
            text += f"📊 **Максимум повторений:** {max_reps}\n"
            text += f"💪 Отличный результат!"
    
    text += f"\n\n💡 **Теперь вы можете использовать этот результат в тренировках с процентами!**"
    
    return text

def format_test_history(tests: list) -> str:
    """Форматирование истории тестов пользователя"""
    if not tests:
        return "📊 **У вас пока нет результатов тестов**\n\nПройдите первый тест для отслеживания прогресса!"
    
    text = f"📊 **История ваших тестов:**\n\n"
    
    for test in tests:
        emoji = {
            'strength': '🏋️',
            'endurance': '⏱️',
            'speed': '🏃', 
            'quantity': '🔢'
        }.get(test.get('test_type'), '📊')
        
        date = test.get('tested_at', '').strftime('%d.%m.%Y') if test.get('tested_at') else 'Неизвестно'
        
        text += f"{emoji} **{test.get('exercise_name', 'Упражнение')}**\n"
        text += f"📈 Результат: **{test.get('result_value', 0)} {format_measurement_unit(test.get('result_unit', ''))}**\n"
        
        # Дополнительные данные
        if test.get('test_type') == 'strength' and test.get('test_weight'):
            text += f"📝 Тест: {test.get('test_weight')}кг × {test.get('test_reps')} раз\n"
        
        text += f"📅 {date}\n\n"
    
    return text

def format_measurement_unit(unit: str) -> str:
    """Форматирование единиц измерения для отображения"""
    unit_display = {
        'kg': 'кг',
        'seconds': 'сек',
        'm/s': 'м/с',
        'reps': 'повт.',
        'meters': 'м',
        'minutes': 'мин'
    }
    
    return unit_display.get(unit, unit)

def format_test_type_name(test_type: str) -> str:
    """Форматирование названия типа теста"""
    names = {
        'strength': '🏋️ Силовой',
        'endurance': '⏱️ Выносливость',
        'speed': '🏃 Скоростной',
        'quantity': '🔢 Количественный',
        'none': '❌ Не тестируемое'
    }
    
    return names.get(test_type, 'Неизвестно')

def format_user_profile(user_data):
    """Форматирование профиля пользователя"""
    first_name = user_data.get('first_name', 'Пользователь')
    role = user_data.get('role', 'player')
    created_at = user_data.get('created_at')
    
    role_names = {
        'player': 'Спортсмен',
        'coach': 'Тренер', 
        'admin': 'Администратор'
    }
    
    text = f"👤 **{first_name}**\n"
    text += f"🎯 **Роль:** {role_names.get(role, role.title())}\n"
    
    if created_at:
        date = created_at.strftime('%d.%m.%Y')
        text += f"📅 **Регистрация:** {date}\n"
    
    return text

def format_test_recommendation(test_result: dict, target_percent: int) -> str:
    """Форматирование рекомендации по тесту с процентами"""
    if not test_result or not target_percent:
        return ""
    
    result_value = test_result.get('result_value', 0)
    result_unit = test_result.get('result_unit', '')
    test_type = test_result.get('test_type', '')
    
    # Рассчитываем целевое значение
    if test_type == 'speed':
        # Для скорости: меньший процент = медленнее (хуже)
        # Больший процент = быстрее (лучше, но нереально)
        # Инвертируем логику: 80% от времени = 125% от скорости
        if result_unit in ['seconds', 'сек']:
            target_value = result_value * (100 / target_percent)
            display_unit = format_measurement_unit(result_unit)
        else:
            target_value = result_value * (target_percent / 100)
            display_unit = format_measurement_unit(result_unit)
    else:
        # Для остальных типов: процент напрямую
        target_value = result_value * (target_percent / 100)
        display_unit = format_measurement_unit(result_unit)
    
    return f"📊 **Цель:** {target_value:.1f} {display_unit} ({target_percent}% от рекорда)"

def format_exercise_search_results(exercises, search_term):
    """Форматирование результатов поиска упражнений"""
    if not exercises:
        return f"❌ Упражнения по запросу '{search_term}' не найдены\n\nПопробуйте другие ключевые слова."
    
    text = f"🔍 **Найдено: {len(exercises)} упражнений**\n\n"
    for ex in exercises:
        # Добавляем эмодзи в зависимости от типа теста
        test_emoji = {
            'strength': '🏋️',
            'endurance': '⏱️',
            'speed': '🏃',
            'quantity': '🔢',
            'none': '💪'
        }.get(ex.get('test_type'), '💪')
        
        text += f"{test_emoji} **{ex['name']}**\n"
        text += f"📂 {ex['category']} • {ex['muscle_group']}\n"
        text += f"📝 {ex['description'][:100]}{'...' if len(ex['description']) > 100 else ''}\n\n"
    
    return text

def format_time_duration(seconds):
    """Форматирование времени в читаемый вид"""
    if seconds < 60:
        return f"{seconds} сек"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        if remaining_seconds:
            return f"{minutes} мин {remaining_seconds} сек"
        return f"{minutes} мин"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours} ч {minutes} мин"

def format_difficulty_level(level):
    """Форматирование уровня сложности"""
    levels = {
        'beginner': '🟢 Новичок',
        'intermediate': '🟡 Средний',
        'advanced': '🔴 Продвинутый'
    }
    
    return levels.get(level, f"⚪ {level.title()}")

# ===== СОВМЕСТИМОСТЬ СО СТАРЫМ КОДОМ =====

def format_1rm_results(exercise_name, weight, reps, results):
    """Форматирование результатов теста 1ПМ (совместимость)"""
    return format_test_results(exercise_name, 'strength', results['average'], 'kg', {
        'test_weight': weight,
        'test_reps': reps,
        'formulas': results
    })

def format_weight_recommendation(test_result_value, percent):
    """Форматирование рекомендации по весу (совместимость)"""
    if not test_result_value or not percent:
        return ""
    
    recommended_weight = round(test_result_value * percent / 100, 1)
    return f"📊 **Рекомендуемый вес:** {recommended_weight} кг ({percent}% от рекорда)"

__all__ = [
    # Основные форматтеры
    'format_workout_summary',
    'format_exercise_info',
    'format_exercise_config',
    'format_workout_block_info',
    'format_exercise_list',
    'format_block_summary',
    'format_user_profile',
    'format_exercise_search_results',
    'format_time_duration',
    'format_difficulty_level',
    
    # Новые форматтеры для тестов
    'format_test_results',
    'format_test_history',
    'format_measurement_unit',
    'format_test_type_name',
    'format_test_recommendation',
    
    # Совместимость
    'format_1rm_results',
    'format_weight_recommendation'
]