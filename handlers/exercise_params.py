# handlers/exercise_params_simple.py
"""
Модуль для быстрого добавления упражнения с параметрами в одну строку.
Формат: 4 10 75 120
(4 подхода, 10 повторений, 75% от 1ПМ, 120 сек отдыха)

Если известен 1ПМ упражнения - показывает вес в кг.
"""

import logging
from typing import Optional, Dict, Any, Tuple

from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import db_manager
from states.workout_states import CreateWorkoutStates

logger = logging.getLogger(__name__)

exercise_params_router = Router()


# ===================== HELPER FUNCTIONS =====================

def _parse_int_suffix(callback_data: str) -> Optional[int]:
    """Возвращает целый суффикс после '_' или None."""
    try:
        part = callback_data.split("_")[-1]
        return int(part) if part.isdigit() else None
    except Exception:
        return None


async def _safe_edit_or_send(message, text, reply_markup=None, parse_mode=None):
    """Пробуем edit_text, если не удалось — answer."""
    try:
        await message.edit_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception:
        await message.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)


def parse_exercise_params(text: str) -> Tuple[Optional[int], Optional[int], Optional[int], Optional[int]]:
    """
    Парсит параметры упражнения из строки формата: "4 10 75 120"
    
    Returns: (sets, reps, percent_1rm, rest_seconds) или (None, None, None, None) при ошибке
    """
    try:
        parts = text.strip().split()
        
        if len(parts) < 1 or len(parts) > 4:
            return None, None, None, None
        
        sets = int(parts[0]) if len(parts) >= 1 else None
        reps = int(parts[1]) if len(parts) >= 2 else None
        percent = int(parts[2]) if len(parts) >= 3 else None
        rest = int(parts[3]) if len(parts) >= 4 else None
        
        # Базовая валидация
        if sets and not (1 <= sets <= 20):
            return None, None, None, None
        if reps and not (1 <= reps <= 100):
            return None, None, None, None
        if percent and not (1 <= percent <= 200):
            return None, None, None, None
        if rest and not (0 <= rest <= 600):
            return None, None, None, None
        
        return sets, reps, percent, rest
    
    except (ValueError, IndexError):
        return None, None, None, None


def calculate_weight_from_1rm(one_rm_kg: Optional[float], percent: Optional[int]) -> Optional[float]:
    """
    Вычисляет вес на основе 1ПМ и процента.
    
    Args:
        one_rm_kg: Максимум на одно повторение в кг
        percent: Процент от 1ПМ (0-200)
    
    Returns:
        Вес в кг или None
    """
    if not one_rm_kg or not percent:
        return None
    
    return round(one_rm_kg * percent / 100, 1)


# ===================== ГЛАВНЫЙ ОБРАБОТЧИК =====================

@exercise_params_router.callback_query(F.data.startswith("add_exercise_with_params_"))
async def add_exercise_with_params_start(callback: CallbackQuery, state: FSMContext):
    """
    Запускает добавление упражнения с параметрами в одну строку.
    
    Параметр: add_exercise_with_params_{exercise_id}
    """
    exercise_id = _parse_int_suffix(callback.data)
    
    if exercise_id is None:
        await callback.answer("❌ Неверный ID упражнения", show_alert=True)
        return
    
    try:
        # Получаем данные упражнения (включая 1ПМ если известен)
        async with db_manager.pool.acquire() as conn:
            exercise = await conn.fetchrow(
                """
                SELECT 
                    id, name, muscle_group, category, 
                    default_sets, default_reps_min, default_reps_max,
                    one_rm_kg, description
                FROM exercises
                WHERE id = $1 AND is_active = true
                """,
                exercise_id
            )
        
        if not exercise:
            await callback.answer("❌ Упражнение не найдено", show_alert=True)
            return
        
        # Сохраняем упражнение в state
        await state.update_data(
            selected_exercise_id=exercise_id,
            selected_exercise_name=exercise['name'],
            selected_exercise_1rm=exercise.get('one_rm_kg'),
            selected_exercise_defaults={
                'sets': exercise.get('default_sets') or 3,
                'reps': exercise.get('default_reps_min') or 8,
                'percent': 75,
                'rest': 120,
            }
        )
        
        # Формируем подсказку по формату
        defaults = exercise.get('default_sets') or 3
        default_reps = exercise.get('default_reps_min') or 8
        one_rm_info = ""
        
        if exercise.get('one_rm_kg'):
            one_rm_info = f"\n\n💡 **1ПМ известен: {exercise['one_rm_kg']} кг**\nПосле ввода % будет показан точный вес"
        
        text = f"""
🏋️ **{exercise['name']}**
💪 {exercise.get('muscle_group', 'Неизвестно')} | {exercise.get('category', 'Без категории')}

📝 **Введите параметры в одну строку:**

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
            callback_data=f"exercise_params_quick_{exercise_id}_{defaults}_{default_reps}_75_120"
        )
        kb.button(text="🔙 Выбрать другое", callback_data="search_exercise_for_block")
        kb.adjust(1)
        
        await _safe_edit_or_send(
            callback.message,
            text,
            reply_markup=kb.as_markup(),
            parse_mode="Markdown"
        )
        
        await state.set_state(CreateWorkoutStates.configuring_exercise)
        await callback.answer()
    
    except Exception as e:
        logger.exception("Ошибка в add_exercise_with_params_start: %s", e)
        await callback.answer("❌ Ошибка при загрузке упражнения", show_alert=True)


# ===================== БЫСТРОЕ ДОБАВЛЕНИЕ (КНОПКА) =====================

@exercise_params_router.callback_query(F.data.startswith("exercise_params_quick_"))
async def exercise_params_quick(callback: CallbackQuery, state: FSMContext):
    """Добавляет упражнение с параметрами из кнопки (быстрый способ)."""
    parts = callback.data.split("_")
    try:
        exercise_id = int(parts[3])
        sets = int(parts[4])
        reps = int(parts[5])
        percent = int(parts[6])
        rest = int(parts[7])
    except (ValueError, IndexError):
        await callback.answer("❌ Ошибка при парсинге параметров", show_alert=True)
        return
    
    await finalize_exercise(callback.message, state, sets, reps, percent, rest)
    await callback.answer()


# ===================== ВВОД В ОДНУ СТРОКУ =====================

@exercise_params_router.message(StateFilter(CreateWorkoutStates.configuring_exercise))
async def handle_exercise_params_input(message: Message, state: FSMContext):
    """
    Обрабатывает ввод параметров в формате: "4 10 75 120"
    Автоматически вычисляет вес если известен 1ПМ.
    """
    text = (message.text or "").strip()
    
    # Парсим параметры
    sets, reps, percent, rest = parse_exercise_params(text)
    
    # Используем значения по умолчанию для пропущенных параметров
    data = await state.get_data()
    defaults = data.get("selected_exercise_defaults", {})
    
    if sets is None:
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
    
    # Подставляем значения по умолчанию если не указаны
    sets = sets or defaults.get('sets', 3)
    reps = reps or defaults.get('reps', 8)
    percent = percent or defaults.get('percent', 75)
    rest = rest or defaults.get('rest', 120)
    
    await finalize_exercise(message, state, sets, reps, percent, rest)


# ===================== ФИНАЛИЗАЦИЯ =====================

async def finalize_exercise(message, state: FSMContext, sets: int, reps: int, 
                           percent: Optional[int], rest: Optional[int]):
    """
    Завершает добавление упражнения с вычислением веса.
    """
    data = await state.get_data()
    current_block = data.get("current_block")
    exercise_id = data.get("selected_exercise_id")
    exercise_name = data.get("selected_exercise_name")
    one_rm_kg = data.get("selected_exercise_1rm")
    
    if not current_block:
        await message.answer("❌ Блок не выбран")
        return
    
    # Вычисляем вес на основе 1ПМ и процента
    calculated_weight = None
    if one_rm_kg and percent:
        calculated_weight = calculate_weight_from_1rm(one_rm_kg, percent)
    
    # Создаём запись упражнения
    exercise_entry = {
        "id": exercise_id,
        "name": exercise_name,
        "sets": sets,
        "reps": reps,
        "reps_min": reps,  # совместимость
        "reps_max": reps,  # совместимость
        "one_rm_percent": percent,
        "rest_seconds": rest,
        "weight_kg": calculated_weight,
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
    if calculated_weight:
        weight_info = f"\n  💪 Вес: **{calculated_weight} кг** (при {percent}% от {one_rm_kg}кг 1ПМ)"
    elif percent:
        weight_info = f"\n  📊 {percent}% от 1ПМ"
    
    rest_info = f"\n  ⏱ Отдых: {rest} сек" if rest else ""
    
    text = f"""
✅ **{exercise_name}** добавлено!

📋 **Параметры:**
  • **{sets}x{reps}** подходы x повторения{weight_info}{rest_info}

Что дальше?
"""
    
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Добавить ещё упражнение", callback_data="search_exercise_for_block")
    kb.button(text="✅ Завершить блок", callback_data="finish_current_block")
    kb.button(text="🔙 К блокам", callback_data="back_to_constructor")
    kb.adjust(1)
    
    await message.answer(text, reply_markup=kb.as_markup(), parse_mode="Markdown")
    await state.clear()


# ===================== РЕГИСТРАЦИЯ =====================

def register_exercise_params_handlers(dp):
    """Регистрирует router параметров упражнения."""
    try:
        dp.include_router(exercise_params_router)
        logger.info("✅ exercise_params_router успешно подключён!")
    except RuntimeError as e:
        logger.warning(f"⚠️ exercise_params_router уже был подключён: {e}")


__all__ = ["exercise_params_router", "register_exercise_params_handlers"]
