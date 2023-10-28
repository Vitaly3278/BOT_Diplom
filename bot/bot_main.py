import logging
import bot_markups as mks
from aiogram import Bot, Dispatcher, executor
from aiogram.types import ReplyKeyboardRemove, Message, CallbackQuery
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
import requests


logging.basicConfig(level=logging.INFO, filename='bot_log.txt', filemode='a',
                    format='%(asctime)s: %(levelname)s %(funcName)s-%(lineno)d %(message)s')

with open('key.txt', 'r') as f:
    text = f.readline()
TOKEN = str(text)
MSG = '{}, choose an action'

bot = Bot(token=TOKEN)
dp = Dispatcher(bot=bot, storage=MemoryStorage())
login_status = False
start_status = False
lgn = ''


@dp.message_handler(commands=['start'])
async def start_handler(message: Message):
    global start_status
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    user_full_name = message.from_user.full_name
    user_bot = message.from_user.is_bot
    user_message = message.text
    logging.info(f'{user_id=} {user_bot=} {user_message=}')
    await message.reply(f'Hi, {user_full_name}!')
    start_status = True
    await bot.send_message(user_id, MSG.format(user_name), reply_markup=mks.button)


class Form(StatesGroup):
    login_user = State()
    password_user = State()


@dp.message_handler(commands=['login'])
async def login_handler(message: Message):
    global start_status
    if start_status == True:
        user_id = message.from_user.id
        await Form.login_user.set()
        await bot.send_message(user_id, 'enter login:')


@dp.message_handler(state=Form.login_user)
async def login_text(message: Message, state: FSMContext):
    user_id = message.from_user.id
    async with state.proxy() as data:
        data['login_user'] = message.text
    await Form.next()
    await bot.send_message(user_id, 'enter password:')


@dp.message_handler(state=Form.password_user)
async def password_text(message: Message, state: FSMContext):
    global lgn
    global login_status
    user_name = message.from_user.first_name
    user_id = message.from_user.id
    async with state.proxy() as data:
        data['password_user'] = message.text
    # await bot.send_message(user_id, data['login_user'])
    # await bot.send_message(user_id, data['password_user'])
    lgn = data['login_user']
    pswd = data['password_user']
    await state.finish()
    await bot.send_message(user_id, f'{lgn}, {pswd}')

    # Запрос к Django api/token для получения ответа
    url = "http://localhost:8000/api/token/"
    data = {"email": lgn, "password": pswd}
    response = requests.post(url, data)

    # Обработка ответа
    if response.status_code == 200: # Аутентификация прошла успешно
        print('Аутентификация прошла успешно')
        response_data = response.json()
        access_token = response_data['access']
        refresh_token = response_data['refresh']
        login_status = True

        # Запрос к Django api/v1/task для получения списка заданий
        url = "http://127.0.0.1:8000/api/v1/task/"
        response = requests.get(url, access_token)

        if response.status_code == 200:  # Аутентификация прошла успешно
            print('Данные получены')
            response_task = response.json()
        else:
            # Аутентификация не удалась
            print('Ошибка:', response.status_code)
            await bot.send_message(user_id, 'Данные не удалось получить')



        for i in response_task:
            print(f"id :{ i['id']}\nName : {i['user_first_name']}\nLast Name : {i['user_last_name']}\nDescription : {i['description']}")
            print('-------------------------')
            # await bot.send_message(i['id'],i['user_first_name'], i['user_last_name'], i['title'],
            #                        i['description'], i['date_creation'], i['update_date'],
            #                        i['status'], i['lead_time'], i['user'])

    else:
        # Аутентификация не удалась
        print('Ошибка:', response.status_code)
        await bot.send_message(user_id, 'Аутентификация не удалась')


@dp.message_handler(commands=['options'])
async def options_handler(message: Message):
    global login_status
    if login_status == True:
        await bot.send_message(message.from_user.id, 'select an option:', reply_markup=mks.keyboard)


@dp.message_handler(commands=['quit'])
async def quit_handler(message: Message):
    global login_status
    global start_status
    await bot.send_message(message.from_user.id, 'Goodbye! See you...',
                           reply_markup=ReplyKeyboardRemove())
    login_status = False
    start_status = False
    await bot.delete_webhook(drop_pending_updates=True)


@dp.message_handler()
async def data_handler(message: Message, data):
    # text = *data
    await bot.send_message(message.from_user.id, data)


value = ""
old_value = ""


@dp.callback_query_handler(lambda call: True)
async def callback_options(query: CallbackQuery):

    global value, old_value
    data = query.data
    global lgn

    if data == 'tasks':
        value = 'your tasks now'
        await bot.edit_message_text(chat_id=query.message.chat.id,
                                    message_id=query.message.message_id,
                                    text=value, reply_markup=mks.keyboard_next)
        old_value = value
        value = ""

    elif data == 'new task':
        value = 'add a new task'
        await bot.edit_message_text(chat_id=query.message.chat.id,
                                    message_id=query.message.message_id,
                                    text=value, reply_markup=mks.keyboard_new)
        old_value = value
        value = ""

    elif data == 'task 1':
        value = 'your task 1:'
        res = db.user_task(lgn)
        await bot.edit_message_text(chat_id=query.message.chat.id,
                                    message_id=query.message.message_id,
                                    text=res, reply_markup=None)
        old_value = value
        value = ""


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)


  # print(access_token, refresh_token)
        await bot.send_message(user_id, 'Hello world')
        url = "http://127.0.0.1:8000/api/v1/task/"
        response = requests.get(url, access_token)
        response_task = response.json()
        for i in response_task:
            print(f"id :{ i['id']}\nName : {i['user_first_name']}\nLast Name : {i['user_last_name']}\nDescription : {i['description']}")
            print('-------------------------')
            # await bot.send_message(i['id'],i['user_first_name'], i['user_last_name'], i['title'],
            #                        i['description'], i['date_creation'], i['update_date'],
            #                        i['status'], i['lead_time'], i['user'])