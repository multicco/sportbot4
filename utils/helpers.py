# utils/helpers.py
from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest


async def _safe_edit_or_send(message: Message, text: str, reply_markup=None, parse_mode=None):
    """Отредактировать сообщение, а при неудаче — отправить новое.

    При ошибке разметки (например, из-за спецсимволов Markdown в
    пользовательском тексте) повторяем без parse_mode, чтобы сообщение
    всё равно дошло до пользователя.
    """
    try:
        await message.edit_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
        return
    except TelegramBadRequest:
        pass

    try:
        await message.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)
    except TelegramBadRequest:
        await message.answer(text, reply_markup=reply_markup, parse_mode=None)