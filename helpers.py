import asyncio
import json
import time

from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from yookassa import Payment

from database import User, Group, Teacher
from settings import session, levels, pairs, env

replacements = {}


def get_user(chat_id, check_rep=True) -> User:
    if int(chat_id) in list(replacements) and check_rep:
        chat_id = str(replacements[chat_id])
    user = session.query(User).filter_by(chat_id=chat_id).first()
    return user or None


def get_group(group_id) -> Group:
    group = session.query(Group).filter_by(id=group_id).first()
    return group or None


class Pair:
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __getitem__(self, item):
        return self.left if item == self.right else self.right if item == self.left else None

    def __contains__(self, item):
        return item == self.left or item == self.right


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


def get_teacher(chat_id):
    return session.query(Teacher).filter_by(chat_id=chat_id).first()


async def check_buy(message):
    user = get_user(message.chat.id)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Оплатить", callback_data="buy")]])
    if user and user.access_level > 0:
        if user.buy_expires and len(user.buy_expires) > 2 and int(user.buy_expires) > round(time.time()):
            return True
        user.access_level = 0
        await message.answer("Ваша подписка закончена(", keyboard=keyboard)
    user.state = ""
    session.commit()
    return False


def check_state(message, state):
    return get_user(message.chat.id).state.split("::")[0] == state


async def check_payment(payment_id, chat_id):
    payment = json.loads((Payment.find_one(payment_id)).json())
    while payment['status'] == 'pending':
        payment = json.loads((Payment.find_one(payment_id)).json())
        await asyncio.sleep(3)

    if payment['status'] == 'succeeded':
        print(f"SUCCSESS RETURN {chat_id}")
        print(payment)
        return True
    else:
        print(f"BAD RETURN {chat_id}")
        print(payment)
        return False


def check_access(message, access, check_rep=True):
    user = get_user(message.chat.id, check_rep)
    if user and user.access_level >= access:
        return True
    return False


def help(message: Message):
    user: User = get_user(message.chat.id)
    text = "Вот доступные команды:\n\n" \
           "/schedule - моё расписание\n"
    if user.access_level >= 10:
        text += "/users {count}- список пользователей\n" \
                "/login {id} - войти в аккаут пользователя\n" \
                "/exit - вернуться в свой аккаунт\n" \
                "/chat - Войти в чат с пользователем\n" \
                "/stop - Остановить чат с пользователем\n" \
                "/send {id} {text} - отправить сообщение пользователю"

    return text


def id_in_pairs(ident):
    for pair in pairs:
        if ident in pair:
            return True
    return False


def get_pair(ident):
    for pair in pairs:
        if ident in pair:
            return pair
    return False
