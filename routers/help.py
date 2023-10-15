from aiogram import F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from helpers import check_buy
from settings import dp
from helpers import help


@dp.callback_query(F.data == "help")
async def help_callback(query: CallbackQuery):
    if not await check_buy(query.message):
        await query.answer()
        return await query.message.answer("Сначала оплатите подписку. Команда: /buy")

    await query.message.answer(help(query.message))
    await query.answer()


@dp.message(Command("help"))
async def help_message(message: Message):
    if not await check_buy(message):
        return await message.answer("Сначала оплатите подписку. Команда: /buy")

    await message.answer(help(message))
