import telebot
from telebot import types
from config import TOKEN
from extensions import CBRInfo
import CBR_Exceptions as Exc
import re

bot = telebot.TeleBot(TOKEN)

command_list = '''/start - Запуск бота
/help - Список доступных команд
/current_codes - Справочник доступных кодов валют
/find_name_code - Поиск кода валюты по названию
/news - Последние новости
/convert - Конвертер валют
/current_rate - Курс валют ЦБ
/key_rate - Ключевая ставка ЦБ
'''
info_text = 'Курс ЦБ обновляется в 12:00 по МСК с ПН по ПТ!\n'
CBR_Bot = CBRInfo()


@bot.message_handler(commands=['start'])
def start(message: telebot.types.Message):
    # user = message.from_user
    bot.send_message(message.chat.id, 'Привет, я бот Стен!!!\n')
    with open('pictures/Stan1.jpg', 'rb') as photo:
        bot.send_photo(message.chat.id, photo)
    text = 'Могу сообщить вам последнюю информацию ЦБ.'
    text = '\n'.join([text, info_text, 'Выберите команду из списка:', command_list])
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['help'])
def help(message: telebot.types.Message):
    with open('pictures/Stan5.jpg', 'rb') as photo:
        bot.send_photo(message.chat.id, photo)
    text = 'Список доступных команд:'
    text = '\n'.join([info_text, text, command_list])
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['current_codes'])
def current_codes(message: telebot.types.Message):
    text = 'Список доступных валюты:'
    codes = CBR_Bot.get_curr_codes()
    for value_code, value_name in codes.items():
        if value_code and value_name:
            text = '\n'.join([text, f'{value_code} - {value_name[0]}'])
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['find_name_code'])
def find_name_code(message: telebot.types.Message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item_help = types.KeyboardButton("Образец")
    item_cancel = types.KeyboardButton("Отмена")
    markup.add(item_help, item_cancel)
    msg = bot.send_message(message.chat.id, 'Введите код или часть названия искомой валюты для поиска.', reply_markup=markup)
    bot.register_next_step_handler(msg, find_name_code_step)


def find_name_code_step(message):
    clear_butt = telebot.types.ReplyKeyboardRemove()
    if message.text == 'Образец':
        example = 'Примеры:\nRUB, rub, рубл'
        msg = bot.send_message(message.chat.id, example)
        bot.register_next_step_handler(msg, find_name_code_step)
    elif message.text == 'Отмена':
        bot.send_message(message.from_user.id, 'Ок', reply_markup=clear_butt)
        help(message)
    else:
        text = ''
        codes = CBR_Bot.find_curr_codes(message.text)
        for value_code, value_name in codes.items():
            if value_code and value_name:
                text = '\n'.join([text, f'{value_code} - {value_name[0]}'])
        if text:
            bot.send_message(message.chat.id, text, reply_markup=clear_butt)
        else:
            text = f'"{message.text}": Ничего не найдено!'
            msg = bot.send_message(message.chat.id, text)
            bot.register_next_step_handler(msg, find_name_code_step)


# В работе!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
@bot.message_handler(commands=['news'])
def news(message: telebot.types.Message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    item_news = types.InlineKeyboardButton('Последние новости', callback_data='item_news')
    item_news_date = types.InlineKeyboardButton('Новости за определенную дату', callback_data='item_ndate')
    item_cancel = types.InlineKeyboardButton('Отмена', callback_data='item_cancel')

    markup.add(item_news, item_news_date, item_cancel)
    msg = bot.send_message(message.chat.id, 'Какие новости вам интересны?\
                                            \nВыберети "Последние новоси" - чтобы увидить последние 15 новостей\
                                            \nВыберите "Новости за определенную дату" - чтобы получить новости за конкретную дату',
                           reply_markup=markup)
    bot.register_next_step_handler(msg, convert_step)


@bot.callback_query_handler(func=lambda callback: callback.data)
def check_callback_data(callback):
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    if callback.data == 'item_news':
        news = CBR_Bot.get_news()
        text = ''
        markup = types.InlineKeyboardMarkup(row_width=1)
        for new in news:
            # text = '\n'.join([text, new[3]])
            item_new = types.InlineKeyboardButton(text=new[2], url=new[3])
            markup.add(item_new)
        bot.send_message(callback.message.chat.id, 'Последние новости', reply_markup=markup)


# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    elif callback.data == 'item_ndate':
        msg = bot.send_message(callback.message.chat.id, 'Укажите дату в формате: дд.мм.гггг')
        bot.register_next_step_handler(msg, news_date_step)
    elif callback.data == 'item_cancel':
        bot.send_message(callback.message.from_user.id, 'Ок')
        # help(message)


def news_date_step(message):
    try:
        news = CBR_Bot.get_news(i_date=message.text)
    except Exc.CBRException as err:  # Отлавливаем исключения и возвращаемся назад к вводу
        msg = bot.send_message(message.chat.id, err.message)
        with open('pictures/Stan2.jpg', 'rb') as photo:
            bot.send_photo(message.chat.id, photo)


@bot.message_handler(commands=['convert'])
def convert(message: telebot.types.Message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item_help = types.KeyboardButton("Образец")
    item_cancel = types.KeyboardButton("Отмена")
    markup.add(item_help, item_cancel)
    msg = bot.send_message(message.chat.id, 'Укажите колличество и коды валют для конвертации.', reply_markup=markup)
    bot.register_next_step_handler(msg, convert_step)


def convert_step(message):
    clear_butt = telebot.types.ReplyKeyboardRemove()
    if message.text == 'Образец':
        example = 'Примеры (по умолчанию USD/RUB):\
                   \n1) 100 - конвертация USD в RUB\
                   \n2) 100 EUR - конвертация EUR в RUB\
                   \n3) 1000 USD/EUR - конвертация USD в EUR\
                   \n4) 01.01.2001 1000 EUR - конвертация EUR в RUB по курсу 01.01.2001\
                   \n5) 01.01.2001 1000 USD/EUR - конвертация USD в EUR по курсу 01.01.2001'
        msg = bot.send_message(message.chat.id, example)
        bot.register_next_step_handler(msg, convert_step)
    elif message.text == 'Отмена':
        bot.send_message(message.from_user.id, 'Ок', reply_markup=clear_butt)
        help(message)
    else:
        pattern_1 = re.compile(r'^[0-9]{1,13}$')  # Пр.: 1000000
        pattern_2 = re.compile(r'^[0-9]{1,13} [A-Z]{3}$')  # Пр.: 100 EUR
        pattern_3 = re.compile(r'^[0-9]{1,13} [A-Z]{3}/[A-Z]{3}$')  # Пр.: 100 USD/EUR
        pattern_4 = re.compile(r'^\d{2}.\d{2}.\d{4}.[0-9]{1,13} [A-Z]{3}$')  # Пр.: 01.01.2001 100 EUR
        pattern_5 = re.compile(r'^\d{2}.\d{2}.\d{4}.[0-9]{1,13} [A-Z]{3}/[A-Z]{3}$')  # Пр.: 01.01.2001 1000 USD/EUR
        msg_text = message.text.upper()
        conv_curr = {}
        try:
            if pattern_1.match(msg_text):
                conv_curr = CBR_Bot.convert_currency(volume=msg_text)
            elif pattern_2.match(msg_text):
                vol, curr = msg_text.split(" ")
                conv_curr = CBR_Bot.convert_currency(volume=vol, code_from=curr)
            elif pattern_3.match(msg_text):
                vol, currs = msg_text.split(" ")
                curr1, curr2 = currs.split("/")
                conv_curr = CBR_Bot.convert_currency(volume=vol, code_from=curr1, code_to=curr2)
            elif pattern_4.match(msg_text):
                date, vol, curr = msg_text.split(" ")
                date = date.replace('.', '/')
                conv_curr = CBR_Bot.convert_currency(date=date, volume=vol, code_from=curr)
            elif pattern_5.match(msg_text):
                date, vol, currs = msg_text.split(" ")
                curr1, curr2 = currs.split("/")
                date = date.replace('.', '/')
                conv_curr = CBR_Bot.convert_currency(date=date, volume=vol, code_from=curr1, code_to=curr2)
            else:
                text = f'"{message.text}" - Не соответствует образцу!'
            if conv_curr:
                text = f'Конвертация валюты по курсу ЦБ на {conv_curr["date"]}:\
                        \n{conv_curr["volume"]} {conv_curr["code_from"]} = {conv_curr["result"]} {conv_curr["code_to"]}'
            msg = bot.send_message(message.chat.id, text)
        except Exc.CBRException as err:  # Отлавливаем исключения и возвращаемся назад к вводу
            msg = bot.send_message(message.chat.id, err.message)
            with open('pictures/Stan2.jpg', 'rb') as photo:
                bot.send_photo(message.chat.id, photo)
        bot.register_next_step_handler(msg, convert_step)


@bot.message_handler(commands=['current_rate'])
def current_rate(message: telebot.types.Message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item_all = types.KeyboardButton("Все")
    item_help = types.KeyboardButton("Образец")
    item_cancel = types.KeyboardButton("Отмена")
    markup.add(item_all, item_help, item_cancel)
    msg = bot.send_message(message.chat.id, 'Курс какой валюты вам интересен?\nУкажите код валюты.', reply_markup=markup)
    bot.register_next_step_handler(msg, current_rate_step)


def current_rate_step(message):
    clear_butt = telebot.types.ReplyKeyboardRemove()
    if message.text in ('Все', 'ALL'):
        curr_rate_all = CBR_Bot.get_curr_rate(code_from='ALL')
        bot.send_message(message.chat.id, curr_rate_all, reply_markup=clear_butt)
    elif message.text == 'Образец':
        example = 'Пример(по умолчанию на последнюю доступную дату):\
                \n1) 01.01.2001 USD - курс USD к RUB на указанную дату\
                \n2) USD - курс USD к RUB\
                \n3) USD/EUR - курс USD к EUR\
                \n4) Всех или ALL - вывести курсы всех валют к RUB'
        msg = bot.send_message(message.chat.id, example)
        bot.register_next_step_handler(msg, current_rate_step)
    elif message.text == 'Отмена':
        bot.send_message(message.from_user.id, 'Ок', reply_markup=clear_butt)
        help(message)
    else:
        pattern_1 = re.compile(r'^[A-Z]{3}$')  #Пр.: USD
        pattern_2 = re.compile(r'^[A-Z]{3}/[A-Z]{3}$')  #Пр.: USD/EUR
        pattern_3 = re.compile(r'^\d{2}.\d{2}.\d{4}.[A-Z]{3}$')  #Пр.: 01.01.2001 USD
        pattern_4 = re.compile(r'^\d{2}.\d{2}.\d{4}.[A-Z]{3}/[A-Z]{3}$')  #Пр.: 01.01.2001 USD/EUR
        msg_text = message.text.upper()
        # Проверяем соответствие введенных данных шаблону
        # Отлавливаем ошибки связанные с данными
        try:
            if pattern_1.match(msg_text):
                curr_rate = CBR_Bot.get_curr_rate(code_from=msg_text)
                bot.send_message(message.chat.id, curr_rate, reply_markup=clear_butt)
            elif pattern_2.match(msg_text):
                value = msg_text.split("/")
                curr_rate = CBR_Bot.get_curr_rate(code_from=value[0], code_to=value[1])
                bot.send_message(message.chat.id, curr_rate, reply_markup=clear_butt)
            elif pattern_3.match(msg_text):
                date, value = msg_text.split(" ")
                date = date.replace('.', '/')
                curr_rate = CBR_Bot.get_curr_rate(date=date, code_from=value)
                bot.send_message(message.chat.id, curr_rate, reply_markup=clear_butt)
            elif pattern_4.match(msg_text):
                date, value = msg_text.split(" ")
                date = date.replace('.', '/')
                value = value.split("/")
                curr_rate = CBR_Bot.get_curr_rate(date=date, code_from=value[0], code_to=value[1])
                bot.send_message(message.chat.id, curr_rate, reply_markup=clear_butt)
            else:
                msg = bot.send_message(message.chat.id, f'"{message.text}" - Не соответствует образцу!')
                bot.register_next_step_handler(msg, current_rate_step)
        except Exc.CBRException as err:  # Отлавливаем исключения и возвращаемся назад к вводу
            msg = bot.send_message(message.chat.id, err.message)
            with open('pictures/Stan2.jpg', 'rb') as photo:
                bot.send_photo(message.chat.id, photo)
            bot.register_next_step_handler(msg, current_rate_step)


@bot.message_handler(commands=['key_rate'])
def key_rate(message: telebot.types.Message):
    key_rate = CBR_Bot.get_key_rate()
    text = ''
    for d_rate, k_rate in key_rate.items():
        text = f'Текущая ключевая ставка ЦБ — {k_rate}%\n(обновление от {d_rate})'
    bot.send_message(message.chat.id, text)


bot.polling(none_stop=True)



# markup = types.InlineKeyboardMarkup(row_width=1)
# item_all = types.InlineKeyboardButton('Все', callback_data='item_all')
# item_help = types.InlineKeyboardButton('Образец', callback_data='item_help')
# item_cancel = types.InlineKeyboardButton('Отмена', callback_data='item_cancel')
# @bot.callback_query_handler(func=lambda callback: callback.data)
# def check_callback_data(callback):
#     if callback.data == 'item_all':
#         curr_rate_all = CBR_Bot.get_curr_rate(code_from='ALL')
#         bot.send_message(callback.message.chat.id, curr_rate_all)
#     elif callback.data == 'item_help':
#         example = 'Пример(по умолчанию на последнюю доступную дату):\
#                         \n01.01.2001 USD - курс USD к RUB на указанную дату\
#                         \nUSD - курс USD к RUB\
#                         \nUSD/EUR - курс USD к EUR\
#                         \nВсех или ALL - вывести курсы всех валют к RUB'
#         msg = bot.send_message(callback.message.chat.id, example)
#         bot.register_next_step_handler(msg, current_rate_step)
#     elif callback.data == 'item_cancel':
#         bot.send_message(callback.message.from_user.id, 'Ок')
#         # help(message)
