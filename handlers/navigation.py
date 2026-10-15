# ===== НАВИГАЦИОННЫЙ СЛОЙ (гарантированные кнопки «Назад») =====
#
# Проблема: в части меню и экранов бота нет кнопки «Назад», и пользователь
# мог выйти только через «Главное меню» — при этом текущий процесс терялся.
#
# Что делает этот модуль (подключается ОДНИМ include_router):
#   1) Запоминает каждый пройденный экран (nav_back в FSM-данных). Универсальная
#      кнопка «⬅️ Назад» ведёт ровно туда, а не в главное меню. Также перехватываются
#      «битые» callback_data старых кнопок назад (back_to_constructor и т.п.).
#   2) outer_middleware на callback_query: если обработчик показал экран без
#      единой возвращающей кнопки, автоматически добавляется строка
#      «⬅️ Назад / 🏠 Главное меню».
#   3) При выходе в «Главное меню» незавершённый процесс НЕ теряется: состояние
#      и черновик сохраняются в снимке, появляется кнопка «▶️ Продолжить».

import json
import logging

from aiogram import F, Dispatcher, Router
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

logger = logging.getLogger(__name__)

navigation_router = Router(name="navigation")

NAV_BACK_KEY = "nav_back"
SAVED_PROCESS_KEY = "saved_process"

# Старые «тупиковые» адреса кнопок назад (обработчики не зарегистрированы)
BROKEN_TARGETS = {
    "back_to_constructor",
    "back_to_add_exercises",
    "back_to_edit",
    "back_to_test_set_creation",
    "my_trainees_menu",
}

SECTION_ROOTS = {"workouts_menu", "tests_menu", "search_exercise", "teams_menu", "main_menu"}

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


@navigation_router.callback_query(F.data.notin(BROKEN_TARGETS) & (F.data != "nav_back"))
async def remember_screen(callback: CallbackQuery, state: FSMContext):
    """Первый хендлер на колбэках: запоминаем пройденный экран.

    Фильтр не пропускает сюда nav_back/broken-цели (их обрабатывает наш же
    handle_universal_back). В конце поднимаем SkipHandler — это штатный способ
    aiogram «не перехватывать» событие: остальные роутеры обработают колбэк
    как обычно. Хендлеры с `yield` в aiogram 3.x запрещены — они ломают
    propagate_event ("object async_generator can't be used in 'await'")."""
    try:
        await state.update_data({NAV_BACK_KEY: callback.data})
    except Exception as e:
        logger.debug("navigation: не удалось запомнить экран: %s", e)
    raise SkipHandler


@navigation_router.callback_query(lambda c: c.data in BROKEN_TARGETS or c.data == "nav_back")
async def handle_universal_back(callback: CallbackQuery, state: FSMContext):
    """«⬅️ Назад»: возврат к последнему экрану раздела БЕЗ сброса FSM-процесса."""
    data = await state.get_data()
    target = data.get(NAV_BACK_KEY) or "main_menu"
    await callback.answer()

    dp = Dispatcher.get_current()
    if dp is None:
        logger.warning("navigation: Dispatcher.get_current() вернул None")
        return
    new_cb = callback.model_copy(update={"data": target})
    try:
        await dp.propagate_event("callback_query", new_cb, state=state, bot=callback.bot)
    except Exception as e:
        logger.exception("navigation: не удалось вернуться на '%s': %s", target, e)


@navigation_router.callback_query(F.data == "main_menu")
async def save_process_on_exit(callback: CallbackQuery, state: FSMContext):
    """Выход в главное меню без потери процесса (снимок состояния + кнопка «Продолжить»)."""
    current = await state.get_state()
    data = await state.get_data()

    snapshot_raw = None
    if current:
        snapshot = {"state": current, "data": {k: v for k, v in data.items() if k != SAVED_PROCESS_KEY}}
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


def _markup_has_exit(markup) -> bool:
    if not markup or not getattr(markup, "inline_keyboard", None):
        return False
    for row in markup.inline_keyboard:
        for btn in row:
            d = (btn.callback_data or "").lower()
            t = (btn.text or "").lower()
            if (d in SECTION_ROOTS or "back" in d or "cancel" in d or "menu" in d
                    or "назад" in t or "меню" in t or "отмен" in t):
                return True
    return False


@navigation_router.callback_query.outer_middleware()
async def ensure_back_button(handler, callback: CallbackQuery, data: dict):
    """Если обработчик показал экран без возвращающих кнопок — добавить «Назад».

    Обычный (не генераторный) outer-middleware: пропускает колбэк через все
    остальные роутеры, дожидаётся результата, а затем проверяет клавиатуру
    сообщения и при необходимости дорисовывает кнопки возврата.

    Сигнатура для aiogram 3.13.1: wrap_middlewares делает
        middleware = functools.partial(m, handler_wrapper)
        await wrapped_outer(event, data)
    поэтому первый параметр — обёрнутый следующий обработчик (его подставляет
    partial), второй — событие, третий — контекстный dict. Внутри next-обработчик
    вызывается как await handler(event, **data). Возврат значения ОБЯЗАТЕЛЕН:
    aiogram ожидает awaitable, а НЕ async-генератор (yield здесь ломает
    диспетчер: "object async_generator can't be used in 'await' expression").

    Дополнительно: aiogram проверяет outer-middleware роутера только когда этот
    роутер участвует в обработке события, поэтому у navigation_router есть
    catch-all хендлер remember_screen — он гарантирует участие роутера.
    """
    result = await handler(callback, data)

    try:
        msg = callback.message
        if not msg or getattr(msg, "reply_markup", None) is None:
            return result
        markup = msg.reply_markup
        if not getattr(markup, "inline_keyboard", None):
            return result
        if _markup_has_exit(markup):
            return result

        state: FSMContext = data.get("state")
        back_target = None
        if isinstance(state, FSMContext):
            state_data = await state.get_data()
            back_target = state_data.get(NAV_BACK_KEY)

        builder = InlineKeyboardBuilder()
        for row in markup.inline_keyboard:
            for btn in row:
                builder.button(text=btn.text, callback_data=btn.callback_data, url=btn.url)
        if back_target and back_target != "main_menu":
            builder.button(text="⬅️ Назад", callback_data="nav_back")
        builder.button(text="🏠 Главное меню", callback_data="main_menu")
        builder.adjust(2)
        await msg.edit_reply_markup(reply_markup=builder.as_markup())
    except Exception as e:
        logger.debug("navigation: авто-кнопка «Назад» пропущена: %s", e)

    return result


__all__ = ["navigation_router", "NAV_BACK_KEY", "SAVED_PROCESS_KEY"]