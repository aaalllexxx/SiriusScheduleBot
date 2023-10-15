import asyncio
import os
from checker import Checker, print
from settings import dp, bot
import routers.tech
import routers.list_users_message
import routers.send_users
import routers.login
import routers.chat
import routers.payment
import routers.menu
import routers.help
import routers.profile
import routers.schedule

Checker(os.getpid())


async def main():
    print("start\n")
    await dp.start_polling(bot)
    print("bye!")


if __name__ == "__main__":
    asyncio.run(main())
