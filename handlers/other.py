import requests
import json
from create_bot import bot, chat_id
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import API_TOKEN

"""Выгружаем в словарь все игры которые нужно проверять"""


def get_prod_list():
    with open('products.json', 'r') as f:
        prod_list = json.load(f)
    return prod_list


"""Получаем название игры по ее id"""


def get_prod_name(product_id):
    headers = {
        'X-Api-Key': API_TOKEN
    }
    response = requests.get(f'https://gateway.kinguin.net/esa/api/v1/products/{product_id}',
                            headers=headers)
    if response.status_code == 404:
        return None
    else:
        prod = json.loads(response.content)
        return prod['name']


"""Получаем количество остатков продукта"""


def get_prod_qty(product_id):
    headers = {
        'X-Api-Key': API_TOKEN
    }
    response = requests.get(f'https://gateway.kinguin.net/esa/api/v1/products/{product_id}',
                            headers=headers)
    if response.status_code == 404:
        return None
    else:
        prod = json.loads(response.content)
        return prod['qty']


"""Парсим в список данных по каждой игре"""


def get_all_products(prod_list):
    all_games_list = []
    for product in prod_list:
        product_id = product['id']
        headers = {
            'X-Api-Key': API_TOKEN
        }
        response = requests.get(f'https://gateway.kinguin.net/esa/api/v1/products/{product_id}',
                                headers=headers)

        prod = json.loads(response.content)
        # print(prod)
        all_games_list.append(prod)

        # with open('test.json', 'w') as f:
        #     json.dump(all_games_list, f, indent=2)

    return all_games_list


"""Сопоставляем данные из 2х списков, где
        prod_list - это список из данных полученные из файла products.json в корневой директории
        all_games_list - это список с данными по каждой игре полученными от сервера"""


async def check_prod(prod_list, game, checking_prod, check_now=0):
    """Проверяем была ли начала проверка по команде check"""

    if not check_now:

        """Проверяем что если у игры активна опция skip, то сообщение о ней будет отправлено
        только если самая низкая цена не изменилась с прошлой проверки"""
        # print(game['name'], game['price'], checking_prod['last_price'])
        # if game['price'] == checking_prod['last_price'] and checking_prod['skip'] == 1:
        if game['price'] == checking_prod['last_price']:
            return

    product = game['name']
    merchantName = game["merchantName"][0]
    productId = None
    totalQty = game['totalQty']

    """Создаем вложенный список формата [цена, имя продаца, остатки этого продавца по этой игре]
        затем сортируем список по возрастанию цены"""
    s_l = []
    ost = 0
    # ex = 0
    for offer in game['offers']:
        s_l.append([offer['price'], offer['merchantName'], offer['qty']])
        if offer['merchantName'] == 'Sar Sar':
            # ex = offer['price']
            ost = offer['qty']
            productId = offer['offerId']
    s_l.sort()
    # print(s_l)

    """Проходимся по отсортированному списку и формируем строку с данными каждого продавца по этой игре"""
    x = 0
    offer_list = ''
    for s in s_l[:20]:
        if s[1] == 'Sar Sar':
            offer_list = offer_list + f'<b><u>{x + 1} | {s[0]}€ | {s[1]} | {s[2]} шт. |</u></b> \n'
        else:
            offer_list = offer_list + f'{x + 1} | {s[0]}€ | {s[1]} | {s[2]} шт. | \n'.replace('.', '.﻿')
        x += 1

    # if merchantName != "Sar Sar":
    price_edit_btn = InlineKeyboardButton('Изменить цену',
                                          url=f'https://www.kinguin.net/app/merchant/843534/offer/{productId}')
    skip_btn = InlineKeyboardButton('Пропустить', callback_data=f'skip_{prod_list.index(checking_prod)}')
    inline_kb_spec = InlineKeyboardMarkup(row_width=2)
    inline_kb_spec.row(price_edit_btn, skip_btn)

    async def alert():
        for c_id in chat_id:
            await bot.send_message(c_id, text=
            f'''⚠️ИЗМЕНИЛАСЬ ЦЕНА ⚠ \n 
<b>{product}</b> \n
↓ | Цена | Продавец | Остаток | \n
{offer_list}   
Всего ключей в продаже:  <b>{totalQty} шт.</b> \n''',
                                   reply_markup=inline_kb_spec, parse_mode='HTML')

    await alert()
    checking_prod['last_price'] = game['price']
    checking_prod['qty'] = ost
    with open('products.json', 'w') as f:
        json.dump(prod_list, f, indent=2)


def add_product(product_id):
    prod_list = get_prod_list()
    for prod in prod_list:
        if prod['name'] == get_prod_name(product_id):
            return f'Продукт {product_id} уже в списке!'

    prod_name = get_prod_name(product_id)
    prod_qty = get_prod_qty(product_id)

    new_prod = {
        "name": prod_name,
        "id": f"{product_id}",
        "last_price": 0,
        "qty": prod_qty,
        "skip": 0}

    prod_list.append(new_prod)

    with open('products.json', 'w') as f:
        json.dump(prod_list, f, indent=2)
