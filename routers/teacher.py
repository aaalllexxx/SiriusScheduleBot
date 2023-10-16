import time

from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from database import User, Teacher
from helpers import check_access, get_user
from settings import dp, bot, session
import json

delta = 60 * 10


@dp.message(lambda x: "/ask" in x.text)
async def ask_for_teacher(message: Message):
    with open("temp/asks.json") as file:
        data = json.loads(file.read() or "{}")
        file.close()
    chat_id = str(message.chat.id)
    keys = list(data)
    if chat_id in keys and round(time.time()) >= data[chat_id] or chat_id not in keys:
        data[chat_id] = round(time.time()) + delta
        with open("temp/asks.json", "w") as file:
            file.write(json.dumps(data))
            file.close()
        admins = session.query(User).where(User.access_level >= 10).all()
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="Да", callback_data=f"teacher-accept_{message.chat.id}"),
            InlineKeyboardButton(text="Нет", callback_data=f"teacher-decline_{message.chat.id}")
        ]])
        for admin in admins:
            await bot.send_message(
                admin.chat_id,
                f"Новая заявка от <a href='https://t.me/{message.from_user.username}'>{message.from_user.full_name}</a>\n"
                f"Это преподаватель?",
                parse_mode="html",
                reply_markup=keyboard
            )
        return await message.answer("Заявка подана. Ожидайте подтверждения.")
    return message.answer(
        f"Вы уже подавали заявку.\nДля того, чтобы подать её ещё раз, подождите {data[chat_id] - round(time.time())} секунд.")


@dp.callback_query(lambda x: check_access(x.message, 10) and "teacher-accept" in x.data)
async def accept_teacher(query: CallbackQuery):
    await query.answer()
    teacher_id = query.data.split("_")[1]
    user = get_user(teacher_id)
    teacher = Teacher(chat_id=user.chat_id)
    user.access_level = 5
    session.add(teacher)
    session.commit()
    await query.message.answer("Учитель добавлен.")
    await bot.send_message(user.chat_id,
                           "Администратор подтвердил, что вы преподаватель.\n"
                           "Как только ваше расписание подгрузится, вам придёт уведомление.\n"
                           "А сейчас пропишите /start, выберите 'профиль' -> 'изменить' -> 'имя' и отправьте свои ФИО.")


@dp.callback_query(lambda x: check_access(x.message, 10) and "teacher-decline" in x.data)
async def decline_teacher(query: CallbackQuery):
    await query.answer()
    teacher_id = query.data.split("_")[1]
    await query.message.edit_text("Заявка отклонена.")
    await bot.send_message(teacher_id, "Администратор отклонил вашу заявку.")
