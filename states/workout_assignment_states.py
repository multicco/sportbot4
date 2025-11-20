from aiogram.fsm.state import State, StatesGroup

class AssignWorkoutStates(StatesGroup):
    """Состояния для назначения тренировок"""
    choosing_assignment_type = State()  # Выбор: команда или подопечный
    choosing_target = State()  # Выбор конкретной команды/подопечного
    choosing_workout_method = State()  # Метод выбора тренировки (мои/по коду/поиск)
    searching_workout = State()  # Поиск тренировки
    entering_workout_code = State()  # Ввод кода тренировки
    selecting_from_my_workouts = State()  # Выбор из своих тренировок
    adding_notes = State()  # Добавление комментария
    setting_deadline = State()  # Установка дедлайна
    confirming_assignment = State()  # Подтверждение назначения

class WorkoutPlayerStates(StatesGroup):
    """Состояния для выполнения тренировки игроком"""
    viewing_workout = State()
    in_workout = State()
    entering_workout_rpe = State()  # Оценка RPE после тренировки
    adding_workout_notes = State()