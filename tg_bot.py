import logging
from concurrent.futures import ProcessPoolExecutor
from random import randint
import threading
import asyncio
import time

from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton

from aiogram import Bot, Dispatcher, executor, types
from flask import request
from flask_restful import Resource
from requests import get, put, post

from data import db_session
from data.meals import Meals
from data.orders import Orders
from data.shop_now import ShopNow
from data.shops import Shops
from data.users import Users

API_TOKEN = '5305383108:AAFZkZajF_hA03HshrF5-mPnkyTY77caui0'

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

keyboard = InlineKeyboardMarkup(one_time_keyboard=True)
keyboard.add(InlineKeyboardButton(text="Заказ готов!", callback_data="ready"))

keyboard2 = InlineKeyboardMarkup(one_time_keyboard=True)
keyboard2.add(InlineKeyboardButton(text="Готово!✅", callback_data="finished"))

keyboard1 = InlineKeyboardMarkup()
keyboard1.add(InlineKeyboardButton(text="To order", callback_data="order"))


@dp.message_handler(commands=['start', 'help'])
async def process_start_command(message: types.Message):
    await message.reply("Начнем работу!", reply_markup=keyboard1)


@dp.callback_query_handler(text="ready")
async def send_random_value(call: types.CallbackQuery):
    a = call.message.text.split('\n')
    num = int(a[0].split()[2])
    db_sess = db_session.create_session()
    a = db_sess.query(Orders).filter(Orders.shop_order_num == num).first()
    a.is_ready = 2
    db_sess.commit()
    all_meal = list(set(a.meals.split(', ')))
    s = '\n'.join(
        db_sess.query(Meals).filter(Meals.id == i).first().name + f'( {a.meals.count(i)}шт. )' for i in all_meal)
    db_sess.commit()
    await bot.delete_message(
        chat_id=db_sess.query(Shops).filter(Shops.id == db_sess.query(ShopNow).first().shop_id).first().tg_name,
        message_id=call.message.message_id)
    await bot.send_message(
        db_sess.query(Shops).filter(Shops.id == db_sess.query(ShopNow).first().shop_id).first().tg_name,
        f'Номер заказа: {a.id}\nИмя клиента: {db_sess.query(Users).filter(Users.id == a.client_id).first().name}\n{s}',
        reply_markup=keyboard2)


async def order_handler():
    while True:
        await asyncio.sleep(1)  # задержка
        db_session.global_init("db/sabantuy.db")
        db_sess = db_session.create_session()
        a = db_sess.query(Orders).filter(Orders.is_ready == 0).first()
        if a:
            a.is_ready = 1
            all_meal = list(set(a.meals.split(', ')))
            s = '\n'.join(
                db_sess.query(Meals).filter(Meals.id == i).first().name + f'( {a.meals.count(i)}шт. )' for i in
                all_meal)
            db_sess.commit()
            await bot.send_message(
                db_sess.query(Shops).filter(Shops.id == db_sess.query(ShopNow).first().shop_id).first().tg_name,
                f'Номер заказа: {a.id}\nИмя клиента: {db_sess.query(Users).filter(Users.id == a.client_id).first().name}\n{s}',
                reply_markup=keyboard)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(order_handler())
    loop.create_task(executor.start_polling(dp, skip_updates=True))
    loop.run_forever()
