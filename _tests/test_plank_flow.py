"""Интеграционный тест: кнопка «Пройти тест» в тренировке (планка) -> ввод секунд -> сохранение."""
import asyncio, sys
sys.path.insert(0, "/workspace")

from aiogram import Dispatcher, Bot
from aiogram.client.session.base import BaseSession
from aiogram.types import Message, CallbackQuery, User, Chat
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

# ---- мок БД ----
class FakeConn:
    async def fetchrow(self, q, *a):
        if "FROM exercises" in q:
            return {"id": 7, "name": "Планка", "test_type": "endurance"}
        return None
    async def fetch(self, q, *a):
        return []
    async def execute(self, q, *a):
        FakeConn.inserted.append((q, a))
        return "OK"
FakeConn.inserted = []

class Ctx:
    async def __aenter__(self): return FakeConn()
    async def __aexit__(self, *e): pass

class FakePool:
    def acquire(self): return Ctx()
    async def fetchrow(self, q, *a): return await FakeConn().fetchrow(q, *a)
    async def fetch(self, q, *a): return []

import database
db_manager = database.db_manager
db_manager.pool = FakePool()
async def fake_get_user(tg_id): return {"id": 1, "telegram_id": tg_id, "role": "player"}
db_manager.get_user_by_telegram_id = fake_get_user

from handlers import register_all_handlers
from handlers import one_rm

class FakeSession(BaseSession):
    async def close(self): pass
    async def make_request(self, method):
        if method.__class__.__name__ == 'GetMe':
            return User(id=123456, is_bot=True, first_name='test', username='test')
        return method.to_telegram_response({})
    async def stream_content(self, *a, **k):
        yield b''

dp = Dispatcher(storage=MemoryStorage())
register_all_handlers(dp)
bot = Bot("123456:TESTTOKENAAAAAAAAAAAAAAAAAAA", session=FakeSession())

chat = Chat(id=1, type="private")
u = User(id=999, is_bot=False, first_name="Test")

async def edit_text(self, text, **kw):
    print("--- edited message ---\n" + text[:150].replace("\n"," | "))
    return self
Message.edit_text = edit_text
async def cb_answer(self, *a, **k): pass
CallbackQuery.answer = cb_answer

async def main():
    key = ("1", "999")
    state = FSMContext(storage=dp.storage, key=key)

    # 1. Нажатие кнопки «Пройти тест» из карточки упражнения в тренировке
    cb = CallbackQuery(id="q1", from_user=u, data="test1rm_7_55",
                       message=Message(message_id=1, date="2026-10-25T10:00:00+00:00", chat=chat, from_user=u))
    await one_rm.handle_test1rm_from_workout(cb, state)
    st = await state.get_state()
    print("Состояние после нажатия кнопки:", st)
    assert st == "waiting_endurance_data", f"unexpected state {st}"

    # 2. Пользователь вводит секунды «30» — через полный цикл диспетчера
    m = Message(message_id=2, date="2026-10-25T10:00:00+00:00", chat=chat, from_user=u, text="30")
    await dp.feed_new_message(bot=bot, message=m, state=state)
    inserts = [i for i in FakeConn.inserted if "user_endurance_records" in i[0]]
    print("INSERT user_endurance_records выполнен:", bool(inserts))
    if inserts:
        print("   значения:", inserts[0][1])
    assert inserts, "Результат не сохранён в user_endurance_records!"
    st_after = await state.get_state()
    print("Состояние после ввода секунд:", st_after)
    assert st_after is None, "state не очищен"
    print("\nТЕСТ ПРОЙДЕН: секунды приняты и сохранены")

asyncio.run(main())
