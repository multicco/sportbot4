--
-- PostgreSQL database dump
--

\restrict aHARFqiZEIVVTQpnIOBvSODy0v9FeSn4wkkzYZ8tea8NJ5EQM4X9fnqlwI01Sc6

-- Dumped from database version 17.7 (Ubuntu 17.7-0ubuntu0.25.10.1)
-- Dumped by pg_dump version 17.7 (Ubuntu 17.7-0ubuntu0.25.10.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

ALTER TABLE IF EXISTS ONLY public.workouts DROP CONSTRAINT IF EXISTS workouts_created_by_fkey;
ALTER TABLE IF EXISTS ONLY public.workouts DROP CONSTRAINT IF EXISTS workouts_assigned_to_fkey;
ALTER TABLE IF EXISTS ONLY public.workout_teams DROP CONSTRAINT IF EXISTS workout_teams_workout_id_fkey;
ALTER TABLE IF EXISTS ONLY public.workout_teams DROP CONSTRAINT IF EXISTS workout_teams_team_id_fkey;
ALTER TABLE IF EXISTS ONLY public.workout_teams DROP CONSTRAINT IF EXISTS workout_teams_assigned_by_fkey;
ALTER TABLE IF EXISTS ONLY public.workout_team_player_assignments DROP CONSTRAINT IF EXISTS workout_team_player_assignments_workout_team_id_fkey;
ALTER TABLE IF EXISTS ONLY public.workout_team_player_assignments DROP CONSTRAINT IF EXISTS workout_team_player_assignments_team_player_id_fkey;
ALTER TABLE IF EXISTS ONLY public.workout_team_player_assignments DROP CONSTRAINT IF EXISTS workout_team_player_assignments_session_id_fkey;
ALTER TABLE IF EXISTS ONLY public.workout_sessions DROP CONSTRAINT IF EXISTS workout_sessions_workout_id_fkey;
ALTER TABLE IF EXISTS ONLY public.workout_sessions DROP CONSTRAINT IF EXISTS workout_sessions_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.workout_session_sets DROP CONSTRAINT IF EXISTS workout_session_sets_session_exercise_id_fkey;
ALTER TABLE IF EXISTS ONLY public.workout_session_exercises DROP CONSTRAINT IF EXISTS workout_session_exercises_workout_exercise_id_fkey;
ALTER TABLE IF EXISTS ONLY public.workout_session_exercises DROP CONSTRAINT IF EXISTS workout_session_exercises_session_id_fkey;
ALTER TABLE IF EXISTS ONLY public.workout_session_exercises DROP CONSTRAINT IF EXISTS workout_session_exercises_exercise_id_fkey;
ALTER TABLE IF EXISTS ONLY public.workout_individual_students DROP CONSTRAINT IF EXISTS workout_individual_students_workout_id_fkey;
ALTER TABLE IF EXISTS ONLY public.workout_individual_students DROP CONSTRAINT IF EXISTS workout_individual_students_student_id_fkey;
ALTER TABLE IF EXISTS ONLY public.workout_exercises DROP CONSTRAINT IF EXISTS workout_exercises_workout_id_fkey;
ALTER TABLE IF EXISTS ONLY public.workout_exercises DROP CONSTRAINT IF EXISTS workout_exercises_exercise_id_fkey;
ALTER TABLE IF EXISTS ONLY public.user_tests DROP CONSTRAINT IF EXISTS user_tests_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.user_tests DROP CONSTRAINT IF EXISTS user_tests_exercise_id_fkey;
ALTER TABLE IF EXISTS ONLY public.user_speed_records DROP CONSTRAINT IF EXISTS user_speed_records_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.user_speed_records DROP CONSTRAINT IF EXISTS user_speed_records_exercise_id_fkey;
ALTER TABLE IF EXISTS ONLY public.user_endurance_records DROP CONSTRAINT IF EXISTS user_endurance_records_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.user_endurance_records DROP CONSTRAINT IF EXISTS user_endurance_records_exercise_id_fkey;
ALTER TABLE IF EXISTS ONLY public.test_set_results DROP CONSTRAINT IF EXISTS test_set_results_exercise_id_fkey;
ALTER TABLE IF EXISTS ONLY public.test_battery_results DROP CONSTRAINT IF EXISTS test_battery_results_participant_id_fkey;
ALTER TABLE IF EXISTS ONLY public.test_battery_results DROP CONSTRAINT IF EXISTS test_battery_results_exercise_id_fkey;
ALTER TABLE IF EXISTS ONLY public.test_battery_results DROP CONSTRAINT IF EXISTS test_battery_results_battery_id_fkey;
ALTER TABLE IF EXISTS ONLY public.test_battery_participants DROP CONSTRAINT IF EXISTS test_battery_participants_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.test_battery_participants DROP CONSTRAINT IF EXISTS test_battery_participants_battery_id_fkey;
ALTER TABLE IF EXISTS ONLY public.test_battery_exercises DROP CONSTRAINT IF EXISTS test_battery_exercises_exercise_id_fkey;
ALTER TABLE IF EXISTS ONLY public.test_battery_exercises DROP CONSTRAINT IF EXISTS test_battery_exercises_battery_id_fkey;
ALTER TABLE IF EXISTS ONLY public.test_batteries DROP CONSTRAINT IF EXISTS test_batteries_created_by_fkey;
ALTER TABLE IF EXISTS ONLY public.team_stats_visibility DROP CONSTRAINT IF EXISTS team_stats_visibility_updated_by_fkey;
ALTER TABLE IF EXISTS ONLY public.team_players DROP CONSTRAINT IF EXISTS team_players_team_id_fkey;
ALTER TABLE IF EXISTS ONLY public.team_members DROP CONSTRAINT IF EXISTS team_members_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.team_announcements DROP CONSTRAINT IF EXISTS team_announcements_author_id_fkey;
ALTER TABLE IF EXISTS ONLY public.one_rep_max DROP CONSTRAINT IF EXISTS one_rep_max_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.one_rep_max DROP CONSTRAINT IF EXISTS one_rep_max_exercise_id_fkey;
ALTER TABLE IF EXISTS ONLY public.individual_student_workouts DROP CONSTRAINT IF EXISTS individual_student_workouts_workout_id_fkey;
ALTER TABLE IF EXISTS ONLY public.individual_student_workouts DROP CONSTRAINT IF EXISTS individual_student_workouts_student_id_fkey;
ALTER TABLE IF EXISTS ONLY public.exercises DROP CONSTRAINT IF EXISTS exercises_created_by_fkey;
ALTER TABLE IF EXISTS ONLY public.coach_students DROP CONSTRAINT IF EXISTS coach_students_student_id_fkey;
ALTER TABLE IF EXISTS ONLY public.coach_students DROP CONSTRAINT IF EXISTS coach_students_coach_id_fkey;
DROP TRIGGER IF EXISTS trigger_test_batteries_updated_at ON public.test_batteries;
DROP TRIGGER IF EXISTS trigger_set_workout_unique_id ON public.workouts;
DROP TRIGGER IF EXISTS trigger_set_coach_invite_code ON public.coach_students;
DROP INDEX IF EXISTS public.idx_workouts_visibility;
DROP INDEX IF EXISTS public.idx_workouts_unique_id;
DROP INDEX IF EXISTS public.idx_workouts_created_by;
DROP INDEX IF EXISTS public.idx_workouts_assigned_to;
DROP INDEX IF EXISTS public.idx_workouts_active;
DROP INDEX IF EXISTS public.idx_workout_teams_workout;
DROP INDEX IF EXISTS public.idx_workout_teams_team;
DROP INDEX IF EXISTS public.idx_workout_team_player_assignments_status;
DROP INDEX IF EXISTS public.idx_workout_team_player_assignments_player;
DROP INDEX IF EXISTS public.idx_workout_team_player_assignments;
DROP INDEX IF EXISTS public.idx_workout_sessions_user_id;
DROP INDEX IF EXISTS public.idx_workout_sessions_status;
DROP INDEX IF EXISTS public.idx_workout_sessions_completed_at;
DROP INDEX IF EXISTS public.idx_workout_individual_students_student;
DROP INDEX IF EXISTS public.idx_users_telegram_id;
DROP INDEX IF EXISTS public.idx_users_role;
DROP INDEX IF EXISTS public.idx_users_active;
DROP INDEX IF EXISTS public.idx_user_tests_user_exercise;
DROP INDEX IF EXISTS public.idx_user_tests_type;
DROP INDEX IF EXISTS public.idx_user_tests_date;
DROP INDEX IF EXISTS public.idx_test_sets_created_by;
DROP INDEX IF EXISTS public.idx_test_set_results_set_id;
DROP INDEX IF EXISTS public.idx_test_set_results_participant;
DROP INDEX IF EXISTS public.idx_test_set_results_exercise;
DROP INDEX IF EXISTS public.idx_test_set_results_date;
DROP INDEX IF EXISTS public.idx_test_battery_results_participant_id;
DROP INDEX IF EXISTS public.idx_test_battery_results_battery_id;
DROP INDEX IF EXISTS public.idx_test_battery_participants_user_id;
DROP INDEX IF EXISTS public.idx_test_battery_participants_battery_id;
DROP INDEX IF EXISTS public.idx_test_battery_exercises_battery_id;
DROP INDEX IF EXISTS public.idx_test_batteries_created_by;
DROP INDEX IF EXISTS public.idx_teams_coach;
DROP INDEX IF EXISTS public.idx_team_players_telegram;
DROP INDEX IF EXISTS public.idx_team_players_team;
DROP INDEX IF EXISTS public.idx_team_members_team_user;
DROP INDEX IF EXISTS public.idx_team_members_active;
DROP INDEX IF EXISTS public.idx_students_team_id;
DROP INDEX IF EXISTS public.idx_players_team_id;
DROP INDEX IF EXISTS public.idx_one_rep_max_user_exercise;
DROP INDEX IF EXISTS public.idx_one_rep_max_tested_at;
DROP INDEX IF EXISTS public.idx_one_rep_max_active;
DROP INDEX IF EXISTS public.idx_individual_students_telegram;
DROP INDEX IF EXISTS public.idx_individual_students_coach;
DROP INDEX IF EXISTS public.idx_exercises_name;
DROP INDEX IF EXISTS public.idx_exercises_muscle_group;
DROP INDEX IF EXISTS public.idx_exercises_category;
DROP INDEX IF EXISTS public.idx_exercises_active;
DROP INDEX IF EXISTS public.idx_coach_students_status;
DROP INDEX IF EXISTS public.idx_coach_students_invite_code;
ALTER TABLE IF EXISTS ONLY public.workouts DROP CONSTRAINT IF EXISTS workouts_unique_id_key;
ALTER TABLE IF EXISTS ONLY public.workouts DROP CONSTRAINT IF EXISTS workouts_pkey;
ALTER TABLE IF EXISTS ONLY public.workout_teams DROP CONSTRAINT IF EXISTS workout_teams_workout_team_unique;
ALTER TABLE IF EXISTS ONLY public.workout_teams DROP CONSTRAINT IF EXISTS workout_teams_workout_id_team_id_key;
ALTER TABLE IF EXISTS ONLY public.workout_teams DROP CONSTRAINT IF EXISTS workout_teams_pkey;
ALTER TABLE IF EXISTS ONLY public.workout_team_player_assignments DROP CONSTRAINT IF EXISTS workout_team_player_assignments_pkey;
ALTER TABLE IF EXISTS ONLY public.workout_team_player_assignments DROP CONSTRAINT IF EXISTS workout_team_player_assignmen_workout_team_id_team_player_i_key;
ALTER TABLE IF EXISTS ONLY public.workout_sessions DROP CONSTRAINT IF EXISTS workout_sessions_pkey;
ALTER TABLE IF EXISTS ONLY public.workout_session_sets DROP CONSTRAINT IF EXISTS workout_session_sets_pkey;
ALTER TABLE IF EXISTS ONLY public.workout_session_exercises DROP CONSTRAINT IF EXISTS workout_session_exercises_pkey;
ALTER TABLE IF EXISTS ONLY public.workout_individual_students DROP CONSTRAINT IF EXISTS workout_individual_students_workout_id_student_id_key;
ALTER TABLE IF EXISTS ONLY public.workout_individual_students DROP CONSTRAINT IF EXISTS workout_individual_students_pkey;
ALTER TABLE IF EXISTS ONLY public.workout_exercises DROP CONSTRAINT IF EXISTS workout_exercises_pkey;
ALTER TABLE IF EXISTS ONLY public.workout_blocks DROP CONSTRAINT IF EXISTS workout_blocks_pkey;
ALTER TABLE IF EXISTS ONLY public.workout_block_exercises DROP CONSTRAINT IF EXISTS workout_block_exercises_pkey;
ALTER TABLE IF EXISTS ONLY public.users DROP CONSTRAINT IF EXISTS users_telegram_id_unique;
ALTER TABLE IF EXISTS ONLY public.users DROP CONSTRAINT IF EXISTS users_telegram_id_key;
ALTER TABLE IF EXISTS ONLY public.users DROP CONSTRAINT IF EXISTS users_pkey;
ALTER TABLE IF EXISTS ONLY public.user_tests DROP CONSTRAINT IF EXISTS user_tests_pkey;
ALTER TABLE IF EXISTS ONLY public.user_speed_records DROP CONSTRAINT IF EXISTS user_speed_records_pkey;
ALTER TABLE IF EXISTS ONLY public.user_endurance_records DROP CONSTRAINT IF EXISTS user_endurance_records_pkey;
ALTER TABLE IF EXISTS ONLY public.test_sets DROP CONSTRAINT IF EXISTS test_sets_pkey;
ALTER TABLE IF EXISTS ONLY public.test_sets DROP CONSTRAINT IF EXISTS test_sets_access_code_key;
ALTER TABLE IF EXISTS ONLY public.test_set_results DROP CONSTRAINT IF EXISTS test_set_results_pkey;
ALTER TABLE IF EXISTS ONLY public.test_set_results DROP CONSTRAINT IF EXISTS test_set_results_participant_id_exercise_id_attempt_number_key;
ALTER TABLE IF EXISTS ONLY public.test_set_participants DROP CONSTRAINT IF EXISTS test_set_participants_pkey;
ALTER TABLE IF EXISTS ONLY public.test_set_exercises DROP CONSTRAINT IF EXISTS test_set_exercises_pkey;
ALTER TABLE IF EXISTS ONLY public.test_battery_results DROP CONSTRAINT IF EXISTS test_battery_results_pkey;
ALTER TABLE IF EXISTS ONLY public.test_battery_results DROP CONSTRAINT IF EXISTS test_battery_results_participant_id_exercise_id_key;
ALTER TABLE IF EXISTS ONLY public.test_battery_participants DROP CONSTRAINT IF EXISTS test_battery_participants_pkey;
ALTER TABLE IF EXISTS ONLY public.test_battery_participants DROP CONSTRAINT IF EXISTS test_battery_participants_battery_id_user_id_key;
ALTER TABLE IF EXISTS ONLY public.test_battery_exercises DROP CONSTRAINT IF EXISTS test_battery_exercises_pkey;
ALTER TABLE IF EXISTS ONLY public.test_battery_exercises DROP CONSTRAINT IF EXISTS test_battery_exercises_battery_id_exercise_id_key;
ALTER TABLE IF EXISTS ONLY public.test_batteries DROP CONSTRAINT IF EXISTS test_batteries_pkey;
ALTER TABLE IF EXISTS ONLY public.teams DROP CONSTRAINT IF EXISTS teams_pkey;
ALTER TABLE IF EXISTS ONLY public.teams DROP CONSTRAINT IF EXISTS teams_access_code_key;
ALTER TABLE IF EXISTS ONLY public.team_stats_visibility DROP CONSTRAINT IF EXISTS team_stats_visibility_team_id_stat_type_key;
ALTER TABLE IF EXISTS ONLY public.team_stats_visibility DROP CONSTRAINT IF EXISTS team_stats_visibility_pkey;
ALTER TABLE IF EXISTS ONLY public.team_players DROP CONSTRAINT IF EXISTS team_players_pkey;
ALTER TABLE IF EXISTS ONLY public.team_members DROP CONSTRAINT IF EXISTS team_members_team_id_user_id_key;
ALTER TABLE IF EXISTS ONLY public.team_members DROP CONSTRAINT IF EXISTS team_members_pkey;
ALTER TABLE IF EXISTS ONLY public.team_announcements DROP CONSTRAINT IF EXISTS team_announcements_pkey;
ALTER TABLE IF EXISTS ONLY public.students DROP CONSTRAINT IF EXISTS students_pkey;
ALTER TABLE IF EXISTS ONLY public.players DROP CONSTRAINT IF EXISTS players_pkey;
ALTER TABLE IF EXISTS ONLY public.one_rep_max DROP CONSTRAINT IF EXISTS one_rep_max_user_id_exercise_id_tested_at_key;
ALTER TABLE IF EXISTS ONLY public.one_rep_max DROP CONSTRAINT IF EXISTS one_rep_max_pkey;
ALTER TABLE IF EXISTS ONLY public.individual_students DROP CONSTRAINT IF EXISTS individual_students_pkey;
ALTER TABLE IF EXISTS ONLY public.individual_student_workouts DROP CONSTRAINT IF EXISTS individual_student_workouts_workout_id_student_id_key;
ALTER TABLE IF EXISTS ONLY public.individual_student_workouts DROP CONSTRAINT IF EXISTS individual_student_workouts_pkey;
ALTER TABLE IF EXISTS ONLY public.exercises DROP CONSTRAINT IF EXISTS exercises_pkey;
ALTER TABLE IF EXISTS ONLY public.coach_students DROP CONSTRAINT IF EXISTS coach_students_pkey;
ALTER TABLE IF EXISTS ONLY public.coach_students DROP CONSTRAINT IF EXISTS coach_students_invite_code_key;
ALTER TABLE IF EXISTS public.workouts ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.workout_teams ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.workout_team_player_assignments ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.workout_sessions ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.workout_session_sets ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.workout_session_exercises ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.workout_individual_students ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.workout_exercises ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.workout_blocks ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.workout_block_exercises ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.users ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.user_tests ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.user_speed_records ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.user_endurance_records ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.test_sets ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.test_set_results ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.test_set_participants ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.test_set_exercises ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.test_battery_results ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.test_battery_participants ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.test_battery_exercises ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.test_batteries ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.teams ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.team_stats_visibility ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.team_players ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.team_members ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.team_announcements ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.students ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.players ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.one_rep_max ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.individual_students ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.individual_student_workouts ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.exercises ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.coach_students ALTER COLUMN id DROP DEFAULT;
DROP SEQUENCE IF EXISTS public.workouts_id_seq;
DROP TABLE IF EXISTS public.workouts;
DROP SEQUENCE IF EXISTS public.workout_teams_id_seq;
DROP TABLE IF EXISTS public.workout_teams;
DROP SEQUENCE IF EXISTS public.workout_team_player_assignments_id_seq;
DROP TABLE IF EXISTS public.workout_team_player_assignments;
DROP SEQUENCE IF EXISTS public.workout_sessions_id_seq;
DROP TABLE IF EXISTS public.workout_sessions;
DROP SEQUENCE IF EXISTS public.workout_session_sets_id_seq;
DROP TABLE IF EXISTS public.workout_session_sets;
DROP SEQUENCE IF EXISTS public.workout_session_exercises_id_seq;
DROP TABLE IF EXISTS public.workout_session_exercises;
DROP SEQUENCE IF EXISTS public.workout_individual_students_id_seq;
DROP TABLE IF EXISTS public.workout_individual_students;
DROP SEQUENCE IF EXISTS public.workout_exercises_id_seq;
DROP TABLE IF EXISTS public.workout_exercises;
DROP SEQUENCE IF EXISTS public.workout_blocks_id_seq;
DROP TABLE IF EXISTS public.workout_blocks;
DROP SEQUENCE IF EXISTS public.workout_block_exercises_id_seq;
DROP TABLE IF EXISTS public.workout_block_exercises;
DROP SEQUENCE IF EXISTS public.users_id_seq;
DROP TABLE IF EXISTS public.users;
DROP SEQUENCE IF EXISTS public.user_tests_id_seq;
DROP TABLE IF EXISTS public.user_tests;
DROP SEQUENCE IF EXISTS public.user_speed_records_id_seq;
DROP TABLE IF EXISTS public.user_speed_records;
DROP SEQUENCE IF EXISTS public.user_endurance_records_id_seq;
DROP TABLE IF EXISTS public.user_endurance_records;
DROP SEQUENCE IF EXISTS public.test_sets_id_seq;
DROP TABLE IF EXISTS public.test_sets;
DROP SEQUENCE IF EXISTS public.test_set_results_id_seq;
DROP TABLE IF EXISTS public.test_set_results;
DROP SEQUENCE IF EXISTS public.test_set_participants_id_seq;
DROP TABLE IF EXISTS public.test_set_participants;
DROP SEQUENCE IF EXISTS public.test_set_exercises_id_seq;
DROP TABLE IF EXISTS public.test_set_exercises;
DROP SEQUENCE IF EXISTS public.test_battery_results_id_seq;
DROP TABLE IF EXISTS public.test_battery_results;
DROP SEQUENCE IF EXISTS public.test_battery_participants_id_seq;
DROP TABLE IF EXISTS public.test_battery_participants;
DROP SEQUENCE IF EXISTS public.test_battery_exercises_id_seq;
DROP TABLE IF EXISTS public.test_battery_exercises;
DROP SEQUENCE IF EXISTS public.test_batteries_id_seq;
DROP TABLE IF EXISTS public.test_batteries;
DROP SEQUENCE IF EXISTS public.teams_id_seq;
DROP TABLE IF EXISTS public.teams;
DROP SEQUENCE IF EXISTS public.team_stats_visibility_id_seq;
DROP TABLE IF EXISTS public.team_stats_visibility;
DROP SEQUENCE IF EXISTS public.team_players_id_seq;
DROP TABLE IF EXISTS public.team_players;
DROP SEQUENCE IF EXISTS public.team_members_id_seq;
DROP TABLE IF EXISTS public.team_members;
DROP SEQUENCE IF EXISTS public.team_announcements_id_seq;
DROP TABLE IF EXISTS public.team_announcements;
DROP SEQUENCE IF EXISTS public.students_id_seq;
DROP TABLE IF EXISTS public.students;
DROP SEQUENCE IF EXISTS public.players_id_seq;
DROP TABLE IF EXISTS public.players;
DROP SEQUENCE IF EXISTS public.one_rep_max_id_seq;
DROP TABLE IF EXISTS public.one_rep_max;
DROP SEQUENCE IF EXISTS public.individual_students_id_seq;
DROP TABLE IF EXISTS public.individual_students;
DROP SEQUENCE IF EXISTS public.individual_student_workouts_id_seq;
DROP TABLE IF EXISTS public.individual_student_workouts;
DROP SEQUENCE IF EXISTS public.exercises_id_seq;
DROP TABLE IF EXISTS public.exercises;
DROP SEQUENCE IF EXISTS public.coach_students_id_seq;
DROP TABLE IF EXISTS public.coach_students;
DROP FUNCTION IF EXISTS public.update_test_set_updated_at();
DROP FUNCTION IF EXISTS public.update_test_batteries_updated_at();
DROP FUNCTION IF EXISTS public.set_workout_unique_id();
DROP FUNCTION IF EXISTS public.set_test_set_access_code();
DROP FUNCTION IF EXISTS public.set_team_invite_code();
DROP FUNCTION IF EXISTS public.set_coach_invite_code();
DROP FUNCTION IF EXISTS public.generate_workout_id();
DROP FUNCTION IF EXISTS public.generate_test_set_code();
DROP FUNCTION IF EXISTS public.generate_team_invite_code();
DROP FUNCTION IF EXISTS public.generate_coach_invite_code();
DROP FUNCTION IF EXISTS public.create_default_team_stats();
DROP FUNCTION IF EXISTS public.check_test_requirement(p_result_value numeric, p_test_type character varying, p_min_requirement numeric);
DROP FUNCTION IF EXISTS public.calculate_epley_1rm(weight numeric, reps integer);
DROP FUNCTION IF EXISTS public.calculate_brzycki_1rm(weight numeric, reps integer);
DROP FUNCTION IF EXISTS public.calculate_alternative_1rm(weight numeric, reps integer);
DROP FUNCTION IF EXISTS public.add_creator_to_team();
-- *not* dropping schema, since initdb creates it
--
-- Name: public; Type: SCHEMA; Schema: -; Owner: sportbot_user
--

-- *not* creating schema, since initdb creates it


ALTER SCHEMA public OWNER TO sportbot_user;

--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: sportbot_user
--

COMMENT ON SCHEMA public IS '';


--
-- Name: add_creator_to_team(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.add_creator_to_team() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    INSERT INTO team_members (team_id, user_id, role)
    VALUES (NEW.id, NEW.created_by, 'creator')
    ON CONFLICT (team_id, user_id) DO NOTHING;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.add_creator_to_team() OWNER TO postgres;

--
-- Name: calculate_alternative_1rm(numeric, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.calculate_alternative_1rm(weight numeric, reps integer) RETURNS numeric
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF reps = 1 THEN
        RETURN weight;
    END IF;
    RETURN weight * (1 + 0.025 * reps);
END;
$$;


ALTER FUNCTION public.calculate_alternative_1rm(weight numeric, reps integer) OWNER TO postgres;

--
-- Name: calculate_brzycki_1rm(numeric, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.calculate_brzycki_1rm(weight numeric, reps integer) RETURNS numeric
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF reps = 1 THEN
        RETURN weight;
    END IF;
    RETURN weight / (1.0278 - 0.0278 * reps);
END;
$$;


ALTER FUNCTION public.calculate_brzycki_1rm(weight numeric, reps integer) OWNER TO postgres;

--
-- Name: calculate_epley_1rm(numeric, integer); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.calculate_epley_1rm(weight numeric, reps integer) RETURNS numeric
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF reps = 1 THEN
        RETURN weight;
    END IF;
    RETURN weight * (1 + reps / 30.0);
END;
$$;


ALTER FUNCTION public.calculate_epley_1rm(weight numeric, reps integer) OWNER TO postgres;

--
-- Name: check_test_requirement(numeric, character varying, numeric); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.check_test_requirement(p_result_value numeric, p_test_type character varying, p_min_requirement numeric) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF p_min_requirement IS NULL THEN
        RETURN true; -- Нет требований
    END IF;
    
    -- Логика проверки в зависимости от типа теста
    CASE p_test_type
        WHEN 'strength', 'quantity', 'endurance' THEN
            -- Больше = лучше
            RETURN p_result_value >= p_min_requirement;
        WHEN 'speed' THEN
            -- Меньше времени = лучше
            RETURN p_result_value <= p_min_requirement;
        ELSE
            RETURN p_result_value >= p_min_requirement;
    END CASE;
END;
$$;


ALTER FUNCTION public.check_test_requirement(p_result_value numeric, p_test_type character varying, p_min_requirement numeric) OWNER TO postgres;

--
-- Name: create_default_team_stats(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.create_default_team_stats() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    INSERT INTO team_stats_visibility (team_id, stat_type, is_public) VALUES 
    (NEW.id, 'members_list', true),
    (NEW.id, 'members_count', true),
    (NEW.id, 'avg_rpe', false),
    (NEW.id, 'workout_stats', false),
    (NEW.id, 'top_performers', false),
    (NEW.id, 'activity_stats', true),
    (NEW.id, '1rm_rankings', false),
    (NEW.id, 'individual_progress', false)
    ON CONFLICT DO NOTHING;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.create_default_team_stats() OWNER TO postgres;

--
-- Name: generate_coach_invite_code(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.generate_coach_invite_code() RETURNS text
    LANGUAGE plpgsql
    AS $$
DECLARE
    new_code text;
    code_exists boolean;
BEGIN
    LOOP
        new_code := 'COACH-' || 
                   CHR(65 + (random() * 25)::int) || 
                   CHR(65 + (random() * 25)::int) || 
                   CHR(65 + (random() * 25)::int) || 
                   (random() * 9)::int || 
                   (random() * 9)::int ||
                   (random() * 9)::int;

        SELECT EXISTS(
            SELECT 1 FROM coach_students WHERE invite_code = new_code
            UNION
            SELECT 1 FROM teams WHERE invite_code = new_code
        ) INTO code_exists;

        IF NOT code_exists THEN
            EXIT;
        END IF;
    END LOOP;

    RETURN new_code;
END;
$$;


ALTER FUNCTION public.generate_coach_invite_code() OWNER TO postgres;

--
-- Name: generate_team_invite_code(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.generate_team_invite_code() RETURNS text
    LANGUAGE plpgsql
    AS $$
DECLARE
    new_code text;
    code_exists boolean;
BEGIN
    LOOP
        new_code := 'TEAM-' || 
                   CHR(65 + (random() * 25)::int) || 
                   CHR(65 + (random() * 25)::int) || 
                   CHR(65 + (random() * 25)::int) || 
                   (random() * 9)::int || 
                   (random() * 9)::int ||
                   (random() * 9)::int;

        SELECT EXISTS(SELECT 1 FROM teams WHERE invite_code = new_code) INTO code_exists;

        IF NOT code_exists THEN
            EXIT;
        END IF;
    END LOOP;

    RETURN new_code;
END;
$$;


ALTER FUNCTION public.generate_team_invite_code() OWNER TO postgres;

--
-- Name: generate_test_set_code(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.generate_test_set_code() RETURNS character varying
    LANGUAGE plpgsql
    AS $$
DECLARE
    chars VARCHAR(36) := 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    result VARCHAR(10) := 'TS-';
    i INTEGER := 0;
    random_char VARCHAR(1);
BEGIN
    -- Генерируем 4 случайных символа
    FOR i IN 1..4 LOOP
        random_char := SUBSTR(chars, (RANDOM() * LENGTH(chars))::INTEGER + 1, 1);
        result := result || random_char;
        
        -- Добавляем дефис после второго символа
        IF i = 2 THEN
            result := result || '-';
        END IF;
    END LOOP;
    
    RETURN result;
END;
$$;


ALTER FUNCTION public.generate_test_set_code() OWNER TO postgres;

--
-- Name: generate_workout_id(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.generate_workout_id() RETURNS text
    LANGUAGE plpgsql
    AS $$
DECLARE
    new_id text;
    id_exists boolean;
BEGIN
    LOOP
        new_id := 'WKT-' || 
                  CHR(65 + (random() * 25)::int) || 
                  CHR(65 + (random() * 25)::int) || 
                  CHR(65 + (random() * 25)::int) || 
                  (random() * 9)::int || 
                  (random() * 9)::int ||
                  (random() * 9)::int;

        SELECT EXISTS(SELECT 1 FROM workouts WHERE unique_id = new_id) INTO id_exists;

        IF NOT id_exists THEN
            EXIT;
        END IF;
    END LOOP;

    RETURN new_id;
END;
$$;


ALTER FUNCTION public.generate_workout_id() OWNER TO postgres;

--
-- Name: set_coach_invite_code(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.set_coach_invite_code() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF NEW.invite_code IS NULL OR NEW.invite_code = '' THEN
        NEW.invite_code := generate_coach_invite_code();
    END IF;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.set_coach_invite_code() OWNER TO postgres;

--
-- Name: set_team_invite_code(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.set_team_invite_code() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF NEW.invite_code IS NULL OR NEW.invite_code = '' THEN
        NEW.invite_code := generate_team_invite_code();
    END IF;
    NEW.updated_at := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.set_team_invite_code() OWNER TO postgres;

--
-- Name: set_test_set_access_code(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.set_test_set_access_code() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF NEW.access_code IS NULL OR NEW.access_code = '' THEN
        LOOP
            NEW.access_code := generate_test_set_code();
            -- Проверяем уникальность
            IF NOT EXISTS(SELECT 1 FROM test_sets WHERE access_code = NEW.access_code) THEN
                EXIT;
            END IF;
        END LOOP;
    END IF;
    
    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.set_test_set_access_code() OWNER TO postgres;

--
-- Name: set_workout_unique_id(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.set_workout_unique_id() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF NEW.unique_id IS NULL OR NEW.unique_id = '' THEN
        NEW.unique_id := generate_workout_id();
    END IF;
    NEW.updated_at := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.set_workout_unique_id() OWNER TO postgres;

--
-- Name: update_test_batteries_updated_at(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.update_test_batteries_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_test_batteries_updated_at() OWNER TO postgres;

--
-- Name: update_test_set_updated_at(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.update_test_set_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_test_set_updated_at() OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: coach_students; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.coach_students (
    id integer NOT NULL,
    student_id integer,
    invite_code character varying(20) NOT NULL,
    status character varying(20) DEFAULT 'active'::character varying,
    relationship_type character varying(20) DEFAULT 'personal'::character varying,
    started_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    ended_at timestamp without time zone,
    coach_notes text,
    student_goals text,
    coach_id bigint
);


ALTER TABLE public.coach_students OWNER TO postgres;

--
-- Name: coach_students_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.coach_students_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.coach_students_id_seq OWNER TO postgres;

--
-- Name: coach_students_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.coach_students_id_seq OWNED BY public.coach_students.id;


--
-- Name: exercises; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.exercises (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    category character varying(100) NOT NULL,
    muscle_group character varying(100) NOT NULL,
    equipment character varying(100),
    difficulty_level character varying(20) DEFAULT 'beginner'::character varying,
    description text,
    instructions text,
    video_url character varying(500),
    image_url character varying(500),
    created_by integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    is_active boolean DEFAULT true,
    test_type character varying(50) DEFAULT 'none'::character varying,
    measurement_unit character varying(20) DEFAULT 'kg'::character varying,
    tags text
);


ALTER TABLE public.exercises OWNER TO postgres;

--
-- Name: exercises_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.exercises_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.exercises_id_seq OWNER TO postgres;

--
-- Name: exercises_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.exercises_id_seq OWNED BY public.exercises.id;


--
-- Name: individual_student_workouts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.individual_student_workouts (
    id integer NOT NULL,
    workout_id integer,
    student_id integer,
    assigned_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    completed_at timestamp without time zone,
    status character varying(20) DEFAULT 'pending'::character varying,
    rpe double precision,
    CONSTRAINT individual_student_workouts_status_check CHECK (((status)::text = ANY (ARRAY[('pending'::character varying)::text, ('in_progress'::character varying)::text, ('completed'::character varying)::text])))
);


ALTER TABLE public.individual_student_workouts OWNER TO postgres;

--
-- Name: individual_student_workouts_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.individual_student_workouts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.individual_student_workouts_id_seq OWNER TO postgres;

--
-- Name: individual_student_workouts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.individual_student_workouts_id_seq OWNED BY public.individual_student_workouts.id;


--
-- Name: individual_students; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.individual_students (
    id integer NOT NULL,
    coach_telegram_id bigint NOT NULL,
    first_name character varying(100) NOT NULL,
    last_name character varying(100),
    telegram_id bigint,
    phone character varying(20),
    birth_date date,
    specialization character varying(100),
    level character varying(20) DEFAULT 'beginner'::character varying,
    notes text,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.individual_students OWNER TO postgres;

--
-- Name: individual_students_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.individual_students_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.individual_students_id_seq OWNER TO postgres;

--
-- Name: individual_students_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.individual_students_id_seq OWNED BY public.individual_students.id;


--
-- Name: one_rep_max; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.one_rep_max (
    id integer NOT NULL,
    user_id integer,
    exercise_id integer,
    weight numeric(6,2) NOT NULL,
    reps integer NOT NULL,
    test_weight numeric(6,2) NOT NULL,
    weight_type character varying(20) DEFAULT 'external_weight'::character varying,
    formula_brzycki numeric(6,2),
    formula_epley numeric(6,2),
    formula_alternative numeric(6,2),
    formula_average numeric(6,2),
    calculation_method character varying(20) DEFAULT 'average'::character varying,
    tested_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    notes text,
    is_active boolean DEFAULT true,
    CONSTRAINT one_rep_max_reps_check CHECK ((reps > 0))
);


ALTER TABLE public.one_rep_max OWNER TO postgres;

--
-- Name: one_rep_max_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.one_rep_max_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.one_rep_max_id_seq OWNER TO postgres;

--
-- Name: one_rep_max_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.one_rep_max_id_seq OWNED BY public.one_rep_max.id;


--
-- Name: players; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.players (
    id integer NOT NULL,
    team_id integer NOT NULL,
    name character varying(255) NOT NULL,
    "position" character varying(100),
    telegram_user_id bigint,
    added_at timestamp without time zone DEFAULT now(),
    added_by bigint NOT NULL
);


ALTER TABLE public.players OWNER TO postgres;

--
-- Name: players_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.players_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.players_id_seq OWNER TO postgres;

--
-- Name: players_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.players_id_seq OWNED BY public.players.id;


--
-- Name: students; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.students (
    id integer NOT NULL,
    team_id integer NOT NULL,
    name character varying(255) NOT NULL,
    "position" character varying(100),
    telegram_user_id bigint,
    added_at timestamp without time zone DEFAULT now(),
    added_by bigint NOT NULL
);


ALTER TABLE public.students OWNER TO postgres;

--
-- Name: students_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.students_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.students_id_seq OWNER TO postgres;

--
-- Name: students_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.students_id_seq OWNED BY public.students.id;


--
-- Name: team_announcements; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.team_announcements (
    id integer NOT NULL,
    team_id integer,
    author_id integer,
    title character varying(255) NOT NULL,
    content text NOT NULL,
    is_important boolean DEFAULT false,
    is_pinned boolean DEFAULT false,
    expires_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.team_announcements OWNER TO postgres;

--
-- Name: team_announcements_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.team_announcements_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.team_announcements_id_seq OWNER TO postgres;

--
-- Name: team_announcements_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.team_announcements_id_seq OWNED BY public.team_announcements.id;


--
-- Name: team_members; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.team_members (
    id integer NOT NULL,
    team_id integer,
    user_id integer,
    role character varying(20) DEFAULT 'player'::character varying,
    joined_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    left_at timestamp without time zone,
    is_active boolean DEFAULT true,
    member_notes text
);


ALTER TABLE public.team_members OWNER TO postgres;

--
-- Name: team_members_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.team_members_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.team_members_id_seq OWNER TO postgres;

--
-- Name: team_members_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.team_members_id_seq OWNED BY public.team_members.id;


--
-- Name: team_players; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.team_players (
    id integer NOT NULL,
    team_id integer,
    first_name character varying(100) NOT NULL,
    last_name character varying(100),
    "position" character varying(50),
    jersey_number integer,
    telegram_id bigint,
    phone character varying(20),
    birth_date date,
    is_active boolean DEFAULT true,
    joined_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.team_players OWNER TO postgres;

--
-- Name: team_players_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.team_players_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.team_players_id_seq OWNER TO postgres;

--
-- Name: team_players_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.team_players_id_seq OWNED BY public.team_players.id;


--
-- Name: team_stats_visibility; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.team_stats_visibility (
    id integer NOT NULL,
    team_id integer,
    stat_type character varying(50) NOT NULL,
    is_public boolean DEFAULT false,
    updated_by integer,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.team_stats_visibility OWNER TO postgres;

--
-- Name: team_stats_visibility_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.team_stats_visibility_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.team_stats_visibility_id_seq OWNER TO postgres;

--
-- Name: team_stats_visibility_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.team_stats_visibility_id_seq OWNED BY public.team_stats_visibility.id;


--
-- Name: teams; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.teams (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    coach_telegram_id bigint NOT NULL,
    sport_type character varying(50) DEFAULT 'general'::character varying,
    max_players integer DEFAULT 25,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    access_code character varying(20)
);


ALTER TABLE public.teams OWNER TO postgres;

--
-- Name: teams_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.teams_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.teams_id_seq OWNER TO postgres;

--
-- Name: teams_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.teams_id_seq OWNED BY public.teams.id;


--
-- Name: test_batteries; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.test_batteries (
    id integer NOT NULL,
    name character varying(200) NOT NULL,
    description text,
    created_by integer NOT NULL,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.test_batteries OWNER TO postgres;

--
-- Name: TABLE test_batteries; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.test_batteries IS 'Батареи тестов - наборы упражнений для диагностики от тренеров';


--
-- Name: test_batteries_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.test_batteries_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.test_batteries_id_seq OWNER TO postgres;

--
-- Name: test_batteries_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.test_batteries_id_seq OWNED BY public.test_batteries.id;


--
-- Name: test_battery_exercises; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.test_battery_exercises (
    id integer NOT NULL,
    battery_id integer NOT NULL,
    exercise_id integer NOT NULL,
    order_position integer DEFAULT 1 NOT NULL,
    added_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.test_battery_exercises OWNER TO postgres;

--
-- Name: TABLE test_battery_exercises; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.test_battery_exercises IS 'Упражнения входящие в батареи тестов';


--
-- Name: test_battery_exercises_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.test_battery_exercises_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.test_battery_exercises_id_seq OWNER TO postgres;

--
-- Name: test_battery_exercises_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.test_battery_exercises_id_seq OWNED BY public.test_battery_exercises.id;


--
-- Name: test_battery_participants; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.test_battery_participants (
    id integer NOT NULL,
    battery_id integer NOT NULL,
    user_id integer NOT NULL,
    assigned_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.test_battery_participants OWNER TO postgres;

--
-- Name: TABLE test_battery_participants; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.test_battery_participants IS 'Участники батарей тестов';


--
-- Name: test_battery_participants_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.test_battery_participants_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.test_battery_participants_id_seq OWNER TO postgres;

--
-- Name: test_battery_participants_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.test_battery_participants_id_seq OWNED BY public.test_battery_participants.id;


--
-- Name: test_battery_results; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.test_battery_results (
    id integer NOT NULL,
    participant_id integer NOT NULL,
    exercise_id integer NOT NULL,
    battery_id integer NOT NULL,
    test_type character varying(20) NOT NULL,
    result_value numeric(10,2) NOT NULL,
    result_unit character varying(20) NOT NULL,
    test_weight numeric(6,2),
    test_reps integer,
    distance numeric(8,2),
    time_seconds numeric(8,2),
    duration_seconds integer,
    max_reps integer,
    tested_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.test_battery_results OWNER TO postgres;

--
-- Name: TABLE test_battery_results; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.test_battery_results IS 'Результаты прохождения тестов из батарей';


--
-- Name: test_battery_results_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.test_battery_results_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.test_battery_results_id_seq OWNER TO postgres;

--
-- Name: test_battery_results_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.test_battery_results_id_seq OWNED BY public.test_battery_results.id;


--
-- Name: test_set_exercises; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.test_set_exercises (
    id integer NOT NULL,
    test_set_id integer NOT NULL,
    exercise_id integer NOT NULL,
    added_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.test_set_exercises OWNER TO postgres;

--
-- Name: test_set_exercises_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.test_set_exercises_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.test_set_exercises_id_seq OWNER TO postgres;

--
-- Name: test_set_exercises_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.test_set_exercises_id_seq OWNED BY public.test_set_exercises.id;


--
-- Name: test_set_participants; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.test_set_participants (
    id integer NOT NULL,
    test_set_id integer NOT NULL,
    user_id integer NOT NULL,
    joined_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.test_set_participants OWNER TO postgres;

--
-- Name: test_set_participants_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.test_set_participants_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.test_set_participants_id_seq OWNER TO postgres;

--
-- Name: test_set_participants_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.test_set_participants_id_seq OWNED BY public.test_set_participants.id;


--
-- Name: test_set_results; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.test_set_results (
    id integer NOT NULL,
    test_set_id integer NOT NULL,
    participant_id integer NOT NULL,
    exercise_id integer NOT NULL,
    result_value numeric(10,2) NOT NULL,
    result_unit character varying(20) NOT NULL,
    test_type character varying(50) NOT NULL,
    test_weight numeric(8,2),
    test_reps integer,
    distance numeric(8,2),
    time_seconds numeric(8,3),
    duration_seconds integer,
    max_reps integer,
    attempt_number integer DEFAULT 1,
    is_passed boolean DEFAULT false,
    notes text,
    tested_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.test_set_results OWNER TO postgres;

--
-- Name: TABLE test_set_results; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.test_set_results IS 'Результаты прохождения тестов участниками';


--
-- Name: COLUMN test_set_results.attempt_number; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.test_set_results.attempt_number IS 'Номер попытки (1, 2, 3...)';


--
-- Name: COLUMN test_set_results.is_passed; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.test_set_results.is_passed IS 'Выполнен ли минимальный норматив';


--
-- Name: test_set_results_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.test_set_results_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.test_set_results_id_seq OWNER TO postgres;

--
-- Name: test_set_results_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.test_set_results_id_seq OWNED BY public.test_set_results.id;


--
-- Name: test_sets; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.test_sets (
    id integer NOT NULL,
    name character varying(200) NOT NULL,
    description text,
    created_by integer NOT NULL,
    visibility character varying(20) DEFAULT 'private'::character varying,
    access_code character varying(10) DEFAULT upper("substring"(md5((random())::text), 1, 8)) NOT NULL,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.test_sets OWNER TO postgres;

--
-- Name: test_sets_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.test_sets_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.test_sets_id_seq OWNER TO postgres;

--
-- Name: test_sets_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.test_sets_id_seq OWNED BY public.test_sets.id;


--
-- Name: user_endurance_records; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_endurance_records (
    id integer NOT NULL,
    user_id integer,
    exercise_id integer,
    result_seconds numeric(8,2) NOT NULL,
    model_a numeric(8,2),
    model_b numeric(8,2),
    model_c numeric(8,2),
    average numeric(8,2),
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.user_endurance_records OWNER TO postgres;

--
-- Name: user_endurance_records_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.user_endurance_records_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.user_endurance_records_id_seq OWNER TO postgres;

--
-- Name: user_endurance_records_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.user_endurance_records_id_seq OWNED BY public.user_endurance_records.id;


--
-- Name: user_speed_records; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_speed_records (
    id integer NOT NULL,
    user_id integer,
    exercise_id integer,
    result_seconds numeric(8,2) NOT NULL,
    model_a numeric(8,2),
    model_b numeric(8,2),
    model_c numeric(8,2),
    average numeric(8,2),
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.user_speed_records OWNER TO postgres;

--
-- Name: user_speed_records_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.user_speed_records_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.user_speed_records_id_seq OWNER TO postgres;

--
-- Name: user_speed_records_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.user_speed_records_id_seq OWNED BY public.user_speed_records.id;


--
-- Name: user_tests; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_tests (
    id integer NOT NULL,
    user_id integer NOT NULL,
    exercise_id integer NOT NULL,
    test_type character varying(50) NOT NULL,
    result_value numeric(10,2) NOT NULL,
    result_unit character varying(20) NOT NULL,
    test_weight numeric(8,2),
    test_reps integer,
    distance numeric(8,2),
    time_seconds numeric(8,3),
    duration_seconds integer,
    max_reps integer,
    notes text,
    conditions character varying(200),
    tested_at timestamp without time zone DEFAULT now() NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.user_tests OWNER TO postgres;

--
-- Name: TABLE user_tests; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.user_tests IS 'Универсальная таблица для хранения всех типов тестов пользователей';


--
-- Name: COLUMN user_tests.test_type; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.user_tests.test_type IS 'Тип теста: strength, endurance, speed, quantity';


--
-- Name: COLUMN user_tests.result_value; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.user_tests.result_value IS 'Основной результат теста (1ПМ, время, скорость и т.д.)';


--
-- Name: COLUMN user_tests.result_unit; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.user_tests.result_unit IS 'Единица измерения результата (kg, seconds, m/s, reps)';


--
-- Name: user_tests_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.user_tests_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.user_tests_id_seq OWNER TO postgres;

--
-- Name: user_tests_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.user_tests_id_seq OWNED BY public.user_tests.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id integer NOT NULL,
    telegram_id bigint NOT NULL,
    first_name character varying(255) NOT NULL,
    last_name character varying(255),
    username character varying(255),
    role character varying(20) DEFAULT 'player'::character varying,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    body_weight numeric(5,2) DEFAULT 70.0,
    age integer,
    gender character varying(10),
    experience_level character varying(20) DEFAULT 'beginner'::character varying,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    is_active boolean DEFAULT true
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: workout_block_exercises; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.workout_block_exercises (
    id integer NOT NULL,
    workout_block_id integer NOT NULL,
    exercise_id integer NOT NULL,
    exercise_order integer DEFAULT 1 NOT NULL,
    sets integer,
    reps integer,
    weight numeric(6,2),
    duration_seconds integer,
    distance numeric(8,2),
    rest_seconds integer DEFAULT 60,
    rpe_target integer,
    notes text,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.workout_block_exercises OWNER TO postgres;

--
-- Name: workout_block_exercises_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.workout_block_exercises_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.workout_block_exercises_id_seq OWNER TO postgres;

--
-- Name: workout_block_exercises_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.workout_block_exercises_id_seq OWNED BY public.workout_block_exercises.id;


--
-- Name: workout_blocks; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.workout_blocks (
    id integer NOT NULL,
    workout_id integer NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    block_type character varying(20) DEFAULT 'main'::character varying,
    block_order integer DEFAULT 1 NOT NULL,
    rest_between_exercises integer DEFAULT 60,
    created_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.workout_blocks OWNER TO postgres;

--
-- Name: workout_blocks_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.workout_blocks_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.workout_blocks_id_seq OWNER TO postgres;

--
-- Name: workout_blocks_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.workout_blocks_id_seq OWNED BY public.workout_blocks.id;


--
-- Name: workout_exercises; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.workout_exercises (
    id integer NOT NULL,
    workout_id integer,
    exercise_id integer,
    phase character varying(50) DEFAULT 'main'::character varying,
    order_in_phase integer NOT NULL,
    sets integer NOT NULL,
    reps_min integer,
    reps_max integer,
    one_rm_percent numeric(5,2),
    fixed_weight numeric(6,2),
    rest_seconds integer DEFAULT 60,
    tempo character varying(20),
    notes text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    test_percent integer,
    target_value numeric(10,2),
    target_unit character varying(20),
    CONSTRAINT workout_exercises_check CHECK ((reps_max >= reps_min)),
    CONSTRAINT workout_exercises_fixed_weight_check CHECK ((fixed_weight >= (0)::numeric)),
    CONSTRAINT workout_exercises_one_rm_percent_check CHECK (((one_rm_percent > (0)::numeric) AND (one_rm_percent <= (200)::numeric))),
    CONSTRAINT workout_exercises_rest_seconds_check CHECK ((rest_seconds >= 0))
);


ALTER TABLE public.workout_exercises OWNER TO postgres;

--
-- Name: COLUMN workout_exercises.test_percent; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.workout_exercises.test_percent IS 'Процент от личного рекорда в тесте (например, 85%)';


--
-- Name: COLUMN workout_exercises.target_value; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.workout_exercises.target_value IS 'Рассчитанное целевое значение (вес, время и т.д.)';


--
-- Name: COLUMN workout_exercises.target_unit; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.workout_exercises.target_unit IS 'Единица измерения целевого значения';


--
-- Name: workout_exercises_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.workout_exercises_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.workout_exercises_id_seq OWNER TO postgres;

--
-- Name: workout_exercises_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.workout_exercises_id_seq OWNED BY public.workout_exercises.id;


--
-- Name: workout_individual_students; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.workout_individual_students (
    id integer NOT NULL,
    workout_id integer,
    student_id integer,
    assigned_by bigint NOT NULL,
    assigned_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    deadline timestamp without time zone,
    notes text,
    is_active boolean DEFAULT true,
    status character varying(20) DEFAULT 'pending'::character varying,
    started_at timestamp without time zone,
    completed_at timestamp without time zone,
    rpe double precision,
    archived_at timestamp without time zone,
    CONSTRAINT workout_individual_students_status_check CHECK (((status)::text = ANY (ARRAY[('pending'::character varying)::text, ('in_progress'::character varying)::text, ('completed'::character varying)::text, ('archived'::character varying)::text])))
);


ALTER TABLE public.workout_individual_students OWNER TO postgres;

--
-- Name: workout_individual_students_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.workout_individual_students_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.workout_individual_students_id_seq OWNER TO postgres;

--
-- Name: workout_individual_students_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.workout_individual_students_id_seq OWNED BY public.workout_individual_students.id;


--
-- Name: workout_session_exercises; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.workout_session_exercises (
    id integer NOT NULL,
    session_id integer,
    workout_exercise_id integer,
    exercise_id integer,
    sets_completed integer DEFAULT 0,
    sets_total integer NOT NULL,
    status character varying(20) DEFAULT 'pending'::character varying,
    started_at timestamp without time zone,
    completed_at timestamp without time zone,
    exercise_rpe integer,
    notes text,
    CONSTRAINT workout_session_exercises_exercise_rpe_check CHECK (((exercise_rpe >= 1) AND (exercise_rpe <= 10)))
);


ALTER TABLE public.workout_session_exercises OWNER TO postgres;

--
-- Name: workout_session_exercises_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.workout_session_exercises_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.workout_session_exercises_id_seq OWNER TO postgres;

--
-- Name: workout_session_exercises_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.workout_session_exercises_id_seq OWNED BY public.workout_session_exercises.id;


--
-- Name: workout_session_sets; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.workout_session_sets (
    id integer NOT NULL,
    session_exercise_id integer,
    set_number integer NOT NULL,
    planned_reps integer,
    actual_reps integer,
    planned_weight numeric(6,2),
    actual_weight numeric(6,2),
    rpe integer,
    rest_seconds integer,
    completed_at timestamp without time zone,
    form_notes text,
    notes text,
    CONSTRAINT workout_session_sets_actual_reps_check CHECK ((actual_reps >= 0)),
    CONSTRAINT workout_session_sets_actual_weight_check CHECK ((actual_weight >= (0)::numeric)),
    CONSTRAINT workout_session_sets_rest_seconds_check CHECK ((rest_seconds >= 0)),
    CONSTRAINT workout_session_sets_rpe_check CHECK (((rpe >= 1) AND (rpe <= 10))),
    CONSTRAINT workout_session_sets_set_number_check CHECK ((set_number > 0))
);


ALTER TABLE public.workout_session_sets OWNER TO postgres;

--
-- Name: workout_session_sets_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.workout_session_sets_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.workout_session_sets_id_seq OWNER TO postgres;

--
-- Name: workout_session_sets_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.workout_session_sets_id_seq OWNED BY public.workout_session_sets.id;


--
-- Name: workout_sessions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.workout_sessions (
    id integer NOT NULL,
    user_id integer,
    workout_id integer,
    status character varying(20) DEFAULT 'created'::character varying,
    started_at timestamp without time zone,
    completed_at timestamp without time zone,
    paused_at timestamp without time zone,
    total_duration_minutes integer,
    rpe integer,
    rpe_description text,
    notes text,
    session_rating integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT workout_sessions_rpe_check CHECK (((rpe >= 1) AND (rpe <= 10))),
    CONSTRAINT workout_sessions_session_rating_check CHECK (((session_rating >= 1) AND (session_rating <= 5)))
);


ALTER TABLE public.workout_sessions OWNER TO postgres;

--
-- Name: workout_sessions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.workout_sessions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.workout_sessions_id_seq OWNER TO postgres;

--
-- Name: workout_sessions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.workout_sessions_id_seq OWNED BY public.workout_sessions.id;


--
-- Name: workout_team_player_assignments; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.workout_team_player_assignments (
    id integer NOT NULL,
    workout_team_id integer,
    team_player_id integer,
    status character varying(20) DEFAULT 'pending'::character varying,
    started_at timestamp without time zone,
    completed_at timestamp without time zone,
    session_id integer,
    rpe numeric(3,1),
    notes text,
    CONSTRAINT workout_team_player_assignments_rpe_check CHECK (((rpe >= (1)::numeric) AND (rpe <= (10)::numeric))),
    CONSTRAINT workout_team_player_assignments_status_check CHECK (((status)::text = ANY (ARRAY[('pending'::character varying)::text, ('in_progress'::character varying)::text, ('completed'::character varying)::text, ('skipped'::character varying)::text])))
);


ALTER TABLE public.workout_team_player_assignments OWNER TO postgres;

--
-- Name: workout_team_player_assignments_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.workout_team_player_assignments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.workout_team_player_assignments_id_seq OWNER TO postgres;

--
-- Name: workout_team_player_assignments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.workout_team_player_assignments_id_seq OWNED BY public.workout_team_player_assignments.id;


--
-- Name: workout_teams; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.workout_teams (
    id integer NOT NULL,
    workout_id integer,
    team_id integer,
    assigned_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    assigned_by integer,
    deadline timestamp without time zone,
    notes text,
    is_active boolean DEFAULT true
);


ALTER TABLE public.workout_teams OWNER TO postgres;

--
-- Name: workout_teams_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.workout_teams_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.workout_teams_id_seq OWNER TO postgres;

--
-- Name: workout_teams_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.workout_teams_id_seq OWNED BY public.workout_teams.id;


--
-- Name: workouts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.workouts (
    id integer NOT NULL,
    unique_id character varying(20) NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    created_by integer,
    assigned_to integer,
    visibility character varying(20) DEFAULT 'private'::character varying,
    is_template boolean DEFAULT false,
    difficulty_level character varying(20) DEFAULT 'beginner'::character varying,
    estimated_duration_minutes integer,
    tags text[],
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    is_active boolean DEFAULT true
);


ALTER TABLE public.workouts OWNER TO postgres;

--
-- Name: workouts_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.workouts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.workouts_id_seq OWNER TO postgres;

--
-- Name: workouts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.workouts_id_seq OWNED BY public.workouts.id;


--
-- Name: coach_students id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.coach_students ALTER COLUMN id SET DEFAULT nextval('public.coach_students_id_seq'::regclass);


--
-- Name: exercises id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.exercises ALTER COLUMN id SET DEFAULT nextval('public.exercises_id_seq'::regclass);


--
-- Name: individual_student_workouts id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.individual_student_workouts ALTER COLUMN id SET DEFAULT nextval('public.individual_student_workouts_id_seq'::regclass);


--
-- Name: individual_students id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.individual_students ALTER COLUMN id SET DEFAULT nextval('public.individual_students_id_seq'::regclass);


--
-- Name: one_rep_max id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.one_rep_max ALTER COLUMN id SET DEFAULT nextval('public.one_rep_max_id_seq'::regclass);


--
-- Name: players id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.players ALTER COLUMN id SET DEFAULT nextval('public.players_id_seq'::regclass);


--
-- Name: students id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.students ALTER COLUMN id SET DEFAULT nextval('public.students_id_seq'::regclass);


--
-- Name: team_announcements id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.team_announcements ALTER COLUMN id SET DEFAULT nextval('public.team_announcements_id_seq'::regclass);


--
-- Name: team_members id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.team_members ALTER COLUMN id SET DEFAULT nextval('public.team_members_id_seq'::regclass);


--
-- Name: team_players id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.team_players ALTER COLUMN id SET DEFAULT nextval('public.team_players_id_seq'::regclass);


--
-- Name: team_stats_visibility id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.team_stats_visibility ALTER COLUMN id SET DEFAULT nextval('public.team_stats_visibility_id_seq'::regclass);


--
-- Name: teams id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.teams ALTER COLUMN id SET DEFAULT nextval('public.teams_id_seq'::regclass);


--
-- Name: test_batteries id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.test_batteries ALTER COLUMN id SET DEFAULT nextval('public.test_batteries_id_seq'::regclass);


--
-- Name: test_battery_exercises id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.test_battery_exercises ALTER COLUMN id SET DEFAULT nextval('public.test_battery_exercises_id_seq'::regclass);


--
-- Name: test_battery_participants id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.test_battery_participants ALTER COLUMN id SET DEFAULT nextval('public.test_battery_participants_id_seq'::regclass);


--
-- Name: test_battery_results id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.test_battery_results ALTER COLUMN id SET DEFAULT nextval('public.test_battery_results_id_seq'::regclass);


--
-- Name: test_set_exercises id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.test_set_exercises ALTER COLUMN id SET DEFAULT nextval('public.test_set_exercises_id_seq'::regclass);


--
-- Name: test_set_participants id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.test_set_participants ALTER COLUMN id SET DEFAULT nextval('public.test_set_participants_id_seq'::regclass);


--
-- Name: test_set_results id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.test_set_results ALTER COLUMN id SET DEFAULT nextval('public.test_set_results_id_seq'::regclass);


--
-- Name: test_sets id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.test_sets ALTER COLUMN id SET DEFAULT nextval('public.test_sets_id_seq'::regclass);


--
-- Name: user_endurance_records id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_endurance_records ALTER COLUMN id SET DEFAULT nextval('public.user_endurance_records_id_seq'::regclass);


--
-- Name: user_speed_records id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_speed_records ALTER COLUMN id SET DEFAULT nextval('public.user_speed_records_id_seq'::regclass);


--
-- Name: user_tests id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_tests ALTER COLUMN id SET DEFAULT nextval('public.user_tests_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: workout_block_exercises id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workout_block_exercises ALTER COLUMN id SET DEFAULT nextval('public.workout_block_exercises_id_seq'::regclass);


--
-- Name: workout_blocks id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workout_blocks ALTER COLUMN id SET DEFAULT nextval('public.workout_blocks_id_seq'::regclass);


--
-- Name: workout_exercises id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workout_exercises ALTER COLUMN id SET DEFAULT nextval('public.workout_exercises_id_seq'::regclass);


--
-- Name: workout_individual_students id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workout_individual_students ALTER COLUMN id SET DEFAULT nextval('public.workout_individual_students_id_seq'::regclass);


--
-- Name: workout_session_exercises id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workout_session_exercises ALTER COLUMN id SET DEFAULT nextval('public.workout_session_exercises_id_seq'::regclass);


--
-- Name: workout_session_sets id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workout_session_sets ALTER COLUMN id SET DEFAULT nextval('public.workout_session_sets_id_seq'::regclass);


--
-- Name: workout_sessions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workout_sessions ALTER COLUMN id SET DEFAULT nextval('public.workout_sessions_id_seq'::regclass);


--
-- Name: workout_team_player_assignments id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workout_team_player_assignments ALTER COLUMN id SET DEFAULT nextval('public.workout_team_player_assignments_id_seq'::regclass);


--
-- Name: workout_teams id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workout_teams ALTER COLUMN id SET DEFAULT nextval('public.workout_teams_id_seq'::regclass);


--
-- Name: workouts id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workouts ALTER COLUMN id SET DEFAULT nextval('public.workouts_id_seq'::regclass);


--
-- Data for Name: coach_students; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.coach_students (id, student_id, invite_code, status, relationship_type, started_at, ended_at, coach_notes, student_goals, coach_id) FROM stdin;
4	\N	kiH6FUFq	invited	personal	2025-11-19 14:49:27.058395	\N	\N	\N	328980170
\.


--
-- Data for Name: exercises; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.exercises (id, name, category, muscle_group, equipment, difficulty_level, description, instructions, video_url, image_url, created_by, created_at, is_active, test_type, measurement_unit, tags) FROM stdin;
12	Берпи	Функциональные	Все тело	Собственный вес	intermediate	Комплексное упражнение	\N	\N	\N	\N	2025-10-05 15:44:14.475791	t	none	kg	\N
13	Выпады	Функциональные	Ноги	Собственный вес	beginner	Упражнение для баланса	\N	\N	\N	\N	2025-10-05 15:44:14.475791	t	none	kg	\N
14	Горные альпинисты	Функциональные	Корпус	Собственный вес	beginner	Динамическое упражнение	\N	\N	\N	\N	2025-10-05 15:44:14.475791	t	none	kg	\N
15	Подъемы на носки	Функциональные	Икры	Собственный вес	beginner	Упражнение для икр	\N	\N	\N	\N	2025-10-05 15:44:14.475791	t	none	kg	\N
16	Бег трусцой	Кардио	Все тело	Нет	beginner	Аэробная нагрузка	\N	\N	\N	\N	2025-10-05 15:44:14.475791	t	none	kg	\N
17	Велосипед	Кардио	Ноги	Велосипед	beginner	Кардио тренировка	\N	\N	\N	\N	2025-10-05 15:44:14.475791	t	none	kg	\N
18	Прыжки на скакалке	Кардио	Все тело	Скакалка	beginner	Интенсивная кардио нагрузка	\N	\N	\N	\N	2025-10-05 15:44:14.475791	t	none	kg	\N
23	Скручивания на пресс	Функциональные	Корпус	Собственный вес	beginner	Упражнение для пресса	\N	\N	\N	\N	2025-10-05 15:44:14.475791	t	none	kg	\N
26	вертикальный прыжок с подседом	Функциональные	Все тело	Собственный вес	beginner	Атлет должен встать прямо, а затем выполнить выпрыгивание вверх, используя\nбыстрый подсед в ходе которого ноги сгибаются в коленных суставах под\nуглом 90\n- Тренер должен удостовериться в том, что амплитуда подседа во время\nтестирования была достаточной, поскольку неглубокий подсед не\nпозволяет получить максимально возможный результат\n В ходе прыжка атлет должен держать руки на поясе для того, чтобы исключить\nвозможность использования инерционной составляющей махового движения\nрук\n В ходе прыжка атлет должен выпрямить ноги, поднимать колени к груди\nзапрещается	Атлет должен встать прямо, а затем выполнить выпрыгивание вверх, используя\nбыстрый подсед в ходе которого ноги сгибаются в коленных суставах под\nуглом 90\n- Тренер должен удостовериться в том, что амплитуда подседа во время\nтестирования была достаточной, поскольку неглубокий подсед не\nпозволяет получить максимально возможный результат\n В ходе прыжка атлет должен держать руки на поясе для того, чтобы исключить\nвозможность использования инерционной составляющей махового движения\nрук\n В ходе прыжка атлет должен выпрямить ноги, поднимать колени к груди\nзапрещается	\N	\N	1	2025-10-05 18:55:10.181378	t	none	kg	\N
27	прыжок в длину	Функциональные	Все тело	Собственный вес	beginner	прыжок в длину с места	Данный метод оценки также называют тестом прыжком в длину с двух ног\n Атлет должен встать перед размеченной на полу стартовой линией, стопы\nдолжны располагаться непосредственно под тазом\n Затем атлет должен выполнить прыжок вперед, используя быстрый подсед; в\nсравнении с позой четверть-приседа, атлет должен расположить таз несколько\nвыше и слегка отвести его назад, что позволяет получить в ходе прыжка\nмаксимально возможное перемещение по горизонтальной плоскости\n Тренер должен удостовериться в том, что амплитуда подседа во время\nтестирования была достаточной, поскольку неглубокий подсед не позволяет\nполучить максимально возможный результат\n В ходе прыжка атлет должен использовать маховое движение верхними\nконечностями для того, чтобы повысить величину прыжкового импульса, что\nпозволяет получить максимально возможный результат\n- Если атлет сможет выполнить эффективное разгибание в трех суставах\n(тазобедренный, коленный, голеностопный) и задействовать маховое\nдвижение рук, то он сможет создать значительную движущую силу\n Атлет должен выполнить прыжок на максимально возможное расстояние,\nприземлиться на две стопы и не упасть назад	\N	\N	1	2025-10-05 19:00:39.122083	t	none	kg	\N
1	Жим штанги лежа	Силовые	Грудь	Штанга	intermediate	Базовое упражнение для груди	\N	\N	\N	\N	2025-10-05 15:44:14.475791	t	strength	kg	\N
2	Приседания со штангой	Силовые	Ноги	Штанга	intermediate	Базовое упражнение для ног	\N	\N	\N	\N	2025-10-05 15:44:14.475791	t	strength	kg	\N
4	Жим стоя	Силовые	Плечи	Штанга	intermediate	Развитие дельтовидных мышц	\N	\N	\N	\N	2025-10-05 15:44:14.475791	t	strength	kg	\N
5	Подтягивания	Силовые	Спина	Турник	intermediate	Упражнение с собственным весом	\N	\N	\N	\N	2025-10-05 15:44:14.475791	t	strength	kg	\N
6	Отжимания от пола	Силовые	Грудь	Собственный вес	beginner	Базовое упражнение дома	\N	\N	\N	\N	2025-10-05 15:44:14.475791	t	strength	kg	\N
7	Жим гантелей лежа	Силовые	Грудь	Гантели	beginner	Альтернатива жиму штанги	\N	\N	\N	\N	2025-10-05 15:44:14.475791	t	strength	kg	\N
8	Приседания с гантелями	Силовые	Ноги	Гантели	beginner	Упражнение с гантелями	\N	\N	\N	\N	2025-10-05 15:44:14.475791	t	strength	kg	\N
9	Тяга штанги в наклоне	Силовые	Спина	Штанга	intermediate	Развитие мышц спины	\N	\N	\N	\N	2025-10-05 15:44:14.475791	t	strength	kg	\N
10	Подъем на бицепс	Силовые	Бицепс	Штанга	beginner	Изолированное упражнение	\N	\N	\N	\N	2025-10-05 15:44:14.475791	t	strength	kg	\N
19	Жим ногами	Силовые	Ноги	Тренажер	beginner	Безопасная альтернатива приседаниям	\N	\N	\N	\N	2025-10-05 15:44:14.475791	t	strength	kg	\N
20	Тяга верхнего блока	Силовые	Спина	Тренажер	beginner	Развитие широчайших мышц	\N	\N	\N	\N	2025-10-05 15:44:14.475791	t	strength	kg	\N
21	Французский жим	Силовые	Трицепс	Штанга	intermediate	Изолированное упражнение для трицепса	\N	\N	\N	\N	2025-10-05 15:44:14.475791	t	strength	kg	\N
22	Махи гантелями	Силовые	Плечи	Гантели	beginner	Упражнение для дельт	\N	\N	\N	\N	2025-10-05 15:44:14.475791	t	strength	kg	\N
24	Разгибание ног	Силовые	Ноги	Тренажер	beginner	Изолированное упражнение для квадрицепса	\N	\N	\N	\N	2025-10-05 15:44:14.475791	t	strength	kg	\N
25	Сгибание ног	Силовые	Ноги	Тренажер	beginner	Изолированное упражнение для бицепса бедра	\N	\N	\N	\N	2025-10-05 15:44:14.475791	t	strength	kg	\N
11	Планка	Функциональные	Корпус	Собственный вес	beginner	Статическое упражнение	\N	\N	\N	\N	2025-10-05 15:44:14.475791	t	endurance	seconds	\N
28	Бег 100 метров	Кардио	Все тело	Нет	intermediate	Спринтерский забег на максимальной скорости на дистанцию 100 метров	Разогрейтесь, займите стартовую позицию, бегите максимально быстро до финиша	\N	\N	1	2025-10-05 21:55:13.095754	t	speed	seconds	\N
29	Бег 30 метров	Кардио	Все тело	Нет	beginner	Короткий спринт для оценки скоростных качеств	Разогрейтесь, стартуйте из положения высокого старта, бегите максимально быстро	\N	\N	1	2025-10-05 21:55:13.095754	t	speed	seconds	\N
30	Планка классическая	Функциональные	Корпус	Собственный вес	beginner	Статическое упражнение для развития мышц корпуса и выносливости	Примите упор лежа на предплечьях, держите тело прямо, не прогибайтесь в пояснице	\N	\N	1	2025-10-05 21:55:13.095754	t	endurance	seconds	\N
31	Вис на турнике	Функциональные	Спина	Турник	intermediate	Тест силы хвата и выносливости мышц спины	Повисните на турнике, держитесь максимально долго, не раскачивайтесь	\N	\N	1	2025-10-05 21:55:13.095754	t	endurance	seconds	\N
32	Отжимания максимум	Силовые	Грудь	Собственный вес	intermediate	Тест максимального количества отжиманий без отдыха	Примите упор лежа, выполняйте отжимания до мышечного отказа, считайте повторения	\N	\N	1	2025-10-05 21:55:13.095754	t	quantity	reps	\N
33	Супермен	Кардио	Все тело	Собственный вес	beginner	Лягте на живот, вытяните руки вперед, ноги вместе, взгляд в пол. На выдохе одновременно поднимите руки, грудь и ноги на 10-20 см от пола, напрягите пресс и ягодицы	Лягте на живот, вытяните руки вперед, ноги вместе, взгляд в пол. На выдохе одновременно поднимите руки, грудь и ноги на 10-20 см от пола, напрягите пресс и ягодицы	\N	\N	1	2025-12-24 19:41:07.203553	t	none	kg	\N
34	Втягивание подбородка (chin tuck)	Функциональные	Шея	Собственный вес	beginner	упражнение для глубоких мышц шеи	Исходное положение\nСядьте или встаньте прямо, плечи расслаблены, взгляд смотрит вперёд.\n​\n\nСпина фиксирована: не прогибайтесь в пояснице и не запрокидывайте голову.\n\nТехника выполнения\nВытяните подбородок чуть вперёд, не наклоняя голову вверх или вниз, как будто «тянетесь носом к стене перед собой».\n​\n\nЗатем плавно «втяните» подбородок назад, потянувшись затылком к воображаемой стене за головой, удлиняя шею; ощущение — как будто делаете лёгкий «двойной подбородок».\n\nДвижение маленькое, но контролируемое: двигается только шея, не весь корпус.\n​\nПовторы и дыхание\nЗадержитесь в конечном положении 2–5 секунд, дышите спокойно, без задержки дыхания.\n​\nЕсли при упражнении появляется резкая боль, головокружение или онемение рук, выполнение лучше прекратить и обсудить это с врачом или физиотерапевтом.	\N	\N	1	2026-01-21 13:49:53.818868	t	none	kg	\N
35	Присед на стул	Силовые	Ноги	Собственный вес	beginner	подводящее обучающее упражнения к приседу со штангой	Сесть на стул Наклонить корпус вперёд до примерно параллели с голенью, равномерно давить стопами в пол и медленно встать, полностью разогнув тазобедренные суставы, затем таким же контролируемым движением опуститься назад.\nhttps://youtu.be/cB2KF3DAuvg	\N	\N	1	2026-01-21 14:35:38.435489	t	none	kg	\N
36	Мертвый жук (dead bug)	Функциональные	Корпус	Собственный вес	intermediate	укрепляет глубокие мышцы кора, пресса и стабилизаторы поясницы, улучшая координацию и защищая спину от нагрузок	Лягте на спину на коврик, прижмите поясницу к полу, напрягая пресс (ладонь не должна проходить между полом и спиной).\n​\n\nПоднимите прямые руки к потолку, согните ноги в коленях под 90° (голени параллельны полу, колени над тазом).\n\nТехника выполнения\nНа вдохе медленно опустите противоположные конечности: правую руку за голову и левую ногу вперёд, не касаясь пола (удерживайте на 10–15 см), сохраняя поясницу прижатой.\n\nНа выдохе вернитесь в исходное положение, напрягая пресс, затем повторите с левой рукой и правой ногой.\n​\n\nДвижения контролируемые, без рывков; чередуйте стороны	\N	\N	1	2026-01-21 14:44:28.027936	t	none	kg	\N
37	Разгибание спины лежа на животе с упором рук в пол	Функциональные	Спина	Собственный вес	beginner	ЛФК упражнение для спины	Исходное положение\n   Лягте на живот, ноги прямые и плотно прижаты к полу, руки вытяните вперёд ладонями вниз или поставьте ладони под плечами.\n​\n​Поясница слегка расслаблена, взгляд в пол, шея в нейтральном положении.\n​\n\nТехника выполнения\n   На выдохе отожмитесь руками от пола, разгибая локти и поднимая грудь и верх спины вверх, максимально прогибаясь в поясничном отделе (таз остаётся на полу).\n​\n\nУпор идёт через руки, ноги не отрываются; задержитесь, чувствуя растяжение в брюшных мышцах и работу спины.\n​\n​\n\nНа вдохе медленно опуститесь, расслабляя тело	\N	\N	1	2026-01-21 14:54:16.199075	t	none	kg	\N
38	Ягодичный мост на одной ноге	Силовые	Ноги	Собственный вес	intermediate	упражнение на ягодицы и заднюю поверхность бедра	Исходное положение\nЛяг на спину на коврик, поясница прижата к полу, живот чуть подтянут.\n\nОдну ногу согни в колене и поставь на пятку. вторая нога согнута в колене и находится чуть выше опорной\n\nТехника подъёма\nНа выдохе сильно напряги ягодицу опорной ноги и дави пяткой в пол, поднимая таз вверх.\n​\nПоднимай таз до прямой линии: плечи – таз – колено опорной ноги (как «столешница»), без излишнего прогиба в пояснице.\n​\n\nВ верхней точке:\n\nягодица максимально зажата,\n\nтаз не разворачивается и не заваливается в сторону поднятой ноги,\nкорпус стабильный.\n​Задержись вверху 1–2 секунды, продолжая держать напряжение.\n​\nТехника опускания\nНа вдохе медленно опусти таз вниз до лёгкого касания пола, не «роняя» его.\n​\nНе полностью расслабляй ягодицу внизу, чтобы сохранять лёгкое напряжение.	\N	\N	1	2026-01-21 15:21:41.027944	t	none	kg	\N
39	Отжимания с колен	Силовые	Грудь	Собственный вес	beginner	упрощённый вариант классических отжиманий. на грудные мышцы, трицепсы и передние дельты. Упражнение снижает вес тела примерно на 50–60%, делая его доступным, но сохраняя эффективность для проработки верхней части груди	Исходное положение\nВстаньте на четвереньки: ладони на полу чуть шире плеч, пальцы вперёд, колени на ширине бедер (можно подложить коврик или полотенце для комфорта).\n​\nСтопы скрестите или держите параллельно, тело от головы до колен — прямая линия, пресс напряжён, лопатки слегка сведены.\n\nВзгляд вниз на 20–30 см вперёд, шея не напрягается.\n\nТехника выполнения\nНа вдохе медленно сгибайте локти, опуская корпус вниз: локти идут назад под углом 45° к телу, не разводите их в стороны.\n​\nОпуститесь, пока грудь почти коснётся пола (или локти образуют прямой угол), плечи на уровне локтей.\n\nНа выдохе мощно отожмитесь вверх, выпрямляя руки, но не блокируйте локти полностью — сохраняйте лёгкое напряжение.\n\nВ верхней точке сожмите грудные мышцы на 1 секунду.	\N	\N	1	2026-01-21 15:24:26.789781	t	none	kg	\N
43	боковая планка	Выносливость	Корпус	Собственный вес	beginner	укрепление мышц кора	Лечь на бок, опираясь на предплечье. Локоть должен находиться прямо под плечом.\n   Ноги вытянуты прямо, стопы одна на другой или одна перед другой для большей устойчивости.\n  Поднять бёдра вверх, удерживая тело в прямой линии от головы до пяток.\n   Держать голову в нейтральном положении, смотреть вперёд.	\N	\N	1	2026-01-29 14:14:10.462856	t	endurance	kg	\N
60	Присед со штангой на груди	Силовые	Квадрицепсы	Штанга	intermediate	Вариант приседа с расположением снаряда на передних пучках дельтовидных мышц.	1. Расположите гриф на передних дельтах и ключицах, удерживая его параллельным хватом. 2. Поднимите локти до положения, при котором плечевые кости параллельны полу. 3. Выполните присед, сохраняя вертикальное положение туловища, пока бедра не станут параллельны полу. 4. Синхронно разогните ноги, сохраняя грудь поднятой.	\N	\N	1	2026-02-17 15:20:42.275074	t	strength	кг	\N
61	Присед со штангой над головой	Силовые	Все тело	Штанга	advanced	Сложное упражнение на стабильность туловища и контроль центра масс.	1. Удерживайте штангу над головой широким хватом, руки полностью выпрямлены. 2. Зафиксируйте лопатки и напрягите мышцы кора. 3. Медленно опуститесь в присед, удерживая штангу в вертикальной проекции плечевых суставов. 4. Встаньте, сохраняя неподвижное положение снаряда над головой.	\N	\N	1	2026-02-17 15:20:42.275074	t	strength	кг	\N
62	Становая тяга сумо	Силовые	Бедра и спина	Штанга	intermediate	Вариант тяги с широкой постановкой ног, снижающий нагрузку на поясницу.	1. Встаньте в широкую стойку, носки развернуты в стороны. 2. Возьмитесь за гриф узким хватом внутри коленей. 3. Опустите таз, сохраняя спину прямой и грудь поднятой. 4. Выполните подъем за счет мощного разгибания ног, удерживая гриф близко к телу.	\N	\N	1	2026-02-17 15:20:42.275074	t	strength	кг	\N
63	Румынская тяга	Силовые	Задняя поверхность бедра	Штанга	intermediate	Упражнение для акцентированной проработки задней цепи и ягодиц.	1. Удерживайте штангу на уровне бедер, ноги слегка согнуты в коленях (5-10 градусов). 2. Отводите таз назад, плавно опуская штангу вдоль бедер до середины голени. 3. Сохраняйте спину идеально прямой, не допуская скругления. 4. Вернитесь в исходное положение за счет сокращения мышц задней поверхности бедра.	\N	\N	1	2026-02-17 15:20:42.275074	t	strength	кг	\N
64	Силовой подъем штанги на грудь	Силовые	Все тело	Штанга	advanced	Взрывное тяжелоатлетическое упражнение для развития мощности.	1. Выполните тягу штанги с пола с максимальным ускорением. 2. В фазе подрыва выполните "тройное разгибание" (голеностоп, колени, таз). 3. Быстро подсядьте под штангу, принимая ее на передние дельты. 4. Зафиксируйте положение и полностью выпрямитесь.	\N	\N	1	2026-02-17 15:20:42.275074	t	strength	кг	\N
65	Швунг жимовой	Силовые	Плечи и ноги	Штанга	intermediate	Мощностное жимовое движение с использованием импульса ног.	1. Удерживайте штангу на груди, как при фронтальном приседе. 2. Выполните короткий быстрый подсед (10-15 см). 3. Резко вытолкните штангу вверх за счет разгибания ног. 4. Дожмите снаряд руками до полной фиксации над головой.	\N	\N	1	2026-02-17 15:20:42.275074	t	strength	кг	\N
66	Отжимания с хлопком	Функциональные	Грудные мышцы	Без оборудования	advanced	Плиометрический вариант отжиманий для развития взрывной силы верха тела.	1. Примите упор лежа. 2. Быстро опуститесь и мощно оттолкнитесь от пола. 3. В фазе полета выполните хлопок ладонями перед грудью. 4. Мягко приземлитесь на руки, сразу переходя к следующему повторению.	\N	\N	1	2026-02-17 15:20:42.275074	t	quantity	раз	\N
67	Прыжки колени к груди	Функциональные	Ноги и кор	Без оборудования	intermediate	Интенсивное прыжковое упражнение для развития скорости сокращения мышц-сгибателей бедра.	1. Встаньте прямо, ноги на ширине таза. 2. Выполните выпрыгивание вертикально вверх на максимальную высоту. 3. В полете резко подтяните колени как можно ближе к груди. 4. Быстро разогните ноги для мягкого приземления в точку старта.	\N	\N	1	2026-02-17 15:20:42.275074	t	quantity	раз	\N
68	Падающий старт	Скоростные	Ноги	Без оборудования	beginner	Упражнение для отработки наклона туловища при стартовом ускорении.	1. Встаньте прямо, стопы вместе. 2. Медленно наклоняйте все тело вперед, не сгибаясь в талии. 3. В момент потери равновесия сделайте резкий взрывной шаг вперед. 4. Продолжайте ускорение на дистанции 5-10 метров.	\N	\N	1	2026-02-17 15:20:42.275074	t	speed	сек	\N
69	Бег спиной вперед	Скоростные	Ноги	Без оборудования	intermediate	Развивает координацию, проприоцепцию и мышцы-разгибатели бедра.	1. Примите положение низкой стойки, центр масс смещен вперед. 2. Выполняйте шаги назад, отталкиваясь передним отделом стопы. 3. Сохраняйте наклон туловища вперед, не выпрямляясь полностью. 4. Активно работайте руками в такт движения ног.	\N	\N	1	2026-02-17 15:20:42.275074	t	speed	сек	\N
70	Болгарский сплит-присед	Силовые	Ноги	Гантели	intermediate	Одностороннее упражнение для устранения дисбаланса силы мышц ног.	1. Встаньте спиной к скамье, положите на нее носок одной ноги. 2. Удерживайте гантели в опущенных руках. 3. Опуститесь в присед на опорной ноге до параллели бедра с полом. 4. Колено опорной ноги не должно выходить за носок. Поднимитесь вверх.	\N	\N	1	2026-02-17 15:20:42.275074	t	strength	кг	\N
71	Бросок набивного мяча об пол	Функциональные	Все тело	Другое	intermediate	Баллистическое упражнение для развития мощности мышц передней цепи.	1. Поднимите набивной мяч высоко над головой, полностью выпрямив тело. 2. С резким выдохом мощно бросьте мяч в пол прямо перед собой. 3. Задействуйте мышцы пресса и широчайшие, "складываясь" вслед за мячом. 4. Поймайте мяч после отскока и повторите.	\N	\N	1	2026-02-17 15:20:42.275074	t	quantity	раз	\N
72	Тяга толчковая с плинтов	Силовые	Спина и ноги	Штанга	intermediate	Частичная тяга для отработки фазы подрыва и снижения нагрузки на поясницу.	1. Установите штангу на плинты (высота чуть ниже или выше колен). 2. Примите стартовое положение: спина прямая, плечи над грифом. 3. Выполните мощный подрыв штанги вверх за счет разгибания ног и шрага плечами. 4. Контролируемо верните снаряд на плинты.	\N	\N	1	2026-02-17 15:20:42.275074	t	strength	кг	\N
73	Боковая планка с отведением бедра	Функциональные	Мышцы кора	Коврик	intermediate	Усложненный вариант планки для развития поперечной стабильности.	1. Примите положение боковой планки на предплечье. 2. Поднимите таз, образуя прямую линию от головы до стоп. 3. Поднимите верхнюю прямую ногу вверх и удерживайте ее. 4. Сохраняйте положение, не допуская провисания таза.	\N	\N	1	2026-02-17 15:20:42.275074	t	endurance	сек	\N
74	Толчок в ножницы	Силовые	Все тело	Штанга	advanced	Классическое тяжелоатлетическое движение для переноса веса с груди над головой с разбросом ног.	1. Удерживайте штангу на груди в позиции фронтального приседа. 2. Сделайте короткий подсед и мощно вытолкните штангу вверх. 3. Одновременно прыжком разбросайте ноги: одну вперед на всю стопу, другую назад на носок (позиция "ножницы"). 4. Зафиксируйте штангу над головой, подставив ноги друг к другу. 5. Контролируемо опустите снаряд.	\N	\N	1	2026-02-17 15:22:01.42456	t	strength	кг	\N
75	Рывок штанги с виса	Силовые	Все тело	Штанга	advanced	Взрывное упражнение, где штанга поднимается с уровня колен над головой одним движением.	1. Удерживайте штангу широким хватом на уровне чуть выше колен, спина прямая. 2. Выполните мощный подрыв за счет разгибания таза, коленей и голеностопа. 3. Активно работая трапециями и руками, направляйте штангу вертикально вверх. 4. Быстро подсядьте под гриф, принимая его на прямые руки над головой. 5. Встаньте из седа, удерживая штангу зафиксированной.	\N	\N	1	2026-02-17 15:22:01.42456	t	strength	кг	\N
76	Скрестный шаг (Кариока)	Скоростные	Ноги	Без оборудования	beginner	Беговое упражнение на координацию и мобильность тазобедренного сустава при движении боком.	1. Начните движение боком по прямой линии. 2. Сделайте шаг ведущей ногой в сторону. 3. Заднюю ногу пронесите перед ведущей, делая скрестный шаг. 4. Снова шагните ведущей ногой в сторону. 5. Заднюю ногу пронесите позади ведущей. 6. Повторяйте цикл, активно вращая тазом и удерживая туловище прямо.	\N	\N	1	2026-02-17 15:22:01.42456	t	speed	сек	\N
77	Бег в упоре в стену	Скоростные	Ноги	Без оборудования	beginner	Упражнение для отработки механики цикла махового шага и угла наклона туловища.	1. Обопритесь прямыми руками о стену под углом 45-60 градусов. 2. Поднимите одну ногу, согнув ее в колене так, чтобы бедро было параллельно полу. 3. По команде или в ритме выполняйте быструю смену ног ("бег"), акцентированно толкаясь передним отделом стопы. 4. Следите, чтобы таз не провисал, а спина оставалась жесткой линией.	\N	\N	1	2026-02-17 15:22:01.42456	t	speed	сек	\N
78	Слалом на координационной лесенке	Функциональные	Ноги	Другое	intermediate	Координационное упражнение с быстрыми прыжками из стороны в сторону вдоль лесенки.	1. Встаньте боком к первому квадрату лесенки. 2. Прыгните двумя ногами в центр квадрата. 3. Следующим прыжком выпрыгните вперед и в сторону за пределы лесенки. 4. Снова прыгните в следующий квадрат и затем в другую сторону наружу. 5. Сохраняйте минимальное время контакта с полом и работайте на передней части стопы.	\N	\N	1	2026-02-17 15:22:01.42456	t	quantity	раз	\N
79	Прыжки конькобежца	Функциональные	Бедра и ягодицы	Без оборудования	intermediate	Плиометрическое упражнение, имитирующее боковое отталкивание конькобежца.	1. Встаньте прямо, сделайте мощный прыжок в сторону на правую ногу. 2. Левую ногу заведите назад за правую, не касаясь пола или едва касаясь для баланса. 3. Сразу же мощно оттолкнитесь правой ногой и прыгните влево на левую ногу. 4. Помогайте себе активными махами рук в такт движениям.	\N	\N	1	2026-02-17 15:22:01.42456	t	quantity	раз	\N
80	Бросок набивного мяча за спину	Функциональные	Все тело	Другое	intermediate	Мощностное упражнение для развития взрывной силы задней цепи.	1. Встаньте спиной к направлению броска, ноги на ширине плеч, мяч в руках внизу. 2. Выполните глубокий подсед, занося мяч между ног. 3. Мощно разогнитесь (тройное разгибание) и бросьте мяч через голову назад-вверх. 4. Старайтесь придать мячу максимальное ускорение за счет работы таза и спины.	\N	\N	1	2026-02-17 15:22:01.42456	t	quantity	раз	\N
81	Ягодичный мост с опорой на скамью	Силовые	Ягодицы	Другое	intermediate	Вариант мостика с увеличенной амплитудой движения за счет возвышения.	1. Расположите лопатки на краю горизонтальной скамьи, стопы плотно прижаты к полу. 2. Опустите таз вниз, растягивая ягодичные мышцы. 3. Мощным движением поднимите таз вверх до прямой линии с туловищем. 4. В верхней точке сделайте паузу, максимально напрягая ягодицы. 5. Медленно опуститесь в исходное положение.	\N	\N	1	2026-02-17 15:22:01.42456	t	strength	раз	\N
82	Y-разведения рук с эспандером	Функциональные	Плечи и верх спины	Эспандер	beginner	Корригирующее упражнение для стабилизации лопаток и осанки.	1. Закрепите эспандер на уровне груди или ниже. 2. Удерживая концы эспандера, поднимите прямые руки вверх и в стороны, образуя букву "Y". 3. Сводите лопатки и не поднимайте плечи к ушам. 4. Медленно вернитесь в исходное положение, сохраняя натяжение.	\N	\N	1	2026-02-17 15:22:01.42456	t	quantity	раз	\N
83	Тяга Т-грифа	Силовые	Спина	Штанга	intermediate	Базовое упражнение для развития толщины мышц спины.	1. Встаньте над грифом, закрепленным с одной стороны (или в Т-тренажере), ноги согнуты в коленях. 2. Возьмитесь за рукоять узким хватом, спина прямая, таз отведен назад. 3. Притяните вес к животу, сводя лопатки в верхней точке. 4. Медленно опустите вес, полностью растягивая широчайшие мышцы.	\N	\N	1	2026-02-17 15:22:01.42456	t	strength	кг	\N
84	Пулловер с набивным мячом	Функциональные	Грудные и пресс	Другое	intermediate	Функциональное упражнение на связь верха тела и мышц кора.	1. Лягте на спину, ноги согнуты, мяч удерживается прямыми руками над грудью. 2. Медленно заведите прямые руки с мячом за голову, не прогибая поясницу. 3. Верните мяч в исходное положение за счет сокращения мышц груди и пресса. 4. Для усложнения добавьте одновременный подъем ног или переход в положение сидя.	\N	\N	1	2026-02-17 15:22:01.42456	t	quantity	раз	\N
85	Прыжковые подтягивания	Функциональные	Спина и руки	Турник	beginner	Подводящее упражнение для развития мощности тяговых движений.	1. Встаньте под перекладиной, которая находится чуть выше вытянутых рук. 2. Сделайте небольшой подсед и мощно выпрыгните вверх, одновременно помогая себе тяговым движением рук. 3. Подтяните подбородок выше перекладины. 4. Контролируемо опуститесь вниз и сразу повторите прыжок.	\N	\N	1	2026-02-17 15:22:01.42456	t	quantity	раз	\N
86	Тройной прыжок в длину	Скоростные	Ноги	Без оборудования	advanced	Плиометрическое упражнение для развития реактивной силы ног.	1. Выполните прыжок вперед с одной ноги (толчковой). 2. Приземлитесь на маховую ногу и сразу же сделайте второй длинный прыжок (шаг). 3. После приземления на вторую ногу выполните финальный прыжок в длину, приземляясь на обе стопы. 4. Задача — минимизировать время контакта с землей между фазами.	\N	\N	1	2026-02-17 15:22:01.42456	t	speed	м	\N
87	Тяга рывковая	Силовые	Спина и ноги	Штанга	intermediate	Специальное упражнение для наработки фазы подрыва в рывке.	1. Установите штангу на пол, возьмитесь за гриф максимально широким (рывковым) хватом. 2. Начните подъем штанги как в становой тяге, но с акцентом на вертикальную траекторию. 3. В момент прохождения грифом середины бедер выполните мощный шраг плечами и подъем на носки. 4. Локти направляйте вверх, сохраняя штангу близко к телу. Не подсаживайтесь под штангу.	\N	\N	1	2026-02-17 15:22:01.42456	t	strength	кг	\N
88	Отведение стопы (активация)	Функциональные	Ноги	Без оборудования	beginner	Начальное упражнение для пробуждения малоберцовых мышц в первые дни после травмы.	1. Сядьте на пол с вытянутыми ногами.\n2. Удерживайте стопу в нейтральном положении, не натягивая носок на себя или от себя.\n3. Отведите стопу максимально в сторону (наружу), работая только голеностопом.\n4. Медленно вернитесь в исходное положение.\n5. Избегайте вращения всей ногой в колене или бедре.	\N	\N	1	2026-02-17 15:25:29.46425	t	quantity	раз	\N
89	Отведение стопы с эспандером	Силовые	Ноги	Эспандер	beginner	Укрепление малоберцовых мышц, которые являются главными стабилизаторами от повторного подворота.	1. Закрепите эспандер на стопе и создайте сопротивление, натянув его рукой или второй ногой.\n2. Совершайте движение стопой наружу, преодолевая натяжение резины.\n3. Сохраняйте полную амплитуду движения, сравнивая ее с движением без резинки.\n4. Плавно возвращайте стопу обратно, контролируя сопротивление.\n5. Выполняйте до появления легкой усталости.	\N	\N	1	2026-02-17 15:25:29.46425	t	strength	раз	\N
90	Тяга стопы на себя (активация)	Функциональные	Ноги	Без оборудования	beginner	Восстановление контроля над передней большеберцовой мышцей для устранения отека.	1. Вытяните ноги перед собой в положении сидя.\n2. Максимально потяните носок травмированной ноги на себя.\n3. Задержитесь в верхней точке на 1-2 секунды.\n4. Плавно опустите стопу в нейтральное положение.\n5. Выполняйте движение плавно, избегая резких рывков.	\N	\N	1	2026-02-17 15:25:29.46425	t	quantity	раз	\N
91	Тяга стопы на себя с сопротивлением	Силовые	Ноги	Без оборудования	intermediate	Силовая проработка передней цепи голени с использованием самосопротивления.	1. Сядьте на пол, положите пятку здоровой ноги на пальцы травмированной ноги.\n2. Оказывайте давление верхней ногой вниз, создавая нагрузку.\n3. Травмированной стопой тяните носок вверх, преодолевая сопротивление второй ноги.\n4. Сохраняйте напряжение как при движении вверх, так и при медленном возвращении вниз.\n5. Работайте в максимально доступной безболезненной амплитуде.	\N	\N	1	2026-02-17 15:25:29.46425	t	strength	раз	\N
92	Жим стопой от себя с эспандером	Силовые	Ноги	Эспандер	beginner	Подготовка икроножной мышцы к осевой нагрузке и ходьбе.	1. Накиньте ленточный эспандер на верхнюю часть стопы и натяните его руками на себя.\n2. Толкайте стопу от себя, имитируя нажатие на педаль газа.\n3. Удерживайте колено полностью прямым во время выполнения.\n4. Плавно возвращайте стопу в положение «носок на себя», контролируя резину.\n5. Не выполняйте в конечной амплитуде, если это вызывает острую боль.	\N	\N	1	2026-02-17 15:25:29.46425	t	strength	раз	\N
93	Статическое удержание баланса	Выносливость	Ноги	Без оборудования	beginner	Тренировка проприоцепции и стабильности сустава без лишних движений.	1. Встаньте на травмированную ногу, слегка согнув ее в колене.\n2. Вторую ногу оторвите от пола.\n3. Удерживайте равновесие, стараясь не помогать себе руками.\n4. Фокусируйтесь на том, чтобы стопа не «заваливалась» внутрь или наружу.\n5. Удерживайте положение 50-60 секунд.	\N	\N	1	2026-02-17 15:25:29.46425	t	endurance	сек	\N
103	Толкание саней	Силовые	Ноги и кор	Другое	intermediate	Мощностное упражнение для развития силы отталкивания и анаэробной выносливости.	1. Примите упор в рукояти саней, наклонив туловище вперед под углом 45-60 градусов. 2. Удерживайте спину прямой, таз не должен подниматься слишком высоко. 3. Мощно отталкивайтесь передней частью стопы, имитируя бег с акцентом на разгибание бедра. 4. Перемещайте сани на заданную дистанцию без остановки.	\N	\N	1	2026-02-17 15:30:38.119918	t	strength	кг	\N
94	Баланс с поворотами головы	Выносливость	Ноги	Без оборудования	intermediate	Усложнение тренировки баланса за счет отключения вестибулярной стабилизации.	1. Встаньте на одну ногу и поймайте стабильное положение.\n2. Начните медленно поворачивать голову влево до упора, затем вправо.\n3. Следите за голеностопом — он должен активно «подлавливать» центр тяжести.\n4. Не касайтесь пола второй ногой во время поворотов.\n5. Выполняйте в течение одной минуты.	\N	\N	1	2026-02-17 15:25:29.46425	t	endurance	сек	\N
95	Подъем на носки у стены	Силовые	Ноги	Без оборудования	beginner	Базовое укрепление голени при распределении веса на две ноги.	1. Встаньте лицом к стене и слегка упритесь в нее ладонями для баланса.\n2. Распределите вес тела равномерно между обеими стопами.\n3. Плавно поднимитесь на носки максимально высоко.\n4. Медленно опуститесь на пятки.\n5. Контролируйте, чтобы голеностопные суставы не расходились в стороны.	\N	\N	1	2026-02-17 15:25:29.46425	t	strength	раз	\N
96	Подъем на носок на одной ноге	Силовые	Ноги	Без оборудования	intermediate	Ключевое упражнение для восстановления силы, необходимой для бега и прыжков.	1. Встаньте на одну ногу, придерживаясь рукой за опору.\n2. Выполните подъем на носок максимально высоко и мощно.\n3. Опуститесь вниз в медленном, подконтрольном темпе.\n4. Выполняйте упражнение почти до отказа (пока мышцы голени не начнут «гореть»).\n5. Сравните количество повторений со здоровой ногой.	\N	\N	1	2026-02-17 15:25:29.46425	t	strength	раз	\N
97	Функциональный выпад вперед	Функциональные	Ноги	Без оборудования	intermediate	Развитие мобильности сустава и силы в динамическом паттерне ходьбы.	1. Сделайте шаг вперед в положение широкого выпада.\n2. Опускайтесь вниз, активно вынося колено передней ноги за линию пальцев стопы.\n3. Следите, чтобы пятка передней ноги не отрывалась от пола.\n4. Держите колено направленным строго по линии второго пальца стопы.\n5. Вернитесь в исходное положение толчком передней ноги.	\N	\N	1	2026-02-17 15:25:29.46425	t	quantity	раз	\N
98	Приведение стопы внутрь с резиной	Силовые	Ноги	Эспандер	intermediate	Укрепление внутренней группы мышц на этапе поздней реабилитации.	1. Закрепите эспандер с наружной стороны и накиньте его на стопу.\n2. Создайте сопротивление так, чтобы резина тянула стопу наружу.\n3. Совершайте движение стопой внутрь, преодолевая натяжение.\n4. Работайте в медленном темпе, задерживаясь в точке максимального сокращения.\n5. Возвращайте стопу в исходную позицию под контролем.	\N	\N	1	2026-02-17 15:25:29.46425	t	strength	раз	\N
99	Растяжка голеностопа сидя на пятках	Выносливость	Ноги	Коврик	intermediate	Восстановление полной амплитуды подошвенного сгибания.	1. Опуститесь на колени на коврик, стопы вытянуты носками назад.\n2. Медленно садитесь тазом на свои пятки, создавая натяжение по передней части голеностопа.\n3. Регулируйте нагрузку, перенося часть веса тела на руки перед собой.\n4. Оставайтесь в положении 60 секунд при легком ощущении растяжения (2-3 балла боли).\n5. Не выполняйте через острую боль.	\N	\N	1	2026-02-17 15:25:29.46425	t	endurance	сек	\N
100	Боковые прыжки «Конькобежец»	Функциональные	Ноги	Без оборудования	advanced	Тренировка амортизационной функции и уверенности при приземлении.	1. Встаньте на одну ногу, колено слегка согнуто, корпус наклонен вперед.\n2. Сделайте прыжок в сторону, приземляясь на другую ногу.\n3. При приземлении «пружиньте» ногой, сохраняя баланс и не заваливая колено.\n4. Зафиксируйте положение на секунду перед следующим прыжком.\n5. Постепенно увеличивайте ширину прыжка и его высоту.	\N	\N	1	2026-02-17 15:25:29.46425	t	quantity	раз	\N
101	Скоростные прыжки через линию	Скоростные	Ноги	Другое	advanced	Тест на максимальную скорость стабилизации голеностопа на одной ноге.	1. Положите на пол тонкую линию или лист бумаги.\n2. Встаньте на одну ногу сбоку от линии.\n3. Совершайте прыжки через линию туда-обратно максимально быстро.\n4. Старайтесь не задевать препятствие и не касаться пола второй ногой.\n5. Выполняйте тест в течение 30 секунд, считая количество касаний.	\N	\N	1	2026-02-17 15:25:29.46425	t	speed	сек	\N
102	Подъем на носок на ступеньке	Силовые	Ноги	Другое	advanced	Силовая тренировка в увеличенной амплитуде для «железобетонного» голеностопа.	1. Встаньте носком на край ступеньки или платформы.\n2. Медленно опустите пятку максимально ниже уровня ступеньки.\n3. Мощно поднимитесь вверх на носок до отказа.\n4. Опускайтесь плавно, растягивая мышцы голени в нижней точке.\n5. Для усложнения используйте дополнительное отягощение в руке (гирю или гантель).	\N	\N	1	2026-02-17 15:25:29.46425	t	strength	раз	\N
104	Наклоны "Доброе утро"	Силовые	Задняя цепь	Штанга	intermediate	Фундаментальное упражнение для укрепления мышц-разгибателей спины и задней поверхности бедра.	1. Расположите штангу на верхнем отделе трапеций, как при приседаниях. 2. Удерживая спину прямой, плавно отведите таз назад, наклоняя туловище вперед. 3. Опускайтесь до параллели туловища с полом или до момента, когда почувствуете сильное растяжение в бедрах. 4. Вернитесь в вертикальное положение за счет сокращения ягодиц и мышц задней поверхности бедра.	\N	\N	1	2026-02-17 15:30:38.119918	t	strength	кг	\N
105	Отжимания на брусьях	Силовые	Грудь и трицепс	Брусья	intermediate	Базовое упражнение с закрытой кинетической цепью для развития верха тела.	1. Примите положение упора на брусьях на прямых руках. 2. Плавно опуститесь вниз, сгибая руки в локтях до угла 90 градусов. 3. Слегка наклоните туловище вперед для большего акцента на грудные мышцы. 4. Мощным движением выжмите себя вверх до полной фиксации локтей.	\N	\N	1	2026-02-17 15:30:38.119918	t	strength	раз	\N
106	Подъем прямых ног в висе	Функциональные	Пресс	Турник	advanced	Сложное упражнение для глубокой проработки мускулатуры туловища и сгибателей бедра.	1. Повисните на перекладине прямым хватом. 2. Не используя инерцию (раскачку), поднимите прямые ноги до касания перекладины носками. 3. Плавно опустите ноги в исходное положение, сохраняя контроль над тазом. 4. Старайтесь избегать прогиба в пояснице в нижней точке.	\N	\N	1	2026-02-17 15:30:38.119918	t	quantity	раз	\N
107	Становая тяга с трэп-грифом	Силовые	Все тело	Штанга	intermediate	Вариант тяги с использованием шестигранного грифа, снижающий нагрузку на поясницу.	1. Встаньте внутрь трэп-грифа, стопы на ширине плеч. 2. Возьмитесь за параллельные рукояти, опустив таз и удерживая спину прямой. 3. Начните подъем, одновременно разгибая колени и таз. 4. Зафиксируйте вертикальное положение, не отклоняясь назад в верхней точке.	\N	\N	1	2026-02-17 15:30:38.119918	t	strength	кг	\N
108	Жим гантелей на наклонной скамье	Силовые	Верх груди	Гантели	intermediate	Акцентированное развитие верхней части грудных мышц и передних дельт.	1. Лягте на скамью, установленную под углом 30-45 градусов. 2. Удерживайте гантели над грудью, лопатки сведены и прижаты к скамье. 3. Плавно опустите гантели до уровня плеч, растягивая грудные мышцы. 4. Мощным движением выжмите гантели вверх, сводя их в верхней точке.	\N	\N	1	2026-02-17 15:30:38.119918	t	strength	кг	\N
109	Поперечные махи гирей	Функциональные	Все тело	Гиря	intermediate	Баллистическое упражнение для развития стабильности в горизонтальной плоскости.	1. Встаньте прямо, удерживая гирю двумя руками. 2. Выполните мах гирей не вперед, а в сторону, вращая туловище и таз. 3. Гасите инерцию гири за счет мышц кора и переноса веса на одну ногу. 4. Сразу же выполняйте мах в противоположную сторону по дуге.	\N	\N	1	2026-02-17 15:30:38.119918	t	quantity	раз	\N
110	Вертикальный прыжок с махом руками	Функциональные	Ноги	Без оборудования	intermediate	Тестовое упражнение для оценки взрывной мощности нижней части тела.	1. Встаньте прямо, ноги на ширине плеч. 2. Выполните быстрый подсед, одновременно отводя прямые руки назад. 3. Резко выпрыгните вертикально вверх, совершая мощный мах руками над головой. 4. Приземлитесь мягко на обе стопы в полуприсед, контролируя баланс.	\N	\N	1	2026-02-17 15:30:38.119918	t	quantity	раз	\N
111	Упражнение "Лодочка" с набивным мячом	Функциональные	Спина	Другое	intermediate	Укрепление мышц-стабилизаторов позвоночника и задней цепи.	1. Лягте на живот, руки вытянуты вперед и удерживают набивной мяч. 2. Одновременно поднимите прямые руки с мячом и прямые ноги над полом. 3. Зафиксируйте положение на 1-2 секунды, глядя в пол. 4. Плавно опуститесь в исходное положение.	\N	\N	1	2026-02-17 15:30:38.119918	t	quantity	раз	\N
112	Поперечное запрыгивание на плиобокс	Функциональные	Ноги	Другое	advanced	Плиометрическое упражнение для развития боковой мощности и координации.	1. Встаньте боком к плиобоксу (высота 30-45 см). 2. Выполните прыжок в сторону, запрыгивая обеими ногами на бокс. 3. Спрыгните с противоположной стороны бокса. 4. Немедленно запрыгните обратно, двигаясь в обратном направлении.	\N	\N	1	2026-02-17 15:30:38.119918	t	quantity	раз	\N
113	Ходьба с высоким подниманием бедра	Функциональные	Ноги и кор	Без оборудования	beginner	Базовое беговое упражнение для отработки механики шага и активации сгибателей бедра.	1. Двигайтесь вперед короткими шагами. 2. На каждом шаге поднимайте бедро до параллели с полом или выше. 3. Сохраняйте туловище строго вертикально, не наклоняясь назад. 4. Работайте руками активно, согнув их в локтях под углом 90 градусов.	\N	\N	1	2026-02-17 15:30:38.119918	t	quantity	раз	\N
114	Взрывные подскоки ("Олений бег")	Скоростные	Ноги	Без оборудования	intermediate	Прыжковое упражнение для развития длины махового шага и реактивной силы.	1. Начните бег, делая акцентированное выталкивание вверх-вперед на каждом шаге. 2. Маховая нога должна подниматься высоко, колено выносится вперед. 3. Старайтесь "зависнуть" в фазе полета на максимальное время. 4. Приземление должно быть упругим на переднюю часть стопы.	\N	\N	1	2026-02-17 15:30:38.119918	t	speed	сек	\N
115	Диск-щит (Парирование мяча)	Функциональные	Плечи и кор	Штанга	intermediate	Специфическое упражнение на реакцию и стабильность плечевого пояса.	1. Встаньте в стойку готовности, удерживая диск от штанги (10-20 кг) перед грудью на вытянутых или полусогнутых руках. 2. Партнер бросает набивной мяч в вашу сторону. 3. Задача — парировать (отбить) мяч диском, не теряя равновесия и сохраняя жесткость корпуса. 4. После контакта сразу вернитесь в исходное положение для следующего отражения.	\N	\N	1	2026-02-17 15:30:38.119918	t	quantity	раз	\N
116	Прыжки "из седа в сед"	Функциональные	Ноги	Без оборудования	advanced	Плиометрическое упражнение высокой интенсивности для развития взрывной силы.	1. Опуститесь в глубокий присед (ниже параллели). 2. Без паузы в нижней точке мощно выпрыгните вертикально вверх. 3. В полете удерживайте тело ровно. 4. Приземлитесь сразу в глубокий присед и немедленно повторите прыжок.	\N	\N	1	2026-02-17 15:30:38.119918	t	quantity	раз	\N
3	Становая тяга	Силовые	Спина	Штанга	advanced	Комплексное упражнение	\N	\N	\N	\N	2025-10-05 15:44:14.475791	t	strength	kg	база
117	тесттесттесттесттесттест	Силовые	Трицепс	Нет	intermediate	тесттесттесттесттесттесттесттесттест	тесттесттесттесттесттесттесттесттесттесттест	\N	\N	1	2026-02-18 12:41:24.928817	t	strength	kg	#тест
\.


--
-- Data for Name: individual_student_workouts; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.individual_student_workouts (id, workout_id, student_id, assigned_at, completed_at, status, rpe) FROM stdin;
\.


--
-- Data for Name: individual_students; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.individual_students (id, coach_telegram_id, first_name, last_name, telegram_id, phone, birth_date, specialization, level, notes, is_active, created_at) FROM stdin;
11	328980170	Юля	Панчина	\N	beginner	\N	\N	beginner	\N	t	2025-11-18 15:27:59.579415
13	328980170	Юля	\N	516100114	\N	\N	\N	beginner	\N	t	2026-01-29 13:51:16.715033
14	328980170	Данк	\N	418277276	\N	\N	\N	beginner	\N	t	2026-02-02 14:39:54.542599
15	328980170	Неля	\N	1328525699	\N	\N	\N	beginner	\N	t	2026-02-08 15:10:56.162413
16	328980170	tractor	\N	\N	intermediate	\N	\N	beginner	\N	t	2026-02-09 10:09:30.740998
17	328980170	Фея	\N	6969870739	\N	\N	\N	beginner	\N	t	2026-02-12 12:31:58.169884
18	328980170	Илья	\N	643134129	\N	\N	\N	beginner	\N	t	2026-02-18 18:34:02.336719
\.


--
-- Data for Name: one_rep_max; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.one_rep_max (id, user_id, exercise_id, weight, reps, test_weight, weight_type, formula_brzycki, formula_epley, formula_alternative, formula_average, calculation_method, tested_at, notes, is_active) FROM stdin;
1	1	5	99.50	6	85.00	external_weight	98.70	102.00	97.70	99.50	average	2025-10-05 15:58:21.162031	\N	t
2	1	3	121.90	4	110.00	external_weight	120.00	124.70	121.00	121.90	average	2025-10-05 16:24:07.42924	\N	t
3	1	9	152.80	11	111.00	external_weight	153.70	151.70	153.10	152.80	average	2025-10-10 17:51:11.691184	\N	t
4	1	19	21.20	22	10.00	external_weight	24.00	17.30	22.20	21.20	average	2025-10-13 16:27:57.146482	\N	t
5	1	25	152.80	11	111.00	external_weight	153.70	151.70	153.10	152.80	average	2025-10-13 17:13:42.000372	\N	t
6	1	10	26.70	10	20.00	external_weight	26.70	26.70	26.70	26.70	average	2025-10-13 17:35:55.976148	\N	t
7	1	3	153.30	11	111.00	external_weight	153.70	151.70	154.30	153.30	average	2025-10-13 22:49:17.156057	\N	t
8	1	2	106.90	10	80.00	external_weight	106.70	106.70	107.30	106.90	average	2025-11-25 15:39:44.732875	\N	t
26	1	19	91.10	5	80.00	external_weight	90.00	93.30	90.00	91.10	average	2025-12-11 17:01:58.566185	\N	t
27	1	6	91.10	5	80.00	external_weight	90.00	93.30	90.00	91.10	average	2025-12-11 17:19:28.204722	\N	t
28	1	11	78.30	10	60.00	external_weight	80.00	80.00	75.00	78.30	average	2025-12-11 17:19:40.204667	\N	t
29	1	19	78.30	10	60.00	external_weight	80.00	80.00	75.00	78.30	average	2025-12-11 17:45:01.09008	\N	t
30	1	25	78.30	10	60.00	external_weight	80.00	80.00	75.00	78.30	average	2025-12-11 17:57:35.438083	\N	t
31	1	29	91.10	5	80.00	external_weight	90.00	93.30	90.00	91.10	average	2025-12-12 20:09:33.098195	\N	t
\.


--
-- Data for Name: players; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.players (id, team_id, name, "position", telegram_user_id, added_at, added_by) FROM stdin;
\.


--
-- Data for Name: students; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.students (id, team_id, name, "position", telegram_user_id, added_at, added_by) FROM stdin;
\.


--
-- Data for Name: team_announcements; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.team_announcements (id, team_id, author_id, title, content, is_important, is_pinned, expires_at, created_at) FROM stdin;
\.


--
-- Data for Name: team_members; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.team_members (id, team_id, user_id, role, joined_at, left_at, is_active, member_notes) FROM stdin;
\.


--
-- Data for Name: team_players; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.team_players (id, team_id, first_name, last_name, "position", jersey_number, telegram_id, phone, birth_date, is_active, joined_at) FROM stdin;
1	2	Юля	Панчина	центр	13	\N	\N	\N	t	2025-10-17 16:45:21.382353
2	4	педи антена	антена	чурка	11	\N	\N	\N	t	2025-10-17 17:42:16.484282
3	\N	User 516100114	\N	\N	\N	516100114	\N	\N	t	2025-11-18 15:27:24.239301
4	\N	User 516100114	\N	\N	\N	516100114	\N	\N	t	2025-11-18 15:36:39.998705
5	4	User 516100114	\N	\N	\N	516100114	\N	\N	t	2025-11-18 18:37:14.873327
6	\N	User 516100114	\N	\N	\N	516100114	\N	\N	t	2025-11-18 20:53:27.655465
7	\N	User None	\N	\N	\N	\N	\N	\N	t	2025-11-18 20:54:00.466365
8	\N	User None	\N	\N	\N	\N	\N	\N	t	2025-11-18 20:54:05.358868
9	\N	User 516100114	\N	\N	\N	516100114	\N	\N	t	2025-11-19 14:49:44.820301
10	\N	User None	\N	\N	\N	\N	\N	\N	t	2025-11-19 14:52:24.840158
11	\N	User None	\N	\N	\N	\N	\N	\N	t	2025-11-19 14:53:02.455626
12	\N	User None	\N	\N	\N	\N	\N	\N	t	2025-11-19 14:53:05.649165
13	\N	Фея	\N	\N	\N	6969870739	\N	\N	t	2025-11-19 20:28:16.073004
14	\N	User None	\N	\N	\N	\N	\N	\N	t	2025-11-19 20:29:05.112671
15	\N	User None	\N	\N	\N	\N	\N	\N	t	2025-11-19 20:37:52.633256
16	\N	User None	\N	\N	\N	\N	\N	\N	t	2025-11-19 20:37:59.746564
17	\N	Фея	\N	\N	\N	6969870739	\N	\N	t	2025-11-19 20:38:20.24941
18	\N	User None	\N	\N	\N	\N	\N	\N	t	2025-11-19 20:46:52.775153
19	\N	Фея	\N	\N	\N	6969870739	\N	\N	t	2025-11-19 20:47:27.518028
20	\N	User None	\N	\N	\N	\N	\N	\N	t	2025-11-19 20:48:03.173134
21	\N	Фея	\N	\N	\N	6969870739	\N	\N	t	2025-11-19 20:48:26.014407
22	\N	User None	\N	\N	\N	\N	\N	\N	t	2025-11-19 20:48:31.3291
23	\N	User None	\N	\N	\N	\N	\N	\N	t	2025-11-19 20:48:56.381039
24	\N	User None	\N	\N	\N	\N	\N	\N	t	2025-11-20 16:06:23.095846
25	\N	User None	\N	\N	\N	\N	\N	\N	t	2025-11-20 16:19:28.964537
26	\N	User None	\N	\N	\N	\N	\N	\N	t	2025-11-20 16:25:31.963647
27	\N	User None	\N	\N	\N	\N	\N	\N	t	2025-11-20 16:33:19.601543
28	\N	Фея	\N	\N	\N	6969870739	\N	\N	t	2025-11-20 16:33:47.68015
29	4	Фея	\N	\N	\N	6969870739	\N	\N	t	2025-12-04 20:09:42.038041
30	5	Юля	\N	\N	\N	516100114	\N	\N	t	2026-01-27 11:01:34.615918
\.


--
-- Data for Name: team_stats_visibility; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.team_stats_visibility (id, team_id, stat_type, is_public, updated_by, updated_at) FROM stdin;
\.


--
-- Data for Name: teams; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.teams (id, name, description, coach_telegram_id, sport_type, max_players, created_at, updated_at, access_code) FROM stdin;
1	12123	пидорки	328980170	ОФП	25	2025-10-17 16:43:19.093973	2025-10-17 16:43:19.093973	4261a2b0
2	сосиски	тагильские	328980170	плавание	25	2025-10-17 16:44:48.012952	2025-10-17 16:44:48.012952	18e6e530
3	сосухи	крысы	328980170	ОФП	25	2025-10-17 17:32:18.496653	2025-10-17 17:32:18.496653	52c2f131
4	суууси		328980170	ОФП	25	2025-10-17 17:37:25.86434	2025-10-17 17:37:25.86434	6cb5054b
5	тестеры		328980170	ОФП	25	2026-01-27 11:00:02.495645	2026-01-27 11:00:02.495645	\N
\.


--
-- Data for Name: test_batteries; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.test_batteries (id, name, description, created_by, is_active, created_at, updated_at) FROM stdin;
1	Общая физическая подготовка	Базовая диагностика всех систем организма	1	t	2025-10-06 23:12:01.668287	2025-10-06 23:12:01.668287
2	Силовая диагностика	Оценка силовых показателей основных групп мышц	1	t	2025-10-06 23:12:01.668287	2025-10-06 23:12:01.668287
3	Кардио-диагностика	Оценка выносливости и кардио-системы	1	t	2025-10-06 23:12:01.668287	2025-10-06 23:12:01.668287
\.


--
-- Data for Name: test_battery_exercises; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.test_battery_exercises (id, battery_id, exercise_id, order_position, added_at) FROM stdin;
\.


--
-- Data for Name: test_battery_participants; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.test_battery_participants (id, battery_id, user_id, assigned_at) FROM stdin;
\.


--
-- Data for Name: test_battery_results; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.test_battery_results (id, participant_id, exercise_id, battery_id, test_type, result_value, result_unit, test_weight, test_reps, distance, time_seconds, duration_seconds, max_reps, tested_at) FROM stdin;
\.


--
-- Data for Name: test_set_exercises; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.test_set_exercises (id, test_set_id, exercise_id, added_at) FROM stdin;
2	12	32	2025-10-07 20:23:46.774376
3	13	19	2025-10-08 19:40:55.053795
4	13	11	2025-10-08 19:41:19.87752
\.


--
-- Data for Name: test_set_participants; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.test_set_participants (id, test_set_id, user_id, joined_at) FROM stdin;
\.


--
-- Data for Name: test_set_results; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.test_set_results (id, test_set_id, participant_id, exercise_id, result_value, result_unit, test_type, test_weight, test_reps, distance, time_seconds, duration_seconds, max_reps, attempt_number, is_passed, notes, tested_at) FROM stdin;
\.


--
-- Data for Name: test_sets; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.test_sets (id, name, description, created_by, visibility, access_code, is_active, created_at, updated_at) FROM stdin;
1	Общая физическая подготовка	Базовая диагностика всех систем организма	1	private	A7359128	t	2025-10-06 23:56:11.318894	2025-10-06 23:56:11.318894
2	Силовая диагностика	Оценка силовых показателей основных групп мышц	1	private	12735CB0	t	2025-10-06 23:56:11.318894	2025-10-06 23:56:11.318894
3	тест	тест	1	private	6F23EF7A	t	2025-10-06 23:56:20.708136	2025-10-06 23:56:20.708136
4	тест	тест 1	1	private	A544BD1D	t	2025-10-07 19:21:13.827362	2025-10-07 19:21:13.827362
5	тест2	222	1	private	E65C889B	t	2025-10-07 19:22:04.616739	2025-10-07 19:22:04.616739
6	тест3	тест3	1	public	CB666E2D	t	2025-10-07 19:23:04.128711	2025-10-07 19:23:04.128711
7	тест отбор	тесттесттес	1	private	9765BBDE	t	2025-10-07 19:26:16.198161	2025-10-07 19:26:16.198161
8	тест 1	просто тест ебучий	1	private	9376401F	t	2025-10-07 19:58:42.693836	2025-10-07 19:58:42.693836
9	ntcncncnc	gfgfg	1	private	0D0A423D	t	2025-10-07 20:03:55.654135	2025-10-07 20:03:55.654135
10	ffff	dfdf	1	private	3A1B73B1	t	2025-10-07 20:05:01.680742	2025-10-07 20:05:01.680742
11	333	33	1	private	1907C895	t	2025-10-07 20:06:38.981487	2025-10-07 20:06:38.981487
12	мммм	мм	1	private	CD73184C	t	2025-10-07 20:11:10.675468	2025-10-07 20:11:10.675468
13	тееессст	теесссст	1	private	4D9CF1A3	t	2025-10-08 19:40:41.667499	2025-10-08 19:40:41.667499
\.


--
-- Data for Name: user_endurance_records; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.user_endurance_records (id, user_id, exercise_id, result_seconds, model_a, model_b, model_c, average, created_at) FROM stdin;
\.


--
-- Data for Name: user_speed_records; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.user_speed_records (id, user_id, exercise_id, result_seconds, model_a, model_b, model_c, average, created_at) FROM stdin;
1	1	29	8.50	8.07	7.65	7.22	7.65	2025-12-14 11:12:27.30818+00
2	1	28	15.00	14.25	13.50	12.75	13.50	2025-12-14 11:12:54.96733+00
3	1	28	14.00	13.30	12.60	11.90	12.60	2025-12-14 12:45:28.539139+00
4	1	28	13.00	12.35	11.70	11.05	11.70	2025-12-14 12:47:07.155459+00
5	1	28	15.00	14.25	13.50	12.75	13.50	2025-12-14 13:13:59.418391+00
6	1	28	16.00	15.20	14.40	13.60	14.40	2025-12-14 14:15:56.121643+00
7	1	28	15.00	14.25	13.50	12.75	13.50	2025-12-14 14:23:32.106404+00
8	1	28	11.00	10.45	9.90	9.35	9.90	2025-12-14 14:32:17.964749+00
9	1	28	8.50	8.07	7.65	7.22	7.65	2025-12-17 11:38:29.077043+00
10	1	28	8.50	8.07	7.65	7.22	7.65	2025-12-17 12:26:51.861851+00
11	1	29	8.50	8.07	7.65	7.22	7.65	2025-12-17 12:28:49.160504+00
12	1	29	8.50	8.07	7.65	7.22	7.65	2025-12-17 12:29:20.498852+00
13	1	29	8.50	8.07	7.65	7.22	7.65	2025-12-17 12:33:09.885424+00
14	1	28	8.50	8.07	7.65	7.22	7.65	2025-12-17 12:34:07.739202+00
15	1	28	8.50	8.07	7.65	7.22	7.65	2025-12-17 12:47:19.318083+00
16	1	28	8.50	8.07	7.65	7.22	7.65	2025-12-17 12:59:13.463866+00
17	1	28	8.40	7.98	7.56	7.14	7.56	2025-12-17 13:07:06.040027+00
18	1	28	8.50	8.07	7.65	7.22	7.65	2025-12-17 13:08:15.956009+00
\.


--
-- Data for Name: user_tests; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.user_tests (id, user_id, exercise_id, test_type, result_value, result_unit, test_weight, test_reps, distance, time_seconds, duration_seconds, max_reps, notes, conditions, tested_at, created_at) FROM stdin;
1	1	5	strength	99.50	kg	85.00	6	\N	\N	\N	\N	\N	\N	2025-10-05 15:58:21.162031	2025-10-05 21:55:13.095754
2	1	3	strength	121.90	kg	110.00	4	\N	\N	\N	\N	\N	\N	2025-10-05 16:24:07.42924	2025-10-05 21:55:13.095754
3	1	11	endurance	90.00	сек	\N	\N	\N	90.000	90	\N	\N	\N	2025-11-25 16:08:46.219298	2025-11-25 16:08:46.219298
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (id, telegram_id, first_name, last_name, username, role, created_at, body_weight, age, gender, experience_level, updated_at, is_active) FROM stdin;
1	328980170	Tancy	\N	tancyv	admin	2025-09-28 21:54:04.717275	70.00	\N	\N	beginner	2025-10-01 20:33:15.361312	t
6	516100114	Юля	\N	juliahujulia	player	2025-11-19 15:39:17.661983	70.00	\N	\N	beginner	2025-11-19 15:39:17.661983	t
7	418277276	Дима	Кокшаров	c1ooown	player	2026-02-02 14:59:47.295558	70.00	\N	\N	beginner	2026-02-02 14:59:47.295558	t
8	6969870739	Фея	\N	\N	player	2026-02-12 12:28:58.801964	70.00	\N	\N	beginner	2026-02-12 12:28:58.801964	t
9	1328525699	🤨🙂😍	\N	nelicbk	player	2026-02-12 16:48:12.939777	70.00	\N	\N	beginner	2026-02-12 16:48:12.939777	t
10	643134129	Илья	\N	AllYWin	player	2026-02-18 18:29:35.369675	70.00	\N	\N	beginner	2026-02-18 18:29:35.369675	t
\.


--
-- Data for Name: workout_block_exercises; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.workout_block_exercises (id, workout_block_id, exercise_id, exercise_order, sets, reps, weight, duration_seconds, distance, rest_seconds, rpe_target, notes, created_at) FROM stdin;
\.


--
-- Data for Name: workout_blocks; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.workout_blocks (id, workout_id, name, description, block_type, block_order, rest_between_exercises, created_at) FROM stdin;
1	12	🔥 Разминка	Общая подготовка тела к нагрузке	warmup	1	60	2025-10-10 14:56:00.722254
2	12	🔥 Разминка	Общая подготовка тела к нагрузке	warmup	2	60	2025-10-10 15:00:54.624464
3	12	🧠 Подготовка ЦНС	Активация центральной нервной системы	cns_preparation	3	60	2025-10-10 15:01:01.470865
4	12	💪 Основная часть	Целевая нагрузка тренировки	main	4	60	2025-10-10 15:01:05.090322
5	12	🧘 Заминка	Восстановление после нагрузки	cooldown	5	60	2025-10-10 15:01:06.585497
\.


--
-- Data for Name: workout_exercises; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.workout_exercises (id, workout_id, exercise_id, phase, order_in_phase, sets, reps_min, reps_max, one_rm_percent, fixed_weight, rest_seconds, tempo, notes, created_at, test_percent, target_value, target_unit) FROM stdin;
1	1	1	main	1	4	6	8	80.00	\N	120	\N	\N	2025-10-05 15:45:11.401828	\N	\N	\N
2	1	2	main	2	4	6	8	80.00	\N	120	\N	\N	2025-10-05 15:45:11.401828	\N	\N	\N
3	1	3	main	3	4	6	8	80.00	\N	120	\N	\N	2025-10-05 15:45:11.401828	\N	\N	\N
4	1	9	main	4	4	6	8	80.00	\N	120	\N	\N	2025-10-05 15:45:11.401828	\N	\N	\N
5	2	6	main	1	3	10	15	\N	\N	60	\N	\N	2025-10-05 15:45:11.401828	\N	\N	\N
6	2	8	main	2	3	10	15	\N	\N	60	\N	\N	2025-10-05 15:45:11.401828	\N	\N	\N
7	2	11	main	3	3	10	15	\N	\N	60	\N	\N	2025-10-05 15:45:11.401828	\N	\N	\N
8	2	15	main	4	3	10	15	\N	\N	60	\N	\N	2025-10-05 15:45:11.401828	\N	\N	\N
9	3	11	main	1	4	8	12	\N	\N	60	\N	\N	2025-10-05 15:45:11.401828	\N	\N	\N
10	3	12	main	2	4	8	12	\N	\N	60	\N	\N	2025-10-05 15:45:11.401828	\N	\N	\N
11	3	13	main	3	4	8	12	\N	\N	60	\N	\N	2025-10-05 15:45:11.401828	\N	\N	\N
12	3	14	main	4	4	8	12	\N	\N	60	\N	\N	2025-10-05 15:45:11.401828	\N	\N	\N
13	4	6	main	1	3	10	15	\N	\N	45	\N	\N	2025-10-05 15:45:11.401828	\N	\N	\N
14	4	11	main	2	3	10	15	\N	\N	45	\N	\N	2025-10-05 15:45:11.401828	\N	\N	\N
15	4	13	main	3	3	10	15	\N	\N	45	\N	\N	2025-10-05 15:45:11.401828	\N	\N	\N
16	4	14	main	4	3	10	15	\N	\N	45	\N	\N	2025-10-05 15:45:11.401828	\N	\N	\N
17	6	3	main	1	4	4	6	85.00	\N	90	\N	\N	2025-10-05 16:38:58.149847	\N	\N	\N
18	6	5	main	2	4	4	4	85.00	\N	90	\N	\N	2025-10-05 16:38:58.150891	\N	\N	\N
19	7	11	main	1	1	1	1	\N	\N	90	\N	\N	2025-10-05 17:03:45.747579	\N	\N	\N
20	8	11	warmup	1	3	3	3	\N	\N	90	\N	\N	2025-10-05 17:18:05.123897	\N	\N	\N
21	8	16	nervous_prep	2	3	3	3	\N	\N	90	\N	\N	2025-10-05 17:18:05.124865	\N	\N	\N
22	13	19	warmup	1	3	8	12	\N	\N	60	\N	\N	2025-10-10 15:28:41.01971	\N	\N	\N
23	13	21	warmup	2	3	8	12	\N	\N	60	\N	\N	2025-10-10 15:28:41.023322	\N	\N	\N
24	13	9	main	3	3	8	12	\N	\N	60	\N	\N	2025-10-10 15:28:41.02377	\N	\N	\N
25	14	9	warmup	1	3	10	10	75.00	\N	90	\N	\N	2025-11-06 16:54:32.992365	\N	\N	\N
26	15	9	main	1	3	10	10	75.00	\N	90	\N	\N	2025-11-06 17:05:31.330297	\N	\N	\N
27	16	25	warmup	1	3	10	10	75.00	\N	90	\N	\N	2025-11-06 21:47:54.69551	\N	\N	\N
28	17	23	warmup	1	1	10	10	75.00	\N	120	\N	\N	2025-11-07 16:39:56.771107	\N	\N	\N
29	18	23	warmup	1	3	10	10	75.00	\N	90	\N	\N	2025-11-14 16:43:41.091321	\N	\N	\N
30	19	25	main	1	3	10	10	75.00	\N	90	\N	\N	2025-11-16 17:45:35.430431	\N	\N	\N
31	20	13	warmup	1	3	10	10	75.00	\N	90	\N	\N	2025-11-19 15:42:15.403197	\N	\N	\N
32	21	23	warmup	1	3	10	10	75.00	\N	90	\N	\N	2025-11-19 15:54:38.391869	\N	\N	\N
33	22	32	main	1	3	10	10	75.00	\N	90	\N	\N	2025-12-08 16:12:05.101836	\N	\N	\N
34	23	1	main	1	3	10	10	75.00	\N	90	\N	\N	2025-12-08 16:30:06.955137	\N	\N	\N
35	23	21	main	2	3	10	10	75.00	\N	90	\N	\N	2025-12-08 16:30:06.956269	\N	\N	\N
36	24	23	main	1	3	10	10	75.00	\N	90	\N	\N	2025-12-08 17:07:13.227626	\N	\N	\N
37	25	23	main	1	3	10	10	75.00	\N	90	\N	\N	2025-12-08 17:28:58.07702	\N	\N	\N
38	26	25	main	1	3	10	10	75.00	\N	90	\N	\N	2025-12-09 16:48:12.409234	\N	\N	\N
39	27	25	main	1	3	10	10	75.00	\N	90	\N	\N	2025-12-09 18:35:42.938546	\N	\N	\N
40	28	9	main	1	3	10	10	75.00	\N	90	\N	\N	2025-12-09 19:26:45.935466	\N	\N	\N
41	29	14	main	1	3	10	10	75.00	\N	90	\N	\N	2025-12-09 19:35:27.579137	\N	\N	\N
42	30	23	main	1	3	10	10	75.00	\N	90	\N	\N	2025-12-09 20:45:09.127521	\N	\N	\N
43	31	23	main	1	3	10	10	75.00	\N	90	\N	\N	2025-12-09 21:12:20.927386	\N	\N	\N
44	32	23	main	1	3	10	10	75.00	\N	90	\N	\N	2025-12-10 15:56:08.387427	\N	\N	\N
46	36	18	warmup	1	3	10	10	75.00	\N	90	\N	\N	2025-12-10 16:34:33.043933	\N	\N	\N
47	36	16	main	2	3	10	10	75.00	\N	90	\N	\N	2025-12-10 16:34:33.045021	\N	\N	\N
49	37	18	warmup	1	3	10	10	75.00	\N	90	\N	\N	2025-12-10 16:36:29.693648	\N	\N	\N
50	37	16	main	2	3	10	10	75.00	\N	90	\N	\N	2025-12-10 16:36:29.69436	\N	\N	\N
51	37	\N	main	3	0	0	0	\N	\N	0	\N	Жим лёжа 4×8-10, 75%, отдых 2 мин\n• Бёрпи 3 круга по 20 сек\n• Растяжка спины — 3 минуты	2025-12-10 16:36:29.694794	\N	\N	\N
52	38	\N	warmup	1	0	0	0	\N	\N	0	\N	Разминка флоу	2025-12-11 17:55:52.655319	\N	\N	\N
53	38	25	main	2	3	10	10	75.00	\N	90	\N	\N	2025-12-11 17:55:52.656925	\N	\N	\N
54	38	9	main	3	3	10	10	75.00	\N	90	\N	\N	2025-12-11 17:55:52.657463	\N	\N	\N
55	38	4	main	4	3	10	10	75.00	\N	90	\N	\N	2025-12-11 17:55:52.657876	\N	\N	\N
56	38	12	nervousprep	5	3	10	10	75.00	\N	90	\N	\N	2025-12-11 17:55:52.65841	\N	\N	\N
57	38	16	cooldown	6	3	10	10	75.00	\N	90	\N	\N	2025-12-11 17:55:52.658842	\N	\N	\N
58	39	29	warmup	1	3	1	1	\N	\N	22	\N	\N	2025-12-12 20:08:53.40921	\N	\N	\N
59	40	29	warmup	1	3	15	15	\N	\N	60	\N	\N	2025-12-12 21:32:35.956303	\N	\N	\N
60	41	29	warmup	1	2	1	1	\N	\N	120	\N	\N	2025-12-14 15:35:49.301899	\N	\N	\N
61	41	28	main	2	2	1	1	\N	\N	120	\N	\N	2025-12-14 15:35:49.305259	\N	\N	\N
62	42	28	warmup	1	3	1	1	\N	\N	60	\N	\N	2025-12-14 17:44:53.696377	\N	\N	\N
63	44	28	warmup	1	3	1	1	\N	\N	60	\N	\N	2025-12-14 19:23:13.395786	\N	\N	\N
64	44	29	main	2	3	1	1	\N	\N	60	\N	\N	2025-12-14 19:23:13.396914	\N	\N	\N
65	45	29	warmup	1	3	1	1	90.00	\N	60	\N	\N	2025-12-17 17:28:25.649064	\N	\N	\N
66	45	29	main	2	3	1	1	90.00	\N	60	\N	\N	2025-12-17 17:28:25.65136	\N	\N	\N
67	46	28	warmup	1	3	1	1	90.00	\N	60	\N	\N	2025-12-17 17:33:45.837517	\N	\N	\N
68	47	\N	warmup	1	0	0	0	\N	\N	0	\N	1) просто встаньте со стула и встряхните ноги и руки 30 секунд\n2)  поверните шею очень медленно максимально влево,право, вверх, низ. 2 минуты.\n3) круговые движения плеч (руки опущены) с максимальной амплитудой 1 минуту вперед, 1 назад.\n4) свободный флекс 1-3 минуты. Делайте привычную свою разминку , похрустите пальцами , спиной и прочее.	2026-01-27 10:54:04.365141	\N	\N	\N
69	47	\N	nervousprep	2	0	0	0	\N	\N	0	\N	бесшумный бег на месте с максимальной скоростью, активно работаем руками - 15 секунд.	2026-01-27 10:54:04.406818	\N	\N	\N
70	47	35	main	3	3	10	10	1.00	\N	60	\N	\N	2026-01-27 10:54:04.41519	\N	\N	\N
71	47	36	main	4	3	10	10	1.00	\N	30	\N	\N	2026-01-27 10:54:04.423508	\N	\N	\N
72	47	37	main	5	3	5	5	1.00	\N	5	\N	\N	2026-01-27 10:54:04.43184	\N	\N	\N
73	47	39	main	6	3	10	10	1.00	\N	20	\N	\N	2026-01-27 10:54:04.440183	\N	\N	\N
74	47	38	main	7	3	15	15	1.00	\N	40	\N	\N	2026-01-27 10:54:04.4485	\N	\N	\N
75	47	30	main	8	3	1	1	100.00	\N	15	\N	\N	2026-01-27 10:54:04.45688	\N	\N	\N
76	47	\N	cooldown	9	0	0	0	\N	\N	0	\N	встать на одну ногу и закрыть глаза, медленно поворачивать голову влево право удерживая баланс. По 1 минуте на одну ногу.	2026-01-27 10:54:04.465166	\N	\N	\N
77	48	43	warmup	1	1	1	1	110.00	\N	60	\N	\N	2026-01-29 16:22:16.802518	\N	\N	\N
78	48	\N	main	2	0	0	0	\N	\N	0	\N	тесттесттесттесттесттесттесттест	2026-01-29 16:22:16.844091	\N	\N	\N
\.


--
-- Data for Name: workout_individual_students; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.workout_individual_students (id, workout_id, student_id, assigned_by, assigned_at, deadline, notes, is_active, status, started_at, completed_at, rpe, archived_at) FROM stdin;
16	47	11	328980170	2026-01-29 13:48:21.767147	\N	\N	t	pending	\N	\N	\N	\N
18	47	13	328980170	2026-01-29 13:51:30.802467	\N	\N	f	archived	2026-02-02 14:18:38.058604	2026-02-02 14:19:05.938352	1	2026-02-02 14:19:05.938352
21	47	14	328980170	2026-02-04 16:08:40.9564	\N	\N	t	pending	\N	\N	\N	\N
22	47	15	328980170	2026-02-08 15:12:27.256977	\N	\N	t	pending	\N	\N	\N	\N
23	47	17	328980170	2026-02-12 12:32:16.650036	\N	\N	t	in_progress	2026-02-12 12:32:25.694583	\N	\N	\N
24	47	18	328980170	2026-02-18 18:34:38.657108	\N	\N	t	pending	\N	\N	\N	\N
\.


--
-- Data for Name: workout_session_exercises; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.workout_session_exercises (id, session_id, workout_exercise_id, exercise_id, sets_completed, sets_total, status, started_at, completed_at, exercise_rpe, notes) FROM stdin;
1	15	37	23	3	3	completed	\N	2025-12-08 17:33:11.734888	\N	\N
3	37	76	\N	0	0	pending	\N	\N	\N	\N
10	37	69	\N	0	0	pending	\N	\N	\N	\N
11	37	68	\N	0	0	pending	\N	\N	\N	\N
4	37	70	35	3	3	completed	\N	2026-01-27 11:16:41.215348	\N	\N
5	37	71	36	3	3	completed	\N	2026-01-27 11:23:06.99491	\N	\N
6	37	72	37	3	3	completed	\N	2026-01-27 11:27:17.706677	\N	\N
7	37	73	39	3	3	completed	\N	2026-01-27 11:31:59.056335	\N	\N
8	37	74	38	3	3	completed	\N	2026-01-27 11:42:33.876655	\N	\N
12	39	21	16	0	3	pending	\N	\N	\N	\N
13	39	20	11	3	3	completed	\N	2026-01-29 13:47:07.213423	\N	\N
9	37	75	30	3	3	completed	\N	2026-02-02 12:32:34.09511	\N	\N
24	44	76	\N	0	0	pending	\N	\N	\N	\N
31	44	69	\N	0	0	pending	\N	\N	\N	\N
32	44	68	\N	0	0	pending	\N	\N	\N	\N
25	44	70	35	3	3	completed	\N	2026-02-03 13:36:37.274673	\N	\N
26	44	71	36	3	3	completed	\N	2026-02-03 13:39:48.496347	\N	\N
27	44	72	37	3	3	completed	\N	2026-02-03 13:57:55.148462	\N	\N
28	44	73	39	3	3	completed	\N	2026-02-03 14:36:51.356838	\N	\N
29	44	74	38	3	3	completed	\N	2026-02-03 15:07:35.442942	\N	\N
30	44	75	30	3	3	completed	\N	2026-02-03 15:09:53.614157	\N	\N
33	45	76	\N	0	0	pending	\N	\N	\N	\N
34	45	70	35	0	3	pending	\N	\N	\N	\N
35	45	71	36	0	3	pending	\N	\N	\N	\N
36	45	72	37	0	3	pending	\N	\N	\N	\N
37	45	73	39	0	3	pending	\N	\N	\N	\N
38	45	74	38	0	3	pending	\N	\N	\N	\N
39	45	75	30	0	3	pending	\N	\N	\N	\N
40	45	69	\N	0	0	pending	\N	\N	\N	\N
41	45	68	\N	0	0	pending	\N	\N	\N	\N
\.


--
-- Data for Name: workout_session_sets; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.workout_session_sets (id, session_exercise_id, set_number, planned_reps, actual_reps, planned_weight, actual_weight, rpe, rest_seconds, completed_at, form_notes, notes) FROM stdin;
\.


--
-- Data for Name: workout_sessions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.workout_sessions (id, user_id, workout_id, status, started_at, completed_at, paused_at, total_duration_minutes, rpe, rpe_description, notes, session_rating, created_at) FROM stdin;
1	1	13	in_progress	2025-11-25 15:23:49.735292	\N	\N	\N	\N	\N	\N	\N	2025-11-25 15:23:49.735292
2	1	13	in_progress	2025-11-25 15:24:10.928438	\N	\N	\N	\N	\N	\N	\N	2025-11-25 15:24:10.928438
3	1	19	in_progress	2025-11-27 15:14:15.207921	\N	\N	\N	\N	\N	\N	\N	2025-11-27 15:14:15.207921
4	1	18	in_progress	2025-11-27 15:51:26.862562	\N	\N	\N	\N	\N	\N	\N	2025-11-27 15:51:26.862562
5	1	20	in_progress	2025-11-27 16:58:45.162789	\N	\N	\N	\N	\N	\N	\N	2025-11-27 16:58:45.162789
6	1	14	in_progress	2025-11-27 17:03:13.431118	\N	\N	\N	\N	\N	\N	\N	2025-11-27 17:03:13.431118
8	1	4	in_progress	2025-12-01 15:08:10.9264	\N	\N	\N	\N	\N	\N	\N	2025-12-01 15:08:10.9264
9	1	4	in_progress	2025-12-01 15:08:25.231809	\N	\N	\N	\N	\N	\N	\N	2025-12-01 15:08:25.231809
12	1	22	in_progress	2025-12-08 16:12:25.099804	\N	\N	\N	\N	\N	\N	\N	2025-12-08 16:12:25.099804
13	1	23	in_progress	2025-12-08 16:30:19.314051	\N	\N	\N	\N	\N	\N	\N	2025-12-08 16:30:19.314051
14	1	24	in_progress	2025-12-08 17:07:26.160481	\N	\N	\N	\N	\N	\N	\N	2025-12-08 17:07:26.160481
15	1	25	in_progress	2025-12-08 17:29:05.518994	\N	\N	\N	\N	\N	\N	\N	2025-12-08 17:29:05.518994
16	1	25	in_progress	2025-12-08 17:33:34.153238	\N	\N	\N	\N	\N	\N	\N	2025-12-08 17:33:34.153238
17	1	26	in_progress	2025-12-09 16:48:27.159792	\N	\N	\N	\N	\N	\N	\N	2025-12-09 16:48:27.159792
18	1	28	in_progress	2025-12-09 19:27:02.289358	\N	\N	\N	\N	\N	\N	\N	2025-12-09 19:27:02.289358
19	1	29	in_progress	2025-12-09 19:35:41.753505	\N	\N	\N	\N	\N	\N	\N	2025-12-09 19:35:41.753505
20	1	31	in_progress	2025-12-09 21:12:37.108571	\N	\N	\N	\N	\N	\N	\N	2025-12-09 21:12:37.108571
21	1	30	in_progress	2025-12-10 15:39:36.138544	\N	\N	\N	\N	\N	\N	\N	2025-12-10 15:39:36.138544
22	1	32	in_progress	2025-12-10 15:56:22.094893	\N	\N	\N	\N	\N	\N	\N	2025-12-10 15:56:22.094893
24	1	37	in_progress	2025-12-10 16:36:53.891707	\N	\N	\N	\N	\N	\N	\N	2025-12-10 16:36:53.891707
25	1	36	in_progress	2025-12-11 17:05:07.699319	\N	\N	\N	\N	\N	\N	\N	2025-12-11 17:05:07.699319
26	1	4	in_progress	2025-12-11 17:19:56.844226	\N	\N	\N	\N	\N	\N	\N	2025-12-11 17:19:56.844226
27	1	3	in_progress	2025-12-11 17:30:37.26731	\N	\N	\N	\N	\N	\N	\N	2025-12-11 17:30:37.26731
28	1	38	in_progress	2025-12-11 17:56:58.441488	\N	\N	\N	\N	\N	\N	\N	2025-12-11 17:56:58.441488
29	1	38	in_progress	2025-12-11 17:58:20.771465	\N	\N	\N	\N	\N	\N	\N	2025-12-11 17:58:20.771465
30	1	39	in_progress	2025-12-12 20:09:05.410914	\N	\N	\N	\N	\N	\N	\N	2025-12-12 20:09:05.410914
31	1	40	in_progress	2025-12-12 21:32:46.931999	\N	\N	\N	\N	\N	\N	\N	2025-12-12 21:32:46.931999
32	1	41	in_progress	2025-12-14 15:36:10.156357	\N	\N	\N	\N	\N	\N	\N	2025-12-14 15:36:10.156357
33	1	42	in_progress	2025-12-14 17:45:06.644604	\N	\N	\N	\N	\N	\N	\N	2025-12-14 17:45:06.644604
34	1	44	in_progress	2025-12-14 19:23:23.753967	\N	\N	\N	\N	\N	\N	\N	2025-12-14 19:23:23.753967
35	1	45	in_progress	2025-12-17 17:28:37.675443	\N	\N	\N	\N	\N	\N	\N	2025-12-17 17:28:37.675443
36	1	46	in_progress	2025-12-17 17:33:55.963978	\N	\N	\N	\N	\N	\N	\N	2025-12-17 17:33:55.963978
38	1	47	in_progress	2026-01-27 11:47:46.571713	\N	\N	\N	\N	\N	\N	\N	2026-01-27 11:47:46.571713
39	6	8	in_progress	2026-01-29 13:46:54.644638	\N	\N	\N	\N	\N	\N	\N	2026-01-29 13:46:54.644638
41	1	48	in_progress	2026-01-29 16:22:26.166862	\N	\N	\N	\N	\N	\N	\N	2026-01-29 16:22:26.166862
37	6	47	completed	2026-01-27 11:02:12.491392	2026-02-02 14:19:05.914288	\N	\N	1	\N	\N	\N	2026-01-27 11:02:12.491392
44	7	47	completed	2026-02-02 15:29:07.681801	2026-02-03 17:44:03.607224	\N	\N	10	\N	\N	\N	2026-02-02 15:29:07.681801
45	8	47	in_progress	2026-02-12 12:32:25.718319	\N	\N	\N	\N	\N	\N	\N	2026-02-12 12:32:25.718319
\.


--
-- Data for Name: workout_team_player_assignments; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.workout_team_player_assignments (id, workout_team_id, team_player_id, status, started_at, completed_at, session_id, rpe, notes) FROM stdin;
1	2	2	pending	\N	\N	\N	\N	\N
2	2	5	pending	\N	\N	\N	\N	\N
3	2	29	in_progress	2025-12-05 15:48:41.540285	\N	\N	\N	\N
4	3	2	pending	\N	\N	\N	\N	\N
6	3	29	pending	\N	\N	\N	\N	\N
7	4	30	completed	2026-01-27 11:02:12.410011	2026-01-27 11:45:30.978141	\N	6.0	\N
5	3	5	completed	2026-01-29 13:46:54.593784	2026-01-29 13:47:17.631322	\N	1.0	\N
\.


--
-- Data for Name: workout_teams; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.workout_teams (id, workout_id, team_id, assigned_at, assigned_by, deadline, notes, is_active) FROM stdin;
2	19	4	2025-12-04 22:00:40.392382	1	\N	\N	t
3	8	4	2025-12-05 17:13:17.452774	1	\N	\N	t
4	47	5	2026-01-27 11:01:50.117892	1	\N	\N	t
\.


--
-- Data for Name: workouts; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.workouts (id, unique_id, name, description, created_by, assigned_to, visibility, is_template, difficulty_level, estimated_duration_minutes, tags, created_at, updated_at, is_active) FROM stdin;
8	WKT-FSY206	Сосис		1	\N	private	f	intermediate	16	\N	2025-10-05 17:18:05.120691	2025-11-16 18:21:56.864427	t
12	WKT-TQK583	ввавав	вавв	1	\N	private	f	beginner	\N	\N	2025-10-10 14:56:00.703467	2025-11-16 18:21:56.864427	f
6	WKT-PRT483	Тест	Тест	1	\N	private	f	intermediate	20	\N	2025-10-05 16:38:58.146317	2025-11-16 18:21:56.864427	f
7	WKT-SPR931	Ттт	Рро	1	\N	private	f	intermediate	10	\N	2025-10-05 17:03:45.744117	2025-11-16 18:21:56.864427	f
16	WKT-YFW393	ваваавп		1	\N	private	f	beginner	\N	\N	2025-11-06 21:47:54.615985	2025-11-16 18:21:56.864427	f
9	WKT-CKI921	fffffff	fff	1	\N	private	f	beginner	\N	\N	2025-10-08 20:05:45.454638	2025-11-16 18:21:56.864427	f
15	WKT-KOZ746	fdsddfsdff		1	\N	private	f	beginner	\N	\N	2025-11-06 17:05:31.327257	2025-11-16 18:21:56.864427	f
10	WKT-XYK581	ffff	cccc	1	\N	private	f	beginner	\N	\N	2025-10-08 20:06:26.812822	2025-11-16 18:21:56.864427	f
31	WKT-EJM649	рпрпр		1	\N	private	f	beginner	\N	\N	2025-12-09 21:12:20.924407	2025-12-10 15:55:12.852339	f
1	WKT-SNJ992	Базовая силовая	Классическая программа для развития основных групп мышц	\N	\N	public	t	intermediate	60	\N	2025-10-05 15:44:42.726292	2025-12-24 11:51:18.136395	f
2	WKT-PAB284	Для начинающих	Легкая программа для новичков	\N	\N	public	t	beginner	45	\N	2025-10-05 15:44:42.726292	2025-12-24 11:51:36.881431	f
3	WKT-IZB137	Функциональная	Комплекс упражнений для функциональной силы	\N	\N	public	t	intermediate	40	\N	2025-10-05 15:44:42.726292	2025-12-24 11:52:12.645083	f
4	WKT-BWW855	Домашняя тренировка	Эффективная тренировка без оборудования	\N	\N	public	t	beginner	30	\N	2025-10-05 15:44:42.726292	2025-12-24 11:52:21.518959	f
11	WKT-FCY253	авава	вавав	1	\N	private	f	beginner	\N	\N	2025-10-08 20:07:30.530877	2025-12-24 11:52:34.133224	f
13	WKT-PXI657	33333	333333	1	\N	private	f	beginner	\N	\N	2025-10-10 15:28:41.01693	2025-12-24 11:52:42.414216	f
14	WKT-TDU151	аваывавыва		1	\N	private	f	beginner	\N	\N	2025-11-06 16:54:32.982114	2025-12-24 11:52:51.575472	f
17	WKT-BWJ290	ddfdf		1	\N	private	f	beginner	\N	\N	2025-11-07 16:39:56.757962	2025-12-24 11:53:02.652851	f
18	WKT-HJH496	fgfgfg		1	\N	private	f	beginner	\N	\N	2025-11-14 16:43:41.071823	2025-12-24 11:53:12.212394	f
19	WKT-NRH841	test123		1	\N	private	f	beginner	\N	\N	2025-11-16 17:45:35.425205	2025-12-24 11:53:24.661145	f
5	WKT-RMT984	Кардио микс	Интенсивная кардио тренировка	\N	\N	public	t	intermediate	35	\N	2025-10-05 15:44:42.726292	2025-12-24 11:53:36.376262	f
20	WKT-KOE783	тренировка юля		6	\N	private	f	beginner	\N	\N	2025-11-19 15:42:15.397698	2025-12-24 11:53:45.084963	f
22	WKT-JFC364	teststststst		1	\N	private	f	beginner	\N	\N	2025-12-08 16:12:04.967782	2025-12-24 11:53:54.907401	f
23	WKT-KGR884	vvvvvv		1	\N	private	f	beginner	\N	\N	2025-12-08 16:30:06.950875	2025-12-24 11:54:03.188174	f
24	WKT-VCE209	ccccxxxx		1	\N	private	f	beginner	\N	\N	2025-12-08 17:07:13.223571	2025-12-24 11:54:12.192688	f
46	WKT-HEE033	р7р7р7р7		1	\N	private	f	beginner	0	\N	2025-12-17 17:33:45.835183	2025-12-24 11:54:22.10601	f
45	WKT-LSV066	b8888		1	\N	private	f	beginner	0	\N	2025-12-17 17:28:25.636025	2025-12-24 11:54:30.148211	f
44	WKT-TGQ781	ттцтцтцтцт		1	\N	private	f	beginner	0	\N	2025-12-14 19:23:13.3931	2025-12-24 11:54:38.958223	f
43	WKT-ZHS465	rerrvvv		1	\N	private	f	beginner	0	\N	2025-12-14 19:16:50.988361	2025-12-24 11:54:47.25977	f
42	WKT-SMO842	333рпиим		1	\N	private	f	beginner	0	\N	2025-12-14 17:44:53.671516	2025-12-24 11:54:54.552096	f
41	WKT-LZD536	zapupa		1	\N	private	f	beginner	\N	\N	2025-12-14 15:35:49.27781	2025-12-24 11:55:01.275346	f
40	WKT-LTO142	444		1	\N	private	f	beginner	\N	\N	2025-12-12 21:32:35.953296	2025-12-24 11:55:09.856698	f
39	WKT-YIU855	-0-0-0-0-88		1	\N	private	f	beginner	\N	\N	2025-12-12 20:08:53.39992	2025-12-24 11:55:16.953436	f
38	WKT-ZRK446	тест бета3	тренировка лоххов	1	\N	private	f	beginner	\N	\N	2025-12-11 17:55:52.64413	2025-12-24 11:55:27.401459	f
37	WKT-SWI405	2131223333333		1	\N	private	f	beginner	\N	\N	2025-12-10 16:36:29.692916	2025-12-24 11:55:40.440592	f
36	WKT-XMD463	2131223333333		1	\N	private	f	beginner	\N	\N	2025-12-10 16:34:33.040989	2025-12-24 11:55:50.305137	f
35	WKT-CNQ065	231123213123		1	\N	private	f	beginner	\N	\N	2025-12-10 16:32:45.008813	2025-12-24 11:55:58.078296	f
34	WKT-UAM051	231123213123		1	\N	private	f	beginner	\N	\N	2025-12-10 16:30:37.418984	2025-12-24 11:56:09.546059	f
33	WKT-NCN843	161616		1	\N	private	f	beginner	\N	\N	2025-12-10 16:23:35.756991	2025-12-24 11:56:16.703611	f
32	WKT-NBE467	6666		1	\N	private	f	beginner	\N	\N	2025-12-10 15:56:08.383108	2025-12-24 11:56:24.211172	f
30	WKT-WGT565	777		1	\N	private	f	beginner	\N	\N	2025-12-09 20:45:09.121071	2025-12-24 11:56:32.578754	f
29	WKT-WFT013	cvcvv8888		1	\N	private	f	beginner	\N	\N	2025-12-09 19:35:27.560733	2025-12-24 11:56:40.588806	f
28	WKT-BTA523	12 09		1	\N	private	f	beginner	\N	\N	2025-12-09 19:26:45.931821	2025-12-24 11:56:47.681386	f
27	WKT-YIT881	qqqqqqqqqqqqqqwww		1	\N	private	f	beginner	\N	\N	2025-12-09 18:35:42.926999	2025-12-24 11:57:03.024059	f
26	WKT-CXO763	ииииииииииии		1	\N	private	f	beginner	\N	\N	2025-12-09 16:48:12.392776	2025-12-24 11:57:13.858476	f
25	WKT-KFW585	яяяяяя		1	\N	private	f	beginner	\N	\N	2025-12-08 17:28:58.074466	2025-12-24 11:57:22.745811	f
47	WKT-CWK638	начинающий	домашняя для старта	1	\N	private	f	beginner	0	\N	2026-01-27 10:54:04.078946	2026-01-27 10:54:04.078946	t
48	WKT-UUZ268	тест планка		1	\N	private	f	beginner	0	\N	2026-01-29 16:22:16.70776	2026-01-29 16:22:16.70776	t
21	WKT-UGL166	тест		\N	\N	private	f	beginner	\N	\N	2025-11-19 15:54:38.389334	2026-02-09 10:22:51.177294	f
\.


--
-- Name: coach_students_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.coach_students_id_seq', 4, true);


--
-- Name: exercises_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.exercises_id_seq', 117, true);


--
-- Name: individual_student_workouts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.individual_student_workouts_id_seq', 1, false);


--
-- Name: individual_students_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.individual_students_id_seq', 18, true);


--
-- Name: one_rep_max_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.one_rep_max_id_seq', 31, true);


--
-- Name: players_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.players_id_seq', 1, false);


--
-- Name: students_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.students_id_seq', 1, false);


--
-- Name: team_announcements_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.team_announcements_id_seq', 1, false);


--
-- Name: team_members_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.team_members_id_seq', 1, false);


--
-- Name: team_players_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.team_players_id_seq', 30, true);


--
-- Name: team_stats_visibility_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.team_stats_visibility_id_seq', 1, false);


--
-- Name: teams_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.teams_id_seq', 5, true);


--
-- Name: test_batteries_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.test_batteries_id_seq', 3, true);


--
-- Name: test_battery_exercises_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.test_battery_exercises_id_seq', 1, false);


--
-- Name: test_battery_participants_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.test_battery_participants_id_seq', 1, false);


--
-- Name: test_battery_results_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.test_battery_results_id_seq', 1, false);


--
-- Name: test_set_exercises_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.test_set_exercises_id_seq', 4, true);


--
-- Name: test_set_participants_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.test_set_participants_id_seq', 1, false);


--
-- Name: test_set_results_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.test_set_results_id_seq', 1, false);


--
-- Name: test_sets_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.test_sets_id_seq', 13, true);


--
-- Name: user_endurance_records_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.user_endurance_records_id_seq', 1, false);


--
-- Name: user_speed_records_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.user_speed_records_id_seq', 18, true);


--
-- Name: user_tests_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.user_tests_id_seq', 3, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.users_id_seq', 10, true);


--
-- Name: workout_block_exercises_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.workout_block_exercises_id_seq', 1, false);


--
-- Name: workout_blocks_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.workout_blocks_id_seq', 5, true);


--
-- Name: workout_exercises_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.workout_exercises_id_seq', 78, true);


--
-- Name: workout_individual_students_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.workout_individual_students_id_seq', 24, true);


--
-- Name: workout_session_exercises_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.workout_session_exercises_id_seq', 41, true);


--
-- Name: workout_session_sets_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.workout_session_sets_id_seq', 1, false);


--
-- Name: workout_sessions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.workout_sessions_id_seq', 45, true);


--
-- Name: workout_team_player_assignments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.workout_team_player_assignments_id_seq', 7, true);


--
-- Name: workout_teams_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.workout_teams_id_seq', 4, true);


--
-- Name: workouts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.workouts_id_seq', 48, true);


--
-- Name: coach_students coach_students_invite_code_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.coach_students
    ADD CONSTRAINT coach_students_invite_code_key UNIQUE (invite_code);


--
-- Name: coach_students coach_students_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.coach_students
    ADD CONSTRAINT coach_students_pkey PRIMARY KEY (id);


--
-- Name: exercises exercises_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.exercises
    ADD CONSTRAINT exercises_pkey PRIMARY KEY (id);


--
-- Name: individual_student_workouts individual_student_workouts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.individual_student_workouts
    ADD CONSTRAINT individual_student_workouts_pkey PRIMARY KEY (id);


--
-- Name: individual_student_workouts individual_student_workouts_workout_id_student_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.individual_student_workouts
    ADD CONSTRAINT individual_student_workouts_workout_id_student_id_key UNIQUE (workout_id, student_id);


--
-- Name: individual_students individual_students_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.individual_students
    ADD CONSTRAINT individual_students_pkey PRIMARY KEY (id);


--
-- Name: one_rep_max one_rep_max_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.one_rep_max
    ADD CONSTRAINT one_rep_max_pkey PRIMARY KEY (id);


--
-- Name: one_rep_max one_rep_max_user_id_exercise_id_tested_at_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.one_rep_max
    ADD CONSTRAINT one_rep_max_user_id_exercise_id_tested_at_key UNIQUE (user_id, exercise_id, tested_at);


--
-- Name: players players_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.players
    ADD CONSTRAINT players_pkey PRIMARY KEY (id);


--
-- Name: students students_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.students
    ADD CONSTRAINT students_pkey PRIMARY KEY (id);


--
-- Name: team_announcements team_announcements_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.team_announcements
    ADD CONSTRAINT team_announcements_pkey PRIMARY KEY (id);


--
-- Name: team_members team_members_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.team_members
    ADD CONSTRAINT team_members_pkey PRIMARY KEY (id);


--
-- Name: team_members team_members_team_id_user_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.team_members
    ADD CONSTRAINT team_members_team_id_user_id_key UNIQUE (team_id, user_id);


--
-- Name: team_players team_players_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.team_players
    ADD CONSTRAINT team_players_pkey PRIMARY KEY (id);


--
-- Name: team_stats_visibility team_stats_visibility_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.team_stats_visibility
    ADD CONSTRAINT team_stats_visibility_pkey PRIMARY KEY (id);


--
-- Name: team_stats_visibility team_stats_visibility_team_id_stat_type_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.team_stats_visibility
    ADD CONSTRAINT team_stats_visibility_team_id_stat_type_key UNIQUE (team_id, stat_type);


--
-- Name: teams teams_access_code_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.teams
    ADD CONSTRAINT teams_access_code_key UNIQUE (access_code);


--
-- Name: teams teams_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.teams
    ADD CONSTRAINT teams_pkey PRIMARY KEY (id);


--
-- Name: test_batteries test_batteries_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.test_batteries
    ADD CONSTRAINT test_batteries_pkey PRIMARY KEY (id);


--
-- Name: test_battery_exercises test_battery_exercises_battery_id_exercise_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.test_battery_exercises
    ADD CONSTRAINT test_battery_exercises_battery_id_exercise_id_key UNIQUE (battery_id, exercise_id);


--
-- Name: test_battery_exercises test_battery_exercises_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.test_battery_exercises
    ADD CONSTRAINT test_battery_exercises_pkey PRIMARY KEY (id);


--
-- Name: test_battery_participants test_battery_participants_battery_id_user_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.test_battery_participants
    ADD CONSTRAINT test_battery_participants_battery_id_user_id_key UNIQUE (battery_id, user_id);


--
-- Name: test_battery_participants test_battery_participants_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.test_battery_participants
    ADD CONSTRAINT test_battery_participants_pkey PRIMARY KEY (id);


--
-- Name: test_battery_results test_battery_results_participant_id_exercise_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.test_battery_results
    ADD CONSTRAINT test_battery_results_participant_id_exercise_id_key UNIQUE (participant_id, exercise_id);


--
-- Name: test_battery_results test_battery_results_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.test_battery_results
    ADD CONSTRAINT test_battery_results_pkey PRIMARY KEY (id);


--
-- Name: test_set_exercises test_set_exercises_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.test_set_exercises
    ADD CONSTRAINT test_set_exercises_pkey PRIMARY KEY (id);


--
-- Name: test_set_participants test_set_participants_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.test_set_participants
    ADD CONSTRAINT test_set_participants_pkey PRIMARY KEY (id);


--
-- Name: test_set_results test_set_results_participant_id_exercise_id_attempt_number_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.test_set_results
    ADD CONSTRAINT test_set_results_participant_id_exercise_id_attempt_number_key UNIQUE (participant_id, exercise_id, attempt_number);


--
-- Name: test_set_results test_set_results_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.test_set_results
    ADD CONSTRAINT test_set_results_pkey PRIMARY KEY (id);


--
-- Name: test_sets test_sets_access_code_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.test_sets
    ADD CONSTRAINT test_sets_access_code_key UNIQUE (access_code);


--
-- Name: test_sets test_sets_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.test_sets
    ADD CONSTRAINT test_sets_pkey PRIMARY KEY (id);


--
-- Name: user_endurance_records user_endurance_records_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_endurance_records
    ADD CONSTRAINT user_endurance_records_pkey PRIMARY KEY (id);


--
-- Name: user_speed_records user_speed_records_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_speed_records
    ADD CONSTRAINT user_speed_records_pkey PRIMARY KEY (id);


--
-- Name: user_tests user_tests_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_tests
    ADD CONSTRAINT user_tests_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_telegram_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_telegram_id_key UNIQUE (telegram_id);


--
-- Name: users users_telegram_id_unique; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_telegram_id_unique UNIQUE (telegram_id);


--
-- Name: workout_block_exercises workout_block_exercises_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workout_block_exercises
    ADD CONSTRAINT workout_block_exercises_pkey PRIMARY KEY (id);


--
-- Name: workout_blocks workout_blocks_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workout_blocks
    ADD CONSTRAINT workout_blocks_pkey PRIMARY KEY (id);


--
-- Name: workout_exercises workout_exercises_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workout_exercises
    ADD CONSTRAINT workout_exercises_pkey PRIMARY KEY (id);


--
-- Name: workout_individual_students workout_individual_students_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workout_individual_students
    ADD CONSTRAINT workout_individual_students_pkey PRIMARY KEY (id);


--
-- Name: workout_individual_students workout_individual_students_workout_id_student_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workout_individual_students
    ADD CONSTRAINT workout_individual_students_workout_id_student_id_key UNIQUE (workout_id, student_id);


--
-- Name: workout_session_exercises workout_session_exercises_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workout_session_exercises
    ADD CONSTRAINT workout_session_exercises_pkey PRIMARY KEY (id);


--
-- Name: workout_session_sets workout_session_sets_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workout_session_sets
    ADD CONSTRAINT workout_session_sets_pkey PRIMARY KEY (id);


--
-- Name: workout_sessions workout_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workout_sessions
    ADD CONSTRAINT workout_sessions_pkey PRIMARY KEY (id);


--
-- Name: workout_team_player_assignments workout_team_player_assignmen_workout_team_id_team_player_i_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workout_team_player_assignments
    ADD CONSTRAINT workout_team_player_assignmen_workout_team_id_team_player_i_key UNIQUE (workout_team_id, team_player_id);


--
-- Name: workout_team_player_assignments workout_team_player_assignments_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workout_team_player_assignments
    ADD CONSTRAINT workout_team_player_assignments_pkey PRIMARY KEY (id);


--
-- Name: workout_teams workout_teams_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workout_teams
    ADD CONSTRAINT workout_teams_pkey PRIMARY KEY (id);


--
-- Name: workout_teams workout_teams_workout_id_team_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workout_teams
    ADD CONSTRAINT workout_teams_workout_id_team_id_key UNIQUE (workout_id, team_id);


--
-- Name: workout_teams workout_teams_workout_team_unique; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workout_teams
    ADD CONSTRAINT workout_teams_workout_team_unique UNIQUE (workout_id, team_id);


--
-- Name: workouts workouts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workouts
    ADD CONSTRAINT workouts_pkey PRIMARY KEY (id);


--
-- Name: workouts workouts_unique_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workouts
    ADD CONSTRAINT workouts_unique_id_key UNIQUE (unique_id);


--
-- Name: idx_coach_students_invite_code; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_coach_students_invite_code ON public.coach_students USING btree (invite_code);


--
-- Name: idx_coach_students_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_coach_students_status ON public.coach_students USING btree (status);


--
-- Name: idx_exercises_active; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_exercises_active ON public.exercises USING btree (is_active);


--
-- Name: idx_exercises_category; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_exercises_category ON public.exercises USING btree (category);


--
-- Name: idx_exercises_muscle_group; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_exercises_muscle_group ON public.exercises USING btree (muscle_group);


--
-- Name: idx_exercises_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_exercises_name ON public.exercises USING gin (to_tsvector('russian'::regconfig, (name)::text));


--
-- Name: idx_individual_students_coach; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_individual_students_coach ON public.individual_students USING btree (coach_telegram_id);


--
-- Name: idx_individual_students_telegram; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_individual_students_telegram ON public.individual_students USING btree (telegram_id);


--
-- Name: idx_one_rep_max_active; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_one_rep_max_active ON public.one_rep_max USING btree (is_active);


--
-- Name: idx_one_rep_max_tested_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_one_rep_max_tested_at ON public.one_rep_max USING btree (tested_at DESC);


--
-- Name: idx_one_rep_max_user_exercise; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_one_rep_max_user_exercise ON public.one_rep_max USING btree (user_id, exercise_id);


--
-- Name: idx_players_team_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_players_team_id ON public.players USING btree (team_id);


--
-- Name: idx_students_team_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_students_team_id ON public.students USING btree (team_id);


--
-- Name: idx_team_members_active; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_team_members_active ON public.team_members USING btree (is_active);


--
-- Name: idx_team_members_team_user; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_team_members_team_user ON public.team_members USING btree (team_id, user_id);


--
-- Name: idx_team_players_team; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_team_players_team ON public.team_players USING btree (team_id);


--
-- Name: idx_team_players_telegram; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_team_players_telegram ON public.team_players USING btree (telegram_id);


--
-- Name: idx_teams_coach; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_teams_coach ON public.teams USING btree (coach_telegram_id);


--
-- Name: idx_test_batteries_created_by; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_test_batteries_created_by ON public.test_batteries USING btree (created_by);


--
-- Name: idx_test_battery_exercises_battery_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_test_battery_exercises_battery_id ON public.test_battery_exercises USING btree (battery_id);


--
-- Name: idx_test_battery_participants_battery_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_test_battery_participants_battery_id ON public.test_battery_participants USING btree (battery_id);


--
-- Name: idx_test_battery_participants_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_test_battery_participants_user_id ON public.test_battery_participants USING btree (user_id);


--
-- Name: idx_test_battery_results_battery_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_test_battery_results_battery_id ON public.test_battery_results USING btree (battery_id);


--
-- Name: idx_test_battery_results_participant_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_test_battery_results_participant_id ON public.test_battery_results USING btree (participant_id);


--
-- Name: idx_test_set_results_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_test_set_results_date ON public.test_set_results USING btree (tested_at);


--
-- Name: idx_test_set_results_exercise; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_test_set_results_exercise ON public.test_set_results USING btree (exercise_id);


--
-- Name: idx_test_set_results_participant; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_test_set_results_participant ON public.test_set_results USING btree (participant_id);


--
-- Name: idx_test_set_results_set_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_test_set_results_set_id ON public.test_set_results USING btree (test_set_id);


--
-- Name: idx_test_sets_created_by; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_test_sets_created_by ON public.test_sets USING btree (created_by);


--
-- Name: idx_user_tests_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_user_tests_date ON public.user_tests USING btree (tested_at);


--
-- Name: idx_user_tests_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_user_tests_type ON public.user_tests USING btree (test_type);


--
-- Name: idx_user_tests_user_exercise; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_user_tests_user_exercise ON public.user_tests USING btree (user_id, exercise_id);


--
-- Name: idx_users_active; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_users_active ON public.users USING btree (is_active);


--
-- Name: idx_users_role; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_users_role ON public.users USING btree (role);


--
-- Name: idx_users_telegram_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_users_telegram_id ON public.users USING btree (telegram_id);


--
-- Name: idx_workout_individual_students_student; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_workout_individual_students_student ON public.workout_individual_students USING btree (student_id);


--
-- Name: idx_workout_sessions_completed_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_workout_sessions_completed_at ON public.workout_sessions USING btree (completed_at DESC);


--
-- Name: idx_workout_sessions_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_workout_sessions_status ON public.workout_sessions USING btree (status);


--
-- Name: idx_workout_sessions_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_workout_sessions_user_id ON public.workout_sessions USING btree (user_id);


--
-- Name: idx_workout_team_player_assignments; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_workout_team_player_assignments ON public.workout_team_player_assignments USING btree (workout_team_id);


--
-- Name: idx_workout_team_player_assignments_player; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_workout_team_player_assignments_player ON public.workout_team_player_assignments USING btree (team_player_id);


--
-- Name: idx_workout_team_player_assignments_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_workout_team_player_assignments_status ON public.workout_team_player_assignments USING btree (status);


--
-- Name: idx_workout_teams_team; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_workout_teams_team ON public.workout_teams USING btree (team_id);


--
-- Name: idx_workout_teams_workout; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_workout_teams_workout ON public.workout_teams USING btree (workout_id);


--
-- Name: idx_workouts_active; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_workouts_active ON public.workouts USING btree (is_active);


--
-- Name: idx_workouts_assigned_to; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_workouts_assigned_to ON public.workouts USING btree (assigned_to);


--
-- Name: idx_workouts_created_by; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_workouts_created_by ON public.workouts USING btree (created_by);


--
-- Name: idx_workouts_unique_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_workouts_unique_id ON public.workouts USING btree (unique_id);


--
-- Name: idx_workouts_visibility; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_workouts_visibility ON public.workouts USING btree (visibility);


--
-- Name: coach_students trigger_set_coach_invite_code; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trigger_set_coach_invite_code BEFORE INSERT ON public.coach_students FOR EACH ROW EXECUTE FUNCTION public.set_coach_invite_code();


--
-- Name: workouts trigger_set_workout_unique_id; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trigger_set_workout_unique_id BEFORE INSERT OR UPDATE ON public.workouts FOR EACH ROW EXECUTE FUNCTION public.set_workout_unique_id();


--
-- Name: test_batteries trigger_test_batteries_updated_at; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trigger_test_batteries_updated_at BEFORE UPDATE ON public.test_batteries FOR EACH ROW EXECUTE FUNCTION public.update_test_batteries_updated_at();


--
-- Name: coach_students coach_students_coach_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.coach_students
    ADD CONSTRAINT coach_students_coach_id_fkey FOREIGN KEY (coach_id) REFERENCES public.users(telegram_id);


--
-- Name: coach_students coach_students_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.coach_students
    ADD CONSTRAINT coach_students_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: exercises exercises_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.exercises
    ADD CONSTRAINT exercises_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: individual_student_workouts individual_student_workouts_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.individual_student_workouts
    ADD CONSTRAINT individual_student_workouts_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.individual_students(id) ON DELETE CASCADE;


--
-- Name: individual_student_workouts individual_student_workouts_workout_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.individual_student_workouts
    ADD CONSTRAINT individual_student_workouts_workout_id_fkey FOREIGN KEY (workout_id) REFERENCES public.workouts(id) ON DELETE CASCADE;


--
-- Name: one_rep_max one_rep_max_exercise_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.one_rep_max
    ADD CONSTRAINT one_rep_max_exercise_id_fkey FOREIGN KEY (exercise_id) REFERENCES public.exercises(id) ON DELETE CASCADE;


--
-- Name: one_rep_max one_rep_max_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.one_rep_max
    ADD CONSTRAINT one_rep_max_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: team_announcements team_announcements_author_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.team_announcements
    ADD CONSTRAINT team_announcements_author_id_fkey FOREIGN KEY (author_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: team_members team_members_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.team_members
    ADD CONSTRAINT team_members_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: team_players team_players_team_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.team_players
    ADD CONSTRAINT team_players_team_id_fkey FOREIGN KEY (team_id) REFERENCES public.teams(id) ON DELETE CASCADE;


--
-- Name: team_stats_visibility team_stats_visibility_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.team_stats_visibility
    ADD CONSTRAINT team_stats_visibility_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.users(id);


--
-- Name: test_batteries test_batteries_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.test_batteries
    ADD CONSTRAINT test_batteries_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: test_battery_exercises test_battery_exercises_battery_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.test_battery_exercises
    ADD CONSTRAINT test_battery_exercises_battery_id_fkey FOREIGN KEY (battery_id) REFERENCES public.test_batteries(id) ON DELETE CASCADE;


--
-- Name: test_battery_exercises test_battery_exercises_exercise_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.test_battery_exercises
    ADD CONSTRAINT test_battery_exercises_exercise_id_fkey FOREIGN KEY (exercise_id) REFERENCES public.exercises(id) ON DELETE CASCADE;


--
-- Name: test_battery_participants test_battery_participants_battery_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.test_battery_participants
    ADD CONSTRAINT test_battery_participants_battery_id_fkey FOREIGN KEY (battery_id) REFERENCES public.test_batteries(id) ON DELETE CASCADE;


--
-- Name: test_battery_participants test_battery_participants_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.test_battery_participants
    ADD CONSTRAINT test_battery_participants_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: test_battery_results test_battery_results_battery_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.test_battery_results
    ADD CONSTRAINT test_battery_results_battery_id_fkey FOREIGN KEY (battery_id) REFERENCES public.test_batteries(id) ON DELETE CASCADE;


--
-- Name: test_battery_results test_battery_results_exercise_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.test_battery_results
    ADD CONSTRAINT test_battery_results_exercise_id_fkey FOREIGN KEY (exercise_id) REFERENCES public.exercises(id) ON DELETE CASCADE;


--
-- Name: test_battery_results test_battery_results_participant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.test_battery_results
    ADD CONSTRAINT test_battery_results_participant_id_fkey FOREIGN KEY (participant_id) REFERENCES public.test_battery_participants(id) ON DELETE CASCADE;


--
-- Name: test_set_results test_set_results_exercise_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.test_set_results
    ADD CONSTRAINT test_set_results_exercise_id_fkey FOREIGN KEY (exercise_id) REFERENCES public.exercises(id) ON DELETE CASCADE;


--
-- Name: user_endurance_records user_endurance_records_exercise_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_endurance_records
    ADD CONSTRAINT user_endurance_records_exercise_id_fkey FOREIGN KEY (exercise_id) REFERENCES public.exercises(id) ON DELETE CASCADE;


--
-- Name: user_endurance_records user_endurance_records_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_endurance_records
    ADD CONSTRAINT user_endurance_records_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_speed_records user_speed_records_exercise_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_speed_records
    ADD CONSTRAINT user_speed_records_exercise_id_fkey FOREIGN KEY (exercise_id) REFERENCES public.exercises(id) ON DELETE CASCADE;


--
-- Name: user_speed_records user_speed_records_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_speed_records
    ADD CONSTRAINT user_speed_records_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: user_tests user_tests_exercise_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_tests
    ADD CONSTRAINT user_tests_exercise_id_fkey FOREIGN KEY (exercise_id) REFERENCES public.exercises(id) ON DELETE CASCADE;


--
-- Name: user_tests user_tests_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_tests
    ADD CONSTRAINT user_tests_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: workout_exercises workout_exercises_exercise_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workout_exercises
    ADD CONSTRAINT workout_exercises_exercise_id_fkey FOREIGN KEY (exercise_id) REFERENCES public.exercises(id) ON DELETE CASCADE;


--
-- Name: workout_exercises workout_exercises_workout_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workout_exercises
    ADD CONSTRAINT workout_exercises_workout_id_fkey FOREIGN KEY (workout_id) REFERENCES public.workouts(id) ON DELETE CASCADE;


--
-- Name: workout_individual_students workout_individual_students_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workout_individual_students
    ADD CONSTRAINT workout_individual_students_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.individual_students(id) ON DELETE CASCADE;


--
-- Name: workout_individual_students workout_individual_students_workout_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workout_individual_students
    ADD CONSTRAINT workout_individual_students_workout_id_fkey FOREIGN KEY (workout_id) REFERENCES public.workouts(id) ON DELETE CASCADE;


--
-- Name: workout_session_exercises workout_session_exercises_exercise_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workout_session_exercises
    ADD CONSTRAINT workout_session_exercises_exercise_id_fkey FOREIGN KEY (exercise_id) REFERENCES public.exercises(id);


--
-- Name: workout_session_exercises workout_session_exercises_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workout_session_exercises
    ADD CONSTRAINT workout_session_exercises_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.workout_sessions(id) ON DELETE CASCADE;


--
-- Name: workout_session_exercises workout_session_exercises_workout_exercise_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workout_session_exercises
    ADD CONSTRAINT workout_session_exercises_workout_exercise_id_fkey FOREIGN KEY (workout_exercise_id) REFERENCES public.workout_exercises(id);


--
-- Name: workout_session_sets workout_session_sets_session_exercise_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workout_session_sets
    ADD CONSTRAINT workout_session_sets_session_exercise_id_fkey FOREIGN KEY (session_exercise_id) REFERENCES public.workout_session_exercises(id) ON DELETE CASCADE;


--
-- Name: workout_sessions workout_sessions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workout_sessions
    ADD CONSTRAINT workout_sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: workout_sessions workout_sessions_workout_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workout_sessions
    ADD CONSTRAINT workout_sessions_workout_id_fkey FOREIGN KEY (workout_id) REFERENCES public.workouts(id) ON DELETE CASCADE;


--
-- Name: workout_team_player_assignments workout_team_player_assignments_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workout_team_player_assignments
    ADD CONSTRAINT workout_team_player_assignments_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.workout_sessions(id);


--
-- Name: workout_team_player_assignments workout_team_player_assignments_team_player_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workout_team_player_assignments
    ADD CONSTRAINT workout_team_player_assignments_team_player_id_fkey FOREIGN KEY (team_player_id) REFERENCES public.team_players(id) ON DELETE CASCADE;


--
-- Name: workout_team_player_assignments workout_team_player_assignments_workout_team_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workout_team_player_assignments
    ADD CONSTRAINT workout_team_player_assignments_workout_team_id_fkey FOREIGN KEY (workout_team_id) REFERENCES public.workout_teams(id) ON DELETE CASCADE;


--
-- Name: workout_teams workout_teams_assigned_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workout_teams
    ADD CONSTRAINT workout_teams_assigned_by_fkey FOREIGN KEY (assigned_by) REFERENCES public.users(id);


--
-- Name: workout_teams workout_teams_team_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workout_teams
    ADD CONSTRAINT workout_teams_team_id_fkey FOREIGN KEY (team_id) REFERENCES public.teams(id) ON DELETE CASCADE;


--
-- Name: workout_teams workout_teams_workout_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workout_teams
    ADD CONSTRAINT workout_teams_workout_id_fkey FOREIGN KEY (workout_id) REFERENCES public.workouts(id) ON DELETE CASCADE;


--
-- Name: workouts workouts_assigned_to_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workouts
    ADD CONSTRAINT workouts_assigned_to_fkey FOREIGN KEY (assigned_to) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: workouts workouts_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.workouts
    ADD CONSTRAINT workouts_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: sportbot_user
--

REVOKE USAGE ON SCHEMA public FROM PUBLIC;


--
-- Name: TABLE workouts; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.workouts TO PUBLIC;


--
-- Name: SEQUENCE workouts_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT SELECT,USAGE ON SEQUENCE public.workouts_id_seq TO PUBLIC;


--
-- PostgreSQL database dump complete
--

\unrestrict aHARFqiZEIVVTQpnIOBvSODy0v9FeSn4wkkzYZ8tea8NJ5EQM4X9fnqlwI01Sc6

