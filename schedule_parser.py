import asyncio
import json
import time

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import bot
from settings import session, days, days_ru
from database import Group, User, Teacher
from checker import print
from parser import parse, parse_teacher

start_time = time.time()
last = 0
time_delta = 30 * 60


async def parse_schedule():
    global last
    admin = session.query(User).filter_by(access_level=10).first()
    print("start parsing")
    while True:
        try:
            if last != round(time.time() - start_time):
                last = round(time.time() - start_time)

            if last % time_delta == 0:
                teachers = session.query(Teacher).all()
                print("parsing teachers...")
                for teacher in teachers:
                    sched = parse_teacher(str(teacher.name))
                    if sched:
                        for day in days:
                            sc = json.dumps(sched[day], ensure_ascii=False)
                            if sc != getattr(teacher, day):
                                setattr(teacher, day, sc)
                                session.commit()
                                print(f"schedule for {teacher.name} was set")
                                try:
                                    all_keyboard = InlineKeyboardMarkup(
                                        inline_keyboard=[
                                            [InlineKeyboardButton(text="Посмотреть", callback_data="schedule")]])
                                    await bot.bot.send_message(teacher.chat_id,
                                                               f"Изменение в расписании на {days_ru[days.index(day)]}",
                                                               reply_markup=all_keyboard)
                                except Exception as e:
                                    print(f"exception while parsing: {e}")

                groups = session.query(Group).all()
                print("parsing groups...")
                for group in groups:
                    sched = parse(group.name)
                    if sched:
                        for day in days:
                            sc = json.dumps(sched[day], ensure_ascii=False)
                            if sc != getattr(group, day):
                                setattr(group, day, sc)
                                session.commit()
                                print(f"schedule for {group.name} was set")
                                for user in session.query(User).filter_by(group_id=group.id):
                                    try:
                                        all_keyboard = InlineKeyboardMarkup(
                                            inline_keyboard=[
                                                [InlineKeyboardButton(text="Посмотреть", callback_data="schedule")]])
                                        await bot.bot.send_message(user.chat_id,
                                                                   f"Изменение в расписании на {days_ru[days.index(day)]}",
                                                                   reply_markup=all_keyboard)
                                    except Exception as e:
                                        print(f"exception while parsing: {e}")
                print("stop parsing")
        except Exception as e:
            print(f"exception while parsing: {e}")


if __name__ == "__main__":
    asyncio.run(parse_schedule())
