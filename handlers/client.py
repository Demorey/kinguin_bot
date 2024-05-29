import asyncio
import json
from aiogram.types import InlineKeyboardButton, CallbackQuery, Message

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup, default_state
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command, StateFilter, CommandObject

from create_bot import dp, bot, chat_id_list, TIMER
from handlers.other import get_prod_list, check_prod, add_product, get_prod_name, get_prod

sec_timer = TIMER
msg_to_delete = None


class StatesName(StatesGroup):
    delete = State()
    check = State()


@dp.message(Command('start'))
async def command_start(message: Message):
    await bot.send_message(message.from_user.id, f'Ваш id: {message.from_user.id} \n /help - узнать комманды')


@dp.message(Command('check'))
async def check_now(message: Message, command: CommandObject, state: FSMContext):
    if message.from_user.id in chat_id_list:
        if command.args:
            if len(command.args.split(' ')) > 1:
                await bot.send_message(message.from_user.id, '❌ Введите корректный id')
            else:
                product_id = command.args.split(' ')[0]
                if product_id:
                    prod = await get_prod(product_id)
                    if prod:
                        await check_prod(check_now=1, prod_id=product_id)
                    else:
                        await bot.send_message(message.from_user.id,
                                               f'❌ По id-<b>{product_id}</b> не найдено ни одного продукта!',
                                               parse_mode='HTML')
        else:
            await state.set_state(StatesName.check)
            prod_list = get_prod_list()
            products = ''
            for index, prod in enumerate(prod_list, start=1):
                prod_name = prod['name']
                products = products + f'{index} | {prod_name} \n'

            numb_prod = InlineKeyboardBuilder()
            numb_prod.row(InlineKeyboardButton(text='Отмена', callback_data='check_cancel'))
            global msg_to_delete
            msg_to_delete = await bot.send_message(message.from_user.id,
                                                   f'📜 <b> Список продуктов для проверки:</b>\n \n'
                                                   f'{products}\n'
                                                   '<b>Введите порядковые номера продуктов через пробел для проверки или нажмите "Отмена"</b>',
                                                   parse_mode='HTML', reply_markup=numb_prod.as_markup())


@dp.message(StateFilter(StatesName.check))
async def check_choosed(message: Message, state: FSMContext):
    async with state.get_data() as data:
        data['prods_to_check'] = message.text.split()
        prod_list = get_prod_list()
        await bot.delete_message(msg_to_delete)
        for prod_indx in data['prods_to_check']:
            indx = int(prod_indx) - 1
            if indx > len(prod_list):
                continue
            prod_to_check = prod_list[indx]
            prod_id = prod_to_check['id']
            await check_prod(check_now=1, prod_id=prod_id)

        await state.clear()


@dp.message(Command('check_all'))
async def check_now(message: Message):
    if message.from_user.id in chat_id_list:
        choose = InlineKeyboardBuilder()
        choose.row(InlineKeyboardButton(text='✅', callback_data='check_all_confirm'),
                   InlineKeyboardButton(text='❌', callback_data='check_all_cancel')
                   )

        await bot.send_message(message.from_user.id,
                               f'Вы уверены что хотите сделать проверку всех продуктов?',
                               parse_mode='HTML',
                               reply_markup=choose.as_markup())


@dp.message(Command('add'))
async def add_new_prod(message: Message):
    if message.from_user.id in chat_id_list:
        product_id = message.text.split(' ')
        if len(product_id) < 2:
            await bot.send_message(message.from_user.id, '❌ Введите корректный id')
            return
        product_id.pop(0)
        for prod_id in product_id:
            prod_name = await get_prod_name(prod_id)
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
                    choose = InlineKeyboardBuilder()
                    choose.row(InlineKeyboardButton(text='✅', callback_data=f'add_confirm_{prod_id}'),
                               InlineKeyboardButton(text='❌', callback_data='add_cancel')
                               )
                    await bot.send_message(message.from_user.id,
                                           f'Вы хотите добавить <b>{prod_name}</b> в список для проверки?',
                                           parse_mode='HTML',
                                           reply_markup=choose.as_markup())
            else:
                await bot.send_message(message.from_user.id,
                                       f'❌ По id-<b>{prod_id}</b> не найдено ни одного продукта!', parse_mode='HTML')


@dp.message(Command('delete'), StateFilter(default_state))
async def delete_prod(message: Message, state: FSMContext):
    if message.from_user.id in chat_id_list:
        await state.set_state(StatesName.delete)
        prod_list = get_prod_list()
        products = ''
        for index, prod in enumerate(prod_list, start=1):
            prod_name = prod['name']
            products = products + f'{index} | {prod_name} \n'

        numb_prod = InlineKeyboardBuilder()
        numb_prod.add(InlineKeyboardButton(text='Отмена', callback_data='delete_cancel'))
        await bot.send_message(message.from_user.id,
                               '❌ <b>Список продуктов для удаления:</b>\n \n'
                               f'{products}\n'
                               '<b>Введите порядковые номера продуктов через пробел для удаления или нажмите "Отмена"</b>',
                               parse_mode='HTML', reply_markup=numb_prod.as_markup())


@dp.message(Command('help'))
async def help(message: Message):
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


@dp.message(Command('time'))
async def check_time(message: Message):
    if message.from_user.id in chat_id_list:
        await bot.send_message(message.from_user.id, f'Текущий таймер: {sec_timer} секунд')


@dp.message(Command('timer'))
async def edit_timer(message: Message, command: CommandObject):
    if message.from_user.id in chat_id_list and command.args.isdigit():
        global sec_timer
        sec_timer = int(command.args)
        for chat in chat_id_list:
            await bot.send_message(chat,
                                   f'Таймер до повторной проверки обновлен: {sec_timer} секунд')


@dp.message(StateFilter(StatesName.delete))
async def delete_choosed(message: Message, state: FSMContext):
    async with state.get_data() as data:
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

        await state.clear()


@dp.callback_query(lambda call: call.data)
async def process_callback(callback_query: CallbackQuery, state: FSMContext):
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
                name = await get_prod_name(prod_id)
                await bot.send_message(chat,
                                       f'✅ Продукт\n<b>{name}</b>\nУспешно добавлен в список для проверки!',
                                       parse_mode='HTML')
        else:
            await callback_query.message.delete()
            await bot.send_message(callback_query.from_user.id, '❌ Добавление отменено!')
        await state.clear()

    elif callback_query.data.startswith('delete_'):
        if callback_query.data.split('_')[1] == 'cancel':
            await state.clear()


    elif callback_query.data.startswith('check_'):
        if callback_query.data.startswith('check_all_') and callback_query.data.split('check_all_')[1] == 'confirm':
            await check_prod(check_now=1)
        else:
            if callback_query.data.split('_')[1] == 'cancel':
                await state.clear()

    await callback_query.message.delete()


@dp.message()
async def products_check(message: Message):
    if message.from_user.id in chat_id_list:
        product_id_list = message.text.split(' ')
        if product_id_list:
            for product_id in product_id_list:
                prod = await get_prod(product_id)
                if prod:
                    await check_prod(check_now=1, prod_id=product_id)
                else:
                    await bot.send_message(message.from_user.id,
                                           f'❌ По id-<b>{product_id}</b> не найдено ни одного продукта!',
                                           parse_mode='HTML')


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
