import json
import requests
from lxml import etree
from datetime import datetime
import CBR_Exceptions as Exc


# Класс для преобразования XML
class Convert:
    # Метод преобразования XML в словарь
    @classmethod
    def conv_xml_to_dict(cls, elements):
        result_dist = {}
        for element in elements:
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
    def conv_xml_to_json(cls, data_xml):
        dict_data = cls.conv_xml_to_dict(data_xml)
        json_data = json.dumps(dict_data, ensure_ascii=False)
        return json_data


# Класс телеграм бота ЦБ
class CBRInfo:
    # Сайт ЦБ
    req_cb = f'http://www.cbr.ru'

    # Коды валют (по умолчанию устанавлеваемые ежедневно)
    # Параметры:  'd': устанавлеваемые ежедневно(0)/ежемесячно(1)
    req_curr_code = f'http://www.cbr.ru/scripts/XML_valFull.asp'

    # Получение котировок на заданный день
    # Параметры:  'date_req': Дата
    req_curr_rate = f'http://www.cbr.ru/scripts/XML_daily.asp'

    # Получение ключевой ставки
    # Параметры: 'UniDbQuery.Posted': 'True', 'UniDbQuery.From': Дата с, 'UniDbQuery.To': Дата по
    req_key_rate = f'http://www.cbr.ru/hd_base/KeyRate/'

    # Получение всех новостей
    req_news = f'http://www.cbr.ru/scripts/XML_News.asp'

    # Справочник кодов валют
    curr_codes = {}

    # Список новостей
    news = {}


    def __init__(self):
        self.curr_codes = {}
        self.news = []

    # Регистрация нового пользователя
    def add_user(self):
        pass

    # Заполнение справочника кодов валют
    # @property
    def load_curr_codes(self):
        req = requests.get(self.req_curr_code)  # Коды валют устанавливаемые ежедневно
        root = etree.XML(req.content)  # Парсинг строки, получаем корень
        elements = root.xpath("//Item")  # Находим все теги Item
        req_dict = Convert.conv_xml_to_dict(elements)
        self.curr_codes['RUB'] = ('Российский рубль', 'Russian ruble')  # Добавиль рубль т.к. его нет в справочнике
        # Заполнение справочника кодов валют
        for code in req_dict.get("Item"):
            if code.get("ISO_Char_Code"):
                self.curr_codes[code.get("ISO_Char_Code")] = (code.get("Name"), code.get("EngName"))

    # Получение справочника кодов валют
    def get_curr_codes(self):
        # Если справочник не заполнен, делаем запрос для заполнения
        if not self.curr_codes:
            self.load_curr_codes()
        return self.curr_codes

    # Проверка существования кода валют в справочнике
    def check_curr_code(self, code):
        dict_codes = self.get_curr_codes()
        if not (code in dict_codes):
            raise Exc.CodeError(code)

    # Поиск кода по наименованию
    def find_curr_codes(self, text):
        code = {}
        dict_codes = self.get_curr_codes()
        ltext = text.upper()
        for rkey, rval in dict_codes.items():
            if rkey.find(ltext) != -1 or rval[0].upper().find(ltext) != -1 or rval[1].upper().find(ltext) != -1:
                code[rkey] = rval
        return code

    # Получение курса валют ЦБ на выбранную дату (по умолчанию: USD/RUB на ближайшую доступную дату)
    # (Формат дат %d/%m/%Y)
    def get_curr_rate(self, date=datetime.now().strftime('%d/%m/%Y'), code_from='USD', code_to='RUB'):
        # Проверка корректности даты
        try:
            date_valid = datetime.strptime(date, '%d/%m/%Y').date()
            if date_valid > datetime.now().date():
                raise Exc.DateFutureError(date)
        except ValueError:
            raise Exc.DateError(date)

        # Проверяем полученные коды валют
        if code_from != 'ALL':
            self.check_curr_code(code_from)
        if code_to != 'RUB':
            self.check_curr_code(code_to)

        if date:
            # req_text = self.req_curr_rate + '?date_req=' + date
            load_par = {'date_req': date}
        else:
            # req_text = self.req_curr_rate
            load_par = {}

        # req = requests.get(req_text)
        req = requests.get(self.req_curr_rate, params=load_par)
        root = etree.XML(req.content)
        req_dict = Convert.conv_xml_to_dict(root)
        text = list()
        text.append('Курс ЦБ: ' + root.attrib['Date'])
        if code_to != 'RUB':
            denom_from, denom_to = '', ''
        for data in req_dict.get("Valute"):
            if code_from == 'ALL':
                text.append(data.get('CharCode') + '/RUB - ' + data.get('VunitRate'))
            elif code_from == data.get('CharCode') and code_to == 'RUB':
                text.append(code_from + '/RUB - ' + data.get('VunitRate'))
                break
            elif data.get('CharCode') in (code_from, code_to) and code_to != 'RUB':
                if code_from == data.get('CharCode'):
                    denom_from = data.get('VunitRate').replace(',', '.')
                if code_to == data.get('CharCode'):
                    denom_to = data.get('VunitRate').replace(',', '.')
                if denom_from and denom_to:
                    denom_calc = str(round(float(denom_from) / float(denom_to), 4)).replace('.', ',')
                    text.append(f'{code_from}/{code_to} - {denom_calc}')
                    break
        result = '\n'.join(text) if len(text) > 1 else str(text[0])
        return result


    # Конвертация валюты
    def convert_currency(self, date=datetime.now().strftime('%d/%m/%Y'), volume=0, code_from='USD', code_to='RUB'):
        # Проверка корректности даты
        try:
            date_valid = datetime.strptime(date, '%d/%m/%Y').date()
            if date_valid > datetime.now().date():
                raise Exc.DateFutureError(date)
        except ValueError:
            raise Exc.DateError(date)

        # Проверка корректности введенного объема
        try:
            volume = int(volume)
        except ValueError:
            raise Exc.VolumeError(volume)

        # Проверяем полученные коды валют
        if code_from != 'USD':
            self.check_curr_code(code_from)
        if code_to != 'RUB':
            self.check_curr_code(code_to)

        if date:
            # req_text = self.req_curr_rate + '?date_req=' + date
            load_par = {'date_req': date}
        else:
            # req_text = self.req_curr_rate
            load_par = {}

        req = requests.get(self.req_curr_rate, params=load_par)
        root = etree.XML(req.content)
        req_dict = Convert.conv_xml_to_dict(root)
        if code_to != 'RUB':
            denom_from, denom_to = float(0), float(0)
        res_conv = ''
        for data in req_dict.get("Valute"):
            if code_from == data.get('CharCode') and code_to == 'RUB':
                res_conv = str(round(float(volume * float(data.get('VunitRate').replace(',', '.'))))).replace('.', ',')
                break
            elif data.get('CharCode') in (code_from, code_to) and code_to != 'RUB':
                if code_from == data.get('CharCode'):
                    denom_from = float(data.get('VunitRate').replace(',', '.'))
                if code_to == data.get('CharCode'):
                    denom_to = float(data.get('VunitRate').replace(',', '.'))
                if denom_from and denom_to:
                    res_conv = str(round(float(volume * denom_from / denom_to), 2)).replace('.', ',')
                    break
        result = {'date': date.replace('/', '.'),
                  'volume': volume,
                  'code_from': code_from,
                  'code_to': code_to,
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

        # req_text = f'{self.req_key_rate}?UniDbQuery.Posted=True&UniDbQuery.From={i_date_from}&UniDbQuery.To={i_date_to}'
        # req = requests.get(req_text)
        load_par = {'UniDbQuery.Posted': 'True', 'UniDbQuery.From': i_date_from, 'UniDbQuery.To': i_date_to}
        req = requests.get(self.req_key_rate, params=load_par)
        root = etree.HTML(req.content)
        elements = root.xpath('//table[@class="data"]')  # Находим все теги
        req_dict = Convert.conv_xml_to_dict(elements)
        result = {}
        for data in req_dict.get('table').get('tr'):
            if data.get('td'):
                date_key_rate, key_rate = data.get('td')[0], data.get('td')[1]
                result[date_key_rate] = key_rate
        return result


    # Загрузка новостей
    def load_news(self):
        self.news.clear()
        req = requests.get(self.req_news)
        root = etree.XML(req.content)
        req_dict = Convert.conv_xml_to_dict(root)
        url = ''
        for data in req_dict.get("Item"):
            if data.get("Url"):
                url_news = ''.join([self.req_cb, data.get("Url")]).replace(' ', '')
                self.news.append((data.get("@ID"), data.get("Date"), data.get("Title").rstrip(' '), url_news))

    # Получение новостей
    def get_news(self, i_date=''):
        self.load_news()
        res = []
        # Проверка корректности даты
        if i_date:
            try:
                datetime.strptime(i_date, '%d.%m.%Y').date()
            except ValueError:
                raise Exc.DateError(i_date)
        else:
            n = 15 if len(self.news) > 15 else len(self.news)
            for new in self.news[:n]:
                res.append(new)
        return res
