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

import asyncio
import inspect
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
# (исправлено: show_workouts_menu/show_tests_menu/cmd_teams не существовали —
# из-за этого «Назад» из разделов всегда падал в главное меню)
SECTION_HANDLERS = {
    "workouts_menu": ("handlers.workouts", "workouts_menu"),
    "tests_menu": ("handlers.tests", "tests_menu"),
    "teams_menu": ("handlers.teams", "cb_teams_menu"),
    # раздел упражнений: свой универсальный «Назад» уже есть
    "search_exercise": ("handlers.exercises", "universal_back"),
}

# Экранные колбэки внутри раздела тренировок (конструктор/просмотр).
# Функции вызываются с исходным callback.data — как при обычном нажатии.
WORKOUT_SCREEN_ROUTES = {
    "view_workout_": ("handlers.workouts", "view_workout_details"),
    "start_workout_": ("handlers.player_workouts", "start_workout"),
    "continue_workout_": ("handlers.player_workouts", "continue_workout"),
}

# Колбэки конструктора тренировки → функция отрисовки экрана в workouts.py.
CONSTRUCTOR_SCREEN_ROUTES = {
    "create_back_to_blocks": "_show_block_selection",
    "workout_start_ex_search": "_show_exercises_for_block",
    "manual_add_exercise": "_show_exercises_for_block",
}

# Префиксы колбэков, по которым можно вычленить id тренировки.
# Порядок важен: exdet_/test1rm_ проверяются раньше start_workout_.
_WORKOUT_ID_RULES = (
    ("exdet_", 1),          # exdet_{ex}_{wid}_{sess}_{bex} — второй сегмент
    ("test1rm_", 1),        # test1rm_{wid}_{block_ex_id}
    ("markdone_", -1),      # markdone_{...}_{wid} — последний сегмент
    ("markundone_", -1),
    ("back_", -1),           # back_{wid}
    ("start_workout_", -1),
    ("finish_workout_", -1),
    ("continue_workout_", -1),
    ("view_workout_", -1),
)


def _extract_workout_id(data: str) -> int | None:
    """Вернуть id тренировки из callback_data, если он там есть."""
    for prefix, idx in _WORKOUT_ID_RULES:
        if data.startswith(prefix):
            parts = data[len(prefix):].split("_")
            try:
                candidate = parts[idx] if idx >= 0 else parts[idx]
                return int(candidate)
            except (ValueError, IndexError):
                return None
    return None


async def _call_screen(target: str, cb: CallbackQuery, state: FSMContext) -> bool:
    """Отрисовать экран `target` прямым вызовом его обработчика.

    Возвращает True, если экран открыт. Аргументы подставляются по
    сигнатуре функции (callback/state/workout_id), лишние игнорируются.
    """
    # 1. Специальные корни разделов
    spec = SECTION_HANDLERS.get(target)
    if spec is not None:
        module_name, func_name = spec
        try:
            import importlib

            handler = getattr(importlib.import_module(module_name), func_name)
            await _invoke(handler, cb, state)
            return True
        except Exception as e:
            logger.exception("navigation: не удалось вернуться на '%s': %s", target, e)
            return False

    # 2. Колбэки конструктора тренировки: рисуем целевой экран напрямую
    if target in CONSTRUCTOR_SCREEN_ROUTES:
        try:
            from handlers import workouts as _wk

            renderer = getattr(_wk, CONSTRUCTOR_SCREEN_ROUTES[target])
            await renderer(cb.message, state)
            await cb.answer()
            return True
        except Exception as e:
            logger.exception("navigation: не удалось вернуться на '%s': %s", target, e)
            return False

    # 3. Экранные колбэки тренировок: вызываем обработчик с исходным data
    for prefix, (module_name, func_name) in WORKOUT_SCREEN_ROUTES.items():
        if target.startswith(prefix):
            try:
                import importlib

                handler = getattr(importlib.import_module(module_name), func_name)
                await _invoke(handler, cb, state, data_override=target)
                return True
            except Exception as e:
                logger.exception("navigation: не удалось вернуться на '%s': %s", target, e)
                return False

    # 4. Карточка упражнения в активной тренировке
    if target.startswith("exdet_"):
        try:
            from handlers.player_workouts import exercise_detail

            await _invoke(exercise_detail, cb, state, data_override=target)
            return True
        except Exception as e:
            logger.exception("navigation: не удалось вернуться на '%s': %s", target, e)
            return False

    # 5. Обзор тренировки (для markdone_/back_/test1rm_ и т.п.)
    wid = _extract_workout_id(target)
    if wid is not None:
        try:
            from handlers.player_workouts import show_workout_overview

            await show_workout_overview(cb, state, wid)
            return True
        except Exception as e:
            logger.exception("navigation: не удалось вернуться к обзору тренировки %s: %s", wid, e)
            return False

    return False


async def _invoke(handler, cb: CallbackQuery, state: FSMContext, data_override: str | None = None, **extra):
    """Вызвать обработчик экрана только с теми аргументами, что ему нужны.

    data_override — подменный callback.data для хендлера. Поле data у
    CallbackQuery в aiogram 3.x frozen (pydantic), поэтому менять его напрямую
    нельзя — вместо этого передаём хендлеру поверхностную копию модели.
    """
    if data_override is not None and getattr(cb, "data", None) != data_override:
        try:
            cb = cb.model_copy(update={"data": data_override}, deep=False)
        except Exception:
            pass
    sig = inspect.signature(handler)
    kwargs = {}
    accepts_var_kw = any(
        p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()
    )
    for name, value in {"callback": cb, "state": state, **extra}.items():
        if accepts_var_kw or name in sig.parameters:
            kwargs[name] = value
    result = handler(**kwargs)
    if inspect.isawaitable(result):
        await asyncio.shield(result)

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


# Колбэки, которые НЕ являются «экранами» — их не запоминаем как цель
# возврата (иначе «Назад» привёл бы к повторному действию: тест, старт,
# отмена, переход в главное меню и т.п.).
_NON_SCREEN_PREFIXES = (
    "test1rm_",       # запуск теста из карточки упражнения
    "start_1rm_test", # запуск теста из конструктора
    "create_cancel",
    "cancel_",
    "delete_workout_",
    "finish_workout_",
    "skip_",
    "rpe_",
    "ignore_block_",
    "confirm_",
    "visibility_",
    "required_",
    "add_to_set_",
    "add_to_my_",
    "resume_process",
    "main_menu",
    "nav_back",
)

# Колбэки-действия внутри тренировки: запоминаем их, но нормализуем в
# «безопасную» цель возврата (обзор тренировки обработает сам _call_screen).
_ACTION_TO_SCREEN = {
    "markdone_": "overview",
    "markundone_": "overview",
}


def _is_screen_callback(data: str) -> bool:
    if not data or data in ("main_menu", "resume_process", NAV_BACK_KEY):
        return False
    if data.startswith("back_to_") or data == "nav_back":
        return False  # кнопки назад сами по себе — не экран
    for p in _NON_SCREEN_PREFIXES:
        if data.startswith(p):
            return False
    return True


@navigation_router.callback_query(NotNavigationCallback())
async def remember_screen(callback: CallbackQuery, state: FSMContext):
    """Наблюдатель: запоминаем каждый пройденный ЭКРАН.

    Поднимаем SkipHandler — штатный способ aiogram «не перехватывать»
    событие: остальные роутеры обработают колбэк как обычно. Хендлеры с
    `yield` в aiogram 3.x запрещены (ломают диспетчер), поэтому здесь
    обычный async-хендлер.

    Действия (тесты, отметки выполнения, отмены) экраном не считаем —
    иначе «Назад» повторно запустил бы это действие. Для действий внутри
    тренировки целью делаем обзор тренировки.
    """
    data = callback.data or ""
    try:
        if _is_screen_callback(data):
            await state.update_data({NAV_BACK_KEY: data})
        else:
            for prefix, kind in _ACTION_TO_SCREEN.items():
                if data.startswith(prefix):
                    wid = _extract_workout_id(data)
                    if wid is not None:
                        await state.update_data({NAV_BACK_KEY: f"view_workout_{wid}"})
                    break
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

    if target and target != NAV_BACK_KEY:
        if await _call_screen(target, callback, state):
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