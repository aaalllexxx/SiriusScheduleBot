from aiogram import F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove

from database import User
from helpers import get_user, check_buy
from settings import dp, session


@dp.message(Command("start"))
@dp.callback_query(F.data == "menu")
async def start(message: Message | CallbackQuery):
    if isinstance(message, Message):
        user = get_user(message.chat.id, session)
    else:
        user = get_user(message.message.chat.id, session)
        await message.answer()
        message = message.message
    if not await check_buy(message):
        return await message.answer("Сначала оплатите подписку. Команда: /buy")
    name = ""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Функции⚙️", callback_data="help")],
                                                     [InlineKeyboardButton(text="Расписание🗓",
                                                                           callback_data="schedule")],
                                                     [InlineKeyboardButton(text="Профиль🙎‍♂️",
                                                                           callback_data="profile")]])
    if user:
        name = user.name
    else:
        fname = message.from_user.first_name
        lname = message.from_user.last_name
        new_user = User(chat_id=message.chat.id,
                        name=f"{fname if fname else ''}{' ' + lname if lname else ''}",
                        group_id=0,
                        access_level=0)
        session.add(new_user)
        session.commit()
    if isinstance(message, Message):
        return await message.answer(f"Привет{', ' + name if name else ''}!", reply_markup=keyboard)
    else:
        await message.message.edit_text(f"Привет{', ' + name if name else ''}!", reply_markup=keyboard)
        return await message.answer()


@dp.message(lambda x: x.text.lower() == "меню")
async def menu(message: Message):
    if not await check_buy(message):
        return await message.answer("Сначала оплатите подписку. Команда: /buy")
    user = get_user(message.chat.id, session)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Функции⚙️", callback_data="help")],
                                                     [InlineKeyboardButton(text="Расписание🗓",
                                                                           callback_data="schedule")],
                                                     [InlineKeyboardButton(text="Профиль🙎‍♂️",
                                                                           callback_data="profile")]])
    if user:
        await message.answer(f"Открываю меню.", reply_markup=ReplyKeyboardRemove())
        return await message.answer(f"Привет, {user.name}!", reply_markup=keyboard)
