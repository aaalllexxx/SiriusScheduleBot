from aiogram import F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, \
    ReplyKeyboardMarkup, Message

from database import Group
from helpers import check_buy, get_user, get_group, check_state, get_teacher
from settings import dp, session


def get_inline_for_groups(user_id):
    user = get_user(user_id)

    user_group = get_group(user.group_id)
    groups = [group.name for group in session.query(Group).all()]
    groups.sort()
    keys = []
    for i in range(0, len(groups), 2):
        group = groups[i]
        if group == user_group.name:
            keys.append([InlineKeyboardButton(text=f"{group}✅", callback_data=group),
                         InlineKeyboardButton(text=f"{groups[i + 1]}❌", callback_data=groups[i + 1])])
        elif groups[i + 1] == user_group.name:
            keys.append([InlineKeyboardButton(text=f"{group}❌", callback_data=group),
                         InlineKeyboardButton(text=f"{groups[i + 1]}✅", callback_data=groups[i + 1])])
        else:
            keys.append([InlineKeyboardButton(text=f"{group}❌", callback_data=group),
                         InlineKeyboardButton(text=f"{groups[i + 1]}❌", callback_data=groups[i + 1])])
    keys.append([InlineKeyboardButton(text="Готово", callback_data="menu")])
    return keys


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
    await query.answer()
    if not await check_buy(query.message):
        return await query.message.answer("Сначала оплатите подписку. Команда: /buy")

    user = get_user(query.message.chat.id)
    keyboard = InlineKeyboardMarkup(inline_keyboard=get_inline_for_groups(user.chat_id))
    await query.message.delete()
    await query.message.answer("В какой группе вы учитесь?", reply_markup=keyboard)
    user = get_user(query.message.chat.id)
    user.state = "set_group"
    session.commit()


@dp.message(lambda x: check_state(x, state="set_name"))
async def set_name(message: Message):
    if not await check_buy(message):
        return await message.answer("Сначала оплатите подписку. Команда: /buy")
    user = get_user(message.chat.id)
    if user:
        user.name = message.text[:101]
        teacher = get_teacher(message.chat.id)
        if teacher:
            teacher.name = user.name
        user.state = ""
        session.commit()
        await message.answer("Имя установлено.")


@dp.callback_query(lambda x: check_state(x, state="set_group"))
async def set_group(query: CallbackQuery):
    message = query.message
    if not await check_buy(message):
        return await message.answer("Сначала оплатите подписку. Команда: /buy")

    user = get_user(message.chat.id)
    if user:
        if query.data == get_group(user.group_id).name:
            return await query.answer("Вы уже выбрали эту группу.")

        user.group_id = session.query(Group).filter_by(name=query.data).first().id
        session.commit()
        keyboard = InlineKeyboardMarkup(inline_keyboard=get_inline_for_groups(user.chat_id))
        await query.answer("Группа выбрана.")
        return await message.edit_text("Выберите груупу:", reply_markup=keyboard)
