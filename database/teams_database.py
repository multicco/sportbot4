"""
database/teams_database.py - База данных для команд
ПОЛНАЯ ФУНКЦИОНАЛЬНОСТЬ с PostgreSQL
"""
from dataclasses import dataclass
from typing import Optional, List, Dict
from datetime import datetime, date
import asyncpg
import logging

logger = logging.getLogger(__name__)

@dataclass
class Team:
    id: int
    name: str
    description: str
    coach_telegram_id: int
    sport_type: str
    max_players: int
    created_at: datetime
    updated_at: datetime
    access_code: str = ""
    players_count: int = 0

@dataclass
class TeamPlayer:
    id: int
    team_id: int
    first_name: str
    last_name: Optional[str]
    position: Optional[str]
    jersey_number: Optional[int]
    telegram_id: Optional[int]
    phone: Optional[str]
    birth_date: Optional[date]
    is_active: bool
    joined_at: datetime

@dataclass
class IndividualStudent:
    id: int
    coach_telegram_id: int
    first_name: str
    last_name: Optional[str]
    telegram_id: Optional[int]
    phone: Optional[str]
    birth_date: Optional[date]
    specialization: Optional[str]
    level: str
    notes: Optional[str]
    is_active: bool
    created_at: datetime

@dataclass
class WorkoutAssignment:
    """Назначение тренировки"""
    id: int
    workout_id: int
    workout_name: str
    assigned_at: datetime
    assigned_by: int
    deadline: Optional[datetime]
    notes: Optional[str]
    total_players: int
    completed: int
    in_progress: int
    pending: int

class TeamsDatabase:
    def __init__(self, db_pool: asyncpg.Pool):
        self.pool = db_pool


    




    async def get_student_workouts(self, student_id: int) -> List[Dict]:
        """Получить все тренировки индивидуального подопечного."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT 
                    wis.id,
                    wis.workout_id,
                    w.name as workout_name,
                    w.description,
                    wis.assigned_at,
                    wis.deadline,
                    wis.notes,
                    u.first_name as assigned_by_name
                FROM workout_individual_students wis
                JOIN workouts w ON wis.workout_id = w.id
                LEFT JOIN users u ON wis.assigned_by = u.telegram_id
                WHERE wis.student_id = $1 AND wis.is_active = TRUE
                ORDER BY wis.assigned_at DESC
                """,
                student_id
            )
            
            return [dict(row) for row in rows]




    async def get_individual_student_by_id(self, student_id: int) -> Optional[IndividualStudent]:
     """Получить индивидуального подопечного по ID."""
     async with self.pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT * FROM individual_students 
            WHERE id = $1 AND is_active = TRUE
            """,
            student_id
        )
        
        if not row:
            logger.warning(f"Individual student {student_id} not found")
            return None
            
        return IndividualStudent(
            coach_telegram_id=row['coach_telegram_id'],
            first_name=row['first_name'],
            last_name=row['last_name'],
            telegram_id=row['telegram_id'],
            phone=row['phone'],
            birth_date=row['birth_date'],
            specialization=row['specialization'],
            level=row['level'],
            notes=row['notes'],
            is_active=row['is_active'],
            created_at=row['created_at'],
            id=row['id']
        )

    async def get_individual_student_by_telegram_id(self, telegram_id: int, coach_telegram_id: int) -> Optional[IndividualStudent]:
        """Проверить, есть ли уже такой подопечный у тренера"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM individual_students 
                WHERE telegram_id = $1 
                AND coach_telegram_id = $2 
                AND is_active = TRUE
                """,
                telegram_id, coach_telegram_id
            )
            
            if not row:
                return None
                
            return IndividualStudent(
                coach_telegram_id=row['coach_telegram_id'],
                first_name=row['first_name'],
                last_name=row['last_name'],
                telegram_id=row['telegram_id'],
                phone=row['phone'],
                birth_date=row['birth_date'],
                specialization=row['specialization'],
                level=row['level'],
                notes=row['notes'],
                is_active=row['is_active'],
                created_at=row['created_at'],
                id=row['id']
            )

    async def init_tables(self):
        try:
            async with self.pool.acquire() as conn:
                schema_sql = """
                -- Таблица команд
                CREATE TABLE IF NOT EXISTS teams (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    coach_telegram_id BIGINT NOT NULL,
                    sport_type VARCHAR(50) DEFAULT 'general',
                    max_players INTEGER DEFAULT 25,
                    access_code VARCHAR(20) UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Таблица игроков в командах
                CREATE TABLE IF NOT EXISTS team_players (
                    id SERIAL PRIMARY KEY,
                    team_id INTEGER REFERENCES teams(id) ON DELETE CASCADE,
                    first_name VARCHAR(100) NOT NULL,
                    last_name VARCHAR(100),
                    position VARCHAR(50),
                    jersey_number INTEGER,
                    telegram_id BIGINT,
                    phone VARCHAR(20),
                    birth_date DATE,
                    is_active BOOLEAN DEFAULT TRUE,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Таблица индивидуальных подопечных
                CREATE TABLE IF NOT EXISTS individual_students (
                    id SERIAL PRIMARY KEY,
                    coach_telegram_id BIGINT NOT NULL,
                    first_name VARCHAR(100) NOT NULL,
                    last_name VARCHAR(100),
                    telegram_id BIGINT,
                    phone VARCHAR(20),
                    birth_date DATE,
                    specialization VARCHAR(100),
                    level VARCHAR(20) DEFAULT 'beginner',
                    notes TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Таблица тренировок
                CREATE TABLE IF NOT EXISTS workouts (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    unique_id VARCHAR(20) UNIQUE,
                    created_by INTEGER,
                    visibility VARCHAR(20) DEFAULT 'public',
                    difficulty_level VARCHAR(20),
                    estimated_duration_minutes INTEGER,
                    category VARCHAR(50),
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Таблица назначений тренировок командам
                CREATE TABLE IF NOT EXISTS workout_teams (
                    id SERIAL PRIMARY KEY,
                    workout_id INTEGER REFERENCES workouts(id),
                    team_id INTEGER REFERENCES teams(id),
                    assigned_by INTEGER,
                    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    notes TEXT,
                    deadline TIMESTAMP
                );

                -- Таблица назначений тренировок игрокам
                CREATE TABLE IF NOT EXISTS workout_team_player_assignments (
                    id SERIAL PRIMARY KEY,
                    workout_team_id INTEGER REFERENCES workout_teams(id),
                    team_player_id INTEGER REFERENCES team_players(id),
                    status VARCHAR(20) DEFAULT 'pending',
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    rpe FLOAT,
                    notes TEXT
                );

                -- Индексы
                CREATE INDEX IF NOT EXISTS idx_teams_coach ON teams(coach_telegram_id);
                CREATE INDEX IF NOT EXISTS idx_team_players_team ON team_players(team_id);
                CREATE INDEX IF NOT EXISTS idx_individual_students_coach ON individual_students(coach_telegram_id);
                CREATE INDEX IF NOT EXISTS idx_workout_teams_team ON workout_teams(team_id);
                CREATE INDEX IF NOT EXISTS idx_workout_team_player_assignments ON workout_team_player_assignments(workout_team_id);
                """
                await conn.execute(schema_sql)
                logger.info("✅ Teams database tables initialized")
        except Exception as e:
            logger.error(f"❌ Error initializing teams tables: {e}", exc_info=True)
            raise


    



    # ===== КОМАНДЫ =====
    async def create_team(self, coach_telegram_id: int, name: str, description: str = "", 
                         sport_type: str = "general", max_players: int = 25) -> Team:
        """Создать команду"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
            INSERT INTO teams (name, description, coach_telegram_id, sport_type, max_players)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, name, description, coach_telegram_id, sport_type, max_players, created_at, updated_at
            """, name, description, coach_telegram_id, sport_type, max_players)
            
            team = Team(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                coach_telegram_id=row['coach_telegram_id'],
                sport_type=row['sport_type'],
                max_players=row['max_players'],
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                players_count=0
            )
            logger.info(f"✅ Created team: {name} (ID: {team.id}) by coach {coach_telegram_id}")
            return team

    async def get_coach_teams(self, coach_telegram_id: int) -> List[Team]:
        """Получить команды тренера"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
            SELECT t.*, COUNT(tp.id) as players_count
            FROM teams t
            LEFT JOIN team_players tp ON t.id = tp.team_id AND tp.is_active = TRUE
            WHERE t.coach_telegram_id = $1
            GROUP BY t.id
            ORDER BY t.created_at DESC
            """, coach_telegram_id)
            
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

    async def get_team_by_id(self, team_id: int) -> Optional[Team]:
        """Получить команду по ID"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
            SELECT t.id, t.name, t.description, t.coach_telegram_id, 
                   t.sport_type, t.max_players, t.created_at, t.updated_at,
                   t.access_code, COUNT(tp.id) as players_count
            FROM teams t
            LEFT JOIN team_players tp ON t.id = tp.team_id AND tp.is_active = TRUE
            WHERE t.id = $1
            GROUP BY t.id, t.name, t.description, t.coach_telegram_id, 
                     t.sport_type, t.max_players, t.created_at, t.updated_at, t.access_code
            """, team_id)
            
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
                access_code=row['access_code'],
                players_count=row['players_count']
            )

    # ===== ИГРОКИ КОМАНД =====
    async def add_team_player(self, team_id: int, first_name: str, last_name: str = None,
                             position: str = None, jersey_number: int = None, 
                             telegram_id: int = None, phone: str = None, 
                             birth_date: date = None) -> TeamPlayer:
        """Добавить игрока в команду"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
            INSERT INTO team_players 
            (team_id, first_name, last_name, position, jersey_number, telegram_id, phone, birth_date)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING *
            """, team_id, first_name, last_name, position, jersey_number, telegram_id, phone, birth_date)
            
            player = TeamPlayer(
                id=row['id'],
                team_id=row['team_id'],
                first_name=row['first_name'],
                last_name=row['last_name'],
                position=row['position'],
                jersey_number=row['jersey_number'],
                telegram_id=row['telegram_id'],
                phone=row['phone'],
                birth_date=row['birth_date'],
                is_active=row['is_active'],
                joined_at=row['joined_at']
            )
            logger.info(f"✅ Added player: {first_name} {last_name or ''} to team {team_id}")
            return player

    async def get_team_players(self, team_id: int) -> List[TeamPlayer]:
        """Получить игроков команды"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
            SELECT * FROM team_players 
            WHERE team_id = $1 AND is_active = TRUE
            ORDER BY jersey_number ASC NULLS LAST, first_name ASC
            """, team_id)
            
            players = []
            for row in rows:
                players.append(TeamPlayer(
                    id=row['id'],
                    team_id=row['team_id'],
                    first_name=row['first_name'],
                    last_name=row['last_name'],
                    position=row['position'],
                    jersey_number=row['jersey_number'],
                    telegram_id=row['telegram_id'],
                    phone=row['phone'],
                    birth_date=row['birth_date'],
                    is_active=row['is_active'],
                    joined_at=row['joined_at']
                ))
            return players

    # ===== ИНДИВИДУАЛЬНЫЕ ПОДОПЕЧНЫЕ =====
    async def add_individual_student(self, coach_telegram_id: int, first_name: str, 
                                   last_name: str = None, telegram_id: int = None,
                                   phone: str = None, birth_date: date = None,
                                   specialization: str = None, level: str = "beginner",
                                   notes: str = None) -> IndividualStudent:
        """Добавить индивидуального подопечного"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
            INSERT INTO individual_students 
            (coach_telegram_id, first_name, last_name, telegram_id, phone, birth_date, specialization, level, notes)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING *
            """, coach_telegram_id, first_name, last_name, telegram_id, phone, birth_date, specialization, level, notes)
            
            student = IndividualStudent(
                id=row['id'],
                coach_telegram_id=row['coach_telegram_id'],
                first_name=row['first_name'],
                last_name=row['last_name'],
                telegram_id=row['telegram_id'],
                phone=row['phone'],
                birth_date=row['birth_date'],
                specialization=row['specialization'],
                level=row['level'],
                notes=row['notes'],
                is_active=row['is_active'],
                created_at=row['created_at']
            )
            logger.info(f"✅ Added individual student: {first_name} {last_name or ''} to coach {coach_telegram_id}")
            return student

    async def get_individual_students(self, coach_telegram_id: int) -> List[IndividualStudent]:
        """Получить индивидуальных подопечных"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
            SELECT * FROM individual_students 
            WHERE coach_telegram_id = $1 AND is_active = TRUE
            ORDER BY first_name ASC
            """, coach_telegram_id)
            
            students = []
            for row in rows:
                students.append(IndividualStudent(
                    id=row['id'],
                    coach_telegram_id=row['coach_telegram_id'],
                    first_name=row['first_name'],
                    last_name=row['last_name'],
                    telegram_id=row['telegram_id'],
                    phone=row['phone'],
                    birth_date=row['birth_date'],
                    specialization=row['specialization'],
                    level=row['level'],
                    notes=row['notes'],
                    is_active=row['is_active'],
                    created_at=row['created_at']
                ))
            return students

    # ===== СТАТИСТИКА =====
    async def get_coach_statistics(self, coach_telegram_id: int) -> Dict:
        """Получить статистику тренера"""
        async with self.pool.acquire() as conn:
            stats = await conn.fetchrow("""
            SELECT 
                (SELECT COUNT(*) FROM teams WHERE coach_telegram_id = $1) as teams_count,
                (SELECT COUNT(*) FROM team_players tp 
                 JOIN teams t ON tp.team_id = t.id 
                 WHERE t.coach_telegram_id = $1 AND tp.is_active = TRUE) as team_players_count,
                (SELECT COUNT(*) FROM individual_students 
                 WHERE coach_telegram_id = $1 AND is_active = TRUE) as individual_students_count
            """, coach_telegram_id)
            
            return {
                'teams_count': stats['teams_count'],
                'team_players_count': stats['team_players_count'],
                'individual_students_count': stats['individual_students_count'],
                'total_athletes': stats['team_players_count'] + stats['individual_students_count']
            }

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

    async def find_user_by_telegram_id(self, telegram_id: int) -> Optional[Dict]:
        """Найти пользователя Telegram по ID"""
        async with self.pool.acquire() as conn:
            # Проверяем, есть ли пользователь в системе
            user_row = await conn.fetchrow("""
            SELECT id, telegram_id, first_name, last_name, username
            FROM users
            WHERE telegram_id = $1
            """, telegram_id)

            if user_row:
                return {
                    'id': user_row['id'],
                    'telegram_id': user_row['telegram_id'],
                    'first_name': user_row['first_name'],
                    'last_name': user_row['last_name'],
                    'username': user_row['username']
                }
            return None

    async def find_user_by_username(self, username: str) -> Optional[Dict]:
        """Найти пользователя по username Telegram (@username)"""
        # Убираем @ если передали с ним и приводим к нижнему регистру
        clean_username = username.lstrip('@').strip().lower()
        
        if not clean_username:
            return None
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, telegram_id, first_name, last_name, username 
                FROM users 
                WHERE LOWER(username) = $1
                LIMIT 1
                """,
                clean_username
            )
            
            if row:
                return {
                    'id': row['id'],
                    'telegram_id': row['telegram_id'],
                    'first_name': row['first_name'],
                    'last_name': row['last_name'],
                    'username': row['username']
                }
            return None

    async def add_player_by_telegram_id(self, team_id: int, telegram_id: int, 
                                       added_by: int) -> Optional[TeamPlayer]:
        """Добавить игрока в команду по Telegram ID"""
        async with self.pool.acquire() as conn:
            # Проверяем, не состоит ли уже в команде
            existing = await conn.fetchval("""
            SELECT COUNT(*) FROM team_players
            WHERE team_id = $1 AND telegram_id = $2 AND is_active = TRUE
            """, team_id, telegram_id)

            if existing > 0:
                return None  # Уже в команде

            # Получаем информацию о пользователе
            user_info = await self.find_user_by_telegram_id(telegram_id)

            if user_info:
                # Пользователь есть в системе
                row = await conn.fetchrow("""
                INSERT INTO team_players 
                (team_id, telegram_id, first_name, last_name)
                VALUES ($1, $2, $3, $4)
                RETURNING *
                """, team_id, telegram_id, 
                    user_info['first_name'], 
                    user_info.get('last_name'))
            else:
                # Пользователя нет в системе - добавляем базовую информацию
                row = await conn.fetchrow("""
                INSERT INTO team_players 
                (team_id, telegram_id, first_name)
                VALUES ($1, $2, $3)
                RETURNING *
                """, team_id, telegram_id, f"User {telegram_id}")

            return TeamPlayer(
                id=row['id'],
                team_id=row['team_id'],
                first_name=row['first_name'],
                last_name=row.get('last_name'),
                position=row.get('position'),
                jersey_number=row.get('jersey_number'),
                telegram_id=row['telegram_id'],
                phone=row.get('phone'),
                birth_date=row.get('birth_date'),
                is_active=row['is_active'],
                joined_at=row['joined_at']
            )

    async def update_team_access_code(self, team_id: int, access_code: str) -> bool:
        """Обновить код доступа команды"""
        async with self.pool.acquire() as conn:
            try:
                await conn.execute("""
                UPDATE teams 
                SET access_code = $1, updated_at = CURRENT_TIMESTAMP
                WHERE id = $2
                """, access_code, team_id)
                return True
            except Exception as e:
                logger.error(f"Error updating access code: {e}")
                return False

    # ===== НАЗНАЧЕНИЕ ТРЕНИРОВОК КОМАНДАМ =====
    async def assign_workout_to_team(
        self,
        workout_id: int,
        team_id: int,
        assigned_by: int,  # telegram-id тренера
        notes: str = None,
        deadline: datetime = None
    ) -> bool:
        """Назначить тренировку команде"""
        async with self.pool.acquire() as conn:
            try:
                # 1. Получаем внутренний id тренера из users
                user_row = await conn.fetchrow(
                    "SELECT id FROM users WHERE telegram_id = $1", assigned_by
                )
                if user_row:
                    real_user_id = user_row["id"]
                else:
                    # тренера ещё нет в users – добавляем
                    real_user_id = await conn.fetchval(
                        "INSERT INTO users (telegram_id, first_name, role, is_active) "
                        "VALUES ($1, 'Тренер', 'coach', true) RETURNING id",
                        assigned_by
                    )

                # 2. Создаем назначение команде (уже real_user_id)
                workout_team_id = await conn.fetchval("""
                    INSERT INTO workout_teams 
                    (workout_id, team_id, assigned_by, notes, deadline)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (workout_id, team_id) 
                    DO UPDATE SET 
                        assigned_at = CURRENT_TIMESTAMP,
                        is_active = TRUE,
                        notes = $4,
                        deadline = $5
                    RETURNING id
                """, workout_id, team_id, real_user_id, notes, deadline)

                # 3. Получаем всех активных игроков команды
                players = await conn.fetch("""
                    SELECT id FROM team_players
                    WHERE team_id = $1 AND is_active = TRUE
                """, team_id)

                # 4. Создаем индивидуальные назначения для каждого игрока
                for player in players:
                    await conn.execute("""
                        INSERT INTO workout_team_player_assignments
                        (workout_team_id, team_player_id, status)
                        VALUES ($1, $2, 'pending')
                        ON CONFLICT (workout_team_id, team_player_id) DO NOTHING
                    """, workout_team_id, player['id'])

                logger.info(
                    "✅ Assigned workout %s to team %s, %s players (by user-db-id %s)",
                    workout_id, team_id, len(players), real_user_id
                )
                return True

            except Exception as e:
                logger.error(f"Error assigning workout to team: {e}")
                return False

    # async def assign_workout_to_student(self, workout_id: int, student_id: int,
    #                               assigned_by: int, notes: str = None,
    #                               deadline: datetime = None) -> Dict:
    #     """Назначить тренировку индивидуальному подопечному (создаёт новое или реактивирует архивное)"""
    #     async with self.pool.acquire() as conn:
    #         try:
    #             # Проверяем, есть ли активное назначение
    #             active = await conn.fetchrow("""
    #                 SELECT id, status 
    #                 FROM workout_individual_students
    #                 WHERE workout_id = $1 
    #                 AND student_id = $2 
    #                 AND is_active = TRUE
    #                 AND status IN ('pending', 'in_progress')
    #             """, workout_id, student_id)
                
    #             if active:
    #                 logger.warning(f"⚠️ Уже есть активное назначение: workout_id={workout_id}, student_id={student_id}")
    #                 return {"error": "already_active", "message": "У подопечного уже есть активное назначение этой тренировки"}
                
    #             # Проверяем, было ли архивное назначение (чтобы понять, создаём новое или обновляем)
    #             archived = await conn.fetchrow("""
    #                 SELECT id 
    #                 FROM workout_individual_students
    #                 WHERE workout_id = $1 
    #                 AND student_id = $2
    #             """, workout_id, student_id)
                
    #             if archived:
    #                 # Реактивируем существующее, сбрасывая статус и прогресс
    #                 row = await conn.fetchrow("""
    #                     UPDATE workout_individual_students
    #                     SET is_active = TRUE,
    #                         status = 'pending',
    #                         assigned_by = $3,
    #                         assigned_at = CURRENT_TIMESTAMP,
    #                         notes = $4,
    #                         deadline = $5,
    #                         started_at = NULL,
    #                         completed_at = NULL,
    #                         archived_at = NULL,
    #                         rpe = NULL,
    #                         session_id = NULL
    #                     WHERE workout_id = $1 AND student_id = $2
    #                     RETURNING *
    #                 """, workout_id, student_id, assigned_by, notes, deadline)
                    
    #                 logger.info(f"🔄 Реактивировано назначение: workout_id={workout_id}, student_id={student_id}")
    #             else:
    #                 # Создаём новое назначение
    #                 row = await conn.fetchrow("""
    #                     INSERT INTO workout_individual_students
    #                     (workout_id, student_id, assigned_by, notes, deadline, status, is_active)
    #                     VALUES ($1, $2, $3, $4, $5, 'pending', TRUE)
    #                     RETURNING *
    #                 """, workout_id, student_id, assigned_by, notes, deadline)
                    
    #                 logger.info(f"✅ Создано новое назначение: workout_id={workout_id}, student_id={student_id}")
                
    #             return dict(row) if row else None

    #         except Exception as e:
    #             logger.error(f"❌ Ошибка назначения тренировки: {e}", exc_info=True)
    #             return None
    


    async def assign_workout_to_student(self, workout_id: int, student_id: int,
                                    assigned_by: int, notes: str = None,
                                    deadline: datetime = None) -> Dict:
        """Назначить тренировку индивидуальному подопечному (создаёт новое или реактивирует архивное)"""
        async with self.pool.acquire() as conn:
            try:
                # Проверяем, есть ли активное назначение
                active = await conn.fetchrow("""
                    SELECT id, status 
                    FROM workout_individual_students
                    WHERE workout_id = $1 
                    AND student_id = $2 
                    AND is_active = TRUE
                    AND status IN ('pending', 'in_progress')
                """, workout_id, student_id)
                
                if active:
                    logger.warning(f"⚠️ Уже есть активное назначение: workout_id={workout_id}, student_id={student_id}")
                    return {"error": "already_active", "message": "У подопечного уже есть активное назначение этой тренировки"}
                
                # Проверяем, было ли архивное назначение
                archived = await conn.fetchrow("""
                    SELECT id 
                    FROM workout_individual_students
                    WHERE workout_id = $1 
                    AND student_id = $2
                """, workout_id, student_id)
                
                if archived:
                    # Реактивируем существующее
                    row = await conn.fetchrow("""
                        UPDATE workout_individual_students
                        SET is_active = TRUE,
                            status = 'pending',
                            assigned_by = $3,
                            assigned_at = CURRENT_TIMESTAMP,
                            notes = $4,
                            deadline = $5,
                            started_at = NULL,
                            completed_at = NULL,
                            archived_at = NULL,
                            rpe = NULL
                        WHERE workout_id = $1 AND student_id = $2
                        RETURNING *
                    """, workout_id, student_id, assigned_by, notes, deadline)
                    
                    logger.info(f"🔄 Реактивировано назначение: workout_id={workout_id}, student_id={student_id}")
                else:
                    # Создаём новое назначение
                    row = await conn.fetchrow("""
                        INSERT INTO workout_individual_students
                        (workout_id, student_id, assigned_by, notes, deadline, status, is_active)
                        VALUES ($1, $2, $3, $4, $5, 'pending', TRUE)
                        RETURNING *
                    """, workout_id, student_id, assigned_by, notes, deadline)
                    
                    logger.info(f"✅ Создано новое назначение: workout_id={workout_id}, student_id={student_id}")
                
                return dict(row) if row else None

            except Exception as e:
                logger.error(f"❌ Ошибка назначения тренировки: {e}", exc_info=True)
                return None



    # async def get_workout_with_exercises(self, workout_id: int) -> Optional[Dict]:
    #     """
    #     Получить тренировку со всеми блоками и упражнениями.
    #     Возвращает структуру: {workout, blocks: [{block, exercises: [...]}]}
    #     """
    #     async with self.pool.acquire() as conn:
    #         # Получить саму тренировку
    #         workout = await conn.fetchrow(
    #             """
    #             SELECT id, name, description, created_by, created_at, unique_id
    #             FROM workouts
    #             WHERE id = $1
    #             """,
    #             workout_id
    #         )
            
    #         if not workout:
    #             return None
            
    #         # Получить все блоки тренировки
    #         blocks = await conn.fetch(
    #             """
    #             SELECT id, name, description, position
    #             FROM workout_blocks
    #             WHERE workout_id = $1
    #             ORDER BY position ASC
    #             """,
    #             workout_id
    #         )
            
    #         result = {
    #             'workout': dict(workout),
    #             'blocks': []
    #         }
            
    #         # Для каждого блока получить упражнения
    #         for block in blocks:
    #             exercises = await conn.fetch(
    #                 """
    #                 SELECT 
    #                     wbe.id,
    #                     wbe.exercise_id,
    #                     e.name as exercise_name,
    #                     e.description as exercise_description,
    #                     e.video_url,
    #                     e.image_url,
    #                     wbe.sets,
    #                     wbe.reps,
    #                     wbe.weight,
    #                     wbe.duration,
    #                     wbe.rest_time,
    #                     wbe.position
    #                 FROM workout_block_exercises wbe
    #                 JOIN exercises e ON wbe.exercise_id = e.id
    #                 WHERE wbe.block_id = $1
    #                 ORDER BY wbe.position ASC
    #                 """,
    #                 block['id']
    #             )
                
    #             result['blocks'].append({
    #                 'block': dict(block),
    #                 'exercises': [dict(ex) for ex in exercises]
    #             })
            
    #         return result    


    # async def get_workout_with_exercises(self, workout_id: int) -> Optional[Dict]:
    #     async with self.pool.acquire() as conn:
    #         workout = await conn.fetchrow(
    #             "SELECT id, name, description, created_by, created_at, unique_id FROM workouts WHERE id = $1",
    #             workout_id
    #         )
    #         if not workout:
    #             return None

    #         # Блоки — без position, сортировка по id
    #         blocks = await conn.fetch(
    #             """
    #             SELECT id, workout_id, name, description
    #             FROM workout_blocks 
    #             WHERE workout_id = $1 
    #             ORDER BY id ASC
    #             """,
    #             workout_id
    #         )

    #         result = {'workout': dict(workout), 'blocks': []}

    #         for block in blocks:
    #             # Упражнения — без position, сортировка по id
    #             exercises = await conn.fetch(
    #                 """
    #                 SELECT 
    #                     wbe.id,
    #                     wbe.exercise_id,
    #                     e.name as exercise_name,
    #                     e.description as exercise_description,
    #                     e.video_url,
    #                     e.image_url,
    #                     wbe.sets,
    #                     wbe.reps,
    #                     wbe.weight,
    #                     wbe.duration,
    #                     wbe.rest_time
    #                 FROM workout_block_exercises wbe
    #                 JOIN exercises e ON wbe.exercise_id = e.id
    #                 WHERE wbe.block_id = $1
    #                 ORDER BY wbe.id ASC
    #                 """,
    #                 block['id']
    #             )

    #             result['blocks'].append({
    #                 'block': dict(block),
    #                 'exercises': [dict(ex) for ex in exercises]
    #             })

    #     return result


    async def get_workout_with_exercises(self, workout_id: int) -> Optional[Dict]:
     async with self.pool.acquire() as conn:
        workout = await conn.fetchrow(
            "SELECT id, name, description, created_by, created_at, unique_id FROM workouts WHERE id = $1",
            workout_id
        )
        if not workout:
            return None

        # Читаем из workout_exercises
        exercises = await conn.fetch("""
            SELECT 
                phase as block_name,
                we.id as workout_exercise_id,
                exercise_id,
                e.name as exercise_name,
                e.description as exercise_description,
                e.video_url,
                e.image_url,
                sets,
                reps_min,
                reps_max,
                one_rm_percent,
                rest_seconds as rest_time
            FROM workout_exercises we
            LEFT JOIN exercises e ON we.exercise_id = e.id
            WHERE we.workout_id = $1
            ORDER BY we.phase, we.order_in_phase
        """, workout_id)

        from collections import defaultdict
        blocks_map = defaultdict(list)
        for ex in exercises:
            blocks_map[ex['block_name']].append(dict(ex))

        result = {'workout': dict(workout), 'blocks': []}
        for phase, exs in blocks_map.items():
            result['blocks'].append({
                'block': {'name': phase, 'description': ''},
                'exercises': exs
            })

        return result

  

    async def get_team_workouts(self, team_id: int) -> List[WorkoutAssignment]:
        """Получить назначенные тренировки команды с прогрессом"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
            SELECT 
                wt.id,
                wt.workout_id,
                w.name as workout_name,
                wt.assigned_at,
                wt.assigned_by,
                wt.deadline,
                wt.notes,
                COUNT(wtpa.id) as total_players,
                COUNT(CASE WHEN wtpa.status = 'completed' THEN 1 END) as completed,
                COUNT(CASE WHEN wtpa.status = 'in_progress' THEN 1 END) as in_progress,
                COUNT(CASE WHEN wtpa.status = 'pending' THEN 1 END) as pending
            FROM workout_teams wt
            JOIN workouts w ON wt.workout_id = w.id
            LEFT JOIN workout_team_player_assignments wtpa ON wt.id = wtpa.workout_team_id
            WHERE wt.team_id = $1 AND wt.is_active = TRUE
            GROUP BY wt.id, w.name, wt.assigned_at, wt.assigned_by, wt.deadline, wt.notes
            ORDER BY wt.assigned_at DESC
            """, team_id)

            return [WorkoutAssignment(
                id=row['id'],
                workout_id=row['workout_id'],
                workout_name=row['workout_name'],
                assigned_at=row['assigned_at'],
                assigned_by=row['assigned_by'],
                deadline=row['deadline'],
                notes=row['notes'],
                total_players=row['total_players'],
                completed=row['completed'],
                in_progress=row['in_progress'],
                pending=row['pending']
            ) for row in rows]

    # ===== НОВЫЙ КОД =====
    # ===== ИСПРАВЛЕННЫЙ КОД =====
    async def get_player_workouts(self, telegram_id: int) -> List[Dict]:
        """Получить ВСЕ тренировки: из команд И индивидуальные"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM (
                    SELECT
                    w.id as workout_id,
                    w.name as workout_name,
                    w.description,
                    w.unique_id as workout_code,
                    wt.assigned_at,
                    wt.deadline,
                    wt.notes as coach_notes,
                    wtpa.status,
                    wtpa.rpe,
                    wtpa.completed_at,
                    t.name as team_name,
                    t.id as team_id
                    FROM workout_team_player_assignments wtpa
                    JOIN workout_teams wt ON wtpa.workout_team_id = wt.id
                    JOIN workouts w ON wt.workout_id = w.id
                    JOIN team_players tp ON wtpa.team_player_id = tp.id
                    JOIN teams t ON wt.team_id = t.id
                    WHERE tp.telegram_id = $1 AND tp.is_active = TRUE AND wt.is_active = TRUE
                    
                    UNION ALL
                    
                    SELECT
                    w.id as workout_id,
                    w.name as workout_name,
                    w.description,
                    w.unique_id as workout_code,
                    wis.assigned_at,
                    wis.deadline,
                    wis.notes as coach_notes,
                    'pending'::text as status,
                    NULL::float as rpe,
                    NULL::timestamp as completed_at,
                    NULL::text as team_name,
                    NULL::int as team_id
                    FROM workout_individual_students wis
                    JOIN workouts w ON wis.workout_id = w.id
                    JOIN individual_students s ON wis.student_id = s.id
                    WHERE s.telegram_id = $1 AND s.is_active = TRUE AND wis.is_active = TRUE
                ) AS combined
                ORDER BY
                CASE status
                WHEN 'pending' THEN 1
                WHEN 'in_progress' THEN 2
                WHEN 'completed' THEN 3
                WHEN 'skipped' THEN 4
                END,
                assigned_at DESC
            """, telegram_id)
            
            return [dict(row) for row in rows]
# ===== КОНЕЦ =====

    # ===== КОНЕЦ НОВОГО КОДА =====


    # async def update_player_workout_status(self, telegram_id: int, workout_id: int,
    #                                      status: str, rpe: float = None,
    #                                      session_id: int = None, notes: str = None) -> bool:
    #     """Обновить статус выполнения тренировки игроком"""
    #     async with self.pool.acquire() as conn:
    #         try:
    #             # Находим назначение
    #             assignment = await conn.fetchrow("""
    #             SELECT wtpa.id
    #             FROM workout_team_player_assignments wtpa
    #             JOIN workout_teams wt ON wtpa.workout_team_id = wt.id
    #             JOIN team_players tp ON wtpa.team_player_id = tp.id
    #             WHERE tp.telegram_id = $1 AND wt.workout_id = $2
    #             LIMIT 1
    #             """, telegram_id, workout_id)

    #             if not assignment:
    #                 return False

    #             # Обновляем статус
    #             update_fields = ["status = $2"]
    #             params = [assignment['id'], status]
    #             param_count = 2

    #             if status == 'in_progress':
    #                 update_fields.append(f"started_at = CURRENT_TIMESTAMP")
    #             elif status == 'completed':
    #                 update_fields.append(f"completed_at = CURRENT_TIMESTAMP")
    #                 if rpe:
    #                     param_count += 1
    #                     update_fields.append(f"rpe = ${param_count}")
    #                     params.append(rpe)
    #                 if session_id:
    #                     param_count += 1
    #                     update_fields.append(f"session_id = ${param_count}")
    #                     params.append(session_id)

    #             if notes:
    #                 param_count += 1
    #                 update_fields.append(f"notes = ${param_count}")
    #                 params.append(notes)

    #             query = f"""
    #             UPDATE workout_team_player_assignments
    #             SET {', '.join(update_fields)}
    #             WHERE id = $1
    #             """

    #             await conn.execute(query, *params)
    #             logger.info(f"✅ Updated workout status for user {telegram_id}: {status}")
    #             return True

    #         except Exception as e:
    #             logger.error(f"Error updating workout status: {e}")
    #             return False



    async def update_player_workout_status(self, telegram_id: int, workout_id: int,
                                        status: str, rpe: float = None,
                                        session_id: int = None, notes: str = None) -> bool:
        """Обновить статус выполнения тренировки (индивидуальный, команда, или сам тренер)"""
        async with self.pool.acquire() as conn:
            try:
                # ===== 1️⃣ ВАРИАНТ 1: Индивидуальный подопечный =====
                assignment = await conn.fetchrow("""
                    SELECT 'individual'::text as type, wis.id
                    FROM workout_individual_students wis
                    JOIN individual_students s ON wis.student_id = s.id
                    WHERE s.telegram_id = $1 AND wis.workout_id = $2 AND wis.is_active = TRUE
                    LIMIT 1
                """, telegram_id, workout_id)
                
                # ===== 2️⃣ ВАРИАНТ 2: Команда =====
                if not assignment:
                    assignment = await conn.fetchrow("""
                        SELECT 'team'::text as type, wtpa.id
                        FROM workout_team_player_assignments wtpa
                        JOIN workout_teams wt ON wtpa.workout_team_id = wt.id
                        JOIN team_players tp ON wtpa.team_player_id = tp.id
                        WHERE tp.telegram_id = $1 AND wt.workout_id = $2 AND wt.is_active = TRUE
                        LIMIT 1
                    """, telegram_id, workout_id)
                
                # ===== 3️⃣ ВАРИАНТ 3: Сам тренер (для теста/демо) =====
                if not assignment:
                    # Проверяем, что это тренер и тренировка существует
                    trainer = await conn.fetchrow("""
                        SELECT u.id as user_id
                        FROM users u
                        WHERE u.telegram_id = $1 AND u.role IN ('admin', 'trainer', 'coach')
                    """, telegram_id)
                    
                    if trainer:
                        workout = await conn.fetchrow("""
                            SELECT id FROM workouts WHERE id = $1 AND is_active = TRUE
                        """, workout_id)
                        
                        if workout:
                            # Для тренера: создаем временную сессию если её нет
                            session = await conn.fetchrow("""
                                SELECT id FROM workout_sessions
                                WHERE user_id = $1 AND workout_id = $2 AND status = $3
                                LIMIT 1
                            """, trainer['user_id'], workout_id, status)
                            
                            if not session:
                                # Создаём сессию для тренера
                                session_id = await conn.fetchval("""
                                    INSERT INTO workout_sessions (user_id, workout_id, status, started_at, created_at)
                                    VALUES ($1, $2, $3, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                                    RETURNING id
                                """, trainer['user_id'], workout_id, 'in_progress')
                                
                                logger.info(f"✅ Создана сессия {session_id} для тренера {telegram_id} (тренировка {workout_id})")
                                return True
                            else:
                                # Обновляем существующую сессию
                                await conn.execute("""
                                    UPDATE workout_sessions
                                    SET status = $1::varchar, started_at = CASE WHEN status = 'pending' THEN CURRENT_TIMESTAMP ELSE started_at END,
                                        completed_at = CASE WHEN $1::varchar = 'completed' THEN CURRENT_TIMESTAMP ELSE NULL END
                                    WHERE id = $2
                                """, status, session['id'])
                                
                                logger.info(f"✅ Обновлена сессия {session['id']} для тренера {telegram_id}")
                                return True
                
                if not assignment:
                    logger.error(f"❌ Не найдено назначение: telegram_id={telegram_id}, workout_id={workout_id}")
                    return False
                
                # ===== Обновляем найденное назначение =====
                table_name = "workout_individual_students" if assignment['type'] == 'individual' else "workout_team_player_assignments"
                
                update_fields = ["status = $2"]
                params = [assignment['id'], status]
                param_count = 2
                
                if status == 'in_progress':
                    update_fields.append("started_at = CURRENT_TIMESTAMP")
                elif status in ('completed', 'archived'):
                    # При архивации тоже ставим completed_at
                    update_fields.append("completed_at = CURRENT_TIMESTAMP")
                
                if rpe:
                    param_count += 1
                    update_fields.append(f"rpe = ${param_count}")
                    params.append(rpe)
                
                if session_id:
                    param_count += 1
                    update_fields.append(f"session_id = ${param_count}")
                    params.append(session_id)
                
                if notes:
                    param_count += 1
                    update_fields.append(f"notes = ${param_count}")
                    params.append(notes)
                
                # Для archived дополнительно деактивируем назначение
                if status == 'archived':
                    if assignment['type'] == 'individual':
                        update_fields.append("is_active = FALSE")
                        update_fields.append("archived_at = CURRENT_TIMESTAMP")
                    # Для командных можно добавить логику при необходимости
                
                query = f"""
                    UPDATE {table_name}
                    SET {', '.join(update_fields)}
                    WHERE id = $1
                """
                
                await conn.execute(query, *params)
                assignment_type = "индивидуальная" if assignment['type'] == 'individual' else "команда"
                logger.info(f"✅ Обновлен статус тренировки {workout_id} для {telegram_id} ({assignment_type}): {status}")
                return True
                
            except Exception as e:
                logger.error(f"❌ Ошибка обновления статуса: {e}", exc_info=True)
                return False



    async def get_team_workout_progress(self, workout_team_id: int) -> List[Dict]:
        """Получить детальный прогресс по тренировке для команды"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
            SELECT 
                tp.first_name,
                tp.last_name,
                tp.jersey_number,
                wtpa.status,
                wtpa.started_at,
                wtpa.completed_at,
                wtpa.rpe,
                wtpa.notes
            FROM workout_team_player_assignments wtpa
            JOIN team_players tp ON wtpa.team_player_id = tp.id
            WHERE wtpa.workout_team_id = $1
            ORDER BY 
                CASE wtpa.status
                    WHEN 'completed' THEN 1
                    WHEN 'in_progress' THEN 2
                    WHEN 'pending' THEN 3
                    WHEN 'skipped' THEN 4
                END,
                tp.first_name
            """, workout_team_id)

            return [dict(row) for row in rows]

    async def get_workout_by_code(self, code: str, user_id: int) -> Optional[Dict]:
        """Найти тренировку по коду (учитывая приватность)"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
            SELECT 
                w.id,
                w.unique_id,
                w.name,
                w.description,
                w.visibility,
                w.created_by,
                w.difficulty_level,
                w.estimated_duration_minutes,
                
                u.first_name as creator_name,
                u.last_name as creator_last_name
            FROM workouts w
            LEFT JOIN users u ON w.created_by = u.id
            WHERE w.unique_id = $1 
                AND w.is_active = TRUE
                AND (w.visibility = 'public' OR w.created_by = $2)
            """, code, user_id)

            return dict(row) if row else None
        


    


# Глобальная переменная для БД
teams_database = None

def init_teams_database(db_pool: asyncpg.Pool) -> TeamsDatabase:
    """Инициализация БД команд"""
    global teams_database
    teams_database = TeamsDatabase(db_pool)
    logger.info("✅ teams_database инициализирована")
    return teams_database