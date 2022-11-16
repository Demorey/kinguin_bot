import datetime
from time import sleep
import requests
import json
import logging
from create_bot import bot, chat_id
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import API_TOKEN

"""Выгружаем в словарь все продукты которые нужно проверять"""


def get_prod_list():
    with open('products.json', 'r') as f:
        prod_list = json.load(f)
    # print(datetime.datetime.now(), prod_list)
    logging.basicConfig(filename="loger.log", level=logging.DEBUG,
                        format="%(asctime)s - %(levelname)s - %(funcName)s: %(lineno)d - %(message)s")
    return prod_list


"""Получаем данные по продукту по его id"""


def get_prod(product_id):
    headers = {
        'X-Api-Key': API_TOKEN
    }
    response = requests.get(f'https://gateway.kinguin.net/esa/api/v1/products/{product_id}',
                            headers=headers)
    if response.status_code in (404, 400):
        return None
    else:
        try:
            prod = json.loads(response.content)
            return prod
        except:
            logging.basicConfig(filename="loger.log", level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(funcName)s: %(lineno)d - %(message)s")
            logging.debug("Ошибка при получении ответа по продукту - "+product_id)
            print('get_prod', response.content)
            print(datetime.datetime.now(), '- Error, check logs!')
            sleep(600)

"""Получаем название продукта по его id"""


def get_prod_name(product_id):
    headers = {
        'X-Api-Key': API_TOKEN
    }
    response = requests.get(f'https://gateway.kinguin.net/esa/api/v1/products/{product_id}',
                            headers=headers)
    if response.status_code in (404, 400):
        return None
    else:
        try:
            prod = json.loads(response.content)
            return prod['name']
        except:
            logging.basicConfig(filename="loger.log", level=logging.DEBUG,
                                format="%(asctime)s - %(levelname)s - %(funcName)s: %(lineno)d - %(message)s")
            logging.debug("Ошибка при получении ответа по продукту - " + product_id)
            print('get_prod_name', response.content)
            print(datetime.datetime.now(), '- Error, check logs!')
            sleep(600)

"""Получаем количество остатков продукта"""


def get_prod_qty(product_id):
    headers = {
        'X-Api-Key': API_TOKEN
    }
    response = requests.get(f'https://gateway.kinguin.net/esa/api/v1/products/{product_id}',
                            headers=headers)
    if response.status_code in (404, 400):
        return None
    else:
        try:
            prod = json.loads(response.content)
            return prod['qty']
        except:
            logging.basicConfig(filename="loger.log", level=logging.DEBUG,
                                format="%(asctime)s - %(levelname)s - %(funcName)s: %(lineno)d - %(message)s")
            logging.debug("Ошибка при получении ответа по продукту - " + product_id)
            print('get_prod_qty', response.content)
            print(datetime.datetime.now(), '- Error, check logs!')
            sleep(600)


"""Парсим в список данные по каждому продукту"""


def get_all_products(prod_list=None, prod_id=None):
    all_games_list = []
    if prod_id:
        prod = get_prod(prod_id)
        all_games_list.append(prod)
    else:
        for product in prod_list:
            product_id = product['id']
            prod = get_prod(product_id)
            all_games_list.append(prod)

            # with open('test.json', 'w') as f:
            #     json.dump(all_games_list, f, indent=2)

    return all_games_list


"""Сопоставляем данные из 2х списков, где
        prod_list - это список из данных полученные из файла products.json в корневой директории
        all_games_list - это список с данными по каждой игре полученными от сервера"""


async def check_prod(check_now=0, prod_id=None):
    prod_list = None
    if not prod_id:
        prod_list = get_prod_list()
        all_games_list = get_all_products(prod_list=prod_list)
    else:
        all_games_list = get_all_products(prod_id=prod_id)

    for index, game in enumerate(all_games_list):
        if prod_list:
            checking_prod = prod_list[index]

            """Проверяем была ли начала проверка по команде check"""
            if not check_now:

                """Проверяем что самая низкая цена не изменилась с прошлой проверки, иначе вывести уведомление"""
                if game['price'] == checking_prod['last_price']:
                    return

        product = game['name']
        productId = None
        totalQty = game['totalQty']

        """Создаем вложенный список формата [цена, имя продаца, остатки этого продавца по этой игре]
            затем сортируем список по возрастанию цены"""
        s_l = []
        ost = 0
        for offer in game['offers']:
            try:
                s_l.append([offer['price'], offer['merchantName'], offer['qty']])
                if offer['merchantName'] == 'Sar Sar':
                    ost = offer['qty']
                    productId = offer['offerId']
            except:
                pass
        s_l.sort()
        # print(s_l)

        """Проходимся по отсортированному списку и формируем строку с данными каждого продавца по этой игре"""
        x = 0
        offer_list = ''
        for s in s_l[:20]:
            if s[1] == 'Sar Sar':
                offer_list = offer_list + f'<b><u>{x + 1} | {s[0]}€ | {s[1]} | {s[2]} шт. |</u></b>\n'
            else:
                offer_list = offer_list + f'{x + 1} | {s[0]}€ | {s[1]} | {s[2]} шт. |\n'.replace('.', '.﻿')
            x += 1

        # if merchantName != "Sar Sar":
        price_edit_btn = InlineKeyboardButton('Изменить цену',
                                              url=f'https://www.kinguin.net/app/merchant/843534/offer/{productId}')
        # skip_btn = InlineKeyboardButton('Пропустить', callback_data=f'skip_{prod_list.index(checking_prod)}')
        inline_kb_spec = InlineKeyboardMarkup(row_width=1)
        inline_kb_spec.row(price_edit_btn)

        async def alert():
            if prod_id or check_now:
                for c_id in chat_id:
                    await bot.send_message(c_id, text=
                f'''⚠️ПРОВЕРКА ПРОДУКТА ⚠ \n 
<b>{product}</b> \n
↓ | Цена | Продавец | Остаток | \n
{offer_list}   
Всего ключей в продаже:  <b>{totalQty} шт.</b> \n''',
                                       reply_markup=inline_kb_spec, parse_mode='HTML')
            else:
                for c_id in chat_id:
                    await bot.send_message(c_id, text=
                f'''⚠️ИЗМЕНИЛАСЬ ЦЕНА ⚠ \n 
<b>{product}</b> \n
↓ | Цена | Продавец | Остаток | \n
{offer_list}   
Всего ключей в продаже:  <b>{totalQty} шт.</b> \n''',
                                       reply_markup=inline_kb_spec, parse_mode='HTML')

        await alert()

        if not prod_id:
            checking_prod['last_price'] = game['price']
            checking_prod['qty'] = ost
            with open('products.json', 'w') as f:
                json.dump(prod_list, f, indent=2)


async def add_product(product_id):
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
    }

    prod_list.append(new_prod)

    with open('products.json', 'w') as f:
        json.dump(prod_list, f, indent=2)
