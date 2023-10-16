from aiogram.types import Message

from helpers import check_access, get_user
from settings import session, bot, dp


@dp.message(lambda x: check_access(x, 10, False) and ("/send" in x.text))
async def list_users(message: Message):
    data = message.text.replace("{", "").replace("}", "").replace("\n", " ").split()
    if len(data) >= 3:
        to_id = data[1]
        text = " ".join(data[2:])
        admin = get_user(message.chat.id, False)
        await bot.send_message(to_id, f"Администратор {admin.name} отправил вам сообщение:\n{text}")
        return await message.answer(f"Сообщение пользователю {get_user(to_id, False).name} отправлено.")
    return await message.answer("/send {to_id} {text}")