
-- ===== СХЕМА БАЗЫ ДАННЫХ =====
-- database/teams_schema.sql

-- Таблица тренеров
CREATE TABLE IF NOT EXISTS coaches (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(50),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица команд (много игроков)
CREATE TABLE IF NOT EXISTS teams (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    coach_id BIGINT NOT NULL,
    sport_type VARCHAR(50) DEFAULT 'general',
    max_members INTEGER DEFAULT 50,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (coach_id) REFERENCES coaches(telegram_id) ON DELETE CASCADE
);

-- Таблица игроков команд  
CREATE TABLE IF NOT EXISTS team_players (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT,
    team_id INTEGER NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100),
    username VARCHAR(50),
    position VARCHAR(50),
    jersey_number INTEGER,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE
);

-- Таблица индивидуальных подопечных (1-на-1 тренировки)
CREATE TABLE IF NOT EXISTS individual_students (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT,
    coach_id BIGINT NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100),
    username VARCHAR(50),
    specialization VARCHAR(100), -- Специализация (бег, силовые, etc)
    level VARCHAR(20) DEFAULT 'beginner', -- beginner, intermediate, advanced
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (coach_id) REFERENCES coaches(telegram_id) ON DELETE CASCADE
);

-- Индексы для производительности
CREATE INDEX IF NOT EXISTS idx_teams_coach_id ON teams(coach_id);
CREATE INDEX IF NOT EXISTS idx_team_players_team_id ON team_players(team_id);
CREATE INDEX IF NOT EXISTS idx_individual_students_coach_id ON individual_students(coach_id);
