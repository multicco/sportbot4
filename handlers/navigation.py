# ===== НАВИГАЦИОННЫЙ СЛОЙ (гарантированные кнопки «Назад») =====
#
# Версия 2 — без outer-middleware.
#
# Почему так: в aiogram 3.13.1 outer-middleware, зарегистрированный на
# navigation_router, вызывается для КАЖДОГО дочернего роутера при каскаде
# propagate_event (см. aiogram/dispatcher/router.py). Это приводило к
# повторному прогону уже обработанных колбэков и ошибкам вида
#   TypeError: ... missing 1 required positional argument: 'state'/'context'
# Поэтому middleware удалён, а навигация строится на трёх простых вещах:
#   1) remember_screen — лёгкий наблюдатель, запоминает пройденные экраны;
#   2) handle_universal_back — возврат на последний запомненный экран
#      ПРЯМЫМ вызовом нужного хендлера (без propagate_event — там теряется
#      контекст);
#   3) save_process_on_exit / resume_process — выход в главное меню без
#      потери незавершённого процесса (снимок FSM + кнопка «Продолжить»).
#
# Кнопки «Назад» там, где их не было, добавляет keyboards/nav_patch.py
# (обёртки над клавиатурами конструктора тренировки).

import json
import logging

from aiogram import F, Router
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.filters import BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

logger = logging.getLogger(__name__)

navigation_router = Router(name="navigation")

NAV_BACK_KEY = "nav_back"
SAVED_PROCESS_KEY = "saved_process"

# Экраны-«корни» разделов: прямой вызов хендлера отрисовки.
SECTION_HANDLERS = {
    "workouts_menu": ("handlers.workouts", "show_workouts_menu"),
    "tests_menu": ("handlers.workouts", "show_tests_menu"),
    "teams_menu": ("handlers.teams", "cmd_teams"),
}

STATE_LABELS = {
    "CreateWorkoutStates": "создание тренировки",
    "CreateExerciseStates": "создание упражнения",
    "CreateBatteryStates": "создание батареи тестов",
    "EditBatteryStates": "редактирование батареи",
    "JoinBatteryStates": "присоединение к батарее",
    "CreateTestSetStates": "создание набора тестов",
    "JoinTestSetStates": "присоединение к набору тестов",
    "TeamStates": "создание команды",
    "waiting_": "ввод данных теста",
}


def _label_for_state(state_name: str) -> str:
    for key, label in STATE_LABELS.items():
        if key in state_name:
            return label
    return "незавершённое действие"


class NotNavigationCallback(BaseFilter):
    """True для любых колбэков, которые НЕ относятся к навигационному слою."""

    async def __call__(self, callback: CallbackQuery) -> bool:
        d = callback.data or ""
        return not (
            d in ("nav_back", "main_menu", "resume_process")
            or d.startswith("back_to_")
        )


@navigation_router.callback_query(NotNavigationCallback())
async def remember_screen(callback: CallbackQuery, state: FSMContext):
    """Наблюдатель: запоминаем каждый пройденный экран.

    Поднимаем SkipHandler — штатный способ aiogram «не перехватывать»
    событие: остальные роутеры обработают колбэк как обычно. Хендлеры с
    `yield` в aiogram 3.x запрещены (ломают диспетчер), поэтому здесь
    обычный async-хендлер.

    Не запоминаем main_menu/resume_process — иначе после выхода в главное
    меню «Назад» повёл бы обратно в уже завершённый процесс.
    """
    data = callback.data or ""
    if data not in ("main_menu", "resume_process"):
        try:
            await state.update_data({NAV_BACK_KEY: data})
        except Exception as e:
            logger.debug("navigation: не удалось запомнить экран: %s", e)
    raise SkipHandler


@navigation_router.callback_query(F.data == "nav_back")
async def handle_universal_back(callback: CallbackQuery, state: FSMContext):
    """«⬅️ Назад»: возврат к последнему экрану БЕЗ сброса FSM-процесса.

    Реализация — прямой вызов хендлера целевого экрана (никакого
    propagate_event: при ручной пересылке теряются kwargs state/bot,
    что давало TypeError у вас в логах). Если цель неизвестна —
    открываем корневой экран раздела или главное меню.
    """
    sdata = await state.get_data()
    target = sdata.get(NAV_BACK_KEY)
    await callback.answer()

    # Конструктор тренировки: свои экранные колбэки wc_* обрабатывает
    # handlers/workouts.py напрямую — сюда мы попадаем только если цель
    # сама является колбэком раздела. Прямые вызовы ниже покрывают корни.
    if target and target != "nav_back":
        spec = SECTION_HANDLERS.get(target)
        if spec is not None:
            module_name, func_name = spec
            try:
                import importlib

                mod = importlib.import_module(module_name)
                handler = getattr(mod, func_name)
                await handler(callback, state)
                return
            except Exception as e:
                logger.exception("navigation: не удалось вернуться на '%s': %s", target, e)
                return

    # Нет цели или неизвестная цель → главное меню (с сохранением процесса)
    await save_process_on_exit(callback, state)


@navigation_router.callback_query(F.data.startswith("back_to_"))
async def handle_broken_back(callback: CallbackQuery, state: FSMContext):
    """Старые «битые» кнопки назад: ведём на последний запомненный экран.

    Например back_to_constructor → экран конструктора. Так как реальных
    обработчиков у этих callback_data нет, используем ту же логику, что и
    для универсального «Назад».
    """
    await handle_universal_back(callback, state)


@navigation_router.callback_query(F.data == "main_menu")
async def save_process_on_exit(callback: CallbackQuery, state: FSMContext):
    """Выход в главное меню без потери процесса (снимок + «▶️ Продолжить»)."""
    current = await state.get_state()
    data = await state.get_data()

    snapshot_raw = None
    if current:
        snapshot = {
            "state": current,
            "data": {k: v for k, v in data.items() if k != SAVED_PROCESS_KEY},
        }
        new_data = dict(data)
        new_data[SAVED_PROCESS_KEY] = json.dumps(snapshot, ensure_ascii=False, default=str)
        await state.clear()
        await state.set_data(new_data)
        snapshot_raw = new_data[SAVED_PROCESS_KEY]
    else:
        snapshot_raw = data.get(SAVED_PROCESS_KEY)

    from keyboards.main_keyboards_old import get_main_menu_keyboard

    kb_builder = InlineKeyboardBuilder()
    if snapshot_raw:
        try:
            snap = json.loads(snapshot_raw)
            kb_builder.button(
                text=f"▶️ Продолжить: {_label_for_state(snap['state'])}",
                callback_data="resume_process",
            )
        except Exception:
            pass

    markup = get_main_menu_keyboard()
    for row in markup.inline_keyboard:
        for btn in row:
            kb_builder.button(text=btn.text, callback_data=btn.callback_data, url=btn.url)
    kb_builder.adjust(2)

    text = f"🏠 <b>Главное меню</b>\n\n{callback.from_user.first_name}, выберите раздел."
    if snapshot_raw:
        text += "\n\nℹ️ Незавершённое действие сохранено — нажмите «Продолжить»."
    try:
        await callback.message.edit_text(text, reply_markup=kb_builder.as_markup(), parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb_builder.as_markup(), parse_mode="HTML")
    await callback.answer()


@navigation_router.callback_query(F.data == "resume_process")
async def resume_process(callback: CallbackQuery, state: FSMContext):
    """Восстановить сохранённый процесс из главного меню."""
    data = await state.get_data()
    snapshot_raw = data.get(SAVED_PROCESS_KEY)
    if not snapshot_raw:
        await callback.answer("Нечего продолжать", show_alert=True)
        return
    try:
        snap = json.loads(snapshot_raw)
    except Exception:
        await callback.answer("Сохранённый процесс повреждён", show_alert=True)
        return

    restored = {k: v for k, v in snap["data"].items() if k != SAVED_PROCESS_KEY}
    restored[NAV_BACK_KEY] = data.get(NAV_BACK_KEY)
    await state.set_data(restored)
    await state.set_state(snap["state"])
    await callback.answer()

    label = _label_for_state(snap["state"])
    try:
        await callback.message.edit_text(
            f"▶️ Процесс восстановлен: <b>{label}</b>.\n\n"
            "Продолжите — отправьте данные или используйте кнопки.",
            parse_mode="HTML",
        )
    except Exception:
        pass


__all__ = ["navigation_router", "NAV_BACK_KEY", "SAVED_PROCESS_KEY"]