from aiogram import Bot
import os
from dotenv import load_dotenv
from aiogram import Dispatcher

load_dotenv()

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher(bot=bot)
chat_id_list = os.getenv("CHAT_ID").split(',')
chat_id_list = list(map(int, chat_id_list))
TIMER = int(os.getenv("TIMER"))
