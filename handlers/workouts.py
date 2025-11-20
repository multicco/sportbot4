# handlers/workouts.py
# -*- coding: utf-8 -*-
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import StateFilter
from aiogram.enums import ParseMode
from utils.helpers import _safe_edit_or_send
from database import db_manager
from states.workout_states import CreateWorkoutStates

logger = logging.getLogger(__name__)
workouts_router = Router()
#from handlers.exercises import search_exercise_menu
#........................nazaz.....................





@workouts_router.callback_query(F.data == "back_to_constructor")
async def back_to_constructor(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CreateWorkoutStates.adding_exercises)
    await _show_block_selection(callback.message, state)
    await callback.answer()


# ----------------- HELPERS -----------------
def _parse_int_suffix(callback_data: str) -> Optional[int]:
    """Возвращает целый суффикс после '_' или None."""
    try:
        part = callback_data.split("_")[-1]
        return int(part) if part.isdigit() else None
    except Exception:
        return None

def _parse_id_with_prefix(callback_data: str, prefix: str) -> int:
    """Парсит ID после prefix, бросает ValueError, если не число."""
    if not callback_data.startswith(prefix):
        raise ValueError("prefix mismatch")
    tail = callback_data[len(prefix):]
    if tail.isdigit():
        return int(tail)
    raise ValueError("no numeric id")

async def _safe_edit_or_send(message, text, reply_markup=None, parse_mode=None):
    """Пробуем edit_text, если не удалось — answer."""
    try:
        await message.edit_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception:
        await message.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)

# ==================== ОПЦИОНАЛЬНО: ДОБАВИТЬ ФИЛЬТР ПО РОЛЯМ В ГЛАВНОЕ МЕНЮ =====
@workouts_router.callback_query(F.data == "workouts_menu")
async def workouts_menu(callback: CallbackQuery):
    """Главное меню тренировок - УЛУЧШЕННАЯ версия с учетом ролей"""
    
    try:
        user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
        role = user.get('role', 'player')
        
        kb = InlineKeyboardBuilder()
        
        # ✓ РАЗНЫЕ КНОПКИ ДЛЯ РАЗНЫХ РОЛЕЙ (как в tests.py)
        
        kb.button(text="🏋️ Мои тренировки", callback_data="my_workouts")
        kb.button(text="🔍 Найти тренировку", callback_data="find_workout")
        
        if role in ['trainer', 'coach', 'admin']:
            # Только тренеры видят опции создания и управления
            kb.button(text="➕ Создать тренировку", callback_data="create_workout")
            kb.button(text="📊 Статистика", callback_data="workout_statistics")
        else:
            # Игроки видят поиск и мои достижения
            kb.button(text="🏆 Мои достижения", callback_data="my_achievements")
        
        kb.button(text="🔙 Главное меню", callback_data="main_menu")
        kb.adjust(2)
        
        text = f"🏋️ **Меню тренировок**\n\n"
        text += f"*(Ваша роль: {role})*\n\n"
        text += f"Выберите действие:"
        
        await _safe_edit_or_send(
            callback.message, 
            text, 
            reply_markup=kb.as_markup(), 
            parse_mode="Markdown"
        )
        await callback.answer()
    
    except Exception as e:
        logger.exception(f"Ошибка в workouts_menu: {e}")
        await callback.answer("Ошибка", show_alert=True)

@workouts_router.callback_query(F.data == "manual_add_exercise")
async def add_exercise_manually(callback: CallbackQuery, state: FSMContext):
    """Ручное добавление упражнения текстом"""
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    if user['role'] not in ['trainer', 'coach', 'admin']:
        await callback.answer("Доступно только тренерам.", show_alert=True)
        return  # ← Выходим, не меняя состояние
    await callback.message.edit_text(
        "📝 Введите упражнение вручную:\n\n"
        "_Например:_ «Жим лёжа 3х10 70% от 1ПМ, отдых 90 сек.»",
        parse_mode="Markdown"
    )
    await state.set_state(CreateWorkoutStates.manual_exercise_input)
    await callback.answer()

@workouts_router.message(StateFilter(CreateWorkoutStates.manual_exercise_input))
async def handle_manual_exercise_input(message: Message, state: FSMContext):
    user = await db_manager.get_user_by_telegram_id(message.from_user.id)
    if user['role'] not in ['trainer', 'coach', 'admin']:
        await state.clear()  # ← Очищаем, если игрок попал случайно
        return  # ← Выходим, не обрабатывая
    text = message.text.strip()
    data = await state.get_data()
    exercises = data.get("manual_exercises", [])
    exercises.append(text)
    await state.update_data(manual_exercises=exercises)

    await message.answer(f"✅ Добавлено упражнение:\n\n{text}")

    # Клавиатура для следующего шага
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Добавить ещё", callback_data="manual_add_exercise")
    kb.button(text="⬅️ Назад", callback_data="back_to_constructor")
    kb.adjust(1)
    await message.answer("Что дальше?", reply_markup=kb.as_markup())

    await state.set_state(CreateWorkoutStates.adding_exercises)




# ==================== ЗАЩИТА: ПРОВЕРКА ДОСТУПА ПЕРЕД ПРОСМОТРОМ ====================

async def check_workout_access(user_id: int, telegram_id: int, workout_id: int) -> bool:
    """
    ✓ ФУНКЦИЯ ПРОВЕРКИ ДОСТУПА
    Использует существующий паттерн из системы тестов
    """
    
    try:
        user = await db_manager.get_user_by_telegram_id(telegram_id)
        if not user:
            return False
        
        role = user.get('role', 'player')
        
        # АДМИН видит всё
        if role == 'admin':
            return True
        
        async with db_manager.pool.acquire() as conn:
            workout = await conn.fetchrow(
                "SELECT created_by FROM workouts WHERE id = $1",
                workout_id
            )
            
            if not workout:
                return False
            
            # Если это твоя тренировка
            if workout['created_by'] == user_id:
                return True
            
            # Если ты тренер - проверяем, является ли это подопечным
            if role in ['trainer', 'coach']:
                is_trainee = await conn.fetchval("""
                    SELECT COUNT(*) FROM user_trainee_assignments
                    WHERE trainer_id = $1 AND trainee_id = $2
                """, user_id, workout['created_by'])
                return is_trainee > 0
        
        return False
    
    except Exception as e:
        logger.exception(f"Ошибка проверки доступа: {e}")
        return False

# ----------------- VIEW DETAILS -----------------
@workouts_router.callback_query(F.data.startswith("view_workout_"))
async def view_workout_details(callback: CallbackQuery):

    workout_id = int(callback.data.split("_")[2])
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    
    # ✓ ПРОВЕРЯЕМ ДОСТУП
    can_access = await check_workout_access(user['id'], callback.from_user.id, workout_id)
    
    if not can_access:
        await callback.answer("🚫 У вас нет доступа к этой тренировке", show_alert=True)
        return

    try:
        wid = _parse_id_with_prefix(callback.data, "view_workout_")
    except ValueError:
        await callback.answer("Некорректный ID", show_alert=True)
        return

    try:
        async with db_manager.pool.acquire() as conn:
            workout = await conn.fetchrow("""
                SELECT w.*, u.first_name as creator_name, u.last_name as creator_lastname
                FROM workouts w
                LEFT JOIN users u ON w.created_by = u.id
                WHERE w.id = $1 AND coalesce(w.is_active, true) = true
            """, wid)
            if not workout:
                await callback.answer("Тренировка не найдена", show_alert=True)
                return
            exercises = await conn.fetch("""
                SELECT we.*, e.name as exercise_name, e.muscle_group, e.category
                FROM workout_exercises we
                LEFT JOIN exercises e ON e.id = we.exercise_id
                WHERE we.workout_id = $1
                ORDER BY we.phase, we.order_in_phase
            """, wid)
    except Exception as e:
        logger.exception("view_workout_details db error: %s", e)
        await callback.answer("Ошибка БД", show_alert=True)
        return

    text = f"🏷 **{workout['name']}**\n\n"
    if workout.get('description'):
        text += f"📝 _{workout['description']}_\n\n"
    text += f"👤 Автор: {workout.get('creator_name') or ''} {workout.get('creator_lastname') or ''}\n"
    text += f"⏱ Время: ~{workout.get('estimated_duration_minutes') or 0} мин\n"
    text += f"💡 Код: `{workout.get('unique_id')}`\n\n"

    if exercises:
        phase_map = {'warmup': '🔥 Разминка', 'nervousprep': '⚡ Подготовка НС', 'main': '💪 Основная', 'cooldown': '🧘 Заминка'}
        cur = None
        for ex in exercises:
            if ex['phase'] != cur:
                cur = ex['phase']
                text += f"\n**{phase_map.get(cur, cur)}:**\n"
            # show minimal info
            reps = ""
            if ex.get('reps_min') is not None:
                if ex.get('reps_max') is not None and ex['reps_min'] != ex['reps_max']:
                    reps = f"{ex['reps_min']}-{ex['reps_max']}"
                else:
                    reps = f"{ex['reps_min']}"
            else:
                reps = "-"
            sets = ex.get('sets') or "-"
            text += f"• **{ex['exercise_name']}** — {sets}×{reps}"
            if ex.get('one_rm_percent'):
                text += f" ({ex['one_rm_percent']}% 1ПМ)"
            if ex.get('rest_seconds'):
                rs = ex['rest_seconds']
                text += f" | отдых {rs//60}м{rs%60}s" if rs >= 60 else f" | отдых {rs}s"
            text += "\n"
    else:
        text += "⚠️ Упражнений пока нет."

    kb = InlineKeyboardBuilder()
    kb.button(text="▶️ Начать тренировку", callback_data=f"start_workout_{wid}")
    kb.button(text="✏️ Редактировать", callback_data=f"edit_workout_{wid}")
    kb.button(text="🗑️ Удалить", callback_data=f"delete_workout_{wid}")
    kb.button(text="🔙 В мои", callback_data="my_workouts")
    kb.adjust(2)
    await _safe_edit_or_send(callback.message, text, reply_markup=kb.as_markup(), parse_mode="Markdown")
    await callback.answer()


# ----------------- CREATE FLOW (FSM) -----------------
@workouts_router.callback_query(F.data == "create_workout")
async def create_workout_start(callback: CallbackQuery, state: FSMContext):
    logger.info("create_workout_start by %s", callback.from_user.id)
    kb = InlineKeyboardBuilder()
    kb.button(text="❌ Отменить", callback_data="create_cancel")
    kb.adjust(1)
    await _safe_edit_or_send(callback.message, "🏋️ **Создание тренировки**\n\nВведите название тренировки:", reply_markup=kb.as_markup(), parse_mode="Markdown")
    await state.set_state(CreateWorkoutStates.waiting_workout_name)
    await callback.answer()

@workouts_router.callback_query(F.data == "create_cancel")
async def create_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardBuilder()
    kb.button(text="🏋️ Мои тренировки", callback_data="my_workouts")
    kb.button(text="🔙 В меню", callback_data="workouts_menu")
    kb.adjust(1)
    await _safe_edit_or_send(callback.message, "Создание тренировки отменено.", reply_markup=kb.as_markup())
    await callback.answer()

# Показываем меню выбора блоков
async def _show_block_selection(message, state: FSMContext):
    data = await state.get_data()
    name = data.get('name', 'Без названия')
    selected = data.get('selected_blocks', {})
    text = f"🔧 **Структура тренировки:** {name}\n\nВыберите блок и добавьте упражнения:\n\n"
    blocks = [('warmup', '🔥 Разминка'), ('nervousprep', '⚡ Подготовка НС'), ('main', '💪 Основная'), ('cooldown', '🧘 Заминка')]
    for k, label in blocks:
        status = "✅" if k in selected else "⭕"
        cnt = len(selected.get(k, {}).get('exercises', [])) if k in selected else 0
        text += f"{status} {label} — {cnt} упр.\n"
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Разминка", callback_data="create_add_warmup")
    kb.button(text="➕ Подготовка НС", callback_data="create_add_nervousprep")
    kb.button(text="➕ Основная", callback_data="create_add_main")
    kb.button(text="➕ Заминка", callback_data="create_add_cooldown")
    kb.button(text="✅ Готово — сохранить тренировку", callback_data="create_finish")
    kb.button(text="❌ Отменить", callback_data="create_cancel")
    kb.adjust(2)
    await _safe_edit_or_send(message, text, reply_markup=kb.as_markup(), parse_mode="Markdown")
    await state.set_state(CreateWorkoutStates.selecting_blocks)


# handlers/workouts.py - ТОЛЬКО ОБРАБОТЧИКИ ДЛЯ ПОИСКА (вставить в конец файла перед "# ====" или другими комментариями)

# =====================================================
# ✓ ИСПРАВЛЕНИЕ: НОВЫЕ ОБРАБОТЧИКИ ПОИСКА ТРЕНИРОВКИ
# =====================================================

# Добавить в workouts.py эти функции:

@workouts_router.callback_query(F.data == "find_workout")
async def find_workout(callback: CallbackQuery, state: FSMContext):
    """Меню поиска тренировки - выбор способа поиска"""
    logger.info(f"find_workout menu для user {callback.from_user.id}")
    
    kb = InlineKeyboardBuilder()
    kb.button(text="🔍 Поиск по коду", callback_data="search_by_code")
    kb.button(text="📝 Поиск по названию", callback_data="search_by_name")
    kb.button(text="🔙 В меню", callback_data="workouts_menu")
    kb.adjust(1)
    
    await _safe_edit_or_send(
        callback.message,
        "🔍 **Поиск тренировки**\n\nВыберите способ поиска:",
        reply_markup=kb.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()


@workouts_router.callback_query(F.data == "search_by_code")
async def search_by_code_start(callback: CallbackQuery, state: FSMContext):
    """Начало поиска по коду тренировки"""
    kb = InlineKeyboardBuilder()
    kb.button(text="❌ Отменить", callback_data="find_workout")
    kb.adjust(1)
    
    await _safe_edit_or_send(
        callback.message,
        "📝 Введите код тренировки (например: ABC123):",
        reply_markup=kb.as_markup()
    )
    await state.set_state(CreateWorkoutStates.searching_by_code)
    await callback.answer()


@workouts_router.callback_query(F.data == "search_by_name")
async def search_by_name_start(callback: CallbackQuery, state: FSMContext):
    """Начало поиска по названию тренировки"""
    kb = InlineKeyboardBuilder()
    kb.button(text="❌ Отменить", callback_data="find_workout")
    kb.adjust(1)
    
    await _safe_edit_or_send(
        callback.message,
        "📝 Введите название или часть названия тренировки:",
        reply_markup=kb.as_markup()
    )
    await state.set_state(CreateWorkoutStates.searching_by_name)
    await callback.answer()


async def get_user_role(telegram_id: int) -> str:
    """Получить роль пользователя по telegram_id"""
    try:
        user = await db_manager.get_user_by_telegram_id(telegram_id)
        if user:
            return user.get('role', 'player')
    except Exception as e:
        logger.exception(f"Ошибка получения роли: {e}")
    return 'player'


async def can_access_workout(user_id: int, telegram_id: int, workout_id: int) -> bool:
    """
    ✓ ФУНКЦИЯ ПРОВЕРКИ ДОСТУПА К ТРЕНИРОВКЕ
    
    Правила доступа:
    - АДМИН: видит всё
    - АВТОР: видит свои
    - ТРЕНЕР: видит свои + тренировки своих подопечных
    - ИГРОК: видит только свои
    """
    role = await get_user_role(telegram_id)
    
    if role == 'admin':
        return True
    
    async with db_manager.pool.acquire() as conn:
        workout = await conn.fetchrow(
            "SELECT created_by FROM workouts WHERE id = $1",
            workout_id
        )
        
        if not workout:
            return False
        
        # Если это твоя тренировка
        if workout['created_by'] == user_id:
            return True
        
        # Если ты тренер - проверяем, является ли это твоим игроком
        if role == 'trainer':
            is_trainee = await conn.fetchval("""
                SELECT COUNT(*) FROM user_trainee_assignments
                WHERE trainer_id = $1 AND trainee_id = $2
            """, user_id, workout['created_by'])
            return is_trainee > 0
    
    return False


@workouts_router.message(StateFilter(CreateWorkoutStates.searching_by_code))
async def handle_code_search(message: Message, state: FSMContext):
    """Обработка поиска по коду тренировки"""
    code = message.text.strip().upper()
    
    if len(code) < 3:
        await message.answer("❌ Код должен быть минимум 3 символа")
        return
    
    try:
        user = await db_manager.get_user_by_telegram_id(message.from_user.id)
        if not user:
            await message.answer("❌ Пользователь не найден в БД")
            await state.clear()
            return
        
        async with db_manager.pool.acquire() as conn:
            workout = await conn.fetchrow("""
                SELECT w.id, w.name, w.unique_id, w.description,
                       u.first_name, u.last_name,
                       (SELECT COUNT(*) FROM workout_exercises WHERE workout_id = w.id) as exercise_count
                FROM workouts w
                LEFT JOIN users u ON w.created_by = u.id
                WHERE w.unique_id = $1 AND coalesce(w.is_active, true) = true
            """, code)
            
            if not workout:
                kb = InlineKeyboardBuilder()
                kb.button(text="🔄 Новый поиск", callback_data="search_by_code")
                kb.button(text="🔙 В меню", callback_data="find_workout")
                kb.adjust(1)
                
                await message.answer(
                    "❌ Тренировка с таким кодом не найдена",
                    reply_markup=kb.as_markup()
                )
                await state.clear()
                return
            
            # ✓ ПРОВЕРЯЕМ ДОСТУП перед показом
            can_access = await can_access_workout(user['id'], message.from_user.id, workout['id'])
            
            if not can_access:
                kb = InlineKeyboardBuilder()
                kb.button(text="🔄 Новый поиск", callback_data="search_by_code")
                kb.button(text="🔙 В меню", callback_data="find_workout")
                kb.adjust(1)
                
                await message.answer(
                    "🚫 У вас нет доступа к этой тренировке",
                    reply_markup=kb.as_markup()
                )
                await state.clear()
                return
            
            # Показываем найденную тренировку
            text = f"🏷 **{workout['name']}**\n\n"
            if workout.get('description'):
                text += f"📝 _{workout['description']}_\n\n"
            text += f"👤 Автор: {workout.get('first_name') or ''} {workout.get('last_name') or ''}\n"
            text += f"💡 Код: `{workout['unique_id']}`\n"
            text += f"📊 Упражнений: {workout['exercise_count']}\n"
            
            kb = InlineKeyboardBuilder()
            kb.button(text="👁️ Просмотр", callback_data=f"view_workout_{workout['id']}")
            kb.button(text="➕ Добавить", callback_data=f"add_to_my_{workout['id']}")
            kb.button(text="🔄 Новый поиск", callback_data="search_by_code")
            kb.adjust(1)
            
            await message.answer(text, reply_markup=kb.as_markup(), parse_mode="Markdown")
            await state.clear()
            logger.info(f"✅ Поиск по коду: найдена тренировка {workout['id']}")
    
    except Exception as e:
        logger.exception(f"Ошибка поиска по коду: {e}")
        await message.answer("❌ Ошибка при поиске тренировки")
        await state.clear()


@workouts_router.message(StateFilter(CreateWorkoutStates.searching_by_name))
async def handle_name_search(message: Message, state: FSMContext):
    """Обработка поиска по названию тренировки"""
    search_text = f"%{message.text.strip()}%"
    
    try:
        user = await db_manager.get_user_by_telegram_id(message.from_user.id)
        if not user:
            await message.answer("❌ Пользователь не найден в БД")
            await state.clear()
            return
        
        async with db_manager.pool.acquire() as conn:
            workouts = await conn.fetch("""
                SELECT w.id, w.name, w.unique_id, w.description,
                       u.first_name, u.last_name,
                       (SELECT COUNT(*) FROM workout_exercises WHERE workout_id = w.id) as exercise_count
                FROM workouts w
                LEFT JOIN users u ON w.created_by = u.id
                WHERE (w.name ILIKE $1 OR w.description ILIKE $1)
                AND coalesce(w.is_active, true) = true
                ORDER BY w.created_at DESC
                LIMIT 10
            """, search_text)
            
            if not workouts:
                kb = InlineKeyboardBuilder()
                kb.button(text="🔄 Новый поиск", callback_data="search_by_name")
                kb.button(text="🔙 В меню", callback_data="find_workout")
                kb.adjust(1)
                
                await message.answer(
                    "❌ Тренировки не найдены",
                    reply_markup=kb.as_markup()
                )
                await state.clear()
                return
            
            text = f"🔍 **Найдено {len(workouts)} тренировок:**\n\n"
            
            kb = InlineKeyboardBuilder()
            accessible_count = 0
            
            for w in workouts:
                # ✓ ПРОВЕРЯЕМ ДОСТУП к каждой
                can_access = await can_access_workout(user['id'], message.from_user.id, w['id'])
                
                icon = "✅" if can_access else "🔒"
                text += f"{icon} **{w['name']}** ({w['exercise_count']} упр.)\n"
                text += f"   Код: `{w['unique_id']}`\n"
                
                if can_access:
                    kb.button(text=w['name'][:30], callback_data=f"view_workout_{w['id']}")
                    accessible_count += 1
            
            text += f"\n✅ Доступно: {accessible_count} из {len(workouts)}"
            
            kb.button(text="🔄 Новый поиск", callback_data="search_by_name")
            kb.button(text="🔙 В меню", callback_data="find_workout")
            kb.adjust(1)
            
            await message.answer(text, reply_markup=kb.as_markup(), parse_mode="Markdown")
            await state.clear()
            logger.info(f"✅ Поиск по названию: найдено {accessible_count} доступных из {len(workouts)}")
    
    except Exception as e:
        logger.exception(f"Ошибка поиска по названию: {e}")
        await message.answer("❌ Ошибка при поиске тренировки")
        await state.clear()




# @workouts_router.callback_query(F.data == "my_workouts")
# async def my_workouts(callback: CallbackQuery):
    
#     """Показать тренировки пользователя"""
#     try:
#         logger.info(f"=== my_workouts START user {callback.from_user.id} ===")
        
#         # ЛОГИРОВАНИЕ 1: Получение юзера
#         user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
#         logger.info(f"✓ User found: {user}")
        
#         if not user:
#             logger.error(f"✗ User NOT found for telegram_id {callback.from_user.id}")
#             await callback.answer("❌ Пользователь не найден", show_alert=True)
#             return
        
#         # ✅ ДЛЯ ПОДОПЕЧНОГО (PLAYER) - НЕ ОБРАБАТЫВАЕМ, ВЫХОДИМ
#         if user.get('role') == 'player':
#             logger.info(f"⚠️ Player {user['id']} skip - using teams_menu handler")
#             await callback.answer()
#             return



#         logger.info(f"✓ User ID: {user.get('id')}")
        
#         # ЛОГИРОВАНИЕ 2: Подключение к БД
#         async with db_manager.pool.acquire() as conn:
#             logger.info("✓ DB connection acquired")
            
#             # ЛОГИРОВАНИЕ 3: Запрос к тренировкам
#             workouts = await conn.fetch("""
#                 SELECT w.*, COUNT(we.id) as exercise_count
#                 FROM workouts w
#                 LEFT JOIN workout_exercises we ON w.id = we.workout_id
#                 WHERE w.created_by = $1 AND w.is_active = true
#                 GROUP BY w.id
#                 ORDER BY w.created_at DESC
#                 LIMIT 10
#             """, user['id'])
            
#             logger.info(f"✓ Query executed, found: {len(workouts) if workouts else 0} workouts")
            
#             if workouts:
#                 logger.info(f"✓ First workout keys: {list(workouts[0].keys())}")  # ← ПОКАЖЕТ СТРУКТУРУ
                
#                 text = f"🏋️ **Мои тренировки ({len(workouts)}):**\n\n"
#                 keyboard = InlineKeyboardBuilder()
                
#                 for i, workout in enumerate(workouts):
#                     logger.info(f"✓ Processing workout {i}: {workout.get('name')}")
                    
#                     exercise_count = workout['exercise_count'] or 0
#                     duration = workout.get('estimated_duration_minutes', 'N/A')  # ← ИСПОЛЬЗУЙ .get()!
                    
#                     button_text = f"🏋️ {workout['name']}"
#                     if exercise_count > 0:
#                         button_text += f" ({exercise_count} упр.)"
#                     keyboard.button(
#                         text=button_text,
#                         callback_data=f"view_workout_{workout['id']}"
#                     )
                    
#                     text += f"**{workout['name']}**\n"
#                     text += f"📋 Упражнений: {exercise_count} | ⏱️ ~{duration}мин\n"
#                     text += f"🆔 Код: `{workout['unique_id']}`\n\n"
                
#                 keyboard.button(text="➕ Создать новую", callback_data="create_workout")
#                 keyboard.button(text="🔙 К тренировкам", callback_data="workouts_menu")
#                 keyboard.adjust(1)
                
#                 logger.info("✓ About to edit message")
#             else:
#                 logger.info("⚠️ No workouts found")
#                 text = ("🏋️ **Мои тренировки**\n\n"
#                         "У вас пока нет созданных тренировок.\n\n"
#                         "Создайте первую тренировку с блочной структурой!")
#                 keyboard = InlineKeyboardBuilder()
#                 keyboard.button(text="➕ Создать первую", callback_data="create_workout")
#                 keyboard.button(text="🔙 К тренировкам", callback_data="workouts_menu")
            
#             logger.info("✓ Editing message...")
#             await callback.message.edit_text(
#                 text,
#                 reply_markup=keyboard.as_markup(),
#                 parse_mode="Markdown"
#             )
#             logger.info("✓ Message edited successfully")
            
#             await callback.answer()
#             logger.info("=== my_workouts END (SUCCESS) ===")
            
#     except Exception as e:
#         logger.error(f"=== ERROR in my_workouts ===", exc_info=True)
#         logger.error(f"Error type: {type(e).__name__}")
#         logger.error(f"Error message: {str(e)}")
#         import traceback
#         logger.error(f"Traceback:\n{traceback.format_exc()}")
        
#         await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


@workouts_router.callback_query(F.data == "my_workouts")
async def my_workouts(callback: CallbackQuery):
    """Показать мои тренировки (для тренера/админа)"""
    try:
        logger.info(f"=== my_workouts START user {callback.from_user.id} ===")
        
        # ЛОГИРОВАНИЕ 1: Получение юзера
        user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
        logger.info(f"✓ User found: {user}")
        
        if not user:
            logger.error(f"✗ User NOT found for telegram_id {callback.from_user.id}")
            await callback.answer("❌ Пользователь не найден", show_alert=True)
            return
        
        # ✅ ДЛЯ ПОДОПЕЧНОГО (PLAYER) - НЕ ОБРАБАТЫВАЕМ, ВЫХОДИМ
        if user.get('role') == 'player':
            logger.info(f"⚠️ Player {user['id']} skip - using teams_menu handler")
            await callback.answer()
            return
        
        logger.info(f"✓ User ID: {user.get('id')}")
        
        # ЛОГИРОВАНИЕ 2: Подключение к БД
        async with db_manager.pool.acquire() as conn:
            logger.info("✓ DB connection acquired")
            
            # ЛОГИРОВАНИЕ 3: Запрос к тренировкам
            workouts = await conn.fetch("""
                SELECT w.*, COUNT(we.id) as exercise_count
                FROM workouts w
                LEFT JOIN workout_exercises we ON w.id = we.workout_id
                WHERE w.created_by = $1 AND w.is_active = true
                GROUP BY w.id
                ORDER BY w.created_at DESC
                LIMIT 10
            """, user['id'])
            
            logger.info(f"✓ Query executed, found: {len(workouts) if workouts else 0} workouts")
            
            keyboard = InlineKeyboardBuilder()
            
            if workouts:
                logger.info(f"✓ First workout keys: {list(workouts[0].keys())}")
                
                text = f"🏋️ **Мои тренировки ({len(workouts)}):**\n\n"
                
                for i, workout in enumerate(workouts):
                    logger.info(f"✓ Processing workout {i}: {workout.get('name')}")
                    
                    exercise_count = workout.get('exercise_count') or 0
                    duration = workout.get('estimated_duration_minutes', 'N/A')
                    unique_id = workout.get('unique_id', 'N/A')
                    
                    button_text = f"🏋️ {workout['name']}"
                    if exercise_count > 0:
                        button_text += f" ({exercise_count} упр.)"
                    
                    keyboard.button(
                        text=button_text,
                        callback_data=f"view_workout_{workout['id']}"
                    )
                    
                    text += f"**{workout['name']}**\n"
                    text += f"📋 Упражнений: {exercise_count} | ⏱️ ~{duration} мин\n"
                    text += f"🆔 Код: `{unique_id}`\n\n"
                
            else:
                logger.info("⚠️ No workouts found")
                text = (
                    "🏋️ **Мои тренировки**\n\n"
                    "У вас пока нет созданных тренировок.\n\n"
                    "Создайте первую тренировку с блочной структурой!"
                )
            
            keyboard.button(text="➕ Создать новую", callback_data="create_workout")
            keyboard.button(text="🔙 К тренировкам", callback_data="workouts_menu")
            keyboard.adjust(1)
            
            logger.info("✓ Editing message...")
            await callback.message.edit_text(
                text,
                reply_markup=keyboard.as_markup(),
                parse_mode="Markdown"
            )
            logger.info("✓ Message edited successfully")
            
            await callback.answer()
            logger.info("=== my_workouts END (SUCCESS) ===")
            
    except Exception as e:
        logger.error(f"=== ERROR in my_workouts ===", exc_info=True)
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        import traceback
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)




@workouts_router.callback_query(F.data.in_(["create_add_warmup", "create_add_nervousprep", "create_add_main", "create_add_cooldown"]))
async def create_add_block(callback: CallbackQuery, state: FSMContext):
    """Добавить блок и СРАЗУ показать упражнения (без описания!)"""
    mapping = {
        "create_add_warmup": "warmup",
        "create_add_nervousprep": "nervousprep",
        "create_add_main": "main",
        "create_add_cooldown": "cooldown"
    }
    
    phase = mapping.get(callback.data)
    if not phase:
        await callback.answer()
        return
    
    await state.update_data(current_block=phase)
    
    # Создаём блок с пустым описанием
    data = await state.get_data()
    selected = data.get('selected_blocks', {})
    selected.setdefault(phase, {"description": "", "exercises": []})
    
    await state.update_data(selected_blocks=selected)
    
    # ✅ СРАЗУ К УПРАЖНЕНИЯМ БЕЗ ПРОМЕЖУТОЧНОГО МЕНЮ!
    await _show_exercises_for_block(callback.message, state)
    await callback.answer()


async def _show_exercises_for_block(message, state: FSMContext):
    data = await state.get_data()
    cur = data.get('current_block', 'main')
    phase_map = {'warmup': '🔥 Разминка', 'nervousprep': '⚡ Подготовка НС', 'main': '💪 Основная', 'cooldown': '🧘 Заминка'}
    sel = data.get('selected_blocks', {})
    block = sel.get(cur, {"description": "", "exercises": []})
    text = f"📋 **Блок: {phase_map.get(cur)}**\n\nОписание: {block['description'] or 'Нет'}\n\nУпражнения:\n"
    if block['exercises']:
        for ex in block['exercises']:
            text += f"• {ex['name']}\n"
    else:
        text += "Пока пусто.\n"
    kb = InlineKeyboardBuilder()
    kb.button(text="🔍 Поиск упражнения", callback_data="workout_start_ex_search")
    kb.button(text="📝 Добавить вручную", callback_data="manual_add_exercise")
    kb.button(text="🔙 К блокам", callback_data="create_back_to_blocks")
    kb.adjust(1)
    await _safe_edit_or_send(message, text, reply_markup=kb.as_markup(), parse_mode="Markdown")
    await state.set_state(CreateWorkoutStates.adding_exercises)

@workouts_router.callback_query(F.data.startswith("workout_add_ex_"))
async def workout_add_exercise(callback: CallbackQuery, state: FSMContext):
    ex_id = int(callback.data.split("_")[-1])
    data = await state.get_data()
    block = data.get("searching_in_block")
    if not block:
        await callback.answer("Контекст потерян.", show_alert=True)
        return

    async with db_manager.pool.acquire() as conn:
        ex = await conn.fetchrow("SELECT name FROM exercises WHERE id = $1", ex_id)
    if not ex:
        await callback.answer("Упражнение не найдено.", show_alert=True)
        return

    selected = data.get("selected_blocks", {})
    selected.setdefault(block, {"description": "", "exercises": []})
    selected[block]["exercises"].append({
        "id": ex_id,
        "name": ex["name"],
        "sets": None, "reps_min": None, "reps_max": None,
        "one_rm_percent": None, "rest_seconds": None
    })
    await state.update_data(selected_blocks=selected)

    await callback.message.edit_text(f"**{ex['name']}** добавлено в блок.")
    await _show_exercises_for_block(callback.message, state)
    await callback.answer()

# === ПОИСК УПРАЖНЕНИЙ ЧЕРЕЗ ГЛАВНОЕ МЕНЮ ===
@workouts_router.callback_query(F.data == "workout_start_ex_search")
async def workout_start_ex_search(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    block = data.get("current_block")
    logger.info("workout_start_ex_search: current_block = %s", block)
    if not block:
        await callback.answer("Ошибка: блок не выбран.", show_alert=True)
        return

    # Сохраняем, куда добавить
    await state.update_data(searching_in_block=block)
    await state.set_state(CreateWorkoutStates.searching_exercise_for_block)

    # Открываем ТО ЖЕ МЕНЮ, что и в главном меню
    
    from handlers import exercises
    await exercises.search_exercise_menu(callback, state)

@workouts_router.callback_query(F.data == "create_back_to_blocks")
async def create_back_to_blocks(callback: CallbackQuery, state: FSMContext):
    await _show_block_selection(callback.message, state)
    await callback.answer()

@workouts_router.callback_query(F.data == "workout_start_search")
async def workout_start_search(callback: CallbackQuery, state: FSMContext):
    # Сохраняем, что мы ищем в блоке
    data = await state.get_data()
    block = data.get("current_block")
    if not block:
        await callback.answer("Ошибка: блок не выбран.", show_alert=True)
        return

    await state.update_data(searching_in_block=block)
    await state.set_state(CreateWorkoutStates.searching_exercise_for_block)

    # Показываем ТО ЖЕ МЕНЮ, что и в главном меню!
    
    from handlers import exercises
    await exercises.search_exercise_menu(callback, state)

    await callback.answer()

@workouts_router.callback_query(F.data == "create_search_ex")
async def create_search_ex(callback: CallbackQuery, state: FSMContext):
    # Сохраняем, что мы ищем в блоке
    data = await state.get_data()
    block = data.get("current_block")
    if not block:
        await callback.answer("Ошибка: блок не выбран.", show_alert=True)
        return

    await state.update_data(searching_in_block=block)
    await state.set_state(CreateWorkoutStates.searching_exercise_for_block)

    # Показываем тот же текст, что и в главном меню
    await callback.message.edit_text("Введите название упражнения для поиска:")
    await callback.answer()




# В файле workouts.py замените функцию create_add_ex на эту:

@workouts_router.callback_query(F.data.startswith("create_add_ex_"))
async def create_add_ex(callback: CallbackQuery, state: FSMContext):
    ex_id = _parse_int_suffix(callback.data)
    if ex_id is None:
        await callback.answer("Некорректный ID", show_alert=True)
        return

    data = await state.get_data()
    current_block = data.get("searching_in_block")
    if not current_block:
        await callback.answer("Ошибка: блок не выбран.", show_alert=True)
        return

    try:
        async with db_manager.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, name, muscle_group, category, default_sets, default_reps_min, default_reps_max, one_rm_kg FROM exercises WHERE id = $1",
                ex_id
            )
        if not row:
            await callback.answer("Упражнение не найдено", show_alert=True)
            return

        # Сохраняем ВСЕ нужные данные
        await state.update_data(
            selected_exercise_id=ex_id,
            selected_exercise_name=row['name'],
            selected_exercise_1rm=row.get('one_rm_kg'),
            selected_exercise_defaults={
                'sets': row.get('default_sets') or 3,
                'reps': row.get('default_reps_min') or 8,
                'percent': 75,
                'rest': 120,
            },
            current_block=current_block  # ← КРИТИЧНО!
        )
        
        # Показываем информацию об упражнении и запрашиваем параметры
        one_rm_info = ""
        if row.get('one_rm_kg'):
            one_rm_info = f"\n\n💡 **1ПМ известен: {row['one_rm_kg']} кг**\nПосле ввода % будет показан точный вес"
        
        defaults = row.get('default_sets') or 3
        default_reps = row.get('default_reps_min') or 8
        
        text = f"""
🏋️ **{row['name']}**
💪 {row.get('muscle_group', 'Неизвестно')} | {row.get('category', 'Без категории')}

📝 **Введите параметры упражнения:**

**Формат:** подходы повторения % отдых

📌 **Примеры:**
  • `{defaults} {default_reps}` → {defaults}x{default_reps} по умолчанию
  • `4 10` → 4 подхода по 10 повторений
  • `4 10 75` → 4x10 при 75% от 1ПМ
  • `4 10 75 120` → полный формат + 120с отдыха

❓ **Значения по умолчанию:**
  • Подходы: {defaults}
  • Повторения: {default_reps}
  • % от 1ПМ: 75%
  • Отдых: 120 сек{one_rm_info}

_Или нажмите кнопку для значений по умолчанию:_
"""
        
        kb = InlineKeyboardBuilder()
        kb.button(
            text=f"✅ {defaults}x{default_reps} 75% 120s (по умолчанию)",
            callback_data=f"create_ex_quick_{ex_id}_{defaults}_{default_reps}_75_120"
        )
        kb.button(text="🔙 Выбрать другое", callback_data="create_search_ex")
        kb.adjust(1)
        
        await callback.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="Markdown")
        
        # Устанавливаем состояние для ввода параметров
        await state.set_state(CreateWorkoutStates.configuring_exercise)
        await callback.answer()
    
    except Exception as e:
        logger.exception("Ошибка в create_add_ex: %s", e)
        await callback.answer("❌ Ошибка при загрузке упражнения", show_alert=True)


# ========== БЫСТРОЕ ДОБАВЛЕНИЕ СО ЗНАЧЕНИЯМИ ПО УМОЛЧАНИЮ ==========

@workouts_router.callback_query(F.data.startswith("create_ex_quick_"))
async def create_ex_quick(callback: CallbackQuery, state: FSMContext):
    """Добавляет упражнение со значениями по умолчанию (кнопка)."""
    parts = callback.data.split("_")
    try:
        ex_id = int(parts[3])
        sets = int(parts[4])
        reps = int(parts[5])
        percent = int(parts[6])
        rest = int(parts[7])
    except (ValueError, IndexError):
        await callback.answer("❌ Ошибка при парсинге параметров", show_alert=True)
        return
    
    await _finalize_exercise_for_create(callback.message, state, sets, reps, percent, rest)
    await callback.answer()


# ========== ВВОД ПАРАМЕТРОВ В ОДНУ СТРОКУ ==========

@workouts_router.message(StateFilter(CreateWorkoutStates.configuring_exercise))
async def handle_create_exercise_params_input(message: Message, state: FSMContext):
    logger.info("handle_create_exercise_params_input: START")
    """
    Обрабатывает ввод параметров упражнения в формате: "4 10 75 120"
    """
    text = (message.text or "").strip()
    
    # Парсим параметры
    parts = text.split()
    
    if len(parts) < 1 or len(parts) > 4:
        await message.answer(
            "❌ **Неверный формат!**\n\n"
            "Используйте: `подходы повторения % отдых`\n"
            "Примеры:\n"
            "  • `4` → 4 подхода\n"
            "  • `4 10` → 4x10\n"
            "  • `4 10 75` → 4x10 75%\n"
            "  • `4 10 75 120` → 4x10 75% 120с",
            parse_mode="Markdown"
        )
        return
    
    # Парсим с валидацией
    try:
        sets = int(parts[0]) if len(parts) >= 1 else None
        reps = int(parts[1]) if len(parts) >= 2 else None
        percent = int(parts[2]) if len(parts) >= 3 else None
        rest = int(parts[3]) if len(parts) >= 4 else None
        
        # Валидируем диапазоны
        if sets and not (1 <= sets <= 20):
            raise ValueError("Подходы: 1-20")
        if reps and not (1 <= reps <= 100):
            raise ValueError("Повторения: 1-100")
        if percent and not (1 <= percent <= 200):
            raise ValueError("% от 1ПМ: 1-200")
        if rest and not (0 <= rest <= 600):
            raise ValueError("Отдых: 0-600 сек")
    
    except ValueError as e:
        await message.answer(f"❌ {str(e)}")
        return
    
    # Используем значения по умолчанию для пропущенных параметров
    data = await state.get_data()
    defaults = data.get("selected_exercise_defaults", {})
    
    sets = sets or defaults.get('sets', 3)
    reps = reps or defaults.get('reps', 8)
    percent = percent or defaults.get('percent', 75)
    rest = rest or defaults.get('rest', 120)
    
    # Финализируем упражнение
    await _finalize_exercise_for_create(message, state, sets, reps, percent, rest)


# ========== ФИНАЛИЗАЦИЯ (СОХРАНЕНИЕ В БЛОК) ==========

async def _finalize_exercise_for_create(message, state: FSMContext, sets: int, reps: int,
                                       percent: int, rest: int):
    """
    Сохраняет упражнение с параметрами в текущий блок.
    """
    data = await state.get_data()
    current_block = data.get("current_block")
    exercise_id = data.get("selected_exercise_id")
    exercise_name = data.get("selected_exercise_name")
    one_rm_kg = data.get("selected_exercise_1rm")
    
    if not current_block or not exercise_id:
        await message.answer("❌ Ошибка: блок или упражнение не выбраны")
        return
    
    # Вычисляем вес если известен 1ПМ
    weight_kg = None
    if one_rm_kg and percent:
        weight_kg = round(one_rm_kg * percent / 100, 1)
    
    # Создаём запись упражнения
    exercise_entry = {
        "id": exercise_id,
        "name": exercise_name,
        "sets": sets,
        "reps_min": reps,
        "reps_max": reps,
        "one_rm_percent": percent,
        "rest_seconds": rest,
        "weight_kg": weight_kg,
        "notes": None,
    }
    
    # Добавляем в блок
    selected_blocks = data.get("selected_blocks", {})
    selected_blocks.setdefault(current_block, {"description": "", "exercises": []})
    selected_blocks[current_block]["exercises"].append(exercise_entry)
    
    await state.update_data(selected_blocks=selected_blocks)
    
    # Чистим временные данные
    for key in ["selected_exercise_id", "selected_exercise_name", "selected_exercise_1rm", "selected_exercise_defaults"]:
        await state.update_data({key: None})
    
    # Формируем итоговое сообщение
    weight_info = ""
    if weight_kg:
        weight_info = f"\n  💪 Вес: **{weight_kg} кг** (при {percent}% от {one_rm_kg}кг 1ПМ)"
    elif percent:
        weight_info = f"\n  📊 {percent}% от 1ПМ"
    
    rest_info = f"\n  ⏱ Отдых: {rest} сек" if rest else ""
    
    text = f"""
✅ **{exercise_name}** добавлено в блок!

📋 **Параметры:**
  • **{sets}x{reps}** подходы x повторения{weight_info}{rest_info}

Что дальше?
"""
    
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Добавить ещё упражнение", callback_data="create_search_ex")
    kb.button(text="✅ Завершить блок", callback_data="create_back_to_blocks")
    kb.button(text="🔙 К блокам", callback_data="create_back_to_blocks")
    kb.adjust(1)
    
    await message.answer(text, reply_markup=kb.as_markup(), parse_mode="Markdown")
    
    
    for key in ["selected_exercise_id", "selected_exercise_name", "selected_exercise_1rm", "selected_exercise_defaults"]:
        await state.update_data({key: None})

    # Оставляем current_block, selected_blocks и т.д.
    # Переводим FSM в режим добавления/выбора упражнений в блоке
    await state.set_state(CreateWorkoutStates.adding_exercises)


# Редактирование параметров для только что выбранного упражнения
@workouts_router.callback_query(F.data == "create_configure_pending_ex")
async def create_configure_pending_ex(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    pending = data.get('pending_exercise')
    if not pending:
        await callback.answer("Контекст потерян", show_alert=True)
        return
    # начинаем диалог: запрос подходов
    await state.update_data(config_step="sets")
    await callback.message.edit_text("Введите количество подходов (целое число), или 'пропустить' чтобы добавить без параметров:")
    await state.set_state(CreateWorkoutStates.configuring_exercise)
    await callback.answer()

# подтвердить добавление без параметров
@workouts_router.callback_query(F.data == "create_confirm_add_pending_ex")
async def create_confirm_add_pending_ex(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    pending = data.get('pending_exercise')
    if not pending:
        await callback.answer("Контекст потерян", show_alert=True)
        return
    cur = pending['block']
    sel = data.get('selected_blocks', {})
    sel.setdefault(cur, {"description": "", "exercises": []})
    sel[cur]['exercises'].append({
        "id": pending['id'],
        "name": pending['name'],
        "sets": None,
        "reps_min": None,
        "reps_max": None,
        "one_rm_percent": None,
        "rest_seconds": None
    })
    # чистим pending
    await state.update_data(selected_blocks=sel)
    await state.update_data(pending_exercise=None)
    await callback.message.edit_text(f"✅ Упражнение *{pending['name']}* добавлено в блок.", parse_mode="Markdown")
    await _show_block_selection(callback.message, state)
    await callback.answer()


# Обработка текстового ввода параметров для pending exercise
@workouts_router.message(StateFilter(CreateWorkoutStates.configuring_exercise))
async def configuring_pending_ex_input(message: Message, state: FSMContext):
    text = message.text.strip().lower()
    data = await state.get_data()
    pending = data.get('pending_exercise')
    if not pending:
        await message.answer("Контекст потерян.")
        await state.clear()
        return
    step = data.get('config_step')
    # шаг: sets -> reps -> percent -> rest -> confirm
    if step == "sets":
        if text in ("пропустить", "skip", "-"):
            # добавить без параметров
            sel = data.get('selected_blocks', {})
            cur = pending['block']
            sel.setdefault(cur, {"description": "", "exercises": []})
            sel[cur]['exercises'].append({
                "id": pending['id'],
                "name": pending['name'],
                "sets": None,
                "reps_min": None,
                "reps_max": None,
                "one_rm_percent": None,
                "rest_seconds": None
            })
            await state.update_data(selected_blocks=sel)
            await state.update_data(pending_exercise=None)
            await message.answer("Добавлено без параметров.")
            await _show_block_selection(message, state)
            return
        try:
            sets = int(text)
            await state.update_data(config_sets=sets, config_step="reps")
            await message.answer("Введите количество повторов (одиночное число или диапазон через '-': например '8' или '8-12'):")
            return
        except ValueError:
            await message.answer("Введите целое число для подходов или 'пропустить'.")
            return
    if step == "reps":
        # парсим reps
        if "-" in text:
            try:
                a, b = text.split("-", 1)
                rmin = int(a.strip())
                rmax = int(b.strip())
            except Exception:
                await message.answer("Неверный формат диапазона. Пример: 8-12")
                return
        else:
            try:
                rmin = rmax = int(text)
            except Exception:
                await message.answer("Введите число повторов или диапазон 8-12.")
                return
        await state.update_data(config_reps_min=rmin, config_reps_max=rmax, config_step="percent")
        await message.answer("Укажите % от 1ПМ (например 70) или напишите 'нет' чтобы пропустить:")
        return
    if step == "percent":
        if text in ("нет", "no", "пропустить", "skip", "-"):
            await state.update_data(config_one_rm_percent=None, config_step="rest")
            await message.answer("Укажите отдых между подходами в секундах (например 90) или 'пропустить':")
            return
        try:
            perc = int(text)
            if not (0 < perc <= 200):
                raise ValueError
            await state.update_data(config_one_rm_percent=perc, config_step="rest")
            await message.answer("Укажите отдых между подходами в секундах (например 90) или 'пропустить':")
            return
        except Exception:
            await message.answer("Введите целое число процентов, например 70, или 'нет'.")
            return
    if step == "rest":
        if text in ("пропустить", "skip", "-"):
            rest = None
        else:
            try:
                rest = int(text)
            except Exception:
                await message.answer("Введите число секунд или 'пропустить'.")
                return
        # собираем и добавляем
        sel = data.get('selected_blocks', {})
        cur = pending['block']
        sel.setdefault(cur, {"description": "", "exercises": []})
        entry = {
            "id": pending['id'],
            "name": pending['name'],
            "sets": data.get('config_sets'),
            "reps_min": data.get('config_reps_min'),
            "reps_max": data.get('config_reps_max'),
            "one_rm_percent": data.get('config_one_rm_percent'),
            "rest_seconds": rest
        }
      


            # если указан percent, проверим есть ли 1ПМ у пользователя для этого упражнения
        # если указан percent, проверим есть ли 1ПМ у пользователя для этого упражнения
        if entry.get('one_rm_percent'):
            user = await db_manager.get_user_by_telegram_id(message.from_user.id)

            async with db_manager.pool.acquire() as conn:
                orm = await conn.fetchrow(
                    """
                    SELECT formula_average, calculation_method, tested_at
                    FROM one_rep_max
                    WHERE user_id = $1
                    AND exercise_id = $2
                    AND is_active = true
                    ORDER BY tested_at DESC
                    LIMIT 1
                    """,
                    user['id'], pending['id']
                )

            if not orm:
                # предложим пройти тест (зависит от модуля tests)
                kb = InlineKeyboardBuilder()
                kb.button(text="Пройти тест на 1ПМ", callback_data=f"start_1rm_test_for_{pending['id']}")
                kb.button(text="Добавить без %", callback_data="create_confirm_add_pending_ex")
                kb.button(text="🔙 К блокам", callback_data="create_back_to_blocks")
                kb.adjust(1)
                await message.answer(
                    "1ПМ для этого упражнения не найден — хотите пройти тест?",
                    reply_markup=kb.as_markup()
                )
                return
            else:
                one_rm_value = orm["formula_average"]
                method = orm["calculation_method"]
                tested_at = orm["tested_at"]
                logger.info(
                    f"✅ Найден 1ПМ={one_rm_value} (метод={method}, дата={tested_at}) "
                    f"для user_id={user['id']}, exercise_id={pending['id']}"
                )

        # добавляем упражнение в текущий блок
        sel[cur]['exercises'].append(entry)
        await state.update_data(selected_blocks=sel)
        await state.update_data(pending_exercise=None)

        # чистим временные конфиги
        for k in [
            "config_step",
            "config_sets",
            "config_reps_min",
            "config_reps_max",
            "config_one_rm_percent",
        ]:
            await state.update_data({k: None})

        await message.answer(f"✅ Упражнение {entry['name']} добавлено в {cur}.")
        await _show_block_selection(message, state)
        return
        


# Обработчик кнопки запуска теста 1РМ (ссылка в тестовый модуль)
@workouts_router.callback_query(F.data.startswith("start_1rm_test_for_"))
async def start_1rm_test_for(callback: CallbackQuery, state: FSMContext):
    ex_id = _parse_int_suffix(callback.data)
    if ex_id is None:
        await callback.answer("Некорректно", show_alert=True)
        return
    # перенаправляем пользователя на модуль тестов — предполагается, что он есть
    # ставим состояние, чтобы после теста вернуться: сохраняем контекст
    data = await state.get_data()
    await state.update_data(await_state_return={"after": "add_pending_after_1rm", "exercise_id": ex_id, "context": data})
    # предполагаем, что в handlers.tests есть функция start_1rm_test_from_handlers
    try:
        from . import tests as tests_module
        # если есть готовая функция для запуска 1rm теста — вызываем её (если нет, просто сообщаем)
        if hasattr(tests_module, "start_1rm_test_from_handlers"):
            await tests_module.start_1rm_test_from_handlers(callback, ex_id)
            await callback.answer()
            return
    except Exception:
        logger.info("Модуль tests не предоставляет start_1rm_test_from_handlers, отправим инструкцию")
    await callback.message.edit_text("Пожалуйста пройдите тест 1ПМ вручную (/start_1rm_test), затем вернитесь и добавьте упражнение.")
    await callback.answer()


# Подтвердить завершение создания — сохранить в БД
@workouts_router.callback_query(F.data == "create_finish")
async def create_finish(callback: CallbackQuery, state: FSMContext):
    try:
        data = await state.get_data()
        name = data.get('name')
        if not name:
            await callback.answer("Нет названия тренировки", show_alert=True)
            return

        selected = data.get('selected_blocks', {})
        total_exs = sum(len(b.get('exercises', [])) for b in selected.values())
        if total_exs == 0:
            await callback.answer("Добавьте хотя бы одно упражнение!", show_alert=True)
            return

        user = await db_manager.get_user_by_telegram_id(callback.from_user.id)

        async with db_manager.pool.acquire() as conn:
            wid = await conn.fetchval("""
                INSERT INTO workouts (name, description, created_by, created_at, is_active)
                VALUES ($1, $2, $3, now(), true)
                RETURNING id
            """, name, data.get('description', ''), user['id'])

            order = 0
            for phase, block in selected.items():
                for ex in block.get('exercises', []):
                    order += 1
                    await conn.execute("""
                        INSERT INTO workout_exercises 
                        (workout_id, exercise_id, phase, order_in_phase, sets, reps_min, reps_max, one_rm_percent, rest_seconds, notes)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    """, wid, ex['id'], phase, order,
                         ex.get('sets'), ex.get('reps_min'), ex.get('reps_max'),
                         ex.get('one_rm_percent'), ex.get('rest_seconds'), ex.get('notes'))

            unique = await conn.fetchval("SELECT unique_id FROM workouts WHERE id = $1", wid)

        await callback.message.edit_text(
            f"🎉 Тренировка создана! Код: `{unique}`\nУпражнений: {total_exs}",
            parse_mode="Markdown"
        )
        await state.clear()
        await callback.answer()

    except Exception as e:
        logger.exception("create_finish error: %s", e)
        await callback.answer("Ошибка при сохранении", show_alert=True)


# ----------------- START/FINISH FLOW (player) -----------------
@workouts_router.callback_query(F.data.startswith("start_workout_"))
async def start_workout(callback: CallbackQuery):
    wid = _parse_int_suffix(callback.data)
    if wid is None:
        await callback.answer("Некорректный ID", show_alert=True)
        return
    async with db_manager.pool.acquire() as conn:
        w = await conn.fetchrow("SELECT name FROM workouts WHERE id = $1", wid)
    if not w:
        await callback.answer("Тренировка не найдена", show_alert=True)
        return
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Завершил тренировку", callback_data=f"finish_workout_{wid}")
    kb.button(text="📋 Детали", callback_data=f"view_workout_{wid}")
    kb.adjust(1)
    await _safe_edit_or_send(callback.message, f"▶️ Начинаем: **{w['name']}**\n\nПосле выполнения нажмите «Завершил тренировку»", reply_markup=kb.as_markup(), parse_mode="Markdown")
    await callback.answer()

# @workouts_router.callback_query(F.data.startswith("finish_workout_"))
# async def finish_workout(callback: CallbackQuery, state: FSMContext):
#     wid = _parse_int_suffix(callback.data)
#     if wid is None:
#         await callback.answer()
#         return
#     await state.update_data(finishing_workout_id=wid)
#     await callback.message.edit_text("✅ Оцени тренировку по шкале 1-10 (RPE):")
#     await state.set_state(CreateWorkoutStates.waiting_rpe)
#     await callback.answer()

@workouts_router.callback_query(F.data.startswith("finish_workout_"))
async def finish_workout(callback: CallbackQuery, state: FSMContext):
    wid = _parse_int_suffix(callback.data)
    if wid is None:
        await callback.answer()
        return
    await state.update_data(finishing_workout_id=wid)
    await callback.message.edit_text("✅ Оцени тренировку по шкале 1-10 (RPE):")
    # убираем state – пусть обрабатывает player_workouts.py
    await state.clear()          # или вообще не трогаем state
    await callback.answer()

# ----------------- EDIT / DELETE -----------------
@workouts_router.callback_query(F.data.startswith("edit_workout_"))
async def edit_workout(callback: CallbackQuery, state: FSMContext):
    wid = _parse_int_suffix(callback.data)
    if wid is None:
        await callback.answer("Некорректный ID", show_alert=True)
        return
    async with db_manager.pool.acquire() as conn:
        w = await conn.fetchrow("SELECT id, name, description, created_by FROM workouts WHERE id = $1", wid)
    if not w:
        await callback.answer("Не найдено", show_alert=True)
        return
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    if w['created_by'] != user['id']:
        await callback.answer("Только автор может редактировать", show_alert=True)
        return
    kb = InlineKeyboardBuilder()
    kb.button(text="✏️ Переименовать", callback_data=f"rename_workout_{wid}")
    kb.button(text="📝 Изменить описание", callback_data=f"change_desc_workout_{wid}")
    kb.button(text="🗑️ Удалить", callback_data=f"delete_workout_{wid}")
    kb.button(text="🔙 К тренировке", callback_data=f"view_workout_{wid}")
    kb.adjust(1)
    await _safe_edit_or_send(callback.message, f"✏️ Редактирование: {w['name']}", reply_markup=kb.as_markup())
    await callback.answer()

@workouts_router.callback_query(F.data.startswith("delete_workout_"))
async def delete_workout(callback: CallbackQuery):
    wid = _parse_int_suffix(callback.data)
    if wid is None:
        await callback.answer("Некорректный ID", show_alert=True)
        return
    try:
        async with db_manager.pool.acquire() as conn:
            await conn.execute("UPDATE workouts SET is_active = false WHERE id = $1", wid)
        await callback.message.edit_text("✅ Тренировка удалена.")
        await callback.answer()
    except Exception as e:
        logger.exception("delete_workout error: %s", e)
        await callback.answer("Ошибка", show_alert=True)


# Пропустить описание (legacy compatible)
@workouts_router.callback_query(F.data == "create_skip_description")
async def create_skip_description(callback: CallbackQuery, state: FSMContext):
    await state.update_data(description="")
    await _show_block_selection(callback.message, state)
    await callback.answer()


# Обработка текстового ввода (все состояния создания/редактирования)
# Эта функция вызывается из handle_all_text_messages в __init__.py
async def process_workout_text_input(message: Message, state: FSMContext):
    current = await state.get_state()
    data = await state.get_data()

    # -------------------------------------------------
    # 1. НАЗВАНИЕ ТРЕНИРОВКИ
    # -------------------------------------------------
    if current == CreateWorkoutStates.waiting_workout_name:
        name = message.text.strip()
        if len(name) < 3:
            await message.answer("Название слишком короткое (мин. 3 символа).")
            return
        await state.update_data(name=name)
        kb = InlineKeyboardBuilder()
        kb.button(text="Пропустить описание", callback_data="create_skip_description")
        kb.button(text="Отменить", callback_data="create_cancel")
        kb.adjust(2)
        await message.answer(
            f"Название сохранено: *{name}*\n\nВведите описание или нажмите «Пропустить»",
            reply_markup=kb.as_markup(),
            parse_mode="Markdown"
        )
        await state.set_state(CreateWorkoutStates.waiting_workout_description)
        return

    # -------------------------------------------------
    # 2. ОПИСАНИЕ ТРЕНИРОВКИ
    # -------------------------------------------------
    if current == CreateWorkoutStates.waiting_workout_description:
        await state.update_data(description=message.text.strip())
        await _show_block_selection(message, state)
        return

    # -------------------------------------------------
    # 3. ОПИСАНИЕ БЛОКА
    # -------------------------------------------------
    if current == CreateWorkoutStates.adding_block_description:
        desc = message.text.strip()
        cur_block = data.get('current_block')
        sel = data.get('selected_blocks', {})
        sel.setdefault(cur_block, {"description": "", "exercises": []})
        sel[cur_block]['description'] = desc
        await state.update_data(selected_blocks=sel)
        await message.answer("Описание блока сохранено.")
        await _show_block_selection(message, state)
        return

    # -------------------------------------------------
    # 4. ПОИСК УПРАЖНЕНИЯ В БЛОКЕ
    # -------------------------------------------------
    if current == "searching_exercise_for_block":
        q = message.text.strip().lower()
        async with db_manager.pool.acquire() as conn:
            exs = await conn.fetch("""
                SELECT id, name, category, muscle_group
                FROM exercises
                WHERE lower(name) LIKE $1 OR lower(category) LIKE $1 OR lower(muscle_group) LIKE $1
                ORDER BY name
                LIMIT 20
            """, f"%{q}%")
        if not exs:
            await message.answer("По запросу ничего не найдено.")
            return
        kb = InlineKeyboardBuilder()
        for e in exs:
            cat = e.get('category') or "Без категории"
            kb.button(text=f"{e['name']} ({cat})", callback_data=f"create_add_ex_{e['id']}")
        kb.button(text="Поиск упражнения", callback_data="workout_start_search")
        kb.button(text="К блокам", callback_data="create_back_to_blocks")
        kb.adjust(1)
        await message.answer(f"Найдено: {len(exs)}", reply_markup=kb.as_markup())
        return

    # -------------------------------------------------
    # 5. КОНФИГУРАЦИЯ ПАРАМЕТРОВ УПРАЖНЕНИЯ (configuring_exercise)
    # -------------------------------------------------
    if current == CreateWorkoutStates.configuring_exercise:
        text = message.text.strip().lower()
        pending = data.get('pending_exercise')
        if not pending:
            await message.answer("Контекст потерян. Начните заново.")
            await state.clear()
            return

        step = data.get('config_step')

        # === ПОДХОДЫ (sets) ===
        if step == "sets":
            if text in ("пропустить", "skip", "-", "нет"):
                await _add_exercise_without_params(state, pending, message)
                return
            try:
                sets = int(text)
                if sets <= 0:
                    raise ValueError
                await state.update_data(config_sets=sets, config_step="reps")
                await message.answer("Введите количество повторов (например: 8 или 8-12):")
                return
            except ValueError:
                await message.answer("Введите целое число (например: 3) или «пропустить».")
                return

        # === ПОВТОРЫ (reps) ===
        if step == "reps":
            if "-" in text:
                try:
                    a, b = text.split("-", 1)
                    rmin = int(a.strip())
                    rmax = int(b.strip())
                    if rmin <= 0 or rmax < rmin:
                        raise ValueError
                except Exception:
                    await message.answer("Неверный диапазон. Пример: 8-12")
                    return
            else:
                try:
                    rmin = rmax = int(text)
                    if rmin <= 0:
                        raise ValueError
                except Exception:
                    await message.answer("Введите число повторов (например: 10) или диапазон 8-12.")
                    return
            await state.update_data(config_reps_min=rmin, config_reps_max=rmax, config_step="percent")
            await message.answer("Укажите % от 1ПМ (например: 70) или напишите «нет»:")
            return

        # === % ОТ 1ПМ (percent) ===
        if step == "percent":
            if text in ("нет", "no", "пропустить", "skip", "-"):
                await state.update_data(config_one_rm_percent=None, config_step="rest")
                await message.answer("Отдых между подходами в секундах (например: 90) или «пропустить»:")
                return
            try:
                perc = int(text)
                if not (1 <= perc <= 200):
                    raise ValueError
                await state.update_data(config_one_rm_percent=perc, config_step="rest")
                await message.answer("Отдых между подходами в секундах (например: 90) или «пропустить»:")
                return
            except Exception:
                await message.answer("Введите число от 1 до 200 или «нет».")
                return

        # === ОТДЫХ (rest) ===
        if step == "rest":
            if text in ("пропустить", "skip", "-", "нет"):
                rest = None
            else:
                try:
                    rest = int(text)
                    if rest < 0:
                        raise ValueError
                except Exception:
                    await message.answer("Введите число секунд (например: 90) или «пропустить».")
                    return

            # === ПРОВЕРКА 1ПМ ===
            if data.get('config_one_rm_percent'):
                user = await db_manager.get_user_by_telegram_id(message.from_user.id)
                async with db_manager.pool.acquire() as conn:
                    orm = await conn.fetchrow(
                        "SELECT value FROM one_rep_max WHERE user_id = $1 AND exercise_id = $2",
                        user['id'], pending['id']
                    )
                if not orm:
                    kb = InlineKeyboardBuilder()
                    kb.button(text="Пройти тест 1ПМ", callback_data=f"start_1rm_test_for_{pending['id']}")
                    kb.button(text="Добавить без %", callback_data="create_confirm_add_pending_ex")
                    kb.button(text="К блокам", callback_data="create_back_to_blocks")
                    kb.adjust(1)
                    await message.answer(
                        "1ПМ для этого упражнения не найден — хотите пройти тест?",
                        reply_markup=kb.as_markup()
                    )
                    return

            # === ДОБАВЛЕНИЕ С ПАРАМЕТРАМИ ===
            await _add_exercise_with_params(state, pending, rest, message)
            return

    # -------------------------------------------------
    # 6. РУЧНОЕ ДОБАВЛЕНИЕ УПРАЖНЕНИЯ
    # -------------------------------------------------
    if current == CreateWorkoutStates.manual_exercise_input:
        text = message.text.strip()
        manual = data.get("manual_exercises", [])
        manual.append(text)
        await state.update_data(manual_exercises=manual)

        await message.answer(f"Добавлено:\n\n{text}")

        kb = InlineKeyboardBuilder()
        kb.button(text="Добавить ещё", callback_data="manual_add_exercise")
        kb.button(text="Назад", callback_data="back_to_constructor")
        kb.adjust(1)
        await message.answer("Что дальше?", reply_markup=kb.as_markup())
        await state.set_state(CreateWorkoutStates.adding_exercises)
        return

    # -------------------------------------------------
    # 7. RPE ПОСЛЕ ЗАВЕРШЕНИЯ ТРЕНИРОВКИ
    # -------------------------------------------------
    # if current == CreateWorkoutStates.waiting_rpe:
    #     try:
    #         rpe = int(message.text.strip())
    #         if not 1 <= rpe <= 10:
    #             raise ValueError
    #         wid = data.get("finishing_workout_id")
    #         async with db_manager.pool.acquire() as conn:
    #             await conn.execute(
    #                 """
    #                 INSERT INTO workout_completions (workout_id, user_id, rpe, completed_at)
    #                 VALUES ($1, (SELECT id FROM users WHERE telegram_id = $2), $3, now())
    #                 """,
    #                 wid, message.from_user.id, rpe
    #             )
    #         await message.answer(f"RPE {rpe} сохранено! Тренировка завершена.")
    #         await state.clear()
    #     except Exception:
    #         await message.answer("Введите число от 1 до 10.")
    #     return

    # -------------------------------------------------
    # FALLBACK
    # -------------------------------------------------
    await message.answer("Я не ожидал этот ввод. Используйте кнопки.")


# ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
# ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←

# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===

async def _add_exercise_without_params(state: FSMContext, pending: dict, message: Message):
    data = await state.get_data()
    cur = pending['block']
    sel = data.get('selected_blocks', {})
    sel.setdefault(cur, {"description": "", "exercises": []})
    sel[cur]['exercises'].append({
        "id": pending['id'],
        "name": pending['name'],
        "sets": None, "reps_min": None, "reps_max": None,
        "one_rm_percent": None, "rest_seconds": None
    })
    await state.update_data(selected_blocks=sel, pending_exercise=None)
    for key in ["config_step", "config_sets", "config_reps_min", "config_reps_max", "config_one_rm_percent"]:
        await state.update_data({key: None})
    await message.answer(f"Упражнение *{pending['name']}* добавлено без параметров.", parse_mode="Markdown")
    await _show_block_selection(message, state)






# handlers/workouts.py (добавь этот код в конец файла, перед register_workout_handlers)



# === ОБРАБОТКА ВВОДА ПАРАМЕТРОВ ===

@workouts_router.message(StateFilter(CreateWorkoutStates.configuring_exercise))
async def process_param_input(message: Message, state: FSMContext):
    text = message.text.strip()
    data = await state.get_data()
    ex_id = data.get("pending_ex_id")
    ex_name = data.get("pending_ex_name")
    block = data.get("pending_ex_block")
    one_rm = data.get("pending_one_rm")

    if not all([ex_id, ex_name, block]):
        await message.answer("Контекст потерян. Начните заново.")
        await state.clear()
        return

    parts = text.split()
    if len(parts) != 4:
        await message.answer("Неверный формат. Пример: `3 10 75 90` или `3 10 - 90`")
        return

    try:
        sets = int(parts[0])
        reps = int(parts[1])
        percent = parts[2]
        rest = int(parts[3])

        if sets <= 0 or reps <= 0 or rest < 0:
            raise ValueError

        one_rm_percent = None
        if percent != "-":
            one_rm_percent = int(percent)
            if not (0 < one_rm_percent <= 200):
                raise ValueError

    except ValueError:
        await message.answer("Неверные числа. Подходы/повторы/%/отдых должны быть положительными целыми.")
        return

    # Формируем запись
    entry = {
        "id": ex_id,
        "name": ex_name,
        "sets": sets,
        "reps_min": reps,
        "reps_max": reps,
        "one_rm_percent": one_rm_percent,
        "rest_seconds": rest
    }

    # Добавляем в блок
    selected = data.get("selected_blocks", {})
    selected.setdefault(block, {"description": "", "exercises": []})
    selected[block]["exercises"].append(entry)
    await state.update_data(selected_blocks=selected)

    # Формируем сообщение
    param_text = f"{sets}×{reps}"
    if one_rm_percent:
        if one_rm:
            weight = round(one_rm * one_rm_percent / 100)
            param_text += f" ({weight} кг)"
        else:
            param_text += f" ({one_rm_percent}% от 1ПМ)"
    if rest > 0:
        param_text += f", отдых {rest} сек"

    await message.answer(f"**{ex_name}** добавлено: {param_text}")
    await _show_exercises_for_block(message, state)
    await state.clear()  # очищаем pending



@workouts_router.callback_query(F.data.startswith("use_in_workout_"))
async def add_exercise_with_params_start(callback: CallbackQuery, state: FSMContext):
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    if user['role'] not in ['trainer', 'coach', 'admin']:
        await callback.answer("Доступно только тренерам.", show_alert=True)
        return  # ← Выходим, не меняя состояние
    ex_id = int(callback.data.split("_")[-1])

    # Проверяем, что мы в контексте создания тренировки и добавления упражнений в блок
    current_state = await state.get_state()
    if current_state != CreateWorkoutStates.searching_exercise_for_block:
        await callback.answer("Добавление возможно только при создании тренировки.", show_alert=True)
        return

    data = await state.get_data()
    # ищем откуда добавляем: ожидается, что при выборе блока был установлен searching_in_block или current_block
    block = data.get("searching_in_block") or data.get("current_block")
    if not block:
        await callback.answer("Контекст блока потерян.", show_alert=True)
        return

    # Получаем данные упражнения
    async with db_manager.pool.acquire() as conn:
        ex = await conn.fetchrow("SELECT id, name, test_type FROM exercises WHERE id = $1", ex_id)
    if not ex:
        await callback.answer("Упражнение не найдено.", show_alert=True)
        return

    # Проверяем есть ли 1ПМ (для силовых)
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    one_rm = None
    one_rm_method = None
    one_rm_tested_at = None
    if ex["test_type"] == "strength":
        async with db_manager.pool.acquire() as conn:
            orm = await conn.fetchrow(
                """
                SELECT formula_average, calculation_method, tested_at
                FROM one_rep_max
                WHERE user_id = $1
                  AND exercise_id = $2
                  AND is_active = true
                ORDER BY tested_at DESC
                LIMIT 1
                """,
                user["id"], ex_id
            )
        if orm:
            one_rm = orm["formula_average"]
            one_rm_method = orm["calculation_method"]
            one_rm_tested_at = orm["tested_at"]
            logger.info(
                "Найден 1ПМ=%s (метод=%s, дата=%s) для user_id=%s, exercise_id=%s",
                one_rm, one_rm_method, one_rm_tested_at, user["id"], ex_id
            )
        else:
            logger.info("1ПМ не найден для user_id=%s, exercise_id=%s", user["id"], ex_id)

    # --- ВАЖНО: сохраняем и pending_* (туда куда привыкла логика),
    # --- и selected_*/current_block (чтобы работал _finalize_exercise_for_create)
    await state.update_data(
        pending_ex_id=ex_id,
        pending_ex_name=ex["name"],
        pending_ex_block=block,
        pending_one_rm=one_rm,
        pending_one_rm_method=one_rm_method,
        pending_one_rm_tested_at=one_rm_tested_at,
        # записываем ключи, которые ждёт финализатор:
        selected_exercise_id=ex_id,
        selected_exercise_name=ex["name"],
        selected_exercise_1rm=one_rm,
        # current_block используется в _finalize_exercise_for_create
        current_block=block,
    )

    # Просим пользователя ввести параметры
    await callback.message.edit_text(
        f"**Добавление: {ex['name']}**\n\n"
        "Введите параметры в формате:\n"
        "`подходы повторы %1ПМ отдых_сек`\n\n"
        "Пример: `3 10 75 90`\n"
        "• 3 подхода\n"
        "• 10 повторов\n"
        f"• 75% от 1ПМ ({one_rm if one_rm is not None else '—'} кг если пройден тест)\n"
        "• 90 сек отдыха\n\n"
        "Или пропустите %1ПМ: `3 10 - 90`",
        parse_mode="Markdown"
    )

    # Переводим FSM в состояние ввода параметров
    await state.set_state(CreateWorkoutStates.configuring_exercise)
    await callback.answer()


# === ОБРАБОТКА ВВОДА ПАРАМЕТРОВ ===
async def process_param_input(message: Message, state: FSMContext):
    text = message.text.strip()
    data = await state.get_data()
    ex_id = data.get("pending_ex_id")
    ex_name = data.get("pending_ex_name")
    block = data.get("pending_ex_block")
    one_rm = data.get("pending_one_rm")

    if not all([ex_id, ex_name, block]):
        await message.answer("Контекст потерян. Начните заново.")
        await state.clear()
        return

    parts = text.split()
    if len(parts) != 4:
        await message.answer("Неверный формат. Пример: `3 10 75 90` или `3 10 - 90`")
        return

    try:
        sets = int(parts[0])
        reps = int(parts[1])
        percent = parts[2]
        rest = int(parts[3])

        if sets <= 0 or reps <= 0 or rest < 0:
            raise ValueError

        one_rm_percent = None
        if percent != "-":
            one_rm_percent = int(percent)
            if not (0 < one_rm_percent <= 200):
                raise ValueError

    except ValueError:
        await message.answer("Неверные числа. Подходы/повторы/%/отдых должны быть положительными целыми.")
        return

    # Формируем запись
    entry = {
        "id": ex_id,
        "name": ex_name,
        "sets": sets,
        "reps_min": reps,
        "reps_max": reps,
        "one_rm_percent": one_rm_percent,
        "rest_seconds": rest,
    }

    # Добавляем в блок
    selected = data.get("selected_blocks", {})
    selected.setdefault(block, {"description": "", "exercises": []})
    selected[block]["exercises"].append(entry)
    await state.update_data(selected_blocks=selected)

    # Формируем сообщение
    param_text = f"{sets}×{reps}"
    if one_rm_percent:
        if one_rm:
            weight = round(one_rm * one_rm_percent / 100)
            param_text += f" ({weight} кг)"
        else:
            param_text += f" ({one_rm_percent}% от 1ПМ)"
    if rest > 0:
        param_text += f", отдых {rest} сек"

    await message.answer(f"**{ex_name}** добавлено: {param_text}")
    await _show_exercises_for_block(message, state)
    await state.clear()  # очищаем pending





# === РЕГИСТРАЦИЯ ОБРАБОТЧИКА ПАРАМЕТРОВ ===

@workouts_router.message(StateFilter(CreateWorkoutStates.configuring_exercise))
async def handle_params_input(message: Message, state: FSMContext):
    """Обрабатывает ввод параметров: 3 10 75 90"""
    user = await db_manager.get_user_by_telegram_id(message.from_user.id)
    if user['role'] not in ['trainer', 'coach', 'admin']:
        await state.clear()  # Очищаем состояние, если игрок попал
        return  # Выходим без обработки, чтобы не вызвать цикл
    text = message.text.strip()
    data = await state.get_data()
    
    ex_id = data.get("selected_exercise_id")
    ex_name = data.get("selected_exercise_name")
    block = data.get("current_block")
    one_rm = data.get("pending_one_rm")
    
    if not all([ex_id, ex_name, block]):
        await message.answer("Контекст потерян. Начните заново.")
        await state.clear()
        return
    
    parts = text.split()
    
    if len(parts) != 4:
        await message.answer("Неверный формат. Пример: `3 10 75 90` или `3 10 - 90`", parse_mode="Markdown")
        return
    
    try:
        sets = int(parts[0])
        reps = int(parts[1])
        percent = parts[2]
        rest = int(parts[3])
        
        if sets <= 0 or reps <= 0 or rest < 0:
            raise ValueError
        
        one_rm_percent = None
        if percent != "-":
            one_rm_percent = int(percent)
            if not (0 < one_rm_percent <= 200):
                raise ValueError
    
    except ValueError:
        await message.answer("Неверные числа. Пример: `3 10 75 90`", parse_mode="Markdown")
        return
    
    # Формируем запись
    entry = {
        "id": ex_id,
        "name": ex_name,
        "sets": sets,
        "reps_min": reps,
        "reps_max": reps,
        "one_rm_percent": one_rm_percent,
        "rest_seconds": rest
    }
    
    # Добавляем в блок
    selected = data.get("selected_blocks", {})
    selected.setdefault(block, {"description": "", "exercises": []})
    selected[block]["exercises"].append(entry)
    
    await state.update_data(selected_blocks=selected)
    
    # Формируем сообщение
    param_text = f"{sets}×{reps}"
    
    if one_rm_percent:
        if one_rm:
            weight = round(one_rm * one_rm_percent / 100)
            param_text += f" ({weight} кг)"
        else:
            param_text += f" ({one_rm_percent}% от 1ПМ)"
    
    if rest > 0:
        param_text += f", отдых {rest} сек"
    
    await message.answer(f"**{ex_name}** добавлено: {param_text}", parse_mode="Markdown")
    
    await _show_exercises_for_block(message, state)
    await state.clear()




@workouts_router.callback_query(F.data.startswith("use_in_workout_"))
async def use_in_workout_with_params(callback: CallbackQuery, state: FSMContext):
    user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
    if user['role'] not in ['trainer', 'coach', 'admin']:
        await callback.answer("Доступно только тренерам.", show_alert=True)
        return  # Выходим без установки состояния
    logger.info("=== use_in_workout_with_params: START ===")
    logger.info("callback.data = %s", callback.data)
    logger.info("state = %s", await state.get_state())
    ex_id = int(callback.data.split("_")[-1])
    
    if (await state.get_state()) != CreateWorkoutStates.searching_exercise_for_block:
        await callback.answer("Только при создании тренировки.", show_alert=True)
        return

    data = await state.get_data()
    block = data.get("searching_in_block")
    if not block:
        await callback.answer("Ошибка: блок не выбран.", show_alert=True)
        return

    async with db_manager.pool.acquire() as conn:
        ex = await conn.fetchrow("SELECT name, test_type FROM exercises WHERE id = $1", ex_id)
    if not ex:
        await callback.answer("Упражнение не найдено.", show_alert=True)
        return

    # ← ИСПРАВЛЕНО: правильные ключи
    await state.update_data(
        selected_exercise_id=ex_id,
        selected_exercise_name=ex["name"],
        current_block=block
    )

    await callback.message.edit_text(
        f"**Добавление: {ex['name']}**\n\n"
        "Введите параметры:\n"
        "`подходы повторы %1ПМ отдых`\n\n"
        "Пример: `3 10 75 90`\n"
        "Или без %: `3 10 - 90`",
        parse_mode="Markdown"
    )
    await state.set_state(CreateWorkoutStates.configuring_exercise)
    await callback.answer()



async def process_param_input(message: Message, state: FSMContext):
    user = await db_manager.get_user_by_telegram_id(message.from_user.id)
    if user['role'] not in ['trainer', 'coach', 'admin']:
        await state.clear()  # Очищаем, чтобы не залипало
        return  # Выходим, прерывая цикл
    text = message.text.strip()
    data = await state.get_data()
    ex_id = data.get("pending_ex_id")
    ex_name = data.get("pending_ex_name")
    block = data.get("pending_ex_block")

    if not all([ex_id, ex_name, block]):
        await message.answer("Ошибка. Начните заново.")
        await state.clear()
        return

    parts = text.split()
    if len(parts) != 4:
        await message.answer("Нужно 4 значения: `3 10 75 90`")
        return

    try:
        sets = int(parts[0])
        reps = int(parts[1])
        percent = parts[2]
        rest = int(parts[3])
        if sets <= 0 or reps <= 0 or rest < 0:
            raise ValueError
        one_rm_percent = None if percent == "-" else int(percent)
        if one_rm_percent and not (1 <= one_rm_percent <= 200):
            raise ValueError
    except:
        await message.answer("Неверный формат. Пример: `3 10 75 90`")
        return

    # Добавляем в блок
    selected = data.get("selected_blocks", {})
    selected.setdefault(block, {"description": "", "exercises": []})
    selected[block]["exercises"].append({
        "id": ex_id,
        "name": ex_name,
        "sets": sets,
        "reps_min": reps,
        "reps_max": reps,
        "one_rm_percent": one_rm_percent,
        "rest_seconds": rest
    })
    await state.update_data(selected_blocks=selected)

    param_text = f"{sets}×{reps}"
    if one_rm_percent:
        param_text += f" ({one_rm_percent}%)"
    if rest > 0:
        param_text += f", отдых {rest}с"

    await message.answer(f"**{ex_name}** добавлено: {param_text}")
    await _show_exercises_for_block(message, state)
    await state.clear()
#----------------- REGISTER -----------------
def register_workout_handlers(dp):
    #dp.include_router(workouts_router)
    logger.info("🏋️ Обработчики тренировок зарегистрированы")


__all__ = ["workouts_router", "register_workout_handlers", "process_workout_text_input"]