import telebot
from telebot import types
import re
from datetime import datetime, timezone
from config import TOKEN, DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT
from extensions import CBRInfo
import CBR_Exceptions as Exc
import structure_database

bot = telebot.TeleBot(TOKEN)

command_list = '''/help - Список доступных команд
/current_codes - Справочник доступных кодов валют
/find_name_code - Поиск кода валюты по названию
/oper_info - Оперативная информация
/convert - Конвертер валют
/current_rate - Курс валют ЦБ
/key_rate - Ключевая ставка ЦБ
'''
info_text = 'Курс ЦБ обновляется в 12:00 по МСК с ПН по ПТ!\n'
name_categ_op_inf = {'dkp':'Денежно-кредитная политика',
                     'rbr':'Решения Банка России',
                     'statistics':'Статистика',
                     'analytics':'Аналитика',
                     'hd_base':'База данных',
                     'ec_research':'Исследования',
                     'all_categ':'Все'}
clear_butt = telebot.types.ReplyKeyboardRemove()

# Создание структур БД
structure_database.create_structure_database(DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)

CBR_Bot = CBRInfo()


#Регистрация пользователя
@bot.message_handler(commands=['start'])
def start(message: telebot.types.Message):
    #Собираем данные пользователя
    user = {'id':message.from_user.id, 'username':message.from_user.username,
            'first_name':message.from_user.first_name, 'last_name':message.from_user.last_name,
            'bot_id':bot.bot_id, 'datetimereg':datetime.now(timezone.utc), 'datetimelastactive':datetime.now(timezone.utc)
            }
    CBR_Bot.add_user(user)  #Записываем данные пользователя в БД

    bot.send_message(message.chat.id, 'Привет, я бот Стен!!!\n')
    with open('pictures/Stan1.jpg', 'rb') as photo:
        bot.send_photo(message.chat.id, photo)
    text = 'Могу сообщить вам последнюю информацию ЦБ.'
    text = '\n'.join([text, info_text, 'Выберите команду из списка:', command_list])
    bot.send_message(message.chat.id, text)


#Вызов перечня доступных команд
@bot.message_handler(commands=['help'])
def help(message: telebot.types.Message):
    with open('pictures/Stan5.jpg', 'rb') as photo:
        bot.send_photo(message.chat.id, photo)
    text = 'Список доступных команд:'
    text = '\n'.join([info_text, text, command_list])
    bot.send_message(message.chat.id, text)


#Вывод списка доступных валют
@bot.message_handler(commands=['current_codes'])
def current_codes(message: telebot.types.Message):
    text = 'Список доступных валюты:'
    codes = CBR_Bot.get_curr_codes()  #Получение списка валют
    for value_code, value_name in codes.items():
        if value_code and value_name:
            text = '\n'.join([text, f'{value_code} - {value_name[1]}'])
    bot.send_message(message.chat.id, text)


#Поиск валюты по наименованию
@bot.message_handler(commands=['find_name_code'])
def find_name_code(message: telebot.types.Message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item_help = types.KeyboardButton("Образец")
    item_cancel = types.KeyboardButton("Отмена")
    markup.add(item_help, item_cancel)

    msg = bot.send_message(message.chat.id, 'Введите код или часть названия искомой валюты для поиска.', reply_markup=markup)
    bot.register_next_step_handler(msg, find_name_code_step)   #Регистрируем следующий шаг


def find_name_code_step(message):
    if message.text == 'Образец':
        example = 'Примеры:\nRUB, rub, рубл'
        msg = bot.send_message(message.chat.id, example)
        bot.register_next_step_handler(msg, find_name_code_step)
    elif message.text == 'Отмена':
        bot.send_message(message.from_user.id, 'Ок', reply_markup=clear_butt)
        help(message)
    else:
        text = ''
        codes = CBR_Bot.find_curr_codes(message.text)  #Поиск кода валюты
        for value_code, value_name in codes.items():
            if value_code and value_name:
                text = '\n'.join([text, f'{value_code} - {value_name[1]}'])
        if text:
            bot.send_message(message.chat.id, text, reply_markup=clear_butt)
        else:
            text = f'"{message.text}": Ничего не найдено!'
            msg = bot.send_message(message.chat.id, text)
            bot.register_next_step_handler(msg, find_name_code_step)


#Категория оперативной информации
@bot.message_handler(commands=['oper_info'])
def oper_info_categ(message: telebot.types.Message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    item_dkp = types.InlineKeyboardButton('Денежно-кредитная политика', callback_data='dkp')
    item_rbr = types.InlineKeyboardButton('Решения Банка России', callback_data='rbr')
    item_stat = types.InlineKeyboardButton('Статистика', callback_data='statistics')
    item_anal = types.InlineKeyboardButton('Аналитика', callback_data='analytics')
    item_hd_base = types.InlineKeyboardButton('База данных', callback_data='hd_base')
    item_res = types.InlineKeyboardButton('Исследования', callback_data='ec_research')
    item_all_categ = types.InlineKeyboardButton('Все', callback_data='all_categ')

    markup.add(item_dkp, item_rbr, item_stat, item_anal, item_hd_base, item_res, item_all_categ)
    msg = bot.send_message(message.chat.id, 'Оперативная информация из какой категории вам интересна?',
                           reply_markup=markup)


#Выбираем информации
def oper_info(message: telebot.types.Message, i_categ=''):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item_news = types.KeyboardButton('Последняя информация')
    item_cancel = types.KeyboardButton('Отмена')
    markup.add(item_news, item_cancel)

    name_categ = ''
    if i_categ:
        name_categ = name_categ_op_inf[i_categ] #Получаем наименование категории
    msg = bot.send_message(message.chat.id, f'Какая информация по категории "{name_categ}" вам интересна?\
                                            \nВыберети "Последняя информация" - чтобы увидить последние 15 новостей\
                                            \nЛибо укажите дату за которую хотите получить информацию в формате: 01.01.2001',
                           reply_markup=markup)
    bot.register_next_step_handler(msg, oper_info_step, i_categ)


#Получение оперативной информации
def oper_info_step(message, i_categ = ''):
    text = ''
    if message.text == 'Последняя информация':
        data_oper_info = CBR_Bot.get_oper_info(i_categ=i_categ)  #Загружаем оперативную информации по категории
        markup = types.InlineKeyboardMarkup(row_width=1)

        if i_categ:
            name_categ = name_categ_op_inf[i_categ]  #Получаем наименование категории
            if i_categ == 'all_categ':
                text = f'Ссылки на последнюю информацию по всем категориям'
            else:
                text = f'Ссылки на последнюю информацию по категории "{name_categ}"'
        for data in data_oper_info:
            item_new = types.InlineKeyboardButton(text=data[2], url=data[3])
            markup.add(item_new)
        with open('pictures/Stan3.jpg', 'rb') as photo:
            bot.send_photo(message.chat.id, photo, reply_markup=clear_butt)
        bot.send_message(message.chat.id, text, reply_markup=markup)

    elif message.text == 'Отмена':
        bot.send_message(message.from_user.id, 'Ок', reply_markup=clear_butt)
        help(message)

    else:
        try:
            data_oper_info = CBR_Bot.get_oper_info(i_date=message.text, i_categ=i_categ) #Загружаем ОИ по категории за дату
            markup = types.InlineKeyboardMarkup(row_width=1)

            if data_oper_info:
                if i_categ:
                    name_categ = name_categ_op_inf[i_categ]
                    if i_categ == 'all_categ':
                        text = f'Ссылки на информацию за {message.text} по всем категориям'
                    else:
                        text = f'Ссылки на информацию за {message.text} по категории "{name_categ}"'

                for data in data_oper_info:
                    item_new = types.InlineKeyboardButton(text=data[2], url=data[3])
                    markup.add(item_new)
                with open('pictures/Stan3.jpg', 'rb') as photo:
                    bot.send_photo(message.chat.id, photo, reply_markup=clear_butt)
                bot.send_message(message.chat.id, text, reply_markup=markup)

            else:
                if not (i_categ in ('','all_categ')):
                    name_categ = name_categ_op_inf[i_categ]
                    bot.send_message(message.chat.id, f'Ссылки по категории "{name_categ} отсутствуют', reply_markup=clear_butt)
                else:
                    bot.send_message(message.chat.id, 'Нет информации', reply_markup=markup)

        except Exc.CBRException as err:  #Отлавливаем исключения
            bot.send_message(message.chat.id, err.message, reply_markup=clear_butt)
            with open('pictures/Stan2.jpg', 'rb') as photo:
                bot.send_photo(message.chat.id, photo)


@bot.callback_query_handler(func=lambda callback: callback.data)
def check_callback_data(callback):
    #Проверка по категориям
    if callback.data in ('dkp', 'key-indicators', 'rbr', 'statistics', 'analytics', 'securities_market',
                         'hd_base', 'ec_research', 'all_categ'):
        CBR_Bot.load_oper_info(callback.data) #Загрузка оперативной информации
        oper_info(callback.message, callback.data)


#Конвертация валют
@bot.message_handler(commands=['convert'])
def convert(message: telebot.types.Message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item_help = types.KeyboardButton("Образец")
    item_cancel = types.KeyboardButton("Отмена")
    markup.add(item_help, item_cancel)

    msg = bot.send_message(message.chat.id, 'Укажите количество и коды валют для конвертации.', reply_markup=markup)
    bot.register_next_step_handler(msg, convert_step)


#Конвертация валют
def convert_step(message):
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
        #Шаблоны образцов
        pattern_1 = re.compile(r'^[0-9]{1,13}$')  # Пр.: 1000000
        pattern_2 = re.compile(r'^[0-9]{1,13} [A-Z]{3}$')  # Пр.: 100 EUR
        pattern_3 = re.compile(r'^[0-9]{1,13} [A-Z]{3}/[A-Z]{3}$')  # Пр.: 100 USD/EUR
        pattern_4 = re.compile(r'^\d{2}.\d{2}.\d{4}.[0-9]{1,13} [A-Z]{3}$')  # Пр.: 01.01.2001 100 EUR
        pattern_5 = re.compile(r'^\d{2}.\d{2}.\d{4}.[0-9]{1,13} [A-Z]{3}/[A-Z]{3}$')  # Пр.: 01.01.2001 1000 USD/EUR

        msg_text = message.text.upper()
        conv_curr = {}
        # Проверяем соответствие введенных данных шаблону
        try:
            #Вызываем функцию конвертации валюты
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


#Курс валюты
@bot.message_handler(commands=['current_rate'])
def current_rate(message: telebot.types.Message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item_all = types.KeyboardButton("Все")
    item_help = types.KeyboardButton("Образец")
    item_cancel = types.KeyboardButton("Отмена")
    markup.add(item_all, item_help, item_cancel)

    msg = bot.send_message(message.chat.id, 'Курс какой валюты вам интересен?\nУкажите код валюты.', reply_markup=markup)
    bot.register_next_step_handler(msg, current_rate_step)


#Получение курса по валюте
def current_rate_step(message):
    if message.text in ('Все', 'ALL'):
        curr_rate_all = CBR_Bot.get_curr_rate(code_from='ALL')
        bot.send_message(message.chat.id, curr_rate_all, reply_markup=clear_butt)
    elif message.text == 'Образец':
        example = 'Пример(по умолчанию на последнюю доступную дату):\
                \n1) USD - курс USD к RUB\
                \n2) USD/EUR - курс USD к EUR\
                \n3) 01.01.2001 USD - курс USD к RUB на указанную дату\
                \n4) Все или ALL - вывести курсы всех валют к RUB'
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
        try:
            # Вызываем функцию получения курса
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


#Ключевая ставка
@bot.message_handler(commands=['key_rate'])
def key_rate(message: telebot.types.Message):
    l_key_rate = CBR_Bot.get_key_rate()  #Получение ключевой ставки ЦБ
    text = ''
    for d_rate, k_rate in l_key_rate.items():
        text = f'Текущая ключевая ставка ЦБ — {k_rate}%\n(обновление от {d_rate})'
    bot.send_message(message.chat.id, text)


bot.polling(none_stop=True)