
"""
database.py - Менеджер подключений к базе данных
Совместим с твоим existing кодом в main.py
"""

import asyncpg
import logging
from typing import Optional
import os

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self.database_url = None

    async def init_database(self, config):
        """Инициализация подключения к базе данных"""
        try:
            # Формируем DATABASE_URL из config
            if hasattr(config, 'DATABASE_URL') and config.DATABASE_URL:
                self.database_url = config.DATABASE_URL
            else:
                # Составляем URL из частей
                host = getattr(config, 'DATABASE_HOST', 'localhost')
                port = getattr(config, 'DATABASE_PORT', 5432)
                user = getattr(config, 'DATABASE_USER', 'postgres')
                password = getattr(config, 'DATABASE_PASSWORD', '')
                database = getattr(config, 'DATABASE_NAME', 'sportbot')

                self.database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"

            # Создаем пул подключений
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=2,
                max_size=10,
                command_timeout=60,
                server_settings={
                    'jit': 'off',
                    'application_name': 'SportBot'
                }
            )

            logger.info("✅ База данных инициализирована")
            logger.info(f"📊 Pool создан: min=2, max=10")

            # Проверяем соединение
            async with self.pool.acquire() as conn:
                result = await conn.fetchval("SELECT version();")
                logger.info(f"🔗 PostgreSQL: {result.split()[1]}")

            return True

        except Exception as e:
            logger.error(f"❌ Ошибка инициализации БД: {e}")
            if self.pool:
                await self.pool.close()
                self.pool = None
            raise

    async def close_pool(self):
        """Закрытие пула подключений"""
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("📊 Database pool закрыт")

    def get_pool(self) -> asyncpg.Pool:
        """Получить пул подключений"""
        return self.pool
    async def get_user_by_telegram_id(self, telegram_id: int):
        async with self.pool.acquire() as conn:
            user = await conn.fetchrow(
                "SELECT * FROM users WHERE telegram_id = $1",
                telegram_id
            )
            return user

# Глобальный менеджер БД
db_manager = DatabaseManager()

async def init_database():
    """Функция инициализации БД (совместимость с твоим кодом)"""
    from config import config
    return await db_manager.init_database(config)

# Экспорт для твоего main.py
__all__ = ['init_database', 'db_manager', 'DatabaseManager']
