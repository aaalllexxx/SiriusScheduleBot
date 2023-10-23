from aiogram.types import Message

from helpers import check_access, get_user, replacements
from settings import dp


@dp.message(lambda x: check_access(x, 10, False) and ("/login" in x.text))
async def login(message: Message):
    global replacements
    args = message.text.split()
    if len(args) >= 2:
        ident = int(args[1])
        user = get_user(ident)
        admin = get_user(message.chat.id)
        if admin.access_level > user.access_level:
            replacements[message.chat.id] = ident
            return await message.answer(f"Теперь вы {get_user(message.chat.id).name}")
        return await message.answer(f"Привилегии этого пользователя выше.")
    await message.answer("Введи все нужные параметры. {id}")


@dp.message(lambda x: check_access(x, 10, False) and ("/exit" in x.text))
async def exit_login(message: Message):
    global replacements
    if message.chat.id in list(replacements):
        del replacements[message.chat.id]
    await message.answer("Вы вернулись в свой профиль.")
