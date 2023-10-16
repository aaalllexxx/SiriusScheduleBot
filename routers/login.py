from aiogram.types import Message

from helpers import check_access, get_user, replacements
from settings import session, dp


@dp.message(lambda x: check_access(x, 10, False) and ("/login" in x.text))
async def login(message: Message):
    global replacements
    args = message.text.split()
    if len(args) >= 2:
        ident = int(args[1])
        replacements[message.chat.id] = ident
        await message.answer(f"Теперь вы {get_user(message.chat.id).name}")
    else:
        await message.answer("Введи все нужные параметры. {id}")


@dp.message(lambda x: check_access(x, 10, False) and ("/exit" in x.text))
async def exit_login(message: Message):
    global replacements
    if message.chat.id in list(replacements):
        del replacements[message.chat.id]
    await message.answer("Вы вернулись в свой профиль.")
