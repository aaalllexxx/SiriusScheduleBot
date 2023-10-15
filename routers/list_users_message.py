from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from database import User
from helpers import check_access
from settings import dp, session


@dp.message(lambda x: check_access(x, 10, False) and ("/users" in x.text))
async def list_users_message(message: Message):
    users = session.query(User).all()
    count = 10
    data = message.text.split()
    if len(data) >= 2:
        count = int(data[1])
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="<", callback_data=f"list_-1_{count}"),
                                                      InlineKeyboardButton(text=">", callback_data=f"list_1_{count}")]])

    users = users[0:count]
    if not users:
        users = users[0:]
    max_userID = max([len(u.chat_id) for u in users])
    msg = f"n | chat ID{' ' * (max_userID - 7)} | name\n"
    for j, user in enumerate(users):
        msg += f"{j + 1} | {user.chat_id}{' ' * (max_userID - len(user.chat_id))} | {user.name}\n"

    await message.answer(msg, reply_markup=keyboard)


@dp.callback_query(lambda x: check_access(x.message, 10) and "list" in x.data)
async def list_users(query: CallbackQuery):
    users = session.query(User).all()
    count = int(query.data.split("_")[2])
    max_userID = 7
    i = int(query.data.split("_")[1])
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="<", callback_data=f"list_{i - 1}_{count}"),
                          InlineKeyboardButton(text=">", callback_data=f"list_{i + 1}_{count}")]])

    users = users[i * count:count * (i + 1)]
    if not users:
        users = users[i * count:]
    if users:
        max_userID = max([len(u.chat_id) for u in users])
    msg = f"n | chat ID{' ' * (max_userID - 7)} | name\n"
    for j, user in enumerate(users):
        msg += f"{i * count + j + 1} | {user.chat_id}{' ' * (max_userID - len(user.chat_id))} | {user.name}\n"

    await query.message.edit_text(msg, reply_markup=keyboard)
