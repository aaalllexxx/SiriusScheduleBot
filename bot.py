import asyncio
import uuid
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
from yookassa import Configuration, Payment

Checker(os.getpid())
api_endpoint = "https://api.yookassa.ru/v3/"
env = dotenv_values(".env")
bot = Bot(env["TOKEN"])

test_days = env.get("TEST_DAYS") or 3 / 60 / 60 / 24 * 10

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
SHOP_TOKEN = env["YOOKASSA_TOKEN"]
times = ["9:00-10:30", "10:45-12:15", "13:15-14:45", "15:00-16:30", "16:45-18:15", "18:30-20:00", "", "", ""]
Configuration.account_id = int(env["SHOP_ID"])
Configuration.secret_key = SHOP_TOKEN



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


async def check_payment(payment_id):
    payment = json.loads((Payment.find_one(payment_id)).json())
    while payment['status'] == 'pending':
        payment = json.loads((Payment.find_one(payment_id)).json())
        await asyncio.sleep(3)

    if payment['status'] == 'succeeded':
        print("SUCCSESS RETURN")
        print(payment)
        return True
    else:
        print("BAD RETURN")
        print(payment)
        return False


def check_access(message, access):
    user = get_user(message.chat.id, session)
    if user and user.access_level >= access:
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


@dp.message(lambda x: x.chat.id != 5237472052 and test())
async def tech_work(message):
    return await message.answer("Ведутся технические работы, ожидайте.")


@dp.callback_query(lambda x: x.message.chat.id != 5237472052 and test())
async def tech_callback(query):
    return await query.message.answer("Ведутся технические работы, ожидайте.")


@dp.message(lambda x: not check_access(x, 1))
async def no_payment(message: Message):
    user = get_user(message.chat.id, session)
    k = [[InlineKeyboardButton(text="Оплатить", callback_data="buy")]]
    if user and user.test_period_status == 0:
        k.append([InlineKeyboardButton(text="Активировать пробный период", callback_data="start_test")])
        await message.answer("Вам доступны 3 дня пробного периода.")
    else:
        fname = message.from_user.first_name
        lname = message.from_user.last_name
        new_user = User(chat_id=message.chat.id,
                        name=f"{fname if fname else ''}{' ' + lname if lname else ''}",
                        group_id=0,
                        access_level=0)
        session.add(new_user)
        session.commit()
        k.append([InlineKeyboardButton(text="Активировать пробный период", callback_data="start_test")])
        await message.answer("Вам доступны 3 дня пробного периода.")

    keyboard = InlineKeyboardMarkup(inline_keyboard=k)
    return await message.answer(
        "К сожалению, сервер, на котором хостится бот не бесплатный, так что оплатите, пожалуйста, подписку😁",
        reply_markup=keyboard)


@dp.callback_query(F.data == "start_test")
async def start_test_period(query: CallbackQuery):
    global test_days
    await query.answer()
    user = get_user(query.message.chat.id, session)
    if user.test_period_status == 0:
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[[KeyboardButton(text="Меню")]])
        user.test_period_status = 1
        user.buy_expires = str(int(round(time.time()) + test_days * 60 * 60 * 24))
        user.access_level = 2
        session.commit()
        await query.message.answer("Пробная подписка активна.", keyboard=keyboard)


@dp.callback_query(F.data == "buy")
async def buy(query: CallbackQuery):
    await query.answer()
    user = get_user(query.message.chat.id, session)
    message = query.message
    uid = uuid.uuid4()
    key = str(uuid.uuid4())
    payment = Payment.create({
        "id": f"{uid}",
        "amount": {
            "value": "60.00",
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://t.me/SiriusElzhurBot"
        },
        "capture": True,
        "receipt": {
            "customer": {
                "email": "a.aabdelnur@mail.ru"
            },
            "items": [
                {
                    "description": "Подписка на месяц",
                    "quantity": "1.00",
                    "amount": {
                        "value": "60.00",
                        "currency": "RUB"
                    },
                    "vat_code": "4",
                    "payment_mode": "full_prepayment",
                    "payment_subject": "marked",
                    "mark_mode": 0,
                    "mark_code_info":
                        {
                            "gs_1m": "DFGwNDY0MDE1Mzg2NDQ5MjIxNW9vY2tOelDFuUFwJh05MUVFMDYdOTJXK2ZaMy9uTjMvcVdHYzBjSVR3NFNOMWg1U2ZLV0dRMWhHL0UrZi8ydkDvPQ=="
                        },
                    "measure": "piece"
                }
            ]
        },
        "description": "Подписка на месяц",
    }, key)
    if payment:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Оплатить", url=payment.confirmation.confirmation_url)]])
        await message.answer("Ссылка для оплаты:", reply_markup=keyboard)
        if await check_payment(payment.id):
            print('successful_payment:')
            keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Меню")]], resize_keyboard=True)
            user = get_user(message.chat.id, session)
            user.access_level = 1
            user.buy_expires = str(round(time.time() + 2678400))
            session.commit()
            await message.answer("Оплата успешна.", reply_markup=keyboard)
    else:
        await message.answer("Что-то не так, обратитесь к разработчику.")


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
    print("start\n")
    await dp.start_polling(bot)
    print("bye!")


if __name__ == "__main__":
    asyncio.run(main())
