from helpers import test, get_user
from settings import dp


@dp.message(lambda x: get_user(x.chat.id).chat_id != "5237472052" and test())
async def tech_work(message):
    return await message.answer("Ведутся технические работы, ожидайте.")


@dp.callback_query(lambda x: get_user(x.message.chat.id).chat_id != "5237472052" and test())
async def tech_callback(query):
    await query.answer()
    return await query.message.answer("Ведутся технические работы, ожидайте.")
