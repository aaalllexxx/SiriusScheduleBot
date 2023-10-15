from helpers import test
from settings import dp


@dp.message(lambda x: x.chat.id != 5237472052 and test())
async def tech_work(message):
    return await message.answer("Ведутся технические работы, ожидайте.")


@dp.callback_query(lambda x: x.message.chat.id != 5237472052 and test())
async def tech_callback(query):
    return await query.message.answer("Ведутся технические работы, ожидайте.")
