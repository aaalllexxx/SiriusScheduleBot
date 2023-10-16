import json

from aiogram import F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from helpers import check_buy, get_user, get_group, get_teacher
from settings import dp, session, days, times, days_ru


@dp.callback_query(F.data == "schedule")
@dp.message(Command("schedule"))
async def schedule(message: Message | CallbackQuery):
    if isinstance(message, CallbackQuery):
        await message.answer()
        message = message.message
    if not await check_buy(message):
        return await message.answer("Сначала оплатите подписку. Команда: /buy")

    user = get_user(message.chat.id)
    if user:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Понедельник", callback_data="monday")],
                [InlineKeyboardButton(text="Вторник", callback_data="tuesday")],
                [InlineKeyboardButton(text="Среда", callback_data="wednesday")],
                [InlineKeyboardButton(text="Четверг", callback_data="thursday")],
                [InlineKeyboardButton(text="Пятница", callback_data="friday")],
                [InlineKeyboardButton(text="Суббота", callback_data="saturday")]
            ])
        await message.answer("Выберите день недели:", reply_markup=keyboard)


@dp.callback_query(lambda x: x.data in days)
async def display_schedule(query: CallbackQuery):
    if not await check_buy(query.message):
        await query.answer()
        return await query.message.answer("Сначала оплатите подписку. Команда: /buy")
    user = get_user(query.message.chat.id)
    teacher = get_teacher(user.chat_id)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️", callback_data=f"{days[(days.index(query.data) - 1) % len(days)]}"),
             InlineKeyboardButton(text="➡️", callback_data=f"{days[(days.index(query.data) + 1) % len(days)]}")],
            [InlineKeyboardButton(text="Закрыть❌", callback_data="close_schedule")]
        ])
    if teacher:
        sch = json.loads(getattr(teacher, query.data) or "[]")
        sch_text = ""
        for i, lesson in enumerate(sch):
            tm = lesson["time"]
            if not tm:
                tm = times[i]
            sch_text += f"{i + 1}. <b>{lesson['name']}</b>\n    {tm}\n    <u>{lesson['aud']}</u>\n    {lesson['group']}\n    {lesson['type']}".strip() + "\n\n"
        schedule_text = days_ru[days.index(query.data)] + ":\n" + sch_text
        await query.message.edit_text(schedule_text, reply_markup=keyboard, parse_mode="HTML")
        return await query.answer()
    group = get_group(user.group_id)
    if not group:
        await query.message.answer(
            "Сначала заполните профиль в меню.\nДля этого пропишите /start и выберите нужный пункт.")
        return await query.answer()
    if user and group:
        sch = json.loads(getattr(group, query.data) or "[]")
        sch_text = ""
        for i, lesson in enumerate(sch):
            tm = lesson["time"]
            if not tm:
                tm = times[i]
            sch_text += f"{i + 1}. <b>{lesson['name']}</b>\n    {tm}\n    <u>{lesson['aud']}</u>\n    {lesson['teacher']}\n    {lesson['type']}".strip() + "\n\n"
        schedule_text = days_ru[days.index(query.data)] + ":\n" + sch_text
        await query.message.edit_text(schedule_text, reply_markup=keyboard, parse_mode="HTML")
        return await query.answer()


@dp.callback_query(F.data == "close_schedule")
async def close(query: CallbackQuery):
    await query.message.delete()
    return await query.answer()
