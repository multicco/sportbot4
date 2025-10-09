import asyncpg
import logging
from typing import Optional
from config import config

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def init_pool(self):
        """Инициализация пула подключений к БД"""
        try:
            self.pool = await asyncpg.create_pool(
                host=config.DATABASE_HOST,
                port=config.DATABASE_PORT,
                database=config.DATABASE_NAME,
                user=config.DATABASE_USER,
                password=config.DATABASE_PASSWORD,
                min_size=5,
                max_size=20
            )
            logger.info("✅ Подключение к базе данных установлено")
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к БД: {e}")
            raise

    async def close_pool(self):
        """Закрытие пула подключений"""
        if self.pool:
            await self.pool.close()
            logger.info("🔐 Подключение к базе данных закрыто")

    async def get_user_by_telegram_id(self, telegram_id: int):
        """Получить пользователя по Telegram ID"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM users WHERE telegram_id = $1", 
                telegram_id
            )
            return dict(row) if row else None

    async def create_user(self, telegram_id: int, first_name: str, 
                         last_name: str = None, username: str = None):
        """Создать нового пользователя"""
        async with self.pool.acquire() as conn:
            user_id = await conn.fetchval(
                """INSERT INTO users (telegram_id, first_name, last_name, username, role)
                   VALUES ($1, $2, $3, $4, 'player') RETURNING id""",
                telegram_id, first_name, last_name, username
            )
            return user_id

# Глобальный экземпляр менеджера БД
db_manager = DatabaseManager()

async def init_database():
    """Инициализация базы данных"""
    await db_manager.init_pool()