from datetime import datetime


# Исключения возникающие во время работы бота
class CBRException(Exception):
    pass


# Ошибка: не найден код валюты
class CodeError(CBRException):
    def __init__(self, i_code):
        self.message = f'{i_code} -> Указан неверный код!'


# Ошибка: введена неверная дата
class DateError(CBRException):
    def __init__(self, i_date):
        date = i_date.replace('/', '.')
        self.message = f'{date} -> Указана неверная дата!'


# Ошибка: дата не может превышать текущую
class DateFutureError(CBRException):
    def __init__(self, i_date):
        date = i_date.replace('/', '.')
        date_now = datetime.now().strftime('%d.%m.%Y')
        self.message = f'{date} -> Не должна превышать текущую дату {date_now}!'


# Ошибка: введен неверный объем
class VolumeError(CBRException):
    def __init__(self, i_volume):
        self.message = f'{i_volume} -> Указана неверная дата!'