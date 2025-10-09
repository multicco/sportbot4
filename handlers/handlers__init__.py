# ===== РЕГИСТРАЦИЯ ВСЕХ ОБРАБОТЧИКОВ =====

from . import start
from . import exercises  
from . import workouts
from . import one_rm
from . import teams

def register_all_handlers(dp):
    """Регистрация всех обработчиков событий"""
    
    # Порядок регистрации важен!
    start.register_start_handlers(dp)
    exercises.register_exercise_handlers(dp) 
    workouts.register_workout_handlers(dp)
    one_rm.register_one_rm_handlers(dp)
    teams.register_team_handlers(dp)

__all__ = ['register_all_handlers']