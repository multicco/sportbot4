
"""
database.py - Менеджер подключений к базе данных
Совместим с твоим existing кодом в main.py
"""
from .teams_database import Team

import asyncpg
import logging
from typing import Optional, List 
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

async def get_team_by_access_code(self, access_code: str) -> Optional[Team]:
    """Найти команду по коду доступа"""
    async with self.pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT t.*, COUNT(tp.id) as players_count
            FROM teams t
            LEFT JOIN team_players tp ON t.id = tp.team_id AND tp.is_active = TRUE
            WHERE t.access_code = $1
            GROUP BY t.id
        """, access_code)
        
        if not row:
            return None
        
        return Team(
            id=row['id'],
            name=row['name'],
            description=row['description'],
            coach_telegram_id=row['coach_telegram_id'],
            sport_type=row['sport_type'],
            max_players=row['max_players'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            players_count=row['players_count']
        )

async def get_player_teams(self, telegram_id: int) -> List[Team]:
    """Получить все команды игрока по его telegram_id"""
    async with self.pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT t.*, COUNT(tp2.id) as players_count
            FROM teams t
            JOIN team_players tp ON t.id = tp.team_id
            LEFT JOIN team_players tp2 ON t.id = tp2.team_id AND tp2.is_active = TRUE
            WHERE tp.telegram_id = $1 AND tp.is_active = TRUE
            GROUP BY t.id
            ORDER BY tp.joined_at DESC
        """, telegram_id)
        
        teams = []
        for row in rows:
            teams.append(Team(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                coach_telegram_id=row['coach_telegram_id'],
                sport_type=row['sport_type'],
                max_players=row['max_players'],
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                players_count=row['players_count']
            ))
        return teams

async def check_player_in_team(self, telegram_id: int, team_id: int) -> bool:
    """Проверить, состоит ли игрок в команде"""
    async with self.pool.acquire() as conn:
        count = await conn.fetchval("""
            SELECT COUNT(*) FROM team_players
            WHERE telegram_id = $1 AND team_id = $2 AND is_active = TRUE
        """, telegram_id, team_id)
        return count > 0

async def assign_workout_to_team(self, workout_id: int, team_id: int, assigned_by: int):
    """Назначить тренировку на команду"""
    async with self.pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO workout_teams (workout_id, team_id, assigned_by)
            VALUES ($1, $2, $3)
            ON CONFLICT (workout_id, team_id) DO NOTHING
        """, workout_id, team_id, assigned_by)

async def get_team_workouts(self, team_id: int) -> list[dict]:
    """Получить тренировки команды"""
    async with self.pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT w.*, wt.assigned_at, u.first_name as creator_name
            FROM workouts w
            JOIN workout_teams wt ON w.id = wt.workout_id
            LEFT JOIN users u ON w.created_by = u.id
            WHERE wt.team_id = $1 AND w.is_active = TRUE
            ORDER BY wt.assigned_at DESC
        """, team_id)
        return [dict(row) for row in rows]



# Глобальный менеджер БД
db_manager = DatabaseManager()

async def init_database():
    """Функция инициализации БД (совместимость с твоим кодом)"""
    from config import config
    return await db_manager.init_database(config)

# Экспорт для твоего main.py
__all__ = ['init_database', 'db_manager', 'DatabaseManager']
