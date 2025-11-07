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


# ✓ ИСПРАВЛЕНИЕ: ОБНОВИТЬ ФУНКЦИЮ my_workouts с проверкой ролей
# Замени существующую функцию my_workouts на эту:

@workouts_router.callback_query(F.data == "my_workouts")
async def my_workouts(callback: CallbackQuery):
    logger.info(f"my_workouts by user {callback.from_user.id}")
    
    try:
        user = await db_manager.get_user_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer("Пользователь не найден", show_alert=True)
            return
        
        role = await get_user_role(callback.from_user.id)
        
        async with db_manager.pool.acquire() as conn:
            # ✓ РАЗНЫЕ ЗАПРОСЫ ДЛЯ РАЗНЫХ РОЛЕЙ
            if role == 'admin':
                # АДМИН видит все тренировки
                rows = await conn.fetch("""
                    SELECT w.id, w.name, w.unique_id,
                           (SELECT COUNT(*) FROM workout_exercises we WHERE we.workout_id = w.id) as exercise_count,
                           w.estimated_duration_minutes,
                           u.first_name, u.last_name
                    FROM workouts w
                    LEFT JOIN users u ON w.created_by = u.id
                    WHERE coalesce(w.is_active, true) = true
                    ORDER BY w.created_at DESC
                    LIMIT 50
                """)
                role_display = "_(Админ - все тренировки)_"
            
            elif role == 'trainer':
                # ТРЕНЕР видит свои + своих подопечных
                rows = await conn.fetch("""
                    SELECT DISTINCT w.id, w.name, w.unique_id,
                           (SELECT COUNT(*) FROM workout_exercises we WHERE we.workout_id = w.id) as exercise_count,
                           w.estimated_duration_minutes,
                           u.first_name, u.last_name
                    FROM workouts w
                    LEFT JOIN users u ON w.created_by = u.id
                    WHERE (w.created_by = $1 OR w.created_by IN (
                        SELECT trainee_id FROM user_trainee_assignments WHERE trainer_id = $1
                    ))
                    AND coalesce(w.is_active, true) = true
                    ORDER BY w.created_at DESC
                    LIMIT 50
                """, user['id'])
                role_display = "_(Тренер - свои + подопечных)_"
            
            else:  # 'player'
                # ИГРОК видит только свои
                rows = await conn.fetch("""
                    SELECT w.id, w.name, w.unique_id,
                           (SELECT COUNT(*) FROM workout_exercises we WHERE we.workout_id = w.id) as exercise_count,
                           w.estimated_duration_minutes
                    FROM workouts w
                    WHERE w.created_by = $1 AND coalesce(w.is_active, true) = true
                    ORDER BY w.created_at DESC
                    LIMIT 50
                """, user['id'])
                role_display = "_(Игрок - только свои)_"
        
        if not rows:
            kb = InlineKeyboardBuilder()
            kb.button(text="➕ Создать первую", callback_data="create_workout")
            kb.button(text="🔙 В меню", callback_data="workouts_menu")
            kb.adjust(1)
            
            await _safe_edit_or_send(
                callback.message, 
                "У вас пока нет тренировок.", 
                reply_markup=kb.as_markup()
            )
            await callback.answer()
            return
        
        text = f"🏋️ **Мои тренировки ({len(rows)}):**\n{role_display}\n\n"
        
        kb = InlineKeyboardBuilder()
        for r in rows:
            cnt = r['exercise_count'] or 0
            text += f"**{r['name']}** — {cnt} упр. | Код `{r['unique_id']}`\n"
            kb.button(text=f"{r['name'][:25]} ({cnt})", callback_data=f"view_workout_{r['id']}")
        
        kb.button(text="➕ Создать", callback_data="create_workout")
        kb.button(text="🔙 В меню", callback_data="workouts_menu")
        kb.adjust(1)
        
        await _safe_edit_or_send(
            callback.message, 
            text, 
            reply_markup=kb.as_markup(), 
            parse_mode="Markdown"
        )
        await callback.answer()
        logger.info(f"✅ my_workouts: {len(rows)} тренировок для {role}")
    
    except Exception as e:
        logger.exception(f"my_workouts error: {e}")
        await callback.answer("Ошибка получения тренировок", show_alert=True)