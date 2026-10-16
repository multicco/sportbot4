# ✅ Все callback_data изменены на уникальные с префиксом trainee_
# ✅ Не конфликтуют с teams.py

import logging
from typing import Optional, List
from datetime import datetime

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import StateFilter

from states.workout_assignment_states import AssignWorkoutStates
from database import db_manager

logger = logging.getLogger(__name__)

trainees_router = Router(name="trainees_menu")


# async def debug_all_callbacks(callback: CallbackQuery):
#     logger.info(f"🔴 DEBUG: callback.data={callback.data}")
#     await callback.answer() 


from aiogram.fsm.state import State, StatesGroup

class AddTraineeStates(StatesGroup):
    waiting_first_name = State()
    waiting_last_name = State()
    waiting_specialization = State()
    waiting_level = State()
    waiting_telegram_id = State()



@trainees_router.callback_query(F.data == "add_trainee")
async def start_add_trainee_flow(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    kb = InlineKeyboardBuilder()
    kb.button(text="🆔 По Telegram ID", callback_data="add_trainee_by_id")
    kb.button(text="✍️ Ввести вручную", callback_data="add_trainee_manual")
    kb.button(text="📋 Пригласительная ссылка", callback_data="generate_trainee_invite")
    kb.button(text="🔙 Назад", callback_data="my_trainees")
    kb.adjust(1)

    await callback.message.edit_text(
        "🆕 **Добавление подопечного**\n\n"
        "Выберите способ добавления:",
        reply_markup=kb.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()


@trainees_router.message(AddTraineeStates.waiting_telegram_id)
async def process_trainee_telegram_id(message: Message, state: FSMContext):
    telegram_id_str = message.text.strip()

    if not telegram_id_str.isdigit():
        await message.answer("❌ ID должен содержать только цифры. Попробуйте ещё раз:")
        return

    telegram_id = int(telegram_id_str)

    # Проверяем, не добавлен ли уже
    existing = await db_manager.pool.fetchrow("""
        SELECT id FROM individual_students
        WHERE telegram_id = $1 AND coach_telegram_id = $2 AND is_active = true
    """, telegram_id, message.from_user.id)

    if existing:
        await message.answer("ℹ️ Этот подопечный уже у вас добавлен.")
        await state.clear()
        return

    # Добавляем
    await db_manager.pool.execute("""
        INSERT INTO individual_students (coach_telegram_id, telegram_id, first_name, level, is_active)
        VALUES ($1, $2, 'Пользователь', 'beginner', true)
        ON CONFLICT (coach_telegram_id, telegram_id)
        DO UPDATE SET is_active = true, first_name = 'Пользователь'
    """, message.from_user.id, telegram_id)

    await state.clear()
    kb = InlineKeyboardBuilder()
    kb.button(text="👥 К подопечным", callback_data="my_trainees")
    await message.answer("✅ Подопечный добавлен по Telegram ID!", reply_markup=kb.as_markup())


@trainees_router.callback_query(F.data == "add_trainee_by_id")
async def add_trainee_by_id(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddTraineeStates.waiting_telegram_id)
    kb = InlineKeyboardBuilder()
    kb.button(text="🔙 Назад", callback_data="add_trainee")
    await callback.message.edit_text(
        "🆔 **Добавление по Telegram ID**\n\n"
        "Введите Telegram ID подопечного (только цифры):\n\n"
        "💡 *Как узнать ID:* попросите подопечного написать боту @userinfobot",
        reply_markup=kb.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()



@trainees_router.callback_query(F.data == "generate_trainee_invite")
async def generate_trainee_invite(callback: CallbackQuery):
    import secrets
    from bot_instance import bot

    coach_id = callback.from_user.id
    access_code = secrets.token_urlsafe(8)[:8]

    # ✅ Добавляем тренера в users, если его нет
    await db_manager.pool.execute("""
        INSERT INTO users (telegram_id, first_name, role, is_active)
        VALUES ($1, 'Тренер', 'coach', true)
        ON CONFLICT (telegram_id) DO NOTHING
    """, coach_id)

    # ✅ Теперь вставляем invite
    await db_manager.pool.execute("""
        INSERT INTO coach_students (coach_id, student_id, invite_code, relationship_type, status)
        VALUES ($1, NULL, $2, 'personal', 'invited')
    """, coach_id, access_code)

    bot_username = (await bot.get_me()).username
    invite_link = f"https://t.me/{bot_username}?start=trainee_{access_code}"

    kb = InlineKeyboardBuilder()
    kb.button(text="📋 Скопировать код", callback_data=f"copy_trainee_code_{access_code}")
    kb.button(text="🔙 Назад", callback_data="add_trainee")
    kb.adjust(1)

    await callback.message.edit_text(
        f"📋 **Пригласительная ссылка для подопечного**\n\n"
        f"🔗 **Ссылка:** `{invite_link}`\n\n"
        f"🆔 **Код:** `{access_code}`\n\n"
        f"Отправьте эту ссылку подопечному.",
        reply_markup=kb.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()




# ===== УРОВЕНЬ 1: СПИСОК ПОДОПЕЧНЫХ =====

@trainees_router.callback_query(F.data == "my_trainees")
async def show_trainees_list(callback: CallbackQuery, state: FSMContext):
    """Показать список подопечных тренера"""
    
    await state.clear()
    logger.info(f"🟢 show_trainees_list ВЫЗВАНА! callback.data={callback.data}")

    try:
        async with db_manager.pool.acquire() as conn:
            trainees = await conn.fetch("""
                SELECT id, first_name, last_name, level, specialization, phone
                FROM individual_students
                WHERE coach_telegram_id = $1 AND is_active = true
                ORDER BY first_name ASC
            """, callback.from_user.id)

            if not trainees:
                kb = InlineKeyboardBuilder()
                kb.button(text="➕ Добавить подопечного", callback_data="add_trainee")
                kb.button(text="🔙 В меню", callback_data="teams_menu")
                kb.adjust(1)

                await callback.message.edit_text(
                    "📋 **Мои подопечные**\n\n"
                    "У вас пока нет подопечных.",
                    reply_markup=kb.as_markup(),
                    parse_mode="Markdown"
                )
                await callback.answer()
                return

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

                # ✅ УНИКАЛЬНЫЙ callback_data с префиксом trainee_
                kb.button(
                    text=f"👤 {full_name}",
                    callback_data=f"trainee_profile_{trainee['id']}"
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


# ===== УРОВЕНЬ 2: ПРОФИЛЬ ПОДОПЕЧНОГО =====

@trainees_router.callback_query(F.data.startswith("trainee_profile_"))
async def show_trainee_profile(callback: CallbackQuery, state: FSMContext):
    """Показать профиль подопечного"""
    
    await state.clear()
    
    try:
        trainee_id = int(callback.data.split("_")[-1])
        logger.info(f"🟢 show_trainee_profile: trainee_id={trainee_id}")

        async with db_manager.pool.acquire() as conn:
            trainee = await conn.fetchrow("""
                SELECT id, first_name, last_name, level, specialization, 
                       phone, birth_date, created_at, notes
                FROM individual_students
                WHERE id = $1 AND coach_telegram_id = $2 AND is_active = true
            """, trainee_id, callback.from_user.id)

            if not trainee:
                await callback.answer("❌ Подопечный не найден", show_alert=True)
                return

            workouts_count = await conn.fetchval("""
                SELECT COUNT(*) FROM workout_individual_students
                WHERE student_id = $1 AND is_active = true
            """, trainee_id)

            full_name = f"{trainee['first_name']} {trainee['last_name'] or ''}".strip()
            
            text = f"""👤 **{full_name}**

🎯 **Специализация:** {trainee['specialization'] or 'не указана'}
📊 **Уровень:** {trainee['level'] or 'beginner'}
📱 **Телефон:** {trainee['phone'] or 'не указан'}
📅 **В профиле с:** {trainee['created_at'].strftime('%d.%m.%Y') if trainee['created_at'] else 'неизвестно'}

📊 **Статистика:**
   🏋️ Назначено тренировок: {workouts_count or 0}"""

            if trainee['notes']:
                text += f"\n📝 **Заметки:** {trainee['notes']}"

            kb = InlineKeyboardBuilder()
            kb.button(
                text="➕ Назначить тренировку",
                callback_data=f"trainee_assign_workout_{trainee_id}"
            )
            kb.button(
                text="📋 Тренировки",
                callback_data=f"trainee_workouts_{trainee_id}"
            )
            kb.button(
                text="📊 Статистика",
                callback_data=f"trainee_stats_{trainee_id}"
            )
            kb.button(
                text="🔙 К подопечным",
                callback_data="my_trainees"
            )
            kb.adjust(1)

            await callback.message.edit_text(
                text,
                reply_markup=kb.as_markup(),
                parse_mode="Markdown"
            )
            await callback.answer()
            logger.info(f"✅ Профиль подопечного {trainee_id} загружен")
            
    except ValueError:
        logger.error(f"❌ Ошибка парсинга trainee_id")
        await callback.answer("❌ Ошибка: неверный ID подопечного", show_alert=True)
    except Exception as e:
        logger.exception(f"❌ Ошибка в show_trainee_profile: {e}")
        await callback.answer("❌ Ошибка при загрузке профиля", show_alert=True)


# ===== УРОВЕНЬ 3: ТРЕНИРОВКИ ПОДОПЕЧНОГО =====

@trainees_router.callback_query(F.data.startswith("trainee_workouts_"))
async def show_trainee_workouts(callback: CallbackQuery, state: FSMContext):
    """Показать тренировки подопечного"""
    
    await state.clear()
    
    try:
        trainee_id = int(callback.data.split("_")[-1])
        logger.info(f"🟢 show_trainee_workouts: trainee_id={trainee_id}")

        async with db_manager.pool.acquire() as conn:
            trainee = await conn.fetchrow("""
                SELECT first_name, last_name
                FROM individual_students
                WHERE id = $1 AND coach_telegram_id = $2
            """, trainee_id, callback.from_user.id)

            if not trainee:
                await callback.answer("❌ Подопечный не найден", show_alert=True)
                return

            full_name = f"{trainee['first_name']} {trainee['last_name'] or ''}".strip()

            workouts = await conn.fetch("""
                SELECT w.id, w.name, w.description, w.difficulty_level,
                       w.estimated_duration_minutes, wis.assigned_at, wis.deadline, wis.notes
                FROM workouts w
                JOIN workout_individual_students wis ON w.id = wis.workout_id
                WHERE wis.student_id = $1 AND wis.is_active = true
                ORDER BY wis.assigned_at DESC
            """, trainee_id)

            text = f"📋 **Тренировки подопечного {full_name}**\n\n"
            kb = InlineKeyboardBuilder()

            if workouts:
                text += f"**Всего назначено: {len(workouts)}**\n\n"

                for workout in workouts:
                    difficulty_emoji = {
                        "beginner": "🟢",
                        "intermediate": "🟡",
                        "advanced": "🟠",
                        "expert": "🔴"
                    }.get(workout['difficulty_level'], "⚪")

                    text += f"{difficulty_emoji} **{workout['name']}**\n"

                    if workout['description']:
                        desc = workout['description'][:50]
                        if len(workout['description']) > 50:
                            desc += "..."
                        text += f"   _{desc}_\n"

                    if workout['estimated_duration_minutes']:
                        text += f"   ⏱️ {workout['estimated_duration_minutes']} мин\n"

                    if workout['deadline']:
                        text += f"   📅 До: {workout['deadline'].strftime('%d.%m.%Y')}\n"

                    text += "\n"

                    kb.button(
                        text=f"▶️ {workout['name'][:25]}",
                        callback_data=f"start_workout_{workout['id']}"
                    )
            else:
                text += "_У подопечного нет назначенных тренировок_\n\n"

            kb.button(text="🔙 К подопечному", callback_data=f"trainee_profile_{trainee_id}")
            kb.adjust(1)

            await callback.message.edit_text(
                text,
                reply_markup=kb.as_markup(),
                parse_mode="Markdown"
            )
            await callback.answer()

    except ValueError:
        logger.error(f"❌ Ошибка парсинга trainee_id")
        await callback.answer("❌ Ошибка: неверный ID", show_alert=True)
    except Exception as e:
        logger.exception(f"❌ Ошибка в show_trainee_workouts: {e}")
        await callback.answer("❌ Ошибка при загрузке тренировок", show_alert=True)


# ===== УРОВЕНЬ 3: СТАТИСТИКА ПОДОПЕЧНОГО =====

@trainees_router.callback_query(F.data.startswith("trainee_stats_"))
async def show_trainee_stats(callback: CallbackQuery, state: FSMContext):
    """Показать статистику подопечного"""
    
    await state.clear()
    
    try:
        trainee_id = int(callback.data.split("_")[-1])
        logger.info(f"🟢 show_trainee_stats: trainee_id={trainee_id}")

        async with db_manager.pool.acquire() as conn:
            trainee = await conn.fetchrow("""
                SELECT first_name, last_name, level, specialization, created_at
                FROM individual_students
                WHERE id = $1 AND coach_telegram_id = $2
            """, trainee_id, callback.from_user.id)

            if not trainee:
                await callback.answer("❌ Подопечный не найден", show_alert=True)
                return

            full_name = f"{trainee['first_name']} {trainee['last_name'] or ''}".strip()

            total_workouts = await conn.fetchval("""
                SELECT COUNT(*) FROM workout_individual_students
                WHERE student_id = $1 AND is_active = true
            """, trainee_id)

            text = f"""📊 **Статистика подопечного**

👤 **Имя:** {full_name}
🎯 **Специализация:** {trainee['specialization'] or 'не указана'}
📈 **Уровень:** {trainee['level']}
📅 **В профиле с:** {trainee['created_at'].strftime('%d.%m.%Y')}

**Статистика тренировок:**
   📋 Всего назначено: {total_workouts or 0}

⚠️ _Детальная статистика в разработке_"""

            kb = InlineKeyboardBuilder()
            kb.button(text="🔙 К подопечному", callback_data=f"trainee_profile_{trainee_id}")
            kb.button(text="👥 К подопечным", callback_data="my_trainees")
            kb.adjust(1)

            await callback.message.edit_text(
                text,
                reply_markup=kb.as_markup(),
                parse_mode="Markdown"
            )
            await callback.answer()

    except ValueError:
        logger.error(f"❌ Ошибка парсинга trainee_id")
        await callback.answer("❌ Ошибка: неверный ID", show_alert=True)
    except Exception as e:
        logger.exception(f"❌ Ошибка в show_trainee_stats: {e}")
        await callback.answer("❌ Ошибка при загрузке статистики", show_alert=True)


# ===== НАЗНАЧЕНИЕ ТРЕНИРОВОК ДЛЯ ПОДОПЕЧНЫХ =====

@trainees_router.callback_query(F.data.startswith("trainee_assign_workout_"))
async def trainee_start_assign_workout(callback: CallbackQuery, state: FSMContext):
    """Начать назначение тренировки подопечному"""
    
    try:
        trainee_id = int(callback.data.split("_")[-1])
        logger.info(f"🟢 trainee_start_assign_workout: trainee_id={trainee_id}")

        async with db_manager.pool.acquire() as conn:
            trainee = await conn.fetchrow("""
                SELECT first_name, last_name, specialization, level
                FROM individual_students
                WHERE id = $1 AND coach_telegram_id = $2 AND is_active = true
            """, trainee_id, callback.from_user.id)

            if not trainee:
                await callback.answer("❌ Подопечный не найден", show_alert=True)
                return

            full_name = f"{trainee['first_name']} {trainee['last_name'] or ''}".strip()

            # ✅ Сохраняем данные для подопечного
            await state.update_data(
                trainee_id=trainee_id,
                trainee_name=full_name,
                assignment_type='trainee'
            )
            
            # ✅ Устанавливаем состояние
            await state.set_state(AssignWorkoutStates.choosing_workout_method)

            # Красивое меню выбора способа
            kb = InlineKeyboardBuilder()
            kb.button(text="💪 Мои тренировки", callback_data="trainee_workout_method_my")
            kb.button(text="🔗 По коду", callback_data="trainee_workout_method_code")
            kb.button(text="🆕 Создать новую", callback_data="trainee_workout_method_create")
            kb.button(text="❌ Отмена", callback_data=f"trainee_profile_{trainee_id}")
            kb.adjust(1)

            text = f"""➕ **Назначение тренировки подопечному**

👤 **Подопечный:** {full_name}
🎯 **Специализация:** {trainee['specialization'] or 'не указана'}
📊 **Уровень:** {trainee['level']}

Выберите способ добавления тренировки:"""

            await callback.message.edit_text(
                text,
                reply_markup=kb.as_markup(),
                parse_mode="Markdown"
            )
            await callback.answer()
            logger.info(f"✅ Меню назначения открыто для подопечного {trainee_id}")

    except ValueError:
        logger.error(f"❌ Ошибка парсинга trainee_id")
        await callback.answer("❌ Ошибка: неверный ID", show_alert=True)
    except Exception as e:
        logger.exception(f"❌ Ошибка: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)




    await callback.answer()


