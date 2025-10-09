# ===== ОБНОВЛЕННЫЕ ВАЛИДАТОРЫ С ПОДДЕРЖКОЙ КОМАНДНЫХ ТЕСТОВ =====

import re

# ===== СУЩЕСТВУЮЩИЕ ВАЛИДАТОРЫ (БЕЗ ИЗМЕНЕНИЙ) =====

def validate_exercise_name(name: str) -> dict:
    """Валидация названия упражнения"""
    result = {
        'valid': True,
        'error': None
    }
    
    if not name or len(name.strip()) < 3:
        result['valid'] = False
        result['error'] = "❌ Название слишком короткое. Минимум 3 символа."
    
    elif len(name.strip()) > 100:
        result['valid'] = False 
        result['error'] = "❌ Название слишком длинное. Максимум 100 символов."
    
    return result

def validate_workout_name(name: str) -> dict:
    """Валидация названия тренировки"""
    result = {
        'valid': True,
        'error': None
    }
    
    if not name or len(name.strip()) < 3:
        result['valid'] = False
        result['error'] = "❌ Название слишком короткое. Минимум 3 символа."
    
    elif len(name.strip()) > 100:
        result['valid'] = False
        result['error'] = "❌ Название слишком длинное. Максимум 100 символов."
    
    return result

def validate_exercise_description(description: str) -> dict:
    """Валидация описания упражнения"""
    result = {
        'valid': True,
        'error': None
    }
    
    if not description or len(description.strip()) < 10:
        result['valid'] = False
        result['error'] = "❌ Описание слишком короткое. Минимум 10 символов."
    
    elif len(description.strip()) > 500:
        result['valid'] = False
        result['error'] = "❌ Описание слишком длинное. Максимум 500 символов."
    
    return result

def validate_exercise_instructions(instructions: str) -> dict:
    """Валидация инструкций упражнения"""
    result = {
        'valid': True, 
        'error': None
    }
    
    if not instructions or len(instructions.strip()) < 20:
        result['valid'] = False
        result['error'] = "❌ Инструкции слишком короткие. Минимум 20 символов."
    
    elif len(instructions.strip()) > 1500:
        result['valid'] = False
        result['error'] = "❌ Инструкции слишком длинные. Максимум 1500 символов."
    
    return result

def validate_exercise_config(sets: str, reps_min: str, reps_max: str, one_rm_percent: str = None) -> dict:
    """Валидация конфигурации упражнения"""
    result = {
        'valid': True,
        'error': None,
        'sets': 0,
        'reps_min': 0, 
        'reps_max': 0,
        'one_rm_percent': None
    }
    
    try:
        sets_val = int(sets)
        reps_min_val = int(reps_min)
        reps_max_val = int(reps_max)
        
        if not (1 <= sets_val <= 10):
            result['valid'] = False
            result['error'] = "❌ Подходы должны быть от 1 до 10"
        
        elif not (1 <= reps_min_val <= 200):
            result['valid'] = False
            result['error'] = "❌ Минимальные повторения должны быть от 1 до 200"
        
        elif not (reps_min_val <= reps_max_val <= 200):
            result['valid'] = False
            result['error'] = "❌ Максимальные повторения должны быть >= минимальных и <= 200"
        
        else:
            result['sets'] = sets_val
            result['reps_min'] = reps_min_val
            result['reps_max'] = reps_max_val
            
            if one_rm_percent:
                percent_val = int(one_rm_percent)
                if not (30 <= percent_val <= 120):
                    result['valid'] = False
                    result['error'] = "❌ Процент должен быть от 30% до 120%"
                else:
                    result['one_rm_percent'] = percent_val
    
    except ValueError:
        result['valid'] = False
        result['error'] = "❌ Используйте только числа. Пример: `3 8 12` или `4 6 8 80`"
    
    return result

# ===== ВАЛИДАТОРЫ ТЕСТОВ (БЕЗ ИЗМЕНЕНИЙ) =====

def validate_test_data(test_type: str, data_parts: list) -> dict:
    """Универсальная валидация данных тестов"""
    result = {
        'valid': True,
        'error': None
    }
    
    if test_type == 'strength':
        return validate_strength_test_data(data_parts)
    elif test_type == 'endurance':
        return validate_endurance_test_data(data_parts)
    elif test_type == 'speed':
        return validate_speed_test_data(data_parts)
    elif test_type == 'quantity':
        return validate_quantity_test_data(data_parts)
    else:
        result['valid'] = False
        result['error'] = f"❌ Неизвестный тип теста: {test_type}"
    
    return result

def validate_strength_test_data(data_parts: list) -> dict:
    """Валидация данных силового теста (вес + повторения)"""
    result = {
        'valid': True,
        'error': None,
        'weight': 0,
        'reps': 0
    }
    
    if len(data_parts) != 2:
        result['valid'] = False
        result['error'] = "❌ Введите вес и повторения через пробел.\nПример: `80 5`"
        return result
    
    try:
        weight_val = float(data_parts[0])
        reps_val = int(data_parts[1])
        
        if weight_val <= 0:
            result['valid'] = False
            result['error'] = "❌ Вес должен быть больше 0"
        
        elif not (1 <= reps_val <= 30):
            result['valid'] = False
            result['error'] = "❌ Повторения должны быть от 1 до 30"
        
        else:
            result['weight'] = weight_val
            result['reps'] = reps_val
    
    except ValueError:
        result['valid'] = False
        result['error'] = "❌ Ошибка формата данных. Используйте числа.\nПример: `80 5`"
    
    return result

def validate_endurance_test_data(data_parts: list) -> dict:
    """Валидация данных теста на выносливость (время в секундах)"""
    result = {
        'valid': True,
        'error': None,
        'time_seconds': 0
    }
    
    if len(data_parts) != 1:
        result['valid'] = False
        result['error'] = "❌ Введите время в секундах.\nПример: `90`"
        return result
    
    try:
        time_val = int(data_parts[0])
        
        if not (1 <= time_val <= 3600):  # до 1 часа
            result['valid'] = False
            result['error'] = "❌ Время должно быть от 1 до 3600 секунд (1 час)"
        else:
            result['time_seconds'] = time_val
    
    except ValueError:
        result['valid'] = False
        result['error'] = "❌ Введите время в секундах числом.\nПример: `90`"
    
    return result

def validate_speed_test_data(data_parts: list) -> dict:
    """Валидация данных скоростного теста (дистанция + время)"""
    result = {
        'valid': True,
        'error': None,
        'distance': 0,
        'time_seconds': 0
    }
    
    if len(data_parts) != 2:
        result['valid'] = False
        result['error'] = "❌ Введите дистанцию (м) и время (сек) через пробел.\nПример: `100 15.2`"
        return result
    
    try:
        distance_val = float(data_parts[0])
        time_val = float(data_parts[1])
        
        if not (1 <= distance_val <= 10000):  # до 10 км
            result['valid'] = False
            result['error'] = "❌ Дистанция должна быть от 1 до 10000 метров"
        
        elif not (0.1 <= time_val <= 7200):  # до 2 часов
            result['valid'] = False
            result['error'] = "❌ Время должно быть от 0.1 до 7200 секунд"
        
        else:
            result['distance'] = distance_val
            result['time_seconds'] = time_val
    
    except ValueError:
        result['valid'] = False
        result['error'] = "❌ Ошибка формата данных. Используйте числа.\nПример: `100 15.2`"
    
    return result

def validate_quantity_test_data(data_parts: list) -> dict:
    """Валидация данных количественного теста (максимум повторений)"""
    result = {
        'valid': True,
        'error': None,
        'max_reps': 0
    }
    
    if len(data_parts) != 1:
        result['valid'] = False
        result['error'] = "❌ Введите количество повторений.\nПример: `45`"
        return result
    
    try:
        reps_val = int(data_parts[0])
        
        if not (1 <= reps_val <= 10000):
            result['valid'] = False
            result['error'] = "❌ Количество повторений должно быть от 1 до 10000"
        else:
            result['max_reps'] = reps_val
    
    except ValueError:
        result['valid'] = False
        result['error'] = "❌ Введите количество повторений числом.\nПример: `45`"
    
    return result

# ===== НОВЫЕ ВАЛИДАТОРЫ ДЛЯ КОМАНДНЫХ ТЕСТОВ =====

def validate_test_set_name(name: str) -> dict:
    """Валидация названия набора тестов"""
    result = {
        'valid': True,
        'error': None
    }
    
    if not name or len(name.strip()) < 3:
        result['valid'] = False
        result['error'] = "❌ Название слишком короткое. Минимум 3 символа."
    
    elif len(name.strip()) > 200:
        result['valid'] = False
        result['error'] = "❌ Название слишком длинное. Максимум 200 символов."
    
    return result

def validate_test_set_description(description: str) -> dict:
    """Валидация описания набора тестов"""
    result = {
        'valid': True,
        'error': None
    }
    
    if description and len(description.strip()) > 1000:
        result['valid'] = False
        result['error'] = "❌ Описание слишком длинное. Максимум 1000 символов."
    
    return result

def validate_access_code(code: str) -> dict:
    """Валидация кода доступа к набору тестов"""
    result = {
        'valid': True,
        'error': None,
        'cleaned_code': ''
    }
    
    if not code:
        result['valid'] = False
        result['error'] = "❌ Введите код доступа."
        return result
    
    # Очищаем код: убираем пробелы, приводим к верхнему регистру
    cleaned = re.sub(r'[^A-Z0-9-]', '', code.upper().strip())
    
    # Проверяем формат: TS-XXXX или TS-XX-XX
    if not re.match(r'^TS-[A-Z0-9]{2,4}(-[A-Z0-9]{2})?$', cleaned):
        result['valid'] = False
        result['error'] = "❌ Неверный формат кода. Пример: TS-AB12 или TS-XY-98"
        return result
    
    result['cleaned_code'] = cleaned
    return result

def validate_test_requirement(value: str, test_type: str) -> dict:
    """Валидация минимального требования к тесту"""
    result = {
        'valid': True,
        'error': None,
        'requirement_value': None
    }
    
    if not value or value.strip() == '':
        # Пустое значение допустимо (нет требований)
        return result
    
    try:
        req_value = float(value.strip())
        
        if req_value <= 0:
            result['valid'] = False
            result['error'] = "❌ Требование должно быть больше 0"
            return result
        
        # Проверяем разумные пределы в зависимости от типа теста
        if test_type == 'strength':
            if not (1 <= req_value <= 500):
                result['valid'] = False
                result['error'] = "❌ Требование по весу должно быть от 1 до 500 кг"
        
        elif test_type == 'endurance':
            if not (1 <= req_value <= 3600):
                result['valid'] = False
                result['error'] = "❌ Требование по времени должно быть от 1 до 3600 секунд"
        
        elif test_type == 'speed':
            if not (0.1 <= req_value <= 300):
                result['valid'] = False
                result['error'] = "❌ Требование по времени должно быть от 0.1 до 300 секунд"
        
        elif test_type == 'quantity':
            if not (1 <= req_value <= 1000):
                result['valid'] = False
                result['error'] = "❌ Требование по повторениям должно быть от 1 до 1000"
        
        if result['valid']:
            result['requirement_value'] = req_value
    
    except ValueError:
        result['valid'] = False
        result['error'] = "❌ Введите числовое значение или оставьте пустым"
    
    return result

def validate_max_attempts(attempts: str) -> dict:
    """Валидация максимального количества попыток"""
    result = {
        'valid': True,
        'error': None,
        'attempts': 1
    }
    
    if not attempts or attempts.strip() == '':
        result['attempts'] = 1
        return result
    
    try:
        attempts_val = int(attempts.strip())
        
        if not (1 <= attempts_val <= 10):
            result['valid'] = False
            result['error'] = "❌ Количество попыток должно быть от 1 до 10"
        else:
            result['attempts'] = attempts_val
    
    except ValueError:
        result['valid'] = False
        result['error'] = "❌ Введите целое число от 1 до 10"
    
    return result

def validate_test_notes(notes: str) -> dict:
    """Валидация заметок к тесту"""
    result = {
        'valid': True,
        'error': None
    }
    
    if notes and len(notes.strip()) > 500:
        result['valid'] = False
        result['error'] = "❌ Заметки слишком длинные. Максимум 500 символов."
    
    return result

def validate_test_percent_config(sets: str, target_min: str, target_max: str, test_percent: str = None) -> dict:
    """Валидация конфигурации упражнения с процентами от теста"""
    result = {
        'valid': True,
        'error': None,
        'sets': 0,
        'target_min': 0, 
        'target_max': 0,
        'test_percent': None
    }
    
    try:
        sets_val = int(sets)
        target_min_val = float(target_min)
        target_max_val = float(target_max)
        
        if not (1 <= sets_val <= 10):
            result['valid'] = False
            result['error'] = "❌ Подходы должны быть от 1 до 10"
        
        elif target_min_val <= 0:
            result['valid'] = False
            result['error'] = "❌ Минимальное значение должно быть больше 0"
        
        elif target_min_val > target_max_val:
            result['valid'] = False
            result['error'] = "❌ Максимальное значение должно быть >= минимального"
        
        else:
            result['sets'] = sets_val
            result['target_min'] = target_min_val
            result['target_max'] = target_max_val
            
            if test_percent:
                percent_val = int(test_percent)
                if not (30 <= percent_val <= 120):
                    result['valid'] = False
                    result['error'] = "❌ Процент от теста должен быть от 30% до 120%"
                else:
                    result['test_percent'] = percent_val
    
    except ValueError:
        result['valid'] = False
        result['error'] = "❌ Используйте только числа."
    
    return result

# ===== СОВМЕСТИМОСТЬ =====

def validate_1rm_data(weight: str, reps: str) -> dict:
    """Валидация данных для теста 1ПМ (совместимость со старым кодом)"""
    return validate_strength_test_data([weight, reps])

__all__ = [
    # Валидаторы упражнений
    'validate_exercise_name',
    'validate_workout_name',
    'validate_exercise_description', 
    'validate_exercise_instructions',
    'validate_exercise_config',
    
    # Валидаторы тестов
    'validate_test_data',
    'validate_strength_test_data',
    'validate_endurance_test_data',
    'validate_speed_test_data',
    'validate_quantity_test_data',
    'validate_test_percent_config',
    
    # Новые валидаторы командных тестов
    'validate_test_set_name',
    'validate_test_set_description',
    'validate_access_code',
    'validate_test_requirement',
    'validate_max_attempts',
    'validate_test_notes',
    
    # Совместимость
    'validate_1rm_data'
]