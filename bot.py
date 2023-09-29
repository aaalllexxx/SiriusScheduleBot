import asyncio
import datetime
import json
import os
import time

from aiogram import Bot, Dispatcher, F
from aiogram.types import InlineKeyboardButton, Message, InlineKeyboardMarkup, CallbackQuery, ReplyKeyboardMarkup, \
    KeyboardButton, ReplyKeyboardRemove, LabeledPrice, PreCheckoutQuery
from aiogram.filters import Command
from dotenv import dotenv_values
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, User, Group
from helpers import get_user, get_group
from checker import Checker, print

Checker(os.getpid())

env = dotenv_values(".env")
bot = Bot(env["TOKEN"])

dp = Dispatcher()
engine = create_engine(env["SQLITE_PATH"])
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()
db = engine.connect()
days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
days_ru = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]

levels = {
    "user": 0,
    "duty": 50,
    "admin": 100
}

DEFAULT_PRICE = LabeledPrice(label='Базовая подписка на месяц', amount=6000)
SHOP_TOKEN = env["SHOP_API_TOKEN"]
times = ["9:00-10:30", "10:45-12:15", "13:15-14:45", "15:00-16:30", "16:45-18:15", "18:30-20:00", "", "", ""]


def test():
    return env.get("MODE") and env["MODE"] == "TEST"


async def true():
    return True


def test_check_function(func):
    def decorator(*args, **kwargs):
        if env.get("MODE") and env["MODE"] == "TEST":
            return func(*args, **kwargs)
        return true()

    return decorator


def test_bot_function(func):
    def decorator(*args, **kwargs):
        if env.get("MODE") and env["MODE"] == "TEST":
            return func(*args, **kwargs)
        return False

    return decorator


@test_check_function
async def check_buy(message):
    user = get_user(message.chat.id, session)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Оплатить", callback_data="buy")]])
    if user and user.access_level > 0:
        if user.buy_expires and int(user.buy_expires) > round(time.time()):
            return True
        user.access_level = 0
        await message.answer("Ваша подписка закончена(", keyboard=keyboard)
    user.state = ""
    session.commit()
    return False


def check_state(message, state):
    return get_user(message.chat.id, session).state.split("::")[0] == state


def check_access(message, access):
    user = get_user(message.chat.id, session)
    if user.access_level >= access:
        return True
    return False


def help(message: Message):
    user: User = get_user(message.chat.id, session)
    text = "Вот доступные команды:\n\n" \
           "/schedule - моё расписание\n"
    if user.access_level >= levels["duty"]:
        text += ""

    if user.access_level >= levels["admin"]:
        text += "/users - список пользователей\n" \
                "/ban - далить пользователя"

    return text


@dp.message(F.content_type == "successful_payment")
async def process_successful_payment(message: Message):
    print('successful_payment:')
    keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Меню")]], resize_keyboard=True)
    pmnt = json.loads(message.successful_payment.model_dump_json())
    user = get_user(message.chat.id, session)
    user.access_level = 1
    if payload := pmnt.get("invoice_payload"):
        if "month" in payload:
            user.buy_expires = str(round(time.time() + 2678400))
    session.commit()
    await message.answer("Оплата успешна.", reply_markup=keyboard)


@dp.message(lambda x: not check_access(x, 1) and test())
@test_bot_function
async def no_payment(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Оплатить", callback_data="buy")]])
    return await message.answer(
        "К сожалению, сервер, на котором хостится бот не бесплатный, так что оплатите, пожалуйста, подписку😁",
        reply_markup=keyboard)


@dp.callback_query(F.data == "buy")
async def buy(message: Message | CallbackQuery):
    await message.answer()
    if isinstance(message, CallbackQuery):
        message = message.message
    if SHOP_TOKEN.split(":")[1] == "TEST":
        await bot.send_invoice(
            message.chat.id,
            title="Базовая подписка на месяц",
            description="Вам станут доступны просмотр расписания и оповещения об изменении расписания",
            provider_token=SHOP_TOKEN,
            currency='rub',
            is_flexible=False,  # True если конечная цена зависит от способа доставки
            prices=[DEFAULT_PRICE],
            start_parameter='buy-bot',
            payload='default-buy-month'
        )
    else:
        await bot.send_invoice(
            message.chat.id,
            title="Базовая подписка на месяц",
            description="Вам станут доступны просмотр расписания и оповещения об изменении расписания",
            provider_token=SHOP_TOKEN,
            currency='rub',
            is_flexible=False,
            prices=[DEFAULT_PRICE],
            start_parameter='buy-bot',
            payload='default-buy-month'
        )


@dp.message(Command("start"))
@dp.callback_query(F.data == "menu")
async def start(message: Message | CallbackQuery):
    if isinstance(message, Message):
        user = get_user(message.chat.id, session)
    else:
        user = get_user(message.message.chat.id, session)
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
async def start(message: Message):
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


@dp.callback_query(F.data == "help")
async def help_callback(query: CallbackQuery):
    if not await check_buy(query.message):
        await query.answer()
        return await query.message.answer("Сначала оплатите подписку. Команда: /buy")

    await query.message.answer(help(query.message))
    await query.answer()


@dp.callback_query(F.data == "profile_edit")
async def edit_callback(query: CallbackQuery):
    if not await check_buy(query.message):
        await query.answer()
        return await query.message.answer("Сначала оплатите подписку. Команда: /buy")
    user = get_user(query.message.chat.id, session)
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

    user = get_user(query.message.chat.id, session)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Изменить", callback_data="profile_edit")],
                         [InlineKeyboardButton(text="Назад", callback_data="menu")]])
    if user:
        group = get_group(user.group_id, session)
        text = f"Имя: {user.name}\n" + (f"Группа: {group.name}" if group else "Группа: не установлена.")
        await query.message.edit_text(text, reply_markup=keyboard)
    return await query.answer()


@dp.callback_query(F.data == "edit_name")
async def edit_name(query: CallbackQuery):
    await query.message.answer("Как я могу вас называть?")
    await query.answer()
    user = get_user(query.message.chat.id, session)
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
    user = get_user(query.message.chat.id, session)
    user.state = "set_group"
    session.commit()


@dp.message(lambda x: check_state(x, state="set_name"))
async def set_name(message: Message):
    if not await check_buy(message):
        return await message.answer("Сначала оплатите подписку. Команда: /buy")

    user = get_user(message.chat.id, session)
    if user:
        user.name = message.text
        await message.answer("Имя установлено.")
        user.state = ""
        session.commit()


@dp.message(lambda x: check_state(x, state="set_group"))
async def set_group(message: Message):
    if not await check_buy(message):
        return await message.answer("Сначала оплатите подписку. Команда: /buy")

    user = get_user(message.chat.id, session)
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


@dp.callback_query(F.data == "schedule")
@dp.message(Command("schedule"))
async def schedule(message: Message | CallbackQuery):
    if isinstance(message, CallbackQuery):
        await message.answer()
        message = message.message
    if not await check_buy(message):
        return await message.answer("Сначала оплатите подписку. Команда: /buy")

    user = get_user(message.chat.id, session)
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
    user = get_user(query.message.chat.id, session)
    group = get_group(user.group_id, session)
    if not group:
        await query.message.answer(
            "Сначала заполните профиль в меню.\nДля этого пропишите /start и выберите нужный пункт.")
        return await query.answer()
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️", callback_data=f"{days[(days.index(query.data) - 1) % len(days)]}"),
             InlineKeyboardButton(text="➡️", callback_data=f"{days[(days.index(query.data) + 1) % len(days)]}")],
            [InlineKeyboardButton(text="Закрыть❌", callback_data="close_schedule")]
        ])
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
        await query.answer()


@dp.callback_query(F.data == "close_schedule")
async def close(query: CallbackQuery):
    await query.message.delete()
    return await query.answer()


@dp.pre_checkout_query(lambda query: True)
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


async def main():
    print("start")
    await dp.start_polling(bot)
    print("bye!")


if __name__ == "__main__":
    asyncio.run(main())
