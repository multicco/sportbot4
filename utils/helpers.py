# utils/helpers.py
import re
from typing import Optional

from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, Message


def _markup_key(reply_markup) -> Optional[str]:
    """Стабильная сигнатура клавиатуры (тексты кнопок + callback_data)."""
    if reply_markup is None:
        return None
    try:
        inline_keyboard = getattr(reply_markup, "inline_keyboard", None)
        if inline_keyboard is None:
            keyboard = getattr(reply_markup, "keyboard", None)
            if keyboard is None:
                return str(reply_markup)
            rows = [[(b.text, None) for b in row] for row in keyboard]
        else:
            rows = [[(b.text, getattr(b, "callback_data", None)) for b in row]
                    for row in inline_keyboard]
        return repr(rows)
    except Exception:
        return None


def _normalize_for_compare(text: Optional[str]) -> str:
    """Нормализуем текст для сравнения «изменился ли контент»."""
    if text is None:
        return ""
    # MarkdownV2 требует экранирования, а сервер хранит исходный текст —
    # при сравнении снимаем обратные слеши и схлопываем пробелы.
    t = re.sub(r"\\([_*\[\]()~`>#+\-=|{}.!])", r"\1", text)
    t = re.sub(r"\s+", " ", t)
    return t.strip()


async def _safe_edit_or_send(message: Message, text: str, reply_markup=None, parse_mode=None):
    """Отредактировать сообщение, а при неудаче — отправить новое.

    Если контент и клавиатура идентичны текущим (Telegram ответил бы
    «message is not modified»), редактирование пропускается.
    При ошибке разметки повторяем без parse_mode / с MarkdownV2.
    """
    last_err = None
    attempts = [
        {"text": text, "reply_markup": reply_markup, "parse_mode": parse_mode},
        {"text": text, "reply_markup": reply_markup, "parse_mode": "MarkdownV2"},
        {"text": text, "reply_markup": reply_markup, "parse_mode": None},
    ]
    for i, kw in enumerate(attempts):
        try:
            await message.edit_text(**kw)
            return
        except TelegramBadRequest as e:
            msg = str(e).lower()
            if "not modified" in msg or "same as a current" in msg:
                # Проверяем, действительно ли клавиатура совпадает —
                # если нет, пробуем отредактировать только её.
                new_key = _markup_key(reply_markup)
                cur_key = _markup_key(getattr(message, "reply_markup", None))
                if new_key is not None and cur_key is not None and new_key != cur_key:
                    try:
                        await message.edit_reply_markup(reply_markup=reply_markup)
                        return
                    except TelegramBadRequest as e2:
                        last_err = e2
                return
            last_err = e
            # ошибка разметки на первом/втором шаге — пробуем следующий вариант;
            # на последнем — выходим и отправляем новое сообщение
            continue
        except Exception as e:
            last_err = e
            break

    # Редактирование невозможно (например, «message to edit not found»,
    # слишком старое сообщение или ошибка разметки) — отправляем новое.
    sent = False
    for kw in attempts:
        try:
            await message.answer(**kw)
            sent = True
            break
        except TelegramBadRequest:
            continue
        except Exception:
            break
    if not sent and last_err is not None:
        try:
            await message.answer(text, reply_markup=reply_markup, parse_mode=None)
        except Exception:
            pass


async def safe_callback_answer(callback: CallbackQuery, cache_time: int = 0):
    """answer() с подавлением устаревших/дублирующихся кликов."""
    try:
        await callback.answer(cache_time=cache_time)
    except TelegramBadRequest as e:
        if "query is too old" not in str(e).lower():
            raise


async def ignore_old_updates_handler(callback: CallbackQuery):
    """Глобальный хендлер: молча «закрывает» устаревшие клики по кнопкам.

    Без него aiogram оставляет query unanswered и Telegram показывает
    пользователю «Бот не отвечает» / часики. Регистрация обязательна,
    иначе старые сообщения будут вызывать лишние ошибки.
    """
    try:
        await callback.answer(cache_time=30)
    except TelegramBadRequest:
        pass


async def ensure_state_filter(states):
    """Возвращает StateFilter для списка состояний (обёртка для читаемости)."""
    return StateFilter(*states)