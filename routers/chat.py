from aiogram.types import Message

from helpers import id_in_pairs, get_pair, check_access, get_user, Pair
from settings import dp, bot, pairs, session


@dp.message(lambda x: id_in_pairs(x.chat.id))
async def chat(message: Message):
    pair = get_pair(message.chat.id)
    if "/stop" in message.text:
        await message.answer("Вы вышли из беседы.")
        await bot.send_message(pair[message.chat.id], "Собеседник вышел из беседы.")
        pairs.remove(pair)
        return
    await bot.send_message(pair[message.chat.id], f"{message.from_user.full_name}: {message.text}")


@dp.message(lambda x: check_access(x, 10, False) and ("/chat" in x.text))
async def create_chat(message: Message):
    global replacements
    args = message.text.replace("{", "").replace("}", "").split()
    if len(args) >= 2:
        part = get_user(args[1], session, False)
        if part.access_level > 0:
            pairs.append(Pair(message.chat.id, int(args[1])))
            admin = get_user(message.chat.id, session, False)
            await bot.send_message(args[1],
                                   f"Администратор {admin.name} добавил вас в личный чат.\nОн увидит все последующие сообщения."
                                   f"\nЧтобы выйти из чата, пропишите /stop")
            return await message.answer(f"Вы подключились к {part.name}")
        return await message.answer(f"У {part.name} недостаточно доступа.")
    return await message.answer("/chat {id}")
