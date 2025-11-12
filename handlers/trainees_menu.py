# handlers/trainees_menu.py - УЛУЧШЕННОЕ МЕНЮ ПОДОПЕЧНЫХ
# ✅ Кликабельное меню с функциями управления тренировками и тестами

import logging
from typing import Optional, List
from datetime import datetime

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import db_manager
from states.team_states import JoinTeamStates

logger = logging.getLogger(__name__)

trainees_router = Router(name="trainees_menu")

# ===== УРОВЕНЬ 1: СПИСОК ПОДОПЕЧНЫХ =====

@trainees_router.callback_query(F.data == "my_trainees")
async def show_trainees_list(callback: CallbackQuery, state: FSMContext):
    await state.clear()  # Очистить любой State
     # ✅ DEBUG ЛОГ ДЛЯ ОТЛАДКИ
    logger.info(f"🟢🟢🟢 show_trainees_list ВЫЗВАНА! callback.data={callback.data}")
    
    
    logger.info(f"show_trainees_list for coach {callback.from_user.id}")
    
    try:
        # ✓ ИСПРАВЛЕНО: используем callback.from_user.id НАПРЯМУЮ
        async with db_manager.pool.acquire() as conn:
            # Получаем всех подопечных тренера
            trainees = await conn.fetch("""
                SELECT id, first_name, last_name, level, specialization, phone
                FROM individual_students
                WHERE coach_telegram_id = $1 AND is_active = true
                ORDER BY first_name ASC
            """, callback.from_user.id)  # ← ИСПРАВЛЕНО!
            
            if not trainees:
                kb = InlineKeyboardBuilder()
                kb.button(text="➕ Добавить подопечного", callback_data="add_trainee")
                kb.button(text="🔙 В меню", callback_data="teams_menu")
                kb.adjust(1)
                
                await callback.message.edit_text(
                    "📋 **Мои подопечные**\n\n"
                    "У вас пока нет подопечных.\n"
                    "Добавьте первого подопечного!",
                    reply_markup=kb.as_markup(),
                    parse_mode="Markdown"
                )
                await callback.answer()
                return
            
            # Формируем текст списка
            text = f"📋 **Мои подопечные ({len(trainees)})**\n\n"
            
            kb = InlineKeyboardBuilder()
            
            for trainee in trainees:
                full_name = f"{trainee['first_name']} {trainee['last_name'] or ''}".strip()
                level = trainee['level'] or 'N/A'
                
                text += f"👤 **{full_name}** ({level})\n"
                if trainee['specialization']:
                    text += f"   Специализация: {trainee['specialization']}\n"
                if trainee['phone']:
                    text += f"   📱 {trainee['phone']}\n"
                text += "\n"
                
                kb.button(
                    text=f"👤 {full_name}",
                    callback_data=f"trainee_menu_{trainee['id']}"
                )
            
            kb.button(text="➕ Добавить подопечного", callback_data="add_trainee")
            kb.button(text="🔙 В меню", callback_data="teams_menu")
            kb.adjust(1)
            
            await callback.message.edit_text(
                text,
                reply_markup=kb.as_markup(),
                parse_mode="Markdown"
            )
            await callback.answer()
            logger.info(f"✅ Показано {len(trainees)} подопечных")
    
    except Exception as e:
        logger.exception(f"❌ Ошибка в show_trainees_list: {e}")
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


# ===== УРОВЕНЬ 2: МЕНЮ КОНКРЕТНОГО ПОДОПЕЧНОГО =====

@trainees_router.callback_query(F.data.startswith("trainee_menu_"))
async def trainee_detail_menu(callback: CallbackQuery, state: FSMContext):
    """Меню управления конкретным подопечным"""
    logger.info(f"trainee_detail_menu: {callback.data}")
    
    try:
        # ✅ ИСПРАВЛЕНО:
        trainee_id = int(callback.data.split("_")[2])
        
        
        async with db_manager.pool.acquire() as conn:
            trainee = await conn.fetchrow("""
                SELECT id, first_name, last_name, level, specialization, phone
                FROM individual_students
                WHERE id = $1
            """, trainee_id)
            
            if not trainee:
                await callback.answer("❌ Подопечный не найден", show_alert=True)
                return
            
            full_name = f"{trainee['first_name']} {trainee['last_name'] or ''}".strip()
            
            # ✅ ИСПРАВЛЕНО: использовать правильные таблицы
            workouts_count = await conn.fetchval(
                "SELECT COUNT(*) FROM workout_individual_students WHERE student_id = $1",
                trainee_id
            )
            
            # ✅ СТАЛО:
            tests_count = await conn.fetchval(
                "SELECT COUNT(*) FROM test_set_participants WHERE user_id = $1",
                trainee_id
            )
            
            # Формируем текст
            text = f"👤 **{full_name}**\n\n"
            text += f"📊 **Статистика:**\n"
            text += f"   🏋️ Назначено тренировок: {workouts_count or 0}\n"
            text += f"   🧪 Назначено тестов: {tests_count or 0}\n"
            if trainee['level']:
                text += f"   📈 Уровень: {trainee['level']}\n"
            if trainee['specialization']:
                text += f"   🎯 Специализация: {trainee['specialization']}\n"
            
            kb = InlineKeyboardBuilder()
            kb.button(
                text="📊 Активные назначения",
                callback_data=f"trainee_assignments_{trainee_id}"
            )
            kb.button(text="🔙 К списку", callback_data="my_trainees")
            kb.adjust(1)
            
            await state.update_data(current_trainee_id=trainee_id, current_trainee_name=full_name)
            
            await callback.message.edit_text(
                text,
                reply_markup=kb.as_markup(),
                parse_mode="Markdown"
            )
            await callback.answer()
            logger.info(f"✅ Меню подопечного {full_name}")
    
    except ValueError as e:
        logger.error(f"❌ Ошибка парсинга trainee_id: {e}")
        await callback.answer("❌ Ошибка при обработке запроса", show_alert=True)
    except Exception as e:
        logger.exception(f"❌ Ошибка в trainee_detail_menu: {e}")
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)




# ===== УРОВЕНЬ 3А: ОТПРАВКА ТРЕНИРОВКИ =====

@trainees_router.callback_query(F.data.startswith("send_workout_"))
async def send_workout_to_trainee(callback: CallbackQuery, state: FSMContext):
    """Выбрать тренировку для отправки подопечному"""
    logger.info(f"send_workout_to_trainee: {callback.data}")
    
    try:
        trainee_id = int(callback.data.split("_")[2])
        
        user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
        
        async with db_manager.pool.acquire() as conn:
            # Получаем все тренировки тренера
            workouts = await conn.fetch("""
                SELECT id, name, unique_id, created_at
                FROM workouts
                WHERE created_by = $1 AND is_active = true
                ORDER BY created_at DESC
                LIMIT 10
            """, user['id'])
            
            if not workouts:
                await callback.answer("❌ У вас нет тренировок", show_alert=True)
                return
            
            text = "🏋️ **Выберите тренировку для отправки:**\n\n"
            
            kb = InlineKeyboardBuilder()
            
            for workout in workouts:
                text += f"• {workout['name']}\n"
                kb.button(
                    text=f"📤 {workout['name'][:20]}",
                    callback_data=f"confirm_send_workout_{trainee_id}_{workout['id']}"
                )
            
            kb.button(text="🔙 Назад", callback_data=f"trainee_menu_{trainee_id}")
            kb.adjust(1)
            
            await callback.message.edit_text(
                text,
                reply_markup=kb.as_markup(),
                parse_mode="Markdown"
            )
            await callback.answer()
    
    except Exception as e:
        logger.exception(f"❌ Ошибка в send_workout_to_trainee: {e}")
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


@trainees_router.callback_query(F.data.startswith("confirm_send_workout_"))
async def confirm_send_workout(callback: CallbackQuery, state: FSMContext):
    """Подтвердить отправку тренировки"""
    logger.info(f"confirm_send_workout: {callback.data}")
    
    try:
        parts = callback.data.split("_")
        trainee_id = int(parts[3])
        workout_id = int(parts[4])
        
        async with db_manager.pool.acquire() as conn:
            # Проверяем существует ли уже такое назначение
            existing = await conn.fetchval("""
                SELECT id FROM workout_assignments
                WHERE trainee_id = $1 AND workout_id = $2 AND status = 'active'
            """, trainee_id, workout_id)
            
            if existing:
                await callback.answer("⚠️ Эта тренировка уже назначена подопечному", show_alert=True)
                return
            
            # Получаем информацию о тренировке
            workout = await conn.fetchrow("SELECT name FROM workouts WHERE id = $1", workout_id)
            
            # Создаём назначение
            await conn.execute("""
                INSERT INTO workout_assignments (trainee_id, workout_id, assigned_by, status, assigned_at)
                VALUES ($1, $2, $3, 'active', NOW())
            """, trainee_id, workout_id, callback.from_user.id)
            
            text = f"✅ **Тренировка успешно отправлена!**\n\n"
            text += f"📤 Тренировка: {workout['name']}\n"
            text += f"👤 Подопечному назначена\n\n"
            text += "Подопечный получит уведомление в Telegram"
            
            kb = InlineKeyboardBuilder()
            kb.button(text="🔙 К подопечному", callback_data=f"trainee_menu_{trainee_id}")
            kb.button(text="📤 Отправить ещё", callback_data=f"send_workout_{trainee_id}")
            kb.adjust(1)
            
            await callback.message.edit_text(
                text,
                reply_markup=kb.as_markup(),
                parse_mode="Markdown"
            )
            await callback.answer()
            logger.info(f"✅ Тренировка {workout['name']} назначена подопечному {trainee_id}")
    
    except Exception as e:
        logger.exception(f"❌ Ошибка в confirm_send_workout: {e}")
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


# ===== УРОВЕНЬ 3Б: НАЗНАЧЕНИЕ ТЕСТОВ =====

@trainees_router.callback_query(F.data.startswith("assign_test_"))
async def assign_test_to_trainee(callback: CallbackQuery, state: FSMContext):
    """Выбрать тест для назначения подопечному"""
    logger.info(f"assign_test_to_trainee: {callback.data}")
    
    try:
        trainee_id = int(callback.data.split("_")[2])
        
        user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
        
        async with db_manager.pool.acquire() as conn:
            # Получаем все тесты тренера (батареи)
            tests = await conn.fetch("""
                SELECT id, name, description
                FROM test_sets
                WHERE created_by = $1 AND is_active = true
                ORDER BY created_at DESC
                LIMIT 10
            """, user['id'])
            
            if not tests:
                await callback.answer("❌ У вас нет батарей тестов", show_alert=True)
                return
            
            text = "🧪 **Выберите тест для назначения:**\n\n"
            
            kb = InlineKeyboardBuilder()
            
            for test in tests:
                desc = test['description'][:20] if test['description'] else ''
                text += f"• {test['name']}\n"
                kb.button(
                    text=f"🧪 {test['name'][:18]}",
                    callback_data=f"confirm_assign_test_{trainee_id}_{test['id']}"
                )
            
            kb.button(text="🔙 Назад", callback_data=f"trainee_menu_{trainee_id}")
            kb.adjust(1)
            
            await callback.message.edit_text(
                text,
                reply_markup=kb.as_markup(),
                parse_mode="Markdown"
            )
            await callback.answer()
    
    except Exception as e:
        logger.exception(f"❌ Ошибка в assign_test_to_trainee: {e}")
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


@trainees_router.callback_query(F.data.startswith("confirm_assign_test_"))
async def confirm_assign_test(callback: CallbackQuery, state: FSMContext):
    """Подтвердить назначение теста"""
    logger.info(f"confirm_assign_test: {callback.data}")
    
    try:
        parts = callback.data.split("_")
        trainee_id = int(parts[3])
        test_id = int(parts[4])
        
        async with db_manager.pool.acquire() as conn:
            # Проверяем существует ли уже такое назначение
            existing = await conn.fetchval("""
                SELECT id FROM test_assignments
                WHERE trainee_id = $1 AND test_id = $2 AND status = 'active'
            """, trainee_id, test_id)
            
            if existing:
                await callback.answer("⚠️ Этот тест уже назначен подопечному", show_alert=True)
                return
            
            # Получаем информацию о тесте
            test = await conn.fetchrow("SELECT name FROM test_sets WHERE id = $1", test_id)
            
            # Создаём назначение
            await conn.execute("""
                INSERT INTO test_assignments (trainee_id, test_id, assigned_by, status, assigned_at)
                VALUES ($1, $2, $3, 'active', NOW())
            """, trainee_id, test_id, callback.from_user.id)
            
            text = f"✅ **Тест успешно назначен!**\n\n"
            text += f"🧪 Тест: {test['name']}\n"
            text += f"👤 Подопечному назначен\n\n"
            text += "Подопечный получит уведомление в Telegram"
            
            kb = InlineKeyboardBuilder()
            kb.button(text="🔙 К подопечному", callback_data=f"trainee_menu_{trainee_id}")
            kb.button(text="🧪 Назначить ещё", callback_data=f"assign_test_{trainee_id}")
            kb.adjust(1)
            
            await callback.message.edit_text(
                text,
                reply_markup=kb.as_markup(),
                parse_mode="Markdown"
            )
            await callback.answer()
            logger.info(f"✅ Тест {test['name']} назначен подопечному {trainee_id}")
    
    except Exception as e:
        logger.exception(f"❌ Ошибка в confirm_assign_test: {e}")
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


# ===== УРОВЕНЬ 3В: АКТИВНЫЕ НАЗНАЧЕНИЯ =====

@trainees_router.callback_query(F.data.startswith("trainee_assignments_"))
async def show_trainee_assignments(callback: CallbackQuery, state: FSMContext):
    """Показать все активные назначения подопечному"""
    logger.info(f"show_trainee_assignments: {callback.data}")
    
    try:
        trainee_id = int(callback.data.split("_")[2])
        
        
        async with db_manager.pool.acquire() as conn:
            trainee = await conn.fetchrow(
                "SELECT first_name, last_name FROM individual_students WHERE id = $1",
                trainee_id
            )
            
            # ✅ ИСПРАВЛЕНО: получаем тренировки из workout_individual_students
            workouts = await conn.fetch("""
                SELECT w.name, wis.created_at
                FROM workout_individual_students wis
                JOIN workouts w ON wis.workout_id = w.id
                WHERE wis.student_id = $1
                ORDER BY wis.created_at DESC
            """, trainee_id)
            
            # ✅ ИСПРАВЛЕНО: получаем тесты из test_set_participants
            tests = await conn.fetch("""
                SELECT ts.name, tsp.created_at
                FROM test_set_participants tsp
                JOIN test_sets ts ON tsp.test_set_id = ts.id
                WHERE tsp.user_id = $1
            """, trainee_id)
            
            full_name = f"{trainee['first_name']} {trainee['last_name'] or ''}".strip()
            
            text = f"📊 **Активные назначения для {full_name}**\n\n"
            
            if workouts:
                text += f"🏋️ **Тренировки ({len(workouts)}):**\n"
                for w in workouts:
                    text += f"  • {w['name']}\n"
                text += "\n"
            
            if tests:
                text += f"🧪 **Тесты ({len(tests)}):**\n"
                for t in tests:
                    text += f"  • {t['name']}\n"
                text += "\n"
            
            if not workouts and not tests:
                text += "Нет активных назначений\n"
            
            kb = InlineKeyboardBuilder()
            kb.button(text="🔙 Назад", callback_data=f"trainee_menu_{trainee_id}")
            kb.adjust(1)
            
            await callback.message.edit_text(
                text,
                reply_markup=kb.as_markup(),
                parse_mode="Markdown"
            )
            await callback.answer()
    
    except Exception as e:
        logger.exception(f"❌ Ошибка в show_trainee_assignments: {e}")
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)


# ===== РЕЗЕРВНЫЕ ОБРАБОТЧИКИ =====

@trainees_router.callback_query(F.data.startswith("edit_trainee_"))
async def edit_trainee(callback: CallbackQuery):
    """Редактировать подопечного (placeholder)"""
    await callback.answer("🔧 Функция редактирования в разработке", show_alert=True)


@trainees_router.callback_query(F.data.startswith("remove_trainee_"))
async def remove_trainee(callback: CallbackQuery):
    """Удалить подопечного (placeholder)"""
    await callback.answer("⚠️ Функция удаления в разработке", show_alert=True)


# ✅ СТАЛО (подключаем существующий обработчик):
@trainees_router.callback_query(F.data == "add_trainee")
async def add_trainee_redirect(callback: CallbackQuery, state: FSMContext):
    """Перенаправить на существующий обработчик добавления подопечного"""
    # Перенаправляем на стартовый экран добавления подопечного
    # Предполагается что в teams.py есть функция которая обрабатывает это
    await callback.message.edit_text(
        "📋 **Добавление подопечного**\n\n"
        "Выберите способ добавления:",
        reply_markup=InlineKeyboardBuilder()
        .button(text="🔗 По Telegram ID", callback_data="add_trainee_by_id")
        .button(text="📝 Ручной ввод", callback_data="add_trainee_manual")
        .button(text="🔙 Назад", callback_data="my_trainees")
        .adjust(1)
        .as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()






# # @traintes_router.callback_query(F.data == "back_to_main")
# async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):
#     """Вернуться в меню команд"""
#     await state.clear()
#     logger.info("🟢 back_to_main_menu triggered")
    
#     try:
#         kb = InlineKeyboardBuilder()
#         kb.button(text="🏗️ Создать команду", callback_data="create_team")
#         kb.button(text="👤 Добавить подопечного", callback_data="add_student")
#         kb.button(text="🏆 Мои команды", callback_data="my_teams")
#         kb.button(text="👥 Мои подопечные", callback_data="my_traintes")
#         kb.adjust(1)
        
#         await callback.message.edit_text(
#             "👥 **Командная система**\n\n"
#             "Ваша роль: Тренера\n\n"
#             "🎯 Возможности:\n"
#             "• 🏗️ Командные тренировки с общими целями\n"
#             "• 👨‍🏫 Индивидуальное тренерство и наставничество\n"
#             "• 📊 Мониторинг прогресса учеников в реальном времени\n"
#             "• 🔗 Система кодов приглашений для быстрого подключения\n"
#             "• 📈 Сравнительная статистика и мотивация\n\n"
#             "Выберите действие:",
#             reply_markup=kb.as_markup(),
#             parse_mode="Markdown"
#         )
#         await callback.answer()
#         logger.info("✅ Вернулись в меню команд")
    
#     except Exception as e:
#         logger.exception(f"❌ Ошибка в back_to_main_menu: {e}")
#         await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)