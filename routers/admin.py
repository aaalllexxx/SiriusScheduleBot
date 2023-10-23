from aiogram.types import Message

from database import User
from helpers import check_access, get_user, replacements
from settings import session, dp


@dp.message(lambda x: check_access(x, 11) and "/set" in x.text)
async def set_to_database(message: Message):
    args = message.text.split()[1:]
    if args:
        try:
            args[2] = " ".join(args[2:])
            ident = int(args[0])
            user = get_user(ident)
            setattr(user, args[1], args[2])
            session.commit()
            await message.answer(f"Параметр {args[1]} изменён на {args[2]}")

        except ValueError:
            if "user" in args[0].lower():
                table = User
