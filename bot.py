import asyncio
import os
from checker import Checker, print
from settings import dp, bot
import routers.admin
import routers.list_users_message
import routers.send_users
import routers.login
import routers.chat
import routers.tech
import routers.teacher
import routers.payment  # -------------------------- Внизу оплачиваемые функции
import routers.menu
import routers.help
import routers.profile
import routers.schedule

Checker(os.getpid())
required = ["temp/asks.json", "checker.json", "bot.log"]


def create(paths_list):
    for i in paths_list:
        if not os.path.exists(i):
            path = i.split("/")
            for j, el in enumerate(path):
                if not os.path.exists(el):
                    if "." in el:
                        with open(el, "w") as file:
                            file.close()
                    else:
                        os.mkdir(el)
                        path[j+1] = path[j] + "/" + path[j+1]


async def main():
    create(required)
    print("start\n")
    await dp.start_polling(bot)
    print("bye!")


if __name__ == "__main__":
    asyncio.run(main())
