import asyncio
import json
import time

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import bot
from bot import session, days, days_ru
from database import Group, User
from parser import parse

start_time = time.time()
last = 0
time_delta = 60 * 30


async def parse_schedule():
    global last
    admin = session.query(User).filter_by(access_level=10).first()
    while True:
        try:
            if last != round(time.time() - start_time):
                last = round(time.time() - start_time)

            if last % time_delta == 0:
                await bot.bot.send_message(admin.chat_id, "Начинаю парсинг.")
                groups = session.query(Group).all()
                for group in groups:
                    print(f"start parsing {group.name}")
                    sched = parse(group.name)
                    print(f"finished parsing {group.name} with result {sched}")
                    if sched:
                        for day in days:
                            sc = json.dumps(sched[day], ensure_ascii=False)
                            if sc != getattr(group, day):
                                setattr(group, day, sc)
                                session.commit()
                                for user in session.query(User).filter_by(group_id=group.id):
                                    try:
                                        all_keyboard = InlineKeyboardMarkup(
                                            inline_keyboard=[
                                                [InlineKeyboardButton(text="Посмотреть", callback_data="schedule")]])
                                        await bot.bot.send_message(user.chat_id,
                                                                   f"Изменение в расписании на {days_ru[days.index(day)]}",
                                                                   reply_markup=all_keyboard)
                                    except Exception as e:
                                        print(e)
                        print(f"schedule for {group.name} was set")
                await bot.bot.send_message(admin.chat_id, "Парсинг окончен")
        except Exception as e:
            await bot.bot.send_message(admin.chat_id, str(e))


if __name__ == "__main__":
    asyncio.run(parse_schedule())