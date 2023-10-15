import time
import uuid

from aiogram import F
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, ReplyKeyboardMarkup, \
    KeyboardButton
from yookassa import Payment

from database import User
from helpers import check_access, get_user, check_payment
from settings import session, dp, test_days


@dp.message(lambda x: not check_access(x, 1))
async def no_payment(message: Message):
    user = get_user(message.chat.id, session)
    k = [[InlineKeyboardButton(text="Оплатить", callback_data="buy")]]
    if user and user.test_period_status == 0:
        k.append([InlineKeyboardButton(text="Активировать пробный период", callback_data="start_test")])
        await message.answer("Вам доступны 3 дня пробного периода.")
    elif not user:
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
        if await check_payment(payment.id, message.chat.id):
            print('successful_payment:')
            keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Меню")]], resize_keyboard=True)
            user = get_user(message.chat.id, session)
            user.access_level = 1
            user.buy_expires = str(round(time.time() + 2678400))
            session.commit()
            await message.answer("Оплата успешна.", reply_markup=keyboard)
    else:
        await message.answer("Что-то не так, обратитесь к разработчику.")