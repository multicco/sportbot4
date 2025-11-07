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

async def init_database():
    """Инициализация базы данных и создание таблиц"""
    await db_manager.init_pool()
    
    try:
        async with db_manager.pool.acquire() as conn:
            # Таблица пользователей
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    telegram_id BIGINT UNIQUE NOT NULL,
                    first_name VARCHAR(255),
                    last_name VARCHAR(255),
                    username VARCHAR(255),
                    role VARCHAR(20) DEFAULT 'player' CHECK (role IN ('player', 'trainer', 'admin')),
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # ✓ НОВАЯ ТАБЛИЦА: Связь тренер-подопечный
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_trainee_assignments (
                    id SERIAL PRIMARY KEY,
                    trainer_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    trainee_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    assigned_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(trainer_id, trainee_id)
                )
            """)
            
            # Создаем индексы для оптимизации
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id)
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_trainer_id ON user_trainee_assignments(trainer_id)
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_trainee_id ON user_trainee_assignments(trainee_id)
            """)
            
            logger.info("✅ Таблицы БД созданы/проверены")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации таблиц: {e}")
        raise