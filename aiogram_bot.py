import asyncio
from aiogram.utils import executor
from create_bot import dp
from handlers.client import task  # register_handlers_client


async def on_startup(_):
    print('Бот запущен')


if __name__ == '__main__':
    # register_handlers_client(dp)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(task())

    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
