import datetime
import os
from time import sleep
from typing import List, Any

import requests
import json
import logging
from logging.handlers import RotatingFileHandler
from create_bot import bot, chat_id_list
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

logging.basicConfig(level=logging.DEBUG, encoding='utf-8',
                    handlers=[RotatingFileHandler('logs/debug_loger.log', maxBytes=5000000, backupCount=1)],
                    format="%(asctime)s - [%(levelname)s] - %(funcName)s: %(lineno)d - %(message)s")

API_TOKEN = os.getenv("API_TOKEN")
prod_list = None

"""Выгружаем в словарь все продукты которые нужно проверять"""


def get_prod_list() -> dict:
    with open('data/products.json', 'r') as f:
        prod_list = json.load(f)
    # print(datetime.datetime.now(), prod_list)
    logging.debug("Произведена загрузка данных из файла с продуктами")
    return prod_list


"""Получаем данные по продукту по его id"""


def get_prod(product_id) -> dict or None:
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
        except Exception as e:
            logging.debug("Ошибка при получении ответа по продукту - " + product_id)
            print('get_prod', response.content)
            print(datetime.datetime.now(), '- Error, check logs!')
            await bot.send_message(290768824,
                                   f"{e}\nВозникла проблема при проверке продукта {product_id}")
            sleep(600)


"""Получаем название продукта по его id"""


def get_prod_name(product_id) -> str or None:
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
        except Exception as e:
            logging.debug("Ошибка при получении ответа по продукту - " + product_id)
            print('get_prod_name', response.content)
            print(datetime.datetime.now(), '- Error, check logs!')
            await bot.send_message(290768824,
                                   f"{e}\nВозникла проблема при проверке продукта {product_id}")
            sleep(600)


"""Получаем количество остатков продукта"""


def get_prod_qty(product_id) -> int or None:
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
        except Exception as e:
            logging.debug("Ошибка при получении ответа по продукту - " + product_id)
            print('get_prod_qty', response.content)
            print(datetime.datetime.now(), '- Error, check logs!')
            await bot.send_message(290768824,
                                   f"{e}\nВозникла проблема при проверке продукта {product_id}")
            sleep(600)


"""Парсим в список данные от сервера по каждому продукту"""


def get_all_products(prod_list=None, prod_id=None) -> list[Any] | None:
    all_games_list_from_server = []
    if prod_id:
        prod = get_prod(prod_id)
        all_games_list_from_server.append(prod)
    elif prod_list:
        for product in prod_list:
            prod = get_prod(product['id'])
            all_games_list_from_server.append(prod)
            sleep(2)
    else:
        return None

    with open('data/all_games_list_from_server.json', 'w') as f:
        json.dump(all_games_list_from_server, f, indent=2)

    return all_games_list_from_server


"""Сопоставляем данные из 2х списков, где
        prod_list - это список из данных полученные из файла data/products.json в корневой директории
        all_games_list - это список с данными по каждой игре полученными от сервера"""


async def check_prod(check_now=None, prod_id=None):
    global prod_list
    if prod_id is None:
        prod_list = get_prod_list()
        all_games_list = get_all_products(prod_list=prod_list)
    else:
        all_games_list = get_all_products(prod_id=prod_id)

    for index, game in enumerate(all_games_list):
        try:
            """Проверяем была ли начала проверка по команде check"""
            if prod_id is None and check_now is None:
                checking_prod = prod_list[index]

                """Проверяем что самая низкая цена не изменилась с прошлой проверки, иначе вывести уведомление"""
                if game['price'] == checking_prod['last_price']:
                    continue

            productId = ""

            """Создаем вложенный список формата [[цена, имя продаца, остатки этого продавца по этой игре], ...]
                затем сортируем список по возрастанию цены"""
            s_l = []
            ostatok = 0
            for offer in game['offers']:
                try:
                    s_l.append([offer['price'], offer['merchantName'], offer['qty']])
                    if offer['merchantName'] == 'Sar Sar':
                        productId = offer['offerId']
                        ostatok = offer['qty']
                except:
                    pass
            s_l.sort()
            # print(s_l)

            """Проходимся по отсортированному списку и формируем строку с данными каждого продавца по этой игре"""
            x = 0
            offer_list = ''
            for s in s_l[:20]:
                if s[1] == 'Sar Sar':
                    offer_list = offer_list + f'<b>->| {x + 1} | {s[0]}€ | {s[1]} | {s[2]} шт. |</b>\n'
                else:
                    offer_list = offer_list + f'| {x + 1} | {s[0]}€ | {s[1]} | {s[2]} шт. |\n'.replace('.', '.﻿')
                x += 1

            # if merchantName != "Sar Sar":
            price_edit_btn = InlineKeyboardButton('Изменить цену',
                                                  url=f'https://www.kinguin.net/app/merchant/843534/offer/{productId}')
            # skip_btn = InlineKeyboardButton('Пропустить', callback_data=f'skip_{prod_list.index(checking_prod)}')
            inline_kb_spec = InlineKeyboardMarkup(row_width=1)
            inline_kb_spec.row(price_edit_btn)

            async def alert(c_id, mes_head):
                text = \
f'''⚠️ {mes_head} ⚠️ \n 
<b>{game['name']}</b> \n
| ↓ | Цена | Продавец | Остаток | \n
{offer_list}   
Всего ключей в продаже:  <b>{game['totalQty']} шт.</b> \n'''
                await bot.send_message(c_id, text=text, reply_markup=inline_kb_spec, parse_mode='HTML')


            if prod_id or check_now:
                mes_head = "ПРОВЕРКА ПРОДУКТА"
            else:
                mes_head = "ИЗМЕНИЛАСЬ ЦЕНА"
            for c_id in chat_id_list:
                await alert(c_id, mes_head)
        except Exception as e:
            await bot.send_message(290768824,
                                   f"{e}\nВозникла проблема при проверке продукта {game['name']}")
        if prod_id is None:
            checking_prod['last_price'] = game['price']
            checking_prod['qty'] = ostatok
            with open('data/products.json', 'w') as f:
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

    with open('data/products.json', 'w') as f:
        json.dump(prod_list, f, indent=2)
