# ===== ОБЩИЙ НАВИГАЦИОННЫЙ ХЕЛПЕР =====
# Единая точка для кнопки «⬅️ Назад» (callback_data="nav_back") и возврата
# в меню тренировок (callback_data="workouts_menu").
#
# Обработчик колбэка "workouts_menu" живёт в handlers/workouts.py, а
# "nav_back" — в handlers/navigation.py. Здесь только конструкторы кнопок,
# чтобы любой экран мог легко добавить «Назад» без дублирования логики.

from aiogram.utils.keyboard import InlineKeyboardBuilder

BACK_CB = "nav_back"          # универсальный назад → последний экран
TRAININGS_MENU_CB = "workouts_menu"  # корневое меню тренировки


def add_nav_buttons(
    builder: InlineKeyboardBuilder,
    *,
    back: bool = True,
    to_menu: bool = False,
    adjust_per_row: int = 2,
) -> InlineKeyboardBuilder:
    """Добавить в клавиатуру кнопки «⬅️ Назад» и/или «🏋️ Меню тренировки».

    Вызывать ПОСЛЕ добавления основных кнопок, ПЕРЕД builder.adjust(...).
    Функция мутирует переданный builder и возвращает его же.
    """
    if back:
        builder.button(text="⬅️ Назад", callback_data=BACK_CB)
    if to_menu:
        builder.button(text="🏋️ Меню тренировки", callback_data=TRAININGS_MENU_CB)
    try:
        builder.adjust(adjust_per_row, repeat=True)
    except Exception:
        pass
    return builder


def nav_markup(*, back: bool = True, to_menu: bool = False):
    """Клавиатура из одних навигационных кнопок (для экранов-заглушек)."""
    kb = InlineKeyboardBuilder()
    add_nav_buttons(kb, back=back, to_menu=to_menu)
    return kb.as_markup()


async def is_in_workout_constructor(state) -> bool:
    """True, если сейчас идёт создание/редактирование тренировки."""
    try:
        current = await state.get_state()
    except Exception:
        return False
    return bool(current) and "CreateWorkoutStates" in str(current)


async def add_constructor_nav(
    builder: InlineKeyboardBuilder,
    state,
    *,
    adjust_per_row: int = 2,
) -> InlineKeyboardBuilder:
    """Навигация для ЭКРАНОВ КОНСТРУКТОРА тренировки.

    Пока идёт создание тренировки, кнопка «⬅️ Назад» недопустима — она
    уводит из конструктора. Вместо неё добавляем только «🔙 К блокам»
    (callback create_back_to_blocks — возврат к выбору блоков без потери
    черновика). Если конструктор не активен — обычные кнопки «Назад» и
    «Меню тренировки».

    Вызывать ПОСЛЕ основных кнопок, ПЕРЕД финальным builder.adjust(...).
    """
    if await is_in_workout_constructor(state):
        builder.button(text="🔙 К блокам", callback_data="create_back_to_blocks")
    else:
        builder.button(text="⬅️ Назад", callback_data=BACK_CB)
        builder.button(text="🏋️ Меню тренировки", callback_data=TRAININGS_MENU_CB)
    try:
        builder.adjust(adjust_per_row, repeat=True)
    except Exception:
        pass
    return builder


__all__ = [
    "add_nav_buttons",
    "add_constructor_nav",
    "is_in_workout_constructor",
    "nav_markup",
    "BACK_CB",
    "TRAININGS_MENU_CB",
]
