from aiogram.fsm.state import State, StatesGroup

class JoinTeamStates(StatesGroup):
    """Состояния для присоединения к команде через код"""
    waiting_first_name = State()
    waiting_last_name = State()
    waiting_position = State()
    waiting_jersey_number = State()




class JoinTeamStates(StatesGroup):
    """Состояния для присоединения к команде через код"""
    waiting_first_name = State()
    waiting_last_name = State()
    waiting_position = State()
    waiting_jersey_number = State()

class AddMemberStates(StatesGroup):
    """Состояния для добавления участника тренером"""
    choosing_method = State()  # Выбор метода добавления
    waiting_telegram_id = State()  # Ожидание Telegram ID
    waiting_confirmation = State()  # Подтверждение добавления
    waiting_manual_name = State()  # Ручной ввод имени

