
"""
database/teams_db.py - Работа с базой данных команд
"""

import asyncpg
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class Coach:
    telegram_id: int
    username: Optional[str]
    first_name: str
    last_name: Optional[str]
    id: Optional[int] = None
    created_at: Optional[datetime] = None

@dataclass  
class Team:
    id: int
    name: str
    description: str
    coach_id: int
    sport_type: str
    max_members: int
    created_at: datetime
    updated_at: datetime
    players_count: int = 0

@dataclass
class TeamPlayer:
    id: int
    telegram_id: Optional[int]
    team_id: int
    first_name: str
    last_name: Optional[str]
    username: Optional[str]
    position: Optional[str]
    jersey_number: Optional[int]
    joined_at: datetime
    is_active: bool

@dataclass
class IndividualStudent:
    id: int
    telegram_id: Optional[int]
    coach_id: int
    first_name: str
    last_name: Optional[str]
    username: Optional[str]
    specialization: Optional[str]
    level: str
    joined_at: datetime
    is_active: bool

class TeamsDB:
    def __init__(self, db_pool: asyncpg.Pool):
        self.pool = db_pool

    async def init_tables(self):
        """Создание таблиц"""
        try:
            async with self.pool.acquire() as conn:
                # Читаем схему из файла
                with open('teams_schema.sql', 'r', encoding='utf-8') as f:
                    schema = f.read()
                await conn.execute(schema)
                logger.info("✅ Таблицы команд инициализированы")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации таблиц команд: {e}")
            raise

    # ============== ТРЕНЕРЫ ==============

    async def register_coach(self, telegram_id: int, first_name: str, 
                           last_name: str = None, username: str = None) -> Coach:
        """Регистрация тренера"""
        async with self.pool.acquire() as conn:
            # Проверяем, существует ли тренер
            existing = await conn.fetchrow(
                "SELECT * FROM coaches WHERE telegram_id = $1",
                telegram_id
            )

            if existing:
                return Coach(
                    id=existing['id'],
                    telegram_id=existing['telegram_id'],
                    username=existing['username'],
                    first_name=existing['first_name'],
                    last_name=existing['last_name'],
                    created_at=existing['created_at']
                )

            # Создаем нового тренера
            coach_id = await conn.fetchval(
                """
                INSERT INTO coaches (telegram_id, username, first_name, last_name)
                VALUES ($1, $2, $3, $4)
                RETURNING id
                """,
                telegram_id, username, first_name, last_name
            )

            coach_data = await conn.fetchrow(
                "SELECT * FROM coaches WHERE id = $1", coach_id
            )

            logger.info(f"✅ Зарегистрирован тренер: {first_name} (ID: {telegram_id})")

            return Coach(
                id=coach_data['id'],
                telegram_id=coach_data['telegram_id'],
                username=coach_data['username'],
                first_name=coach_data['first_name'],
                last_name=coach_data['last_name'],
                created_at=coach_data['created_at']
            )

    # ============== КОМАНДЫ ==============

    async def create_team(self, coach_id: int, name: str, description: str = "", 
                         sport_type: str = "general", max_members: int = 50) -> Team:
        """Создание команды"""
        async with self.pool.acquire() as conn:
            team_id = await conn.fetchval(
                """
                INSERT INTO teams (name, description, coach_id, sport_type, max_members)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
                """,
                name, description, coach_id, sport_type, max_members
            )

            team_data = await conn.fetchrow(
                "SELECT * FROM teams WHERE id = $1", team_id
            )

            logger.info(f"✅ Создана команда: {name} (ID: {team_id})")

            return Team(
                id=team_data['id'],
                name=team_data['name'],
                description=team_data['description'],
                coach_id=team_data['coach_id'],
                sport_type=team_data['sport_type'],
                max_members=team_data['max_members'],
                created_at=team_data['created_at'],
                updated_at=team_data['updated_at']
            )

    async def get_coach_teams(self, coach_id: int) -> List[Team]:
        """Получить команды тренера"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT t.*, COUNT(tp.id) as players_count
                FROM teams t
                LEFT JOIN team_players tp ON t.id = tp.team_id AND tp.is_active = TRUE
                WHERE t.coach_id = $1
                GROUP BY t.id
                ORDER BY t.created_at DESC
                """,
                coach_id
            )

            teams = []
            for row in rows:
                team = Team(
                    id=row['id'],
                    name=row['name'],
                    description=row['description'],
                    coach_id=row['coach_id'],
                    sport_type=row['sport_type'],
                    max_members=row['max_members'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    players_count=row['players_count']
                )
                teams.append(team)

            return teams

    async def get_team(self, team_id: int) -> Optional[Team]:
        """Получить команду по ID"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT t.*, COUNT(tp.id) as players_count
                FROM teams t
                LEFT JOIN team_players tp ON t.id = tp.team_id AND tp.is_active = TRUE
                WHERE t.id = $1
                GROUP BY t.id
                """,
                team_id
            )

            if not row:
                return None

            return Team(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                coach_id=row['coach_id'],
                sport_type=row['sport_type'],
                max_members=row['max_members'],
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                players_count=row['players_count']
            )

    # ============== ИГРОКИ КОМАНД ==============

    async def add_team_player(self, team_id: int, first_name: str, last_name: str = None,
                             username: str = None, telegram_id: int = None, 
                             position: str = None, jersey_number: int = None) -> TeamPlayer:
        """Добавить игрока в команду"""
        async with self.pool.acquire() as conn:
            player_id = await conn.fetchval(
                """
                INSERT INTO team_players 
                (team_id, telegram_id, first_name, last_name, username, position, jersey_number)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
                """,
                team_id, telegram_id, first_name, last_name, username, position, jersey_number
            )

            player_data = await conn.fetchrow(
                "SELECT * FROM team_players WHERE id = $1", player_id
            )

            logger.info(f"✅ Добавлен игрок: {first_name} в команду {team_id}")

            return TeamPlayer(
                id=player_data['id'],
                telegram_id=player_data['telegram_id'],
                team_id=player_data['team_id'],
                first_name=player_data['first_name'],
                last_name=player_data['last_name'],
                username=player_data['username'],
                position=player_data['position'],
                jersey_number=player_data['jersey_number'],
                joined_at=player_data['joined_at'],
                is_active=player_data['is_active']
            )

    async def get_team_players(self, team_id: int) -> List[TeamPlayer]:
        """Получить игроков команды"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM team_players 
                WHERE team_id = $1 AND is_active = TRUE
                ORDER BY jersey_number ASC NULLS LAST, first_name ASC
                """,
                team_id
            )

            players = []
            for row in rows:
                players.append(TeamPlayer(
                    id=row['id'],
                    telegram_id=row['telegram_id'],
                    team_id=row['team_id'],
                    first_name=row['first_name'],
                    last_name=row['last_name'],
                    username=row['username'],
                    position=row['position'],
                    jersey_number=row['jersey_number'],
                    joined_at=row['joined_at'],
                    is_active=row['is_active']
                ))

            return players

    # ============== ИНДИВИДУАЛЬНЫЕ ПОДОПЕЧНЫЕ ==============

    async def add_individual_student(self, coach_id: int, first_name: str, 
                                   last_name: str = None, username: str = None,
                                   telegram_id: int = None, specialization: str = None,
                                   level: str = "beginner") -> IndividualStudent:
        """Добавить индивидуального подопечного"""
        async with self.pool.acquire() as conn:
            student_id = await conn.fetchval(
                """
                INSERT INTO individual_students 
                (coach_id, telegram_id, first_name, last_name, username, specialization, level)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
                """,
                coach_id, telegram_id, first_name, last_name, username, specialization, level
            )

            student_data = await conn.fetchrow(
                "SELECT * FROM individual_students WHERE id = $1", student_id
            )

            logger.info(f"✅ Добавлен подопечный: {first_name} к тренеру {coach_id}")

            return IndividualStudent(
                id=student_data['id'],
                telegram_id=student_data['telegram_id'],
                coach_id=student_data['coach_id'],
                first_name=student_data['first_name'],
                last_name=student_data['last_name'],
                username=student_data['username'],
                specialization=student_data['specialization'],
                level=student_data['level'],
                joined_at=student_data['joined_at'],
                is_active=student_data['is_active']
            )

    async def get_individual_students(self, coach_id: int) -> List[IndividualStudent]:
        """Получить индивидуальных подопечных"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM individual_students 
                WHERE coach_id = $1 AND is_active = TRUE
                ORDER BY first_name ASC
                """,
                coach_id
            )

            students = []
            for row in rows:
                students.append(IndividualStudent(
                    id=row['id'],
                    telegram_id=row['telegram_id'],
                    coach_id=row['coach_id'],
                    first_name=row['first_name'],
                    last_name=row['last_name'],
                    username=row['username'],
                    specialization=row['specialization'],
                    level=row['level'],
                    joined_at=row['joined_at'],
                    is_active=row['is_active']
                ))

            return students

    # ============== СТАТИСТИКА ==============

    async def get_coach_stats(self, coach_id: int) -> Dict:
        """Статистика тренера"""
        async with self.pool.acquire() as conn:
            teams_count = await conn.fetchval(
                "SELECT COUNT(*) FROM teams WHERE coach_id = $1", coach_id
            )

            team_players_count = await conn.fetchval(
                """
                SELECT COUNT(tp.*) 
                FROM team_players tp 
                JOIN teams t ON tp.team_id = t.id 
                WHERE t.coach_id = $1 AND tp.is_active = TRUE
                """, 
                coach_id
            )

            individual_students_count = await conn.fetchval(
                "SELECT COUNT(*) FROM individual_students WHERE coach_id = $1 AND is_active = TRUE",
                coach_id
            )

            return {
                'teams_count': teams_count,
                'team_players_count': team_players_count,
                'individual_students_count': individual_students_count,
                'total_athletes': team_players_count + individual_students_count
            }
