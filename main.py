# ===== ГЛАВНЫЙ ФАЙЛ ЗАПУСКА БОТА =====

import asyncio
import logging
from bot import bot, dp
from database import init_database, db_manager
from handlers import register_all_handlers

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Главная функция запуска бота"""
    try:
        # Инициализация базы данных
        await init_database()
        
        # Регистрация всех обработчиков
        register_all_handlers(dp)
        
        # Информация о запуске
        bot_info = await bot.get_me()
        logger.info(f"🚀 Бот {bot_info.first_name} (@{bot_info.username}) запущен!")
        
        # Запуск поллинга
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
    finally:
        # Закрытие соединений
        await db_manager.close_pool()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())