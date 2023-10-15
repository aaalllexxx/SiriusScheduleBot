from aiogram import Dispatcher, Bot
from aiogram.types import LabeledPrice
from dotenv import dotenv_values
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from yookassa import Configuration

from database import Base

env = dotenv_values(".env")

api_endpoint = "https://api.yookassa.ru/v3/"
bot = Bot(env["TOKEN"])

test_days = 3

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

SHOP_TOKEN = env["YOOKASSA_TOKEN"]
times = ["9:00-10:30", "10:45-12:15", "13:15-14:45", "15:00-16:30", "16:45-18:15", "18:30-20:00", "", "", ""]
Configuration.account_id = int(env["SHOP_ID"])
Configuration.secret_key = SHOP_TOKEN
pairs = []
