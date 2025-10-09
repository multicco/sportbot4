# ===== КЛАВИАТУРЫ =====

from .main_keyboards_old import *
from .exercise_keyboards import *  
from .workout_keyboards import *

__all__ = [
    # Main keyboards
    'get_main_menu_keyboard',
    'get_workouts_menu_keyboard',
    'get_one_rm_menu_keyboard', 
    'get_teams_menu_keyboard',
    
    # Exercise keyboards
    'get_exercise_search_keyboard',
    'get_categories_keyboard',
    'get_exercise_creation_keyboard',
    
    # Workout keyboards  
    'get_workout_blocks_keyboard',
    'get_block_exercises_keyboard',
    'get_exercise_config_keyboard'
]