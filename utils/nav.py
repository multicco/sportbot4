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


__all__ = ["add_nav_buttons", "nav_markup", "BACK_CB", "TRAININGS_MENU_CB"]
