import asyncio
import json
from aiogram import types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from create_bot import dp, bot, chat_id_list, TIMER
from handlers.other import get_prod_list, check_prod, add_product, get_prod_name, get_all_products, get_prod_qty, \
    get_prod

sec_timer = TIMER


class states_name(StatesGroup):
    delete = State()
    check = State()


@dp.message_handler(commands='start')
async def command_start(message: types.Message):
    await bot.send_message(message.from_user.id, f'Ваш id: {message.from_user.id} \n /help - узнать комманды')


@dp.message_handler(commands='check')
async def check_now(message: types.Message):
    if message.from_user.id in chat_id_list:
        if not message.get_args() == '':
            if len(message.get_args().split(' ')) > 1:
                await bot.send_message(message.from_user.id, '❌ Введите корректный id')
            else:
                product_id = message.get_args().split(' ')[0]
                if product_id:
                    prod = get_prod(product_id)
                    if prod:
                        await check_prod(check_now=1, prod_id=product_id)
                    else:
                        await bot.send_message(message.from_user.id,
                                               f'❌ По id-<b>{product_id}</b> не найдено ни одного продукта!',
                                               parse_mode='HTML')
        else:
            await states_name.check.set()
            prod_list = get_prod_list()
            products = ''
            # keys = []
            for index, prod in enumerate(prod_list, start=1):
                prod_name = prod['name']
                products = products + f'{index} | {prod_name} \n'
                # btn = InlineKeyboardButton(f'{index}', callback_data=f'check_{index}')
                # keys.append(btn)

            numb_prod = InlineKeyboardMarkup(row_width=5)  # .add(*keys)
            numb_prod.add(InlineKeyboardButton(f'Отмена', callback_data='check_cancel'))
            await bot.send_message(message.from_user.id,
                                   f'📜 <b> Список продуктов для проверки:</b>\n \n'
                                   f'{products}\n'
                                   '<b>Введите порядковые номера продуктов через пробел для проверки или нажмите "Отмена"</b>',
                                   parse_mode='HTML', reply_markup=numb_prod)


@dp.message_handler(state=states_name.check)
async def check_choosed(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['prods_to_check'] = message.text.split()
        prod_list = get_prod_list()
        for prod_indx in data['prods_to_check']:
            indx = int(prod_indx) - 1
            if indx > len(prod_list):
                continue
            prod_to_check = prod_list[indx]
            prod_id = prod_to_check['id']
            await check_prod(check_now=1, prod_id=prod_id)

        await state.finish()


@dp.message_handler(commands='check_all')
async def check_now(message: types.Message):
    if message.from_user.id in chat_id_list:
        confirm_btn = InlineKeyboardButton('✅', callback_data='check_all_confirm')
        cancel_btn = InlineKeyboardButton('❌', callback_data='check_all_cancel')
        choose = InlineKeyboardMarkup(row_width=2).row(confirm_btn, cancel_btn)
        await bot.send_message(message.from_user.id,
                               f'Вы уверены что хотите сделать проверку всех продуктов?',
                               parse_mode='HTML',
                               reply_markup=choose)


@dp.message_handler(commands='add')
async def add_new_prod(message: types.Message):
    if message.from_user.id in chat_id_list:
        product_id = message.text.split(' ')
        if len(product_id) < 2:
            await bot.send_message(message.from_user.id, '❌ Введите корректный id')
            return
        product_id.pop(0)
        for prod_id in product_id:
            prod_name = get_prod_name(prod_id)
            if prod_name is not None:
                prod_list = get_prod_list()
                x = 0
                for prod in prod_list:
                    if prod['id'] == prod_id:
                        await bot.send_message(message.from_user.id, f'❌ Продукт <b>{prod_name}</b> уже в списке!',
                                               parse_mode='HTML')
                        x = 1
                        break
                if not x:
                    confirm_btn = InlineKeyboardButton('✅', callback_data=f'add_confirm_{prod_id}')
                    cancel_btn = InlineKeyboardButton('❌', callback_data='add_cancel')
                    choose = InlineKeyboardMarkup(row_width=2).row(confirm_btn, cancel_btn)
                    await bot.send_message(message.from_user.id,
                                           f'Вы хотите добавить <b>{prod_name}</b> в список для проверки?',
                                           parse_mode='HTML',
                                           reply_markup=choose)
            else:
                await bot.send_message(message.from_user.id,
                                       f'❌ По id-<b>{prod_id}</b> не найдено ни одного продукта!', parse_mode='HTML')


@dp.message_handler(commands='delete', state='*')
async def delete_prod(message: types.Message):
    if message.from_user.id in chat_id_list:
        await states_name.delete.set()
        prod_list = get_prod_list()
        products = ''
        # keys = []
        for index, prod in enumerate(prod_list, start=1):
            prod_name = prod['name']
            products = products + f'{index} | {prod_name} \n'

            # btn = InlineKeyboardButton(f'{index}', callback_data=f'delete_{index}')
            # keys.append(btn)

        numb_prod = InlineKeyboardMarkup(row_width=5)  # .add(*keys)
        numb_prod.add(InlineKeyboardButton(f'Отмена', callback_data='delete_cancel'))
        await bot.send_message(message.from_user.id,
                               '❌ <b>Список продуктов для удаления:</b>\n \n'
                               f'{products}\n'
                               '<b>Введите порядковые номера продуктов через пробел для удаления или нажмите "Отмена"</b>',
                               parse_mode='HTML', reply_markup=numb_prod)


@dp.message_handler(commands='help')
async def help(message: types.Message):
    if message.from_user.id in chat_id_list:
        await bot.send_message(message.from_user.id,
                               f'''<b>Команды для управления:</b>\n
/start - узнать ваш user_id\n
/check - отобразить список отслеживаемых продуктов, чтобы произвести проверку продукта зная его id (пример /check 1234 )\n
/check_all - проверить все продукты в списке <u>(Возможно будет много сообщений!)</u>\n
/time  - узнать текущий таймер для оповещений\n
/timer <u>секунды</u> - где после команды через пробел указать количество секунд через которое будет приходить уведомление, {TIMER} секунд по умолчанию\n
/add <u>id</u> - добавление продукта для отслеживания\n
/delete - отобразить список отслеживаемых продуктов с возможностью удаления''',
                               parse_mode='HTML')


@dp.message_handler(commands='time')
async def check_time(message: types.Message):
    if message.from_user.id in chat_id_list:
        await bot.send_message(message.from_user.id, f'Текущий таймер: {sec_timer} секунд')


@dp.message_handler(commands='timer')
async def edit_timer(message: types.Message):
    if message.from_user.id in chat_id_list and message.get_args().isdigit():
        global sec_timer
        sec_timer = int(message.get_args())
        for chat in chat_id_list:
            await bot.send_message(chat,
                                   f'Таймер до повторной проверки обновлен: {message.get_args()} секунд')


@dp.message_handler(state=states_name.delete)
async def delete_choosed(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['prods_to_delete'] = message.text.split()
        prod_list = get_prod_list()
        removed = ''
        x = 1
        for prod_indx in data['prods_to_delete']:
            indx = int(prod_indx) - x
            if indx > len(prod_list):
                continue
            prod_on_remove = prod_list.pop(indx)
            prod_name = prod_on_remove['name']
            prod_id = prod_on_remove['id']
            removed += f'✅ Продукт\n<b>{prod_name}\nID <code>{prod_id}</code></b>\nУдален из списка!\n\n'
            x += 1

        if removed:
            with open('data/products.json', 'w') as f:
                json.dump(prod_list, f, indent=2)
            for chat in chat_id_list:
                await bot.send_message(chat, removed, parse_mode='HTML')

        await state.finish()


@dp.callback_query_handler(lambda call: call.data, state='*')
async def process_callback(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.data.startswith('skip_'):
        prod_list = get_prod_list()
        index = int(callback_query.data.split('skip_')[1])
        prod_list[index]['skip'] = 1
        with open('data/products.json', 'w') as f:
            json.dump(prod_list, f, indent=2)

    elif callback_query.data.startswith('add_'):
        index = callback_query.data.split('_')[1]
        if index == 'confirm':
            prod_id = callback_query.data.split('_')[2]
            await add_product(prod_id)
            for chat in chat_id_list:
                await bot.send_message(chat,
                                       f'✅ Продукт\n<b>{get_prod_name(prod_id)}</b>\nУспешно добавлен в список для проверки!',
                                       parse_mode='HTML')
        else:
            await callback_query.message.delete()
            await bot.send_message(callback_query.from_user.id, '❌ Добавление отменено!')

    elif callback_query.data.startswith('delete_'):
        if callback_query.data.split('_')[1] == 'cancel':
            await state.finish()
        # else:
        #     prod_indx = int(callback_query.data.split('_')[1])
        #     prod_list = get_prod_list()
        #     prod_on_remove = prod_list.pop(prod_indx - 1)
        #     prod_name = prod_on_remove['name']
        #     prod_id = prod_on_remove['id']
        #     with open('data/products.json', 'w') as f:
        #         json.dump(prod_list, f, indent=2)
        #     for chat in chat_id_list:
        #         await callback_query.message.delete()
        #         await bot.send_message(chat,
        #                                f'✅ Продукт\n<b>{prod_name}\nID <code>{prod_id}</code></b>\nУдален из списка!',
        #                                parse_mode='HTML')

    elif callback_query.data.startswith('check_'):
        if callback_query.data.startswith('check_all_'):
            if callback_query.data.split('check_all_')[1] == 'confirm':
                await check_prod(check_now=1)
        else:
            if callback_query.data.split('_')[1] == 'cancel':
                await state.finish()
        #     else:
        #         prod_indx = int(callback_query.data.split('_')[1])
        #         prod_list = get_prod_list()
        #         prod_on_check = prod_list.pop(prod_indx - 1)
        #         prod_id = prod_on_check['id']
        #         await callback_query.message.delete()
        #         await check_prod(check_now=1, prod_id=prod_id)

    await callback_query.message.delete()


# async def check_price(check_now=0):
#     prod_list = get_prod_list()
#     all_games_list = get_all_products(prod_list)
#     for game in all_games_list:
#         checking_prod = prod_list[all_games_list.index(game)]
#         await check_prod(check_now)


async def task():
    start_iter = 1
    global sec_timer
    while True:
        if start_iter:
            start_iter = None
            await asyncio.sleep(sec_timer)
            continue
        else:
            await check_prod()
            await asyncio.sleep(sec_timer)
