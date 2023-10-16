from aiogram import F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, \
    ReplyKeyboardMarkup, Message

from database import Group
from helpers import check_buy, get_user, get_group, check_state, get_teacher
from settings import dp, session


@dp.callback_query(F.data == "profile_edit")
async def edit_callback(query: CallbackQuery):
    if not await check_buy(query.message):
        await query.answer()
        return await query.message.answer("Сначала оплатите подписку. Команда: /buy")
    user = get_user(query.message.chat.id)
    if user:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Имя", callback_data="edit_name")],
                             [InlineKeyboardButton(text="Группа", callback_data="edit_group")],
                             [InlineKeyboardButton(text="Назад", callback_data="profile")]])
        await query.message.edit_text("Что хотите изменить?", reply_markup=keyboard)
        return await query.answer()


@dp.callback_query(F.data == "profile")
async def profile_callback(query: CallbackQuery):
    if not await check_buy(query.message):
        await query.answer()
        return await query.message.answer("Сначала оплатите подписку. Команда: /buy")

    user = get_user(query.message.chat.id)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Изменить", callback_data="profile_edit")],
                         [InlineKeyboardButton(text="Назад", callback_data="menu")]])
    if user:
        group = get_group(user.group_id)
        text = f"Имя: {user.name}\n" + (f"Группа: {group.name}" if group else "Группа: не установлена.")
        await query.message.edit_text(text, reply_markup=keyboard)
    return await query.answer()


@dp.callback_query(F.data == "edit_name")
async def edit_name(query: CallbackQuery):
    await query.message.answer("Как я могу вас называть?")
    await query.answer()
    user = get_user(query.message.chat.id)
    user.state = "set_name"
    session.commit()
    return query.answer()


@dp.callback_query(F.data == "edit_group")
async def edit_group(query: CallbackQuery):
    if not await check_buy(query.message):
        await query.answer()
        return await query.message.answer("Сначала оплатите подписку. Команда: /buy")

    keys = []
    groups = session.query(Group).all()
    groups.sort(key=lambda x: x.name)
    for group in groups:
        keys.append([KeyboardButton(text=group.name)])
    keyboard = ReplyKeyboardMarkup(keyboard=keys, resize_keyboard=True)
    await query.message.answer("В какой группе вы учитесь?", reply_markup=keyboard)
    await query.answer()
    user = get_user(query.message.chat.id)
    user.state = "set_group"
    session.commit()


@dp.message(lambda x: check_state(x, state="set_name"))
async def set_name(message: Message):
    if not await check_buy(message):
        return await message.answer("Сначала оплатите подписку. Команда: /buy")

    user = get_user(message.chat.id)
    if user:
        user.name = message.text
        teacher = get_teacher(message.chat.id)
        if teacher:
            teacher.name = user.name
        user.state = ""
        session.commit()
        await message.answer("Имя установлено.")


@dp.message(lambda x: check_state(x, state="set_group"))
async def set_group(message: Message):
    if not await check_buy(message):
        return await message.answer("Сначала оплатите подписку. Команда: /buy")

    user = get_user(message.chat.id)
    keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Меню")]], resize_keyboard=True)
    if user:
        name = "".join(message.text.lower().replace("k", "к").replace("m", "м").capitalize().split())
        group = session.query(Group).filter_by(name=name).first()
        if group:
            user.group_id = group.id
            await message.answer("Группа установлена.", reply_markup=keyboard)
        else:
            await message.answer("Такой группы нет в списке.", reply_markup=keyboard)
        user.state = ""
        session.commit()
