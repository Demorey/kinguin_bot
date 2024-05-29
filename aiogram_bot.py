import asyncio
import os
import logging
from handlers.client import task
from create_bot import dp, bot
from logging.handlers import RotatingFileHandler

if not os.path.isdir("logs/"):
    os.makedirs("logs/")
if not os.path.exists("logs/debug_loger.log"):
    open('logs/debug_loger.log', 'a').close()

logging.basicConfig(level=logging.DEBUG, encoding='utf-8',
                    handlers=[RotatingFileHandler('logs/debug_loger.log', maxBytes=5000000, backupCount=1)],
                    format="%(asctime)s - [%(levelname)s] - %(funcName)s: %(lineno)d - %(message)s")

async def bot_start():
    try:
        bot_name = await bot.get_me()
        print('Запущен бот: ' + bot_name.first_name)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


async def main():
    tasks = [bot_start()
             # , task()
             ]
    await asyncio.gather(*tasks)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print('Bot stopped!')
