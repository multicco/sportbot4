# ===== ИНИЦИАЛИЗАЦИЯ БОТА И ДИСПЕТЧЕРА =====

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import config

# Создание экземпляров бота и диспетчера
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Экспорт для использования в других модулях
__all__ = ['bot', 'dp']