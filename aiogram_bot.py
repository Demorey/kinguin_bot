import asyncio
from aiogram.utils import executor
import handlers
from create_bot import dp


async def on_startup(_):
    print('Бот запущен')


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(handlers.client.task())

    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
