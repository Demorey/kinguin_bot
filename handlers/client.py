import asyncio
import json
from aiogram import types, Dispatcher
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from create_bot import dp, bot, chat_id
from handlers.other import get_prod_list, check_prod, add_product, get_prod_name, get_all_products, get_prod_qty
from config import TIMER

sec_timer = TIMER
start_iter = 1


# def register_handlers_client(dp: Dispatcher):
#     dp.register_message_handler(command_start, commands=['start'])
#     dp.register_message_handler(check_now, commands=['check'])
#     dp.register_message_handler(edit_timer, commands=['timer'])
#     dp.register_message_handler(check_time, commands=['time'])
#     dp.register_message_handler(help, commands=['help'])
#     dp.register_message_handler(add_new_prod, commands=['add'])
#     dp.register_message_handler(delete_prod, commands=['delete'])

@dp.message_handler(commands='start')
async def command_start(message: types.Message):
    await bot.send_message(message.from_user.id, f'Ваш id: {message.from_user.id} \n /help - узнать комманды')


@dp.message_handler(commands='check')
async def check_now(message: types.Message):
    if message.from_user.id in chat_id:
        await check_price(check_now=1)


@dp.message_handler(commands='add')
async def add_new_prod(message: types.Message):
    if message.from_user.id in chat_id:
        product_id = message.text.split(' ')[1]
        prod_name = get_prod_name(product_id)
        if prod_name is not None:
            prod_list = get_prod_list()
            for prod in prod_list:
                if prod['name'] == get_prod_name(product_id):
                    await bot.send_message(message.from_user.id, f'❌ Продукт <b>{prod_name}</b> уже в списке!',
                                           parse_mode='HTML')
                    return
            confirm_btn = InlineKeyboardButton('✅', callback_data=f'add_confirm_{product_id}')
            cancel_btn = InlineKeyboardButton('❌', callback_data='add_cancel')
            choose = InlineKeyboardMarkup(row_width=2).row(confirm_btn, cancel_btn)
            await bot.send_message(message.from_user.id,
                                   f'Вы хотите добавить <b>{prod_name}</b> в список для проверки?', parse_mode='HTML',
                                   reply_markup=choose)
        else:
            await bot.send_message(message.from_user.id,
                                   f'❌ По id-<b>{product_id}</b> не найдено ни одного продукта!', parse_mode='HTML')


@dp.message_handler(commands='delete')
async def delete_prod(message: types.Message):
    if message.from_user.id in chat_id:
        prod_list = get_prod_list()
        products = ''
        keys = []
        numb_prod = InlineKeyboardMarkup(row_width=5)
        for prod in prod_list:
            indx = prod_list.index(prod)
            prod_name = prod['name']
            # last_price = prod['last_price']
            # qty = get_prod_qty(prod['id'])
            products = products + f'{indx + 1} | {prod_name} \n' \
                # ' | {last_price} | {qty} шт. | \n'.replace('.', '.﻿')

            btn = InlineKeyboardButton(f'{indx + 1}', callback_data=f'delete_{indx + 1}')
            keys.append(btn)

        numb_prod = InlineKeyboardMarkup(row_width=5).row(*keys)
        numb_prod.add(InlineKeyboardButton(f'Отмена', callback_data='delete_cancel'))
        await bot.send_message(message.from_user.id,
                               f'❌ <b>Список продуктов для удаления:</b>\n \n'
                               f'{products}', parse_mode='HTML', reply_markup=numb_prod)


@dp.message_handler(commands='help')
async def help(message: types.Message):
    if message.from_user.id in chat_id:
        await bot.send_message(message.from_user.id,
                               f'''<b>Команды для управления:</b>\n
/start - узнать ваш user_id\n
/check - отправки команды будет произведена проверка всех продуктов\n
/time  - узнать текущий таймер для оповещений\n
/timer <u>секунды</u> - где после команды через пробел указать количество секунд через которое будет приходить уведомление, {TIMER} секунд по умолчанию\n
/add <u>id</u> - добавление продукта для отслеживания\n
/delete - отобразить список с отслеживаемыми играми с возможностью удаления''',
                               parse_mode='HTML')


@dp.message_handler(commands='time')
async def check_time(message: types.Message):
    if message.from_user.id in chat_id:
        await bot.send_message(message.from_user.id, f'Текущий таймер: {sec_timer} секунд')


@dp.message_handler(commands='timer')
async def edit_timer(message: types.Message):
    if message.from_user.id in chat_id and message.get_args().isdigit():
        global sec_timer
        sec_timer = int(message.get_args())
        for chat in chat_id:
            await bot.send_message(chat,
                                   f'Таймер до повторной проверки обновлен: {message.get_args()} секунд')


@dp.callback_query_handler(lambda call: call.data)
async def process_callback(callback_query: types.CallbackQuery):
    if callback_query.data.startswith('skip_'):
        prod_list = get_prod_list()
        index = int(callback_query.data.split('skip_')[1])
        prod_list[index]['skip'] = 1
        with open('products.json', 'w') as f:
            json.dump(prod_list, f, indent=2)
        await callback_query.message.delete()

    elif callback_query.data.startswith('add_'):
        index = callback_query.data.split('_')[1]
        if index == 'confirm':
            prod_id = callback_query.data.split('_')[2]
            add_product(prod_id)
            for chat in chat_id:
                await bot.send_message(chat,
                                       f'✅ Продукт\n<b>{get_prod_name(prod_id)}</b>\nУспешно добавлен в список для проверки!',
                                       parse_mode='HTML')
        else:
            await callback_query.message.delete()
            await bot.send_message(callback_query.from_user.id, '❌ Добавление отменено!')
        await callback_query.message.delete()

    elif callback_query.data.startswith('delete_'):
        if callback_query.data.split('_')[1] == 'cancel':
            await callback_query.message.delete()
        else:
            prod_indx = int(callback_query.data.split('_')[1])
            prod_list = get_prod_list()
            prod_on_remove = prod_list.pop(prod_indx - 1)
            prod_name = prod_on_remove['name']
            prod_id = prod_on_remove['id']
            with open('products.json', 'w') as f:
                json.dump(prod_list, f, indent=2)
            for chat in chat_id:
                await callback_query.message.delete()
                await bot.send_message(chat,
                                       f'✅ Продукт\n<b>{prod_name}\nID <code>{prod_id}</code></b>\nУдален из списка!',
                                       parse_mode='HTML')


async def check_price(check_now=0):
    prod_list = get_prod_list()
    all_games_list = get_all_products(prod_list)
    for game in all_games_list:
        checking_prod = prod_list[all_games_list.index(game)]
        await check_prod(prod_list, game, checking_prod, check_now)


async def task():
    global start_iter
    global sec_timer
    while True:
        if start_iter == 1:
            start_iter = 0
            await asyncio.sleep(sec_timer)
            continue
        else:
            await check_price()
            await asyncio.sleep(sec_timer)
