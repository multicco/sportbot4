# ===== ЕДИНСТВЕННЫЙ ЭКЗЕМПЛЯР БОТА =====
# Все модули должны импортировать bot отсюда, чтобы избежать
# создания нескольких экземпляров Bot с одним токеном (конфликт поллинга).

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import config

bot = Bot(
    token=config.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

__all__ = ["bot"]
