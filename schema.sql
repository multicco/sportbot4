-- ===== СПОРТИВНЫЙ TELEGRAM БОТ - СХЕМА БАЗЫ ДАННЫХ =====
-- Версия: 1.0
-- Дата: 2025-10-13

-- ===== ПОЛЬЗОВАТЕЛИ =====
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100),
    username VARCHAR(50),
    role VARCHAR(20) DEFAULT 'player' CHECK (role IN ('player', 'coach', 'admin')),
    body_weight DECIMAL(5,2) DEFAULT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_active_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- ===== УПРАЖНЕНИЯ =====
CREATE TABLE IF NOT EXISTS exercises (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    category VARCHAR(100) NOT NULL,
    muscle_group VARCHAR(100) NOT NULL,
    description TEXT,
    instructions TEXT,
    difficulty_level VARCHAR(20) DEFAULT 'beginner' CHECK (difficulty_level IN ('beginner', 'intermediate', 'advanced')),
    equipment VARCHAR(100),
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- ===== РЕЗУЛЬТАТЫ 1ПМ ТЕСТОВ =====
CREATE TABLE IF NOT EXISTS one_rep_max (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    exercise_id INTEGER REFERENCES exercises(id) ON DELETE CASCADE,
    weight DECIMAL(5,2) NOT NULL,
    reps INTEGER NOT NULL CHECK (reps > 0 AND reps <= 30),
    test_weight DECIMAL(5,2) NOT NULL,
    formula_brzycki DECIMAL(5,2),
    formula_epley DECIMAL(5,2),
    formula_alternative DECIMAL(5,2),
    formula_average DECIMAL(5,2),
    tested_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

-- ===== ТРЕНИРОВКИ =====
CREATE TABLE IF NOT EXISTS workouts (
    id SERIAL PRIMARY KEY,
    unique_id VARCHAR(10) UNIQUE NOT NULL DEFAULT substring(md5(random()::text) from 1 for 8),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    created_by INTEGER REFERENCES users(id),
    visibility VARCHAR(20) DEFAULT 'private' CHECK (visibility IN ('private', 'public', 'team')),
    difficulty_level VARCHAR(20) DEFAULT 'intermediate' CHECK (difficulty_level IN ('beginner', 'intermediate', 'advanced')),
    estimated_duration_minutes INTEGER DEFAULT 60,
    category VARCHAR(100) DEFAULT 'general',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- ===== УПРАЖНЕНИЯ В ТРЕНИРОВКАХ =====
CREATE TABLE IF NOT EXISTS workout_exercises (
    id SERIAL PRIMARY KEY,
    workout_id INTEGER REFERENCES workouts(id) ON DELETE CASCADE,
    exercise_id INTEGER REFERENCES exercises(id),
    phase VARCHAR(50) NOT NULL CHECK (phase IN ('warmup', 'nervous_prep', 'main', 'cooldown')),
    order_in_phase INTEGER NOT NULL,
    sets INTEGER NOT NULL CHECK (sets > 0 AND sets <= 20),
    reps_min INTEGER CHECK (reps_min > 0 AND reps_min <= 200),
    reps_max INTEGER CHECK (reps_max >= reps_min AND reps_max <= 200),
    one_rm_percent INTEGER CHECK (one_rm_percent >= 30 AND one_rm_percent <= 120),
    rest_seconds INTEGER DEFAULT 90,
    notes TEXT
);

-- ===== ВЫПОЛНЕНИЯ ТРЕНИРОВОК =====
CREATE TABLE IF NOT EXISTS workout_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    workout_id INTEGER REFERENCES workouts(id),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'in_progress' CHECK (status IN ('in_progress', 'completed', 'paused', 'cancelled')),
    total_duration_minutes INTEGER,
    average_rpe DECIMAL(3,1),
    notes TEXT
);

-- ===== ВЫПОЛНЕНИЯ УПРАЖНЕНИЙ В ТРЕНИРОВКЕ =====
CREATE TABLE IF NOT EXISTS exercise_sessions (
    id SERIAL PRIMARY KEY,
    workout_session_id INTEGER REFERENCES workout_sessions(id) ON DELETE CASCADE,
    workout_exercise_id INTEGER REFERENCES workout_exercises(id),
    set_number INTEGER NOT NULL,
    reps_completed INTEGER,
    weight_used DECIMAL(5,2),
    rpe DECIMAL(3,1) CHECK (rpe >= 1 AND rpe <= 10),
    rest_seconds INTEGER,
    completed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

-- ===== КОМАНДЫ =====
CREATE TABLE IF NOT EXISTS teams (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    coach_id INTEGER REFERENCES users(id),
    access_code VARCHAR(20) UNIQUE NOT NULL DEFAULT substring(md5(random()::text) from 1 for 8),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- ===== УЧАСТНИКИ КОМАНД =====
CREATE TABLE IF NOT EXISTS team_members (
    id SERIAL PRIMARY KEY,
    team_id INTEGER REFERENCES teams(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    role VARCHAR(20) DEFAULT 'player' CHECK (role IN ('player', 'assistant_coach')),
    is_active BOOLEAN DEFAULT true,
    UNIQUE(team_id, user_id)
);

-- ===== ИНДЕКСЫ ДЛЯ ПРОИЗВОДИТЕЛЬНОСТИ =====
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_exercises_category ON exercises(category);
CREATE INDEX IF NOT EXISTS idx_exercises_muscle_group ON exercises(muscle_group);
CREATE INDEX IF NOT EXISTS idx_one_rep_max_user_exercise ON one_rep_max(user_id, exercise_id);
CREATE INDEX IF NOT EXISTS idx_one_rep_max_tested_at ON one_rep_max(tested_at);
CREATE INDEX IF NOT EXISTS idx_workouts_created_by ON workouts(created_by);
CREATE INDEX IF NOT EXISTS idx_workouts_unique_id ON workouts(unique_id);
CREATE INDEX IF NOT EXISTS idx_workout_exercises_workout_id ON workout_exercises(workout_id);
CREATE INDEX IF NOT EXISTS idx_workout_sessions_user_id ON workout_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_teams_access_code ON teams(access_code);
CREATE INDEX IF NOT EXISTS idx_team_members_team_user ON team_members(team_id, user_id);

-- ===== НАЧАЛЬНЫЕ ДАННЫЕ - УПРАЖНЕНИЯ =====
INSERT INTO exercises (name, category, muscle_group, description, instructions, difficulty_level, equipment) VALUES
-- СИЛОВЫЕ УПРАЖНЕНИЯ
('Жим лежа', 'Силовые', 'Грудь', 'Базовое упражнение для развития грудных мышц', 'Лягте на скамью, возьмите штангу хватом шире плеч, медленно опустите до касания груди, выжмите вверх', 'intermediate', 'Штанга, скамья'),
('Приседания со штангой', 'Силовые', 'Ноги', 'Базовое упражнение для развития мышц ног и ягодиц', 'Поставьте штангу на плечи, ноги на ширине плеч, приседайте до параллели с полом', 'intermediate', 'Штанга, стойки'),
('Становая тяга', 'Силовые', 'Спина', 'Базовое упражнение для развития мышц спины и ног', 'Встаньте над штангой, наклонитесь и возьмите штангу, поднимите с прямой спиной', 'advanced', 'Штанга'),
('Подтягивания', 'Силовые', 'Спина', 'Упражнение с собственным весом для развития широчайших мышц', 'Повисните на турнике, подтяните тело до касания подбородком перекладины', 'intermediate', 'Турник'),
('Отжимания', 'Силовые', 'Грудь', 'Упражнение с собственным весом для развития грудных мышц', 'Примите упор лежа, опуститесь до касания грудью пола, отожмитесь', 'beginner', 'Без оборудования'),

-- КАРДИО УПРАЖНЕНИЯ
('Бег на месте', 'Кардио', 'Все тело', 'Аэробное упражнение для развития выносливости', 'Бегите на месте с высоким подниманием колен', 'beginner', 'Без оборудования'),
('Прыжки со сменой ног', 'Кардио', 'Ноги', 'Плиометрическое упражнение для развития взрывной силы', 'Прыгайте попеременно на каждой ноге', 'intermediate', 'Без оборудования'),
('Велосипед', 'Кардио', 'Пресс', 'Упражнение для развития мышц пресса и координации', 'Лежа на спине имитируйте езду на велосипеде', 'beginner', 'Без оборудования'),

-- РАСТЯЖКА
('Растяжка грудных мышц', 'Растяжка', 'Грудь', 'Статическое растягивание грудных мышц', 'Поставьте руку на стену и поверните корпус в противоположную сторону', 'beginner', 'Стена'),
('Растяжка подколенных сухожилий', 'Растяжка', 'Ноги', 'Растягивание задней поверхности бедра', 'Сядьте и потянитесь к носкам ног', 'beginner', 'Без оборудования'),

-- ФУНКЦИОНАЛЬНЫЕ УПРАЖНЕНИЯ
('Планка', 'Функциональные', 'Кор', 'Изометрическое упражнение для укрепления мышц кора', 'Примите упор лежа на предплечьях, держите тело прямо', 'beginner', 'Без оборудования'),
('Берпи', 'Функциональные', 'Все тело', 'Комплексное упражнение для развития силы и выносливости', 'Присядьте, упритесь руками, прыгните в планку, отожмитесь, вернитесь и подпрыгните', 'intermediate', 'Без оборудования'),
('Выпады', 'Функциональные', 'Ноги', 'Одностороннее упражнение для развития мышц ног', 'Сделайте шаг вперед, опуститесь в выпад, вернитесь в исходное положение', 'beginner', 'Без оборудования')

ON CONFLICT (name) DO NOTHING;

-- ===== СОЗДАНИЕ ПОЛЬЗОВАТЕЛЯ-АДМИНИСТРАТОРА (опционально) =====
-- INSERT INTO users (telegram_id, first_name, last_name, username, role) 
-- VALUES (123456789, 'Admin', 'User', 'admin_user', 'admin')
-- ON CONFLICT (telegram_id) DO NOTHING;

COMMIT;
