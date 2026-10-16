
# ===== КОНФИГУРАЦИЯ БОТА =====
# ФАТАЛЬНОЕ ИСПРАВЛЕНИЕ: раньше здесь создавался ВТОРОЙ экземпляр Bot
# с тем же токеном, что и в main.py — два экземпляра одновременно
# поллили апдейты и «съедали» их друг у друга.
# Теперь bot.py — тонкая обёртка над единственным экземпляром из bot_instance.py.

import logging

from bot_instance import bot  # единственный экземпляр Bot во всём проекте

logger = logging.getLogger(__name__)

# НЕ создаем здесь диспетчер! Он создается в main.py с правильным FSM storage
logger.info("🤖 Bot instance imported from bot_instance (single shared instance)")

__all__ = ["bot"]
