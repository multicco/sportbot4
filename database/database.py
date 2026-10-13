
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

    async def init_database(self, config=None):  # ← добавь config=None
        """Инициализация подключения к базе данных"""
        try:
            # Если config не передан, импортируем сами
            if config is None:
                from config import config
            
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
# ⬇️⬇️⬇️ ДОБАВЬ ЭТО ⬇️⬇️⬇️
    async def get_user_by_username(self, username: str):
        """Получить пользователя по username (@nick)"""
        async with self.pool.acquire() as conn:
            # Убираем @ если есть
            clean_username = username.lstrip('@').lower()
            
            user = await conn.fetchrow(
                "SELECT * FROM users WHERE LOWER(username) = $1",
                clean_username
            )
            return user
# ⬆️⬆️⬆️ ДОБАВЬ ЭТО ⬆️⬆️⬆️
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


# database/database.py - ТОЛЬКО ДОБАВЛЯЕМЫЕ МЕТОДЫ ДЛЯ СИСТЕМЫ РОЛЕЙ

# Вставить эти методы в класс DatabaseManager (после existing методов):

    async def set_user_role(self, user_id: int, role: str) -> bool:
        """
        ✓ УСТАНОВИТЬ РОЛЬ ПОЛЬЗОВАТЕЛЮ
        
        Роли:
        - 'player': обычный игрок (по умолчанию)
        - 'trainer': тренер (может видеть тренировки подопечных)
        - 'admin': администратор (видит всё)
        
        Args:
            user_id: ID пользователя в таблице users
            role: одна из ['player', 'trainer', 'admin']
        
        Returns:
            True если успешно, False если ошибка
        """
        valid_roles = ['player', 'trainer', 'admin']
        if role not in valid_roles:
            logger.warning(f"❌ Неверная роль: {role}. Допустимые: {valid_roles}")
            return False
        
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    "UPDATE users SET role = $1 WHERE id = $2",
                    role, user_id
                )
            logger.info(f"✅ Роль пользователя {user_id} установлена: {role}")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка установки роли: {e}")
            return False


    async def get_user_role(self, telegram_id: int) -> str:
        """
        ✓ ПОЛУЧИТЬ РОЛЬ ПОЛЬЗОВАТЕЛЯ ПО TELEGRAM_ID
        
        Args:
            telegram_id: Telegram ID пользователя (из callback.from_user.id)
        
        Returns:
            Роль пользователя: 'player', 'trainer', или 'admin'
            По умолчанию 'player' если не найден
        """
        try:
            user = await self.get_user_by_telegram_id(telegram_id)
            if user:
                return user.get('role', 'player')
        except Exception as e:
            logger.exception(f"Ошибка получения роли для {telegram_id}: {e}")
        return 'player'


    async def add_trainee_to_trainer(self, trainer_id: int, trainee_id: int) -> bool:
        """
        ✓ ДОБАВИТЬ ПОДОПЕЧНОГО К ТРЕНЕРУ
        
        Создает связь: тренер может видеть тренировки подопечного
        
        Args:
            trainer_id: ID тренера в таблице users
            trainee_id: ID подопечного (игрока) в таблице users
        
        Returns:
            True если успешно или уже существует, False если ошибка
        """
        try:
            async with self.pool.acquire() as conn:
                # Проверяем, нет ли уже такой связи
                existing = await conn.fetchval("""
                    SELECT id FROM user_trainee_assignments
                    WHERE trainer_id = $1 AND trainee_id = $2
                """, trainer_id, trainee_id)
                
                if existing:
                    logger.info(f"⚠️ Связь уже существует: тренер {trainer_id} → игрок {trainee_id}")
                    return True
                
                # Создаем новую связь
                await conn.execute("""
                    INSERT INTO user_trainee_assignments (trainer_id, trainee_id)
                    VALUES ($1, $2)
                """, trainer_id, trainee_id)
            
            logger.info(f"✅ Игрок {trainee_id} добавлен к тренеру {trainer_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка добавления подопечного: {e}")
            return False


    async def remove_trainee_from_trainer(self, trainer_id: int, trainee_id: int) -> bool:
        """
        ✓ УДАЛИТЬ ПОДОПЕЧНОГО ИЗ ТРЕНЕРА
        
        Args:
            trainer_id: ID тренера
            trainee_id: ID подопечного
        
        Returns:
            True если успешно
        """
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    DELETE FROM user_trainee_assignments
                    WHERE trainer_id = $1 AND trainee_id = $2
                """, trainer_id, trainee_id)
            logger.info(f"✅ Игрок {trainee_id} удален от тренера {trainer_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка удаления подопечного: {e}")
            return False


    async def get_trainer_trainees(self, trainer_id: int) -> list:
        """
        ✓ ПОЛУЧИТЬ СПИСОК ПОДОПЕЧНЫХ ТРЕНЕРА
        
        Args:
            trainer_id: ID тренера в таблице users
        
        Returns:
            Список словарей с данными подопечных
        """
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT u.id, u.telegram_id, u.first_name, u.last_name, u.username
                    FROM users u
                    INNER JOIN user_trainee_assignments uta ON u.id = uta.trainee_id
                    WHERE uta.trainer_id = $1
                    ORDER BY u.first_name
                """, trainer_id)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"❌ Ошибка получения подопечных: {e}")
            return []


    async def get_user_trainers(self, trainee_id: int) -> list:
        """
        ✓ ПОЛУЧИТЬ СПИСОК ТРЕНЕРОВ ПОЛЬЗОВАТЕЛЯ
        
        Args:
            trainee_id: ID подопечного (игрока)
        
        Returns:
            Список словарей с данными тренеров
        """
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT u.id, u.telegram_id, u.first_name, u.last_name
                    FROM users u
                    INNER JOIN user_trainee_assignments uta ON u.id = uta.trainer_id
                    WHERE uta.trainee_id = $1
                    ORDER BY u.first_name
                """, trainee_id)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"❌ Ошибка получения тренеров: {e}")
            return []


    async def is_admin(self, telegram_id: int) -> bool:
        """
        ✓ БЫСТРАЯ ПРОВЕРКА: АДМИН ЛИ ПОЛЬЗОВАТЕЛЬ
        
        Args:
            telegram_id: Telegram ID
        
        Returns:
            True если админ, False в остальных случаях
        """
        role = await self.get_user_role(telegram_id)
        return role == 'admin'


    async def is_trainer(self, telegram_id: int) -> bool:
        """
        ✓ БЫСТРАЯ ПРОВЕРКА: ТРЕНЕР ЛИ ПОЛЬЗОВАТЕЛЬ (или админ)
        
        Возвращает True для обеих: тренеров и админов
        
        Args:
            telegram_id: Telegram ID
        
        Returns:
            True если тренер или админ, False в остальных случаях
        """
        role = await self.get_user_role(telegram_id)
        return role in ['trainer', 'admin']


    # Также обнови функцию init_database() в конце файла database.py, добавив создание таблицы:

    # async def init_database():
    #     """Инициализация базы данных и создание таблиц"""
    #     await db_manager.init_pool()
        
    #     try:
    #         async with db_manager.pool.acquire() as conn:
    #             # Таблица пользователей
    #             await conn.execute("""
    #                 CREATE TABLE IF NOT EXISTS users (
    #                     id SERIAL PRIMARY KEY,
    #                     telegram_id BIGINT UNIQUE NOT NULL,
    #                     first_name VARCHAR(255),
    #                     last_name VARCHAR(255),
    #                     username VARCHAR(255),
    #                     role VARCHAR(20) DEFAULT 'player' CHECK (role IN ('player', 'trainer', 'admin')),
    #                     created_at TIMESTAMP DEFAULT NOW(),
    #                     updated_at TIMESTAMP DEFAULT NOW()
    #                 )
    #             """)
                
    #             # ✓ НОВАЯ ТАБЛИЦА: Связь тренер-подопечный
    #             await conn.execute("""
    #                 CREATE TABLE IF NOT EXISTS user_trainee_assignments (
    #                     id SERIAL PRIMARY KEY,
    #                     trainer_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    #                     trainee_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    #                     assigned_at TIMESTAMP DEFAULT NOW(),
    #                     UNIQUE(trainer_id, trainee_id)
    #                 )
    #             """)
                
    #             # Создаем индексы для оптимизации
    #             await conn.execute("""
    #                 CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id)
    #             """)
    #             await conn.execute("""
    #                 CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)
    #             """)
    #             await conn.execute("""
    #                 CREATE INDEX IF NOT EXISTS idx_trainer_id ON user_trainee_assignments(trainer_id)
    #             """)
    #             await conn.execute("""
    #                 CREATE INDEX IF NOT EXISTS idx_trainee_id ON user_trainee_assignments(trainee_id)
    #             """)
                
    #             logger.info("✅ Таблицы БД созданы/проверены")
    #     except Exception as e:
    #         logger.error(f"❌ Ошибка инициализации таблиц: {e}")
    #         raise


    async def create_user(self, telegram_id: int, first_name: str, 
                        last_name: str = None, username: str = None, role: str = 'player'):
        """Создать нового пользователя"""
        try:
            async with self.pool.acquire() as conn:
                # Проверяем, не существует ли уже
                existing = await conn.fetchval(
                    "SELECT id FROM users WHERE telegram_id = $1",
                    telegram_id
                )
                if existing:
                    logger.info(f"⚠️ Пользователь {telegram_id} уже существует")
                    return await self.get_user_by_telegram_id(telegram_id)
                
                # Создаем нового пользователя
                row = await conn.fetchrow("""
                    INSERT INTO users (telegram_id, first_name, last_name, username, role, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
                    RETURNING *
                """, telegram_id, first_name, last_name, username, role)
                
                logger.info(f"✅ Создан пользователь {telegram_id} (@{username})")
                return dict(row) if row else None
                
        except Exception as e:
            logger.error(f"❌ Ошибка создания пользователя: {e}")
            return None

# Глобальный менеджер БД
db_manager = DatabaseManager()

async def init_database():
    """Функция инициализации БД (совместимость с твоим кодом)"""
    from config import config
    return await db_manager.init_database(config)

# Экспорт для твоего main.py
__all__ = ['init_database', 'db_manager', 'DatabaseManager']
