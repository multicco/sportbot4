
# ===== ГЛАВНЫЙ ФАЙЛ ЗАПУСКА СПОРТИВНОГО БОТА =====
from handlers.teams import TeamStates
import asyncio
import logging
import sys
from pathlib import Path
from handlers import general_router

# Добавляем текущую директорию в путь для импортов
sys.path.insert(0, str(Path(__file__).parent))

from database import init_database, db_manager
from handlers import register_all_handlers
from config import config

# ВАЖНО: Создаем диспетчер здесь с правильным FSM storage
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# После инициализации основной БД добавь:
from handlers.teams import get_teams_router, init_teams_module_async

from handlers.player_workouts import get_player_workouts_router
from handlers.workouts import workouts_router





# Создаем storage для FSM состояний
storage = MemoryStorage()

# ИСПРАВЛЕНИЕ 1: Правильное создание бота
bot = Bot(
    token=config.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

# Создаем диспетчер с storage
dp = Dispatcher(storage=storage)

# ===== НАСТРОЙКА ЛОГИРОВАНИЯ =====
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

async def setup_bot_commands():
    """Настройка команд бота"""
    try:
        from aiogram.types import BotCommand, BotCommandScopeDefault

        commands = [
            BotCommand(command='start', description='🚀 Запустить бота'),
            BotCommand(command='menu', description='🏠 Главное меню'),
            BotCommand(command='teams', description='🏆 Управление командами'),
            BotCommand(command='help', description='❓ Помощь'),
            BotCommand(command='stats', description='📊 Моя статистика'),
        ]

        await bot.set_my_commands(commands, BotCommandScopeDefault())
        logger.info("✅ Команды бота настроены")

    except Exception as e:
        logger.warning(f"⚠️ Не удалось настроить команды: {e}")

async def check_database_connection():
    """Проверка подключения к базе данных"""
    try:
        if not db_manager.pool:
            raise Exception("Пул подключений не инициализирован")

        async with db_manager.pool.acquire() as conn:
            result = await conn.fetchval("SELECT 1")
            if result != 1:
                raise Exception("Неверный ответ от БД")

        logger.info("✅ Подключение к базе данных проверено")
        return True

    except Exception as e:
        logger.error(f"❌ Ошибка подключения к БД: {e}")
        return False


# # from handlers.teams import init_teams_database_instance
# teams_database = init_teams_database_instance(db_manager.pool)

async def main():
    """Главная функция запуска бота"""
    
    logger.info("🚀 Запуск спортивного бота...")
   

    
    try:
        # Проверяем конфигурацию
        if not config.BOT_TOKEN:
            raise ValueError("❌ BOT_TOKEN не задан в переменных окружения")
        
        if not hasattr(config, 'DATABASE_PASSWORD') or not config.DATABASE_PASSWORD:
            logger.warning("⚠️ DATABASE_PASSWORD не задан")
        
        # Инициализация базы данных
        logger.info("📊 Инициализация базы данных...")
        await init_database()
        
        # Проверка подключения к БД
        db_ok = await check_database_connection()
        if not db_ok:
            raise Exception("Не удалось подключиться к базе данных")
        
        # Инициализация модуля команд
        logger.info("🏆 Инициализация модуля команд...")
        await init_teams_module_async(db_manager)
        
        # ===== ИСПРАВЛЕНИЕ: ПРАВИЛЬНЫЙ ПОРЯДОК РЕГИСТРАЦИИ РОУТЕРОВ =====
        

        
        # 1. Teams router
        logger.info("🏆 Регистрация роутера команд...")
        # teams_router = get_teams_router()
        # dp.include_router(teams_router)
        
        # 2. Player workouts router (НОВЫЙ)
        logger.info("💪 Регистрация роутера тренировок игроков...")
        player_workouts_router = get_player_workouts_router()
        #dp.include_router(player_workouts_router)
        
        #         # 2.1 Основной workouts router
        # from handlers.workouts import workouts_router
        # dp.include_router(workouts_router)

        # 3. Остальные обработчики
        logger.info("🔗 Регистрация основных обработчиков...")
        register_all_handlers(dp)
        
        # dp.include_router(general_router)
        

        #dp.include_router(trainees_router)
        # ===== КОНЕЦ ИСПРАВЛЕНИЙ =====
        
        # Настройка команд бота
        await setup_bot_commands()
        
        # Получение информации о боте
        bot_info = await bot.get_me()
        logger.info(f"🤖 Бот: {bot_info.first_name} (@{bot_info.username})")
        logger.info(f"🆔 ID: {bot_info.id}")
        
        # Информация об администраторах
        if hasattr(config, 'ADMIN_USER_IDS') and config.ADMIN_USER_IDS:
            logger.info(f"👑 Администраторы: {len(config.ADMIN_USER_IDS)} чел.")
        
        logger.info("✅ Бот успешно запущен!")
        logger.info("🔄 Начинаю поллинг...")
        
        # Запуск поллинга
        await dp.start_polling(
            bot,
            skip_updates=True,
            allowed_updates=dp.resolve_used_update_types()
        )
        
    except KeyboardInterrupt:
        logger.info("⏹️ Получен сигнал остановки")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        raise
    finally:
        logger.info("🔄 Завершение работы...")
        
        # Закрытие соединений с БД
        try:
            if 'db_manager' in globals() and db_manager:
                await db_manager.close_pool()
                logger.info("📊 Соединения с БД закрыты")
        except Exception as e:
            logger.error(f"❌ Ошибка при закрытии БД: {e}")
        
        # Закрытие сессии бота
        try:
            await bot.session.close()
            logger.info("🤖 Сессия бота закрыта")
        except Exception as e:
            logger.error(f"❌ Ошибка при закрытии сессии: {e}")
        
        logger.info("👋 Бот остановлен")



def run_bot():
    """Запуск бота с обработкой исключений"""
    try:
        
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен пользователем")
    except Exception as e:
        print(f"💥 Фатальная ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_bot()
