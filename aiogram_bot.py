import os
import asyncio
from aiogram.utils import executor
import handlers
from aiogram import Bot
from aiogram.dispatcher import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from dotenv import load_dotenv

load_dotenv()

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher(bot, storage=MemoryStorage())
chat_id_list = os.getenv("CHAT_ID").split(',')
TIMER = os.getenv("TIMER")


async def on_startup(_):
    print('Бот запущен')


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(handlers.client.task())

    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
