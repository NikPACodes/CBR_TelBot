from config import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT
import json
import requests
from lxml import etree
from datetime import datetime
import CBR_Exceptions as Exc
import databases
from databases import PostgreSQL


# Класс для преобразования XML
class Convert:
    # Метод преобразования XML в словарь
    @classmethod
    def conv_xml_to_dict(cls, i_elements):
        result_dist = {}
        for element in i_elements:
            if len(element):
                value = cls.conv_xml_to_dict(element)
            else:
                value = element.text

            key = element.tag

            # добавляем атрибуты
            if element.attrib:
                atr_dist = {}
                for atr_key, atr_val in element.attrib.items():
                    atr_key = ''.join(['@', atr_key])  # @ - указатель на атрибут тега
                    atr_dist[atr_key] = atr_val
                value, atr_dist = atr_dist, value
                value.update(atr_dist)

            if key in result_dist:
                # Превращаем значение ключа в список
                if not isinstance(result_dist[key], list):
                    result_dist[key] = [result_dist[key]]
                result_dist[key].append(value)
            else:
                result_dist[key] = value
        return result_dist

    @classmethod
    def conv_xml_to_json(cls, i_data_xml):
        dict_data = cls.conv_xml_to_dict(i_data_xml)
        json_data = json.dumps(dict_data, ensure_ascii=False)
        return json_data


# Класс телеграм бота ЦБ
class CBRInfo:
    # Сайт ЦБ
    __req_cb = f'http://www.cbr.ru'

    # Коды валют (по умолчанию обновляющиеся ежедневно)
    # Параметры: 'd': обновляющиеся ежедневно(0)/ежемесячно(1)
    __req_curr_code = f'http://www.cbr.ru/scripts/XML_valFull.asp'

    # Получение котировок на заданный день
    # Параметры: 'date_req': Дата
    __req_curr_rate = f'http://www.cbr.ru/scripts/XML_daily.asp'

    # Получение ключевой ставки
    # Параметры: 'UniDbQuery.Posted': 'True', 'UniDbQuery.From': Дата с, 'UniDbQuery.To': Дата по
    __req_key_rate = f'http://www.cbr.ru/hd_base/KeyRate/'

    # Получение оперативной информации ЦБ
    __req_oper_info = f'http://www.cbr.ru/scripts/XML_News.asp'

    __PostgresDB = None
    _TestLocalDB = None


    def __init__(self):
        self.curr_codes = {} # Справочник кодов валют
        self.oper_info = []  # Оперативная информация
        self.oper_info_lload = datetime(2025, 1, 1) # Время последней загрузки опер.инф.
        self.__PostgresDB = PostgreSQL()

        # Подключение к БД
        try:
            self._TestLocalDB = self.__PostgresDB.connection(DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)
        except databases.DBException as err:
            print(err.message)


    # Регистрация нового пользователя
    def add_user(self, i_user={}):
        if i_user:
            try:
                q_check_user = 'SELECT * FROM users WHERE id = %s'
                check_user = self.__PostgresDB.execute_read_query(self._TestLocalDB, q_check_user, (i_user.get('id'),))
                if not check_user:
                    e_user_inf = (i_user.get('id'), i_user.get('username'), i_user.get('first_name'), i_user.get('last_name'))
                    values = ", ".join(["%s"] * len(e_user_inf))
                    q_ins_user = f"INSERT INTO users (id, username, first_name, last_name) VALUES ({values})"
                    self.__PostgresDB.execute_query(self._TestLocalDB, q_ins_user, e_user_inf)

                    e_bot_inf = (i_user.get('bot_id'), i_user.get('id'), i_user.get('datetimereg'), i_user.get('datetimelastactive'))
                    values = ", ".join(["%s"] * len(e_bot_inf))
                    q_ins_bot = f"INSERT INTO botusers (botid, userid, datetimereg, datetimelastactive) VALUES ({values})"
                    self.__PostgresDB.execute_query(self._TestLocalDB, q_ins_bot, e_bot_inf)
            except databases.DBException as err:
                print(err.message)


    # Заполнение справочника кодов валют
    # i_update - Принудительное обновление БД
    def load_curr_codes(self, i_update = 0):
        self.curr_codes = {}
        try:
            q_ch_currcode = 'SELECT * FROM CurrCodesDirectCBR'
            check_CurrCodes = self.__PostgresDB.execute_read_query(self._TestLocalDB, q_ch_currcode)
            if not check_CurrCodes or i_update == 1:
                e_curr_codes = set()
                e_curr_codes.add(('RUB', '643', 'RUB', 'Russian ruble', 'Российский рубль'))  # Перечень кодов для добавления в БД
                for i in range(2):
                    req = requests.get(self.__req_curr_code, params={'d': i})  # Коды валют устанавливаемые ежедневно/ежемесячно
                    root = etree.XML(req.content)  # Парсинг строки, получаем корень
                    elements = root.xpath("//Item")  # Находим все теги Item
                    req_dict = Convert.conv_xml_to_dict(elements)

                    for code_req in req_dict.get("Item"):
                        if code_req.get("ISO_Char_Code"):
                            e_curr_codes.add((code_req.get("@ID"), code_req.get("ISO_Num_Code"), code_req.get("ISO_Char_Code"), code_req.get("EngName"), code_req.get("Name")))

                if check_CurrCodes:
                    for curr_code_bd in check_CurrCodes:
                        e_curr_codes.discard(curr_code_bd)

                q_ins_code = f"INSERT INTO CurrCodesDirectCBR (ID_CBR, ISO_num, ISO_code, NameEng, NameRus) VALUES (%s, %s, %s, %s, %s)"
                for ins_code in e_curr_codes:
                    self.__PostgresDB.execute_query(self._TestLocalDB, q_ins_code, ins_code)
                check_CurrCodes = self.__PostgresDB.execute_read_query(self._TestLocalDB, q_ch_currcode)

                # Дополняем перечень кодов
            for code_bd in check_CurrCodes:
                self.curr_codes[code_bd[2]] = (code_bd[1], code_bd[4], code_bd[3], code_bd[0])

        except databases.DBException as err:
            print(err.message)


    # Получение справочника кодов валют
    def get_curr_codes(self):
        # Если справочник не заполнен, делаем запрос для заполнения
        if not self.curr_codes:
            self.load_curr_codes()
        return self.curr_codes


    # Проверка существования кода валют в справочнике
    def check_curr_code(self, i_code):
        dict_codes = self.get_curr_codes()
        if not (i_code in dict_codes):
            raise Exc.CodeError(i_code)


    # Поиск кода по наименованию
    def find_curr_codes(self, i_text):
        code = {}
        dict_codes = self.get_curr_codes()
        ltext = i_text.upper()
        for rkey, rval in dict_codes.items():
            if rkey.find(ltext) != -1 or rval[1].upper().find(ltext) != -1 or rval[2].upper().find(ltext) != -1:
                code[rkey] = rval
        return code


    # Получение курса валют ЦБ на выбранную дату (по умолчанию: USD/RUB на ближайшую доступную дату)
    # (Формат дат %d/%m/%Y)
    def get_curr_rate(self, i_date=datetime.now().strftime('%d/%m/%Y'), i_code_from='USD', i_code_to='RUB'):
        sel_data=[]
        sel_data = self.sel_data_ExchRates(i_date, i_code_from, i_code_to)
        res_date = i_date.replace('/', '.')
        text = list()
        text.append('Курс ЦБ: ' + res_date)

        if i_code_to != 'RUB':
            denom_from, denom_to = '', ''

        if sel_data:
            for bd_data in sel_data:
                if i_code_from == 'ALL':
                    text.append(bd_data[1] + '/RUB - ' + str(bd_data[3]).replace('.', ','))
                elif i_code_from == bd_data[1] and i_code_to == 'RUB':
                    text.append(i_code_from + '/RUB - ' + str(bd_data[3]).replace('.', ','))
                    break
                elif bd_data[1] in (i_code_from, i_code_to) and i_code_to != 'RUB':
                    if i_code_from == bd_data[1]:
                        denom_from = bd_data[3]
                    if i_code_to == bd_data[1]:
                        denom_to = bd_data[3]
                    if denom_from and denom_to:
                        denom_calc = str(round((denom_from / denom_to), 4)).replace('.', ',')
                        text.append(f'{i_code_from}/{i_code_to} - {denom_calc}')
                        break
        result = '\n'.join(text) if len(text) > 1 else f'Нет данных ЦБ на {res_date}'
        return result



    # Конвертация валюты
    def convert_currency(self, i_date=datetime.now().strftime('%d/%m/%Y'), i_volume=0, i_code_from='USD', i_code_to='RUB'):
        # Проверка корректности введенного объема
        try:
            i_volume = int(i_volume)
        except ValueError:
            raise Exc.VolumeError(i_volume)

        sel_data = self.sel_data_ExchRates(i_date, i_code_from, i_code_to)

        if i_code_to != 'RUB':
            denom_from, denom_to = '', ''

        if sel_data:
            for bd_data in sel_data:
                if i_code_from == bd_data[1] and i_code_to == 'RUB':
                    res_conv = str(round(float(i_volume * bd_data[3]), 4)).replace('.', ',')
                    break
                elif bd_data[1] in (i_code_from, i_code_to) and i_code_to != 'RUB':
                    if i_code_from == bd_data[1]:
                        denom_from = bd_data[3]
                    if i_code_to == bd_data[1]:
                        denom_to = bd_data[3]
                    if denom_from and denom_to:
                        res_conv = str(round(float(i_volume * denom_from / denom_to), 4)).replace('.', ',')
                        break

        result = {'date': i_date.replace('/', '.'),
                  'volume': i_volume,
                  'code_from': i_code_from,
                  'code_to': i_code_to,
                  'result': res_conv}
        return result


    # Получение ключевой ставки (по умолчанию текущей)
    # (Формат дат %d.%m.%Y)
    def get_key_rate(self, i_date_from=datetime.now().strftime('%d.%m.%Y'), i_date_to=datetime.now().strftime('%d.%m.%Y')):
        # Проверка корректности дат
        for date in [i_date_from, i_date_to]:
            try:
                datetime.strptime(date, '%d.%m.%Y').date()
            except ValueError:
                raise Exc.DateError(date)

        load_par = {'UniDbQuery.Posted': 'True', 'UniDbQuery.From': i_date_from, 'UniDbQuery.To': i_date_to}
        req = requests.get(self.__req_key_rate, params=load_par)
        root = etree.HTML(req.content)
        elements = root.xpath('//table[@class="data"]')  # Находим все теги
        req_dict = Convert.conv_xml_to_dict(elements)
        result = {}
        for data in req_dict.get('table').get('tr'):
            if data.get('td'):
                date_key_rate, key_rate = data.get('td')[0], data.get('td')[1]
                result[date_key_rate] = key_rate
        return result


    # Загрузка оперативной информации
    def load_oper_info(self):
        last_upd = datetime.now() - self.oper_info_lload
        #Обновляем данные если последнее обновление было больше дня назад
        if last_upd.days >= 1:
            req = requests.get(self.__req_oper_info) #Заменить на обновления списка
            root = etree.XML(req.content)
            req_dict = Convert.conv_xml_to_dict(root)
            self.oper_info_lload = datetime.now()

            for check_op_inf in self.oper_info:
                for data_rdict in req_dict.get("Item"):
                    if data_rdict["@ID"] == check_op_inf[0]:
                        req_dict.get("Item").remove(data_rdict)
                        break

            for data in req_dict.get("Item"):
                if data.get("Url"):
                    url_oper_info = ''.join([self.__req_cb, data.get("Url")]).replace(' ', '')
                    self.oper_info.append((data.get("@ID"), data.get("Date"), data.get("Title").rstrip(' '), url_oper_info))


    # Получение оперативной информации
    def get_oper_info(self, i_date='', i_categ = ''):
        if i_categ:
            l_fcateg = f'/{i_categ}/'
        res = []
        # Проверка корректности даты
        if i_date:
            try:
                datetime.strptime(i_date, '%d.%m.%Y').date()
            except ValueError:
                raise Exc.DateError(i_date)

            if not (i_categ in ('','all_categ')):
                for data_op_inf in self.oper_info:
                    if l_fcateg in data_op_inf[3] and data_op_inf[1] == i_date:
                        res.append(data_op_inf)
            else:
                for data_op_inf in self.oper_info:
                    if data_op_inf[1] == i_date:
                        res.append(data_op_inf)

        else:
            if not (i_categ in ('','all_categ')):
                for data_op_inf in self.oper_info:
                    if l_fcateg in data_op_inf[3]:
                        res.append(data_op_inf)
                        if len(res) >= 15:
                            break
            else:
                n = 15 if len(self.oper_info) > 15 else len(self.oper_info)
                for data_op_inf in self.oper_info[:n]:
                    res.append(data_op_inf)
        return res


    # Выбор и обновление данных ExchangeRatesCBR
    def sel_data_ExchRates(self, i_date=datetime.now().strftime('%d/%m/%Y'), i_code_from='USD', i_code_to='RUB'):
        e_data=[]   # Выходная таблица
        # Проверка корректности даты
        try:
            date_valid = datetime.strptime(i_date, '%d/%m/%Y').date()
            if date_valid > datetime.now().date():
                raise Exc.DateFutureError(i_date)
        except ValueError:
            raise Exc.DateError(i_date)

        q_date = datetime.strptime(i_date, '%d/%m/%Y').strftime('%Y-%m-%d')

        query_sel_data = f"""SELECT cc.ID_CBR, cc.ISO_Code, ex.Date, ex.CurrRate \
                                 \nFROM ExchangeRatesCBR as ex \
                                 \nJOIN CurrCodesDirectCBR as cc \
                                   \nON ex.ID_CBR = cc.ID_CBR \
                                \nWHERE ex.Date = '{q_date}'"""
        # Проверяем полученные коды валют
        if i_code_from != 'ALL':
            self.check_curr_code(i_code_from)
            query_sel_data = f"""SELECT cc.ID_CBR, cc.ISO_Code, ex.Date, ex.CurrRate \
                                     \nFROM ExchangeRatesCBR as ex \
                                     \nJOIN CurrCodesDirectCBR as cc ON ex.ID_CBR = cc.ID_CBR \
                                    \nWHERE ex.Date = '{q_date}' \
                                      \nAND cc.ISO_Code = '{i_code_from}'"""
        if i_code_to != 'RUB':
            self.check_curr_code(i_code_to)
            query_sel_data = f"""SELECT cc.ID_CBR, cc.ISO_Code, ex.Date, ex.CurrRate \
                                     \nFROM ExchangeRatesCBR as ex \
                                     \nJOIN CurrCodesDirectCBR as cc ON ex.ID_CBR = cc.ID_CBR \
                                    \nWHERE ex.Date = '{q_date}' \
                                      \nAND cc.ISO_Code in ('{i_code_from}', '{i_code_to}')"""

        try:
            e_data = self.__PostgresDB.execute_read_query(self._TestLocalDB, query_sel_data)
        except databases.DBException as err:
            print(err.message)

        if not e_data: # Если не нашли данных в БД берем их с сервера ЦБ и обновляем данные в БД
            load_par = {'date_req': i_date} if i_date else {}
            req = requests.get(self.__req_curr_rate, params=load_par)
            root = etree.XML(req.content)
            req_dict = Convert.conv_xml_to_dict(root)

            try:
                q_ins_rate = f"INSERT INTO ExchangeRatesCBR (ID_CBR, Date, CurrRate) VALUES (%s, %s, %s)"
                for data in req_dict.get("Valute"):
                    self.__PostgresDB.execute_query(self._TestLocalDB, q_ins_rate, (data.get("@ID"), q_date, data.get('VunitRate').replace(',', '.')))
                e_data = self.__PostgresDB.execute_read_query(self._TestLocalDB, query_sel_data)
            except databases.DBException as err:
                print(err.message)

        return e_data