
# ===== КОНФИГУРАЦИЯ БОТА =====
# ИСПРАВЛЕННАЯ ВЕРСИЯ ДЛЯ AIOGRAM 3.7.0+

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config import config
import logging

logger = logging.getLogger(__name__)

# ИСПРАВЛЕНИЕ: Новый способ создания бота в aiogram 3.7.0+
bot = Bot(
    token=config.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

# НЕ создаем здесь диспетчер! Он создается в main.py с правильным FSM storage
logger.info("🤖 Bot instance created (aiogram 3.7.0+ compatible)")
